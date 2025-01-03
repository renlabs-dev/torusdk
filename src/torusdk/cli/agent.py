from typing import Any, Optional, cast

import typer
from typer import Context

from torusdk._common import intersection_update
from torusdk.balance import from_nano
from torusdk.cli._common import (
    make_custom_context,
    print_module_info,
    print_table_from_plain_dict,
    render_pydantic_table,
)
from torusdk.errors import ChainTransactionError
from torusdk.misc import get_governance_config, get_map_modules

agent_app = typer.Typer(no_args_is_help=True)


# TODO: refactor agent register CLI
# - key can be infered from name or vice-versa?
@agent_app.command(hidden=True)
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

    with context.progress_status(f"Registering Agent {name}..."):
        response = client.register_agent(
            resolved_key,
            name=name,
            url=url,
            metadata=metadata,
        )

        if response.is_success:
            context.info(f"Agent {name} registered")
        else:
            raise ChainTransactionError(response.error_message)  # type: ignore


@agent_app.command()
def list_applications(ctx: Context):
    """
    Lists all agent applications.
    """
    context = make_custom_context(ctx)
    client = context.com_client()

    with context.progress_status("Getting applications..."):
        applications = client.query_map_applications()
    if len(applications) == 0:
        context.info("No applications found.")
        return
    render_pydantic_table(
        [*applications.values()], context.console, title="Applications"
    )


@agent_app.command()
def add_application(
    ctx: Context,
    payer_key: str,
    application_key: str,
    data: str,
    removing: bool = False,
):
    """
    Adds an agent whitelist application.
    """
    context = make_custom_context(ctx)
    client = context.com_client()

    resolved_key = context.load_key(payer_key, None)
    application_addr = context.resolve_key_ss58(application_key, None)
    application_burn = get_governance_config(client).agent_application_cost
    confirm = context.confirm(
        f"{from_nano(application_burn)} tokens will be burned. Do you want to continue?"
    )
    if not confirm:
        context.info("Application addition cancelled")
        return
    with context.progress_status(f"Adding application {application_key}..."):
        client.add_application(
            key=resolved_key,
            application_key=application_addr,
            data=data,
            removing=removing,
        )
    context.info("Application added.")


@agent_app.command(hidden=True)
def deregister(ctx: Context, key: str):
    """
    Deregisters an agent from a subnet.
    """
    context = make_custom_context(ctx)
    client = context.com_client()

    resolved_key = context.load_key(key, None)

    with context.progress_status("Deregistering your agent..."):
        response = client.deregister_module(key=resolved_key)

        if response.is_success:
            context.info("Agent deregistered")
        else:
            raise ChainTransactionError(response.error_message)  # type: ignore


@agent_app.command(hidden=True)
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

    agents = get_map_modules(client, include_balances=False)
    modules_to_list = [value for _, value in agents.items()]

    module = next(
        (
            item
            for item in modules_to_list
            if item["key"] == resolved_key.ss58_address
        ),
        None,
    )

    if module is None:
        raise ValueError(f"Agent {name} not found")
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
    with context.progress_status("Updating Agent..."):
        response = client.update_agent(
            key=resolved_key,
            name=module["name"],
            url=module["url"],
            metadata=module["metadata"],
            staking_fee=module["staking_fee"],
            weight_control_fee=module["weight_control_fee"],
        )

    if response.is_success:
        context.info(f"Agent {key} updated")
    else:
        raise ChainTransactionError(response.error_message)  # type: ignore


@agent_app.command(hidden=True)
def info(ctx: Context, name: str, balance: bool = False):
    """
    Gets agent info
    """
    context = make_custom_context(ctx)
    client = context.com_client()

    with context.progress_status(f"Getting Agent {name}..."):
        agents = get_map_modules(client, include_balances=balance)
        modules_to_list = [value for _, value in agents.items()]

        module = next(
            (item for item in modules_to_list if item["name"] == name), None
        )

    if module is None:
        raise ValueError("Agent not found")

    general_module = cast(dict[str, Any], module)
    print_table_from_plain_dict(
        general_module, ["Params", "Values"], context.console
    )


@agent_app.command(name="list", hidden=True)
def inventory(ctx: Context, balances: bool = False):
    """
    Agents stats on the network.
    """
    context = make_custom_context(ctx)
    client = context.com_client()

    with context.progress_status("Getting agents..."):
        agents = cast(
            dict[str, Any],
            get_map_modules(client, include_balances=balances),
        )

    # Convert the values to a human readable format
    agent_to_list = [value for _, value in agents.items()]
    print_module_info(client, agent_to_list, context.console, "agents")
