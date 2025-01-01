import importlib.util
from typing import Any, Optional, cast

import typer
import uvicorn
from typer import Context

from torus._common import intersection_update
from torus.cli._common import (
    make_custom_context,
    print_module_info,
    print_table_from_plain_dict,
)
from torus.errors import ChainTransactionError
from torus.key import check_ss58_address
from torus.misc import get_map_modules
from torus.module._rate_limiters.limiters import (
    IpLimiterParams,
    StakeLimiterParams,
)
from torus.module.server import ModuleServer
from torus.types import Ss58Address

module_app = typer.Typer(no_args_is_help=True)


def list_to_ss58(str_list: list[str] | None) -> list[Ss58Address] | None:
    """Raises AssertionError if some input is not a valid Ss58Address."""

    if str_list is None:
        return None
    new_list: list[Ss58Address] = []
    for item in str_list:
        new_item = check_ss58_address(item)
        new_list.append(new_item)
    return new_list


# TODO: refactor module register CLI
# - key can be infered from name or vice-versa?
@module_app.command()
def register(
    ctx: Context,
    name: str,
    key: str,
    url: str,
    metadata: str,
):
    """
    Registers an agent.
    """
    context = make_custom_context(ctx)
    client = context.com_client()

    if metadata and len(metadata) > 59:
        raise ValueError("Metadata must be less than 60 characters")

    resolved_key = context.load_key(key, None)

    with context.progress_status(f"Registering Module {name}..."):
        response = client.register_agent(
            resolved_key,
            name=name,
            url=url,
            metadata=metadata,
        )

        if response.is_success:
            context.info(f"Module {name} registered")
        else:
            raise ChainTransactionError(response.error_message)  # type: ignore


@module_app.command()
def add_to_whitelist(ctx: Context, curator_key: str, agent_key: str):
    """
    Adds a module to a whitelist.
    """
    context = make_custom_context(ctx)
    client = context.com_client()

    resolved_curator_key = context.load_key(curator_key, None)
    resolved_module_key = context.resolve_key_ss58(agent_key, None)

    with context.progress_status(f"Adding Module {agent_key} to whitelist..."):
        client.add_to_whitelist(
            curator_key=resolved_curator_key, agent_key=resolved_module_key
        )
    context.info(f"Module {agent_key} added to whitelist")


@module_app.command()
def deregister(ctx: Context, key: str):
    """
    Deregisters a module from a subnet.
    """
    context = make_custom_context(ctx)
    client = context.com_client()

    resolved_key = context.load_key(key, None)

    with context.progress_status("Deregistering your module..."):
        response = client.deregister_module(key=resolved_key)

        if response.is_success:
            context.info("Module deregistered")
        else:
            raise ChainTransactionError(response.error_message)  # type: ignore


@module_app.command()
def update(
    ctx: Context,
    key: str,
    name: Optional[str] = None,
    url: Optional[str] = None,
    metadata: Optional[str] = None,
    staking_fee: Optional[int] = None,
    weight_control_fee: Optional[int] = None,
):
    """
    Update module with custom parameters.
    """

    context = make_custom_context(ctx)
    client = context.com_client()

    if metadata and len(metadata) > 59:
        raise ValueError("Metadata must be less than 60 characters")

    resolved_key = context.load_key(key, None)

    modules = get_map_modules(client, include_balances=False)
    modules_to_list = [value for _, value in modules.items()]

    module = next(
        (
            item
            for item in modules_to_list
            if item["key"] == resolved_key.ss58_address
        ),
        None,
    )

    if module is None:
        raise ValueError(f"Module {name} not found")
    module_params = {
        "name": name,
        "url": url,
        "metadata": metadata,
        "staking_fee": staking_fee,
        "weight_control_fee": weight_control_fee,
    }
    to_update = {
        key: value for key, value in module_params.items() if value is not None
    }
    updated_module = intersection_update(dict(module), to_update)
    module.update(updated_module)  # type: ignore
    with context.progress_status("Updating Module..."):
        response = client.update_agent(
            key=resolved_key,
            name=module["name"],
            url=module["url"],
            metadata=module["metadata"],
            staking_fee=module["staking_fee"],
            weight_control_fee=module["weight_control_fee"],
        )

    if response.is_success:
        context.info(f"Module {key} updated")
    else:
        raise ChainTransactionError(response.error_message)  # type: ignore


