from typing import Protocol, Union, Any, cast, Literal
from pydantic import BaseModel, Field, RootModel, model_validator
from torusdk.types.types import Ss58Address, GlobalParams
from typing_extensions import Self


class ProposalOpen(BaseModel):
    # votes_for: list[Ss58Address]
    # votes_against: list[Ss58Address]
    status: Literal["Open"] = "Open"
    stake_for: int
    stake_against: int


class ProposalRefused(BaseModel):
    status: Literal["Refused"] = "Refused"
    block: int
    stake_for: int
    stake_against: int


class ProposalAccepted(BaseModel):
    status: Literal["Accepted"] = "Accepted"
    block: int
    stake_for: int
    stake_against: int


class ProposalExpired(BaseModel):
    status: Literal["Expired"] = "Expired"


class ProposalStatus(
    RootModel[
        ProposalOpen | ProposalRefused | ProposalAccepted | ProposalExpired
    ]
):
    pass


class TransferDaoTreasury(BaseModel):
    account: Ss58Address
    amount: int


class Emission(BaseModel):
    recycling_percentage: int = Field(..., ge=0, le=100)
    treasury_percentage: int = Field(..., ge=0, le=100)


class GlobalCustom(BaseModel):
    pass


class ProposalData(BaseModel):
    global_params: GlobalParams | None = Field(None, alias="GlobalParams")
    emission: Emission | None = Field(None, alias="Emission")
    transfer_dao_treasury: TransferDaoTreasury | None = Field(
        None, alias="TransferDaoTreasury"
    )
    custom: GlobalCustom | None = Field(None, alias="GlobalCustom")


class Proposal(BaseModel):
    proposal_id: int = Field(..., alias="id")
    proposer: Ss58Address
    expiration_block: int
    status: ProposalAccepted | ProposalRefused | ProposalOpen | ProposalExpired
    metadata: str
    proposal_cost: int
    creation_block: int
    data: Union[GlobalParams, Emission, TransferDaoTreasury, GlobalCustom]

    # TODO: find a better way to do this and remove this cursed thing
    @model_validator(mode="before")
    @classmethod
    def unwrap_data(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary")
        data = cast(dict[Any, Any], data)
        if not data.get("data"):
            raise ValueError("Data must contain a 'data' key")
        if not isinstance(data["data"], dict):
            value = data["data"]
            data["data"] = {"data": value}
            return data
        if len(data.get("data")) != 1:
            raise ValueError("Data must contain only one key")
        data["data"] = [*data["data"].values()][0]
        return data

    @model_validator(mode="before")
    @classmethod
    def fix_status(cls, data: Any) -> Any:
        return extract_value(data, "status")


def extract_value(data: Any, key_to_extract: str):
    if not isinstance(data, dict):
        raise ValueError("Data must be a dictionary")
    data = cast(dict[Any, Any], data)
    if not data.get(key_to_extract):
        raise ValueError("Data must contain a 'data' key")
    if not isinstance(data[key_to_extract], dict):
        raise ValueError("Extracted key must contain a dictionary")
    if len(data.get(key_to_extract)) != 1:
        raise ValueError("Data must contain only one key")
    data[key_to_extract] = [*data[key_to_extract].values()][0]
    return data
