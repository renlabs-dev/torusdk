import re
from typing import Optional

import typer
from rich.progress import track
from typer import Context

from torusdk._common import IPFS_REGEX
from torusdk.balance import to_nano
from torusdk.cli._common import (
    CustomCtx,
    make_custom_context,
    print_table_from_plain_dict,
)
from torusdk.client import TorusClient
from torusdk.key import local_key_adresses
from torusdk.misc import (
    local_keys_to_stakedbalance,
)
from torusdk.util import convert_cid_on_proposal

proposal_app = typer.Typer(no_args_is_help=True)


def get_valid_voting_keys(
    ctx: CustomCtx,
    client: TorusClient,
    threshold: int = 25000000000,  # 25 $TORUS
) -> dict[str, int]:
    local_keys = local_key_adresses(password_provider=ctx.password_manager)
    keys_stake = local_keys_to_stakedbalance(client, local_keys)
    keys_stake = {
        key: stake for key, stake in keys_stake.items() if stake >= threshold
    }
    return keys_stake


@proposal_app.command()
def vote_proposal(
    ctx: Context,
    proposal_id: int,
    key: Optional[str] = None,
    agree: bool = typer.Option(True, "--disagree"),
):
    """
    Casts a vote on a specified proposal. Without specifying a key, all keys on disk will be used.
    """
    context = make_custom_context(ctx)
    client = context.com_client()

    if key is None:
        context.info("Voting with all keys on disk...")
        delegators = client.get_power_users()
        keys_stake = get_valid_voting_keys(context, client)
        keys_stake = {
            key: stake
            for key, stake in keys_stake.items()
            if key not in delegators
        }
    else:
        keys_stake = {key: None}

    for voting_key in track(keys_stake.keys(), description="Voting..."):
        keypair = context.load_key(voting_key, None)
        try:
            client.vote_on_proposal(keypair, proposal_id, agree)
        except Exception as e:
            print(f"Error while voting with key {key}: ", e)
            print("Skipping...")
            continue


@proposal_app.command()
def unvote_proposal(ctx: Context, key: str, proposal_id: int):
    """
    Retracts a previously cast vote on a specified proposal.
    """
    context = make_custom_context(ctx)
    client = context.com_client()

    resolved_key = context.load_key(key, None)
    with context.progress_status(f"Unvoting on a proposal {proposal_id}..."):
        client.unvote_on_proposal(resolved_key, proposal_id)


@proposal_app.command()
def add_custom_proposal(ctx: Context, key: str, cid: str):
    """
    Adds a custom proposal.
    """
    context = make_custom_context(ctx)
    if not re.match(IPFS_REGEX, cid):
        context.error(f"CID provided is invalid: {cid}")
        exit(1)
    else:
        ipfs_prefix = "ipfs://"
        cid = ipfs_prefix + cid
    client = context.com_client()

    resolved_key = context.load_key(key, None)

    with context.progress_status("Adding a proposal..."):
        client.add_custom_proposal(resolved_key, cid)


@proposal_app.command()
def list_proposals(ctx: Context, query_cid: bool = typer.Option(True)):
    """
    Gets proposals
    """
    context = make_custom_context(ctx)
    client = context.com_client()

    with context.progress_status("Getting proposals..."):
        try:
            proposals = client.query_map_proposals()
            if query_cid:
                proposals = convert_cid_on_proposal(proposals)
        except IndexError:
            context.info("No proposals found.")
            return

    for proposal_id, batch_proposal in proposals.items():
        status = batch_proposal["status"]
        if isinstance(status, dict):
            batch_proposal["status"] = [*status.keys()][0]
        print_table_from_plain_dict(
            batch_proposal,
            [f"Proposal id: {proposal_id}", "Params"],
            context.console,
        )


@proposal_app.command()
def transfer_dao_funds(
    ctx: Context,
    signer_key: str,
    amount: float,
    cid_hash: str,
    dest: str,
):
    context = make_custom_context(ctx)

    if not re.match(IPFS_REGEX, cid_hash):
        context.error(f"CID provided is invalid: {cid_hash}")
        raise typer.Exit(code=1)

    ipfs_prefix = "ipfs://"
    cid = ipfs_prefix + cid_hash

    nano_amount = to_nano(amount)
    keypair = context.load_key(signer_key, None)
    dest = context.resolve_ss58(dest)

    client = context.com_client()
    client.add_transfer_dao_treasury_proposal(keypair, cid, nano_amount, dest)