@module_app.command()
def serve(
    ctx: typer.Context,
    class_path: str,
    key: str,
    port: int = 8000,
    ip: Optional[str] = None,
    whitelist: Optional[list[str]] = None,
    blacklist: Optional[list[str]] = None,
    ip_blacklist: Optional[list[str]] = None,
    test_mode: Optional[bool] = False,
    request_staleness: int = typer.Option(120),
    use_ip_limiter: Optional[bool] = typer.Option(
        False, help=("If this value is passed, the ip limiter will be used")
    ),
    token_refill_rate_base_multiplier: Optional[int] = typer.Option(
        None,
        help=(
            "Multiply the base limit per stake. Only used in stake limiter mode."
        ),
    ),
):
    """
    Serves a module on `127.0.0.1` on port `port`. `class_path` should specify
    the dotted path to the module class e.g. `module.submodule.ClassName`.
    """
    context = make_custom_context(ctx)
    use_testnet = context.get_use_testnet()
    path_parts = class_path.split(".")
    match path_parts:
        case [*module_parts, class_name]:
            module_path = ".".join(module_parts)
            if not module_path:
                # This could do some kind of relative import somehow?
                raise ValueError(
                    f"Invalid class path: `{class_path}`, module name is missing"
                )
            if not class_name:
                raise ValueError(
                    f"Invalid class path: `{class_path}`, class name is missing"
                )
        case _:
            # This is impossible
            raise Exception(f"Invalid class path: `{class_path}`")

    try:
        module = importlib.import_module(module_path)
    except ModuleNotFoundError:
        context.error(f"Module `{module_path}` not found")
        raise typer.Exit(code=1)

    try:
        class_obj = getattr(module, class_name)
    except AttributeError:
        context.error(f"Class `{class_name}` not found in module `{module}`")
        raise typer.Exit(code=1)

    keypair = context.load_key(key, None)

    token_refill_rate = token_refill_rate_base_multiplier or 1
    limiter_params = (
        IpLimiterParams()
        if use_ip_limiter
        else StakeLimiterParams(token_ratio=token_refill_rate)
    )

    if whitelist is None:
        context.info(
            "WARNING: No whitelist provided, will accept calls from any key"
        )

    try:
        whitelist_ss58 = list_to_ss58(whitelist)
    except AssertionError:
        context.error("Invalid SS58 address passed to whitelist")
        exit(1)
    try:
        blacklist_ss58 = list_to_ss58(blacklist)
    except AssertionError:
        context.error("Invalid SS58 address passed on blacklist")
        exit(1)
    cast(list[Ss58Address] | None, whitelist)

    server = ModuleServer(
        class_obj(),
        keypair,
        whitelist=whitelist_ss58,
        blacklist=blacklist_ss58,
        max_request_staleness=request_staleness,
        limiter=limiter_params,
        ip_blacklist=ip_blacklist,
        use_testnet=use_testnet,
    )
    app = server.get_fastapi_app()
    host = ip or "127.0.0.1"
    uvicorn.run(app, host=host, port=port)  # type: ignore


@module_app.command()
def info(ctx: Context, name: str, balance: bool = False):
    """
    Gets module info
    """
    context = make_custom_context(ctx)
    client = context.com_client()

    with context.progress_status(f"Getting Module {name}..."):
        modules = get_map_modules(client, include_balances=balance)
        modules_to_list = [value for _, value in modules.items()]

        module = next(
            (item for item in modules_to_list if item["name"] == name), None
        )

    if module is None:
        raise ValueError("Module not found")

    general_module = cast(dict[str, Any], module)
    print_table_from_plain_dict(
        general_module, ["Params", "Values"], context.console
    )


@module_app.command(name="list")
def inventory(ctx: Context, balances: bool = False, netuid: int = 2):
    """
    Modules stats on the network.
    """
    context = make_custom_context(ctx)
    client = context.com_client()

    with context.progress_status("Getting agents..."):
        modules = cast(
            dict[str, Any],
            get_map_modules(client, include_balances=balances),
        )

    # Convert the values to a human readable format
    agent_to_list = [value for _, value in modules.items()]
    print_module_info(client, agent_to_list, context.console, netuid, "agents")
