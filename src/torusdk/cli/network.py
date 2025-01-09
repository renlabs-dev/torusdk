import typer
from typer import Context

import torusdk.balance as c_balance
from torusdk.cli._common import (
    make_custom_context,
    print_table_from_plain_dict,
    tranform_network_params,
)
from torusdk.misc import (
    get_global_params,
)

network_app = typer.Typer(no_args_is_help=True)


@network_app.command()
def last_block(ctx: Context, hash: bool = False):
    """
    Gets the last block
    """
    context = make_custom_context(ctx)
    client = context.com_client()

    info = "number" if not hash else "hash"

    block = client.get_block()
    block_info = None
    if block:
        block_info = block["header"][info]

    context.output(str(block_info))


@network_app.command()
def params(ctx: Context):
    """
    Gets global params
    """
    context = make_custom_context(ctx)
    client = context.com_client()

    with context.progress_status("Getting global network params ..."):
        global_params = get_global_params(client)
    global_params = global_params.model_dump()
    printable_params = tranform_network_params(global_params)
    print_table_from_plain_dict(
        printable_params, ["Global params", "Value"], context.console
    )


@network_app.command()
def registration_burn(
    ctx: Context,
    netuid: int,
):
    """
    Appraises the cost of registering a agent on the torus network.
    """

    context = make_custom_context(ctx)
    client = context.com_client()

    burn = client.get_burn()
    registration_cost = c_balance.from_rems(burn)
    context.info(
        f"The cost to register on a netuid: {netuid} is: {registration_cost} $TORUS"
    )
