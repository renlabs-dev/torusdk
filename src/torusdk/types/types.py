"""
Common types for the torus module.
"""

from enum import Enum
from typing import Any, NewType, TypedDict

from pydantic import (
    BaseModel,
    ValidationError,
    field_serializer,
    field_validator,
)

from torusdk.balance import BalanceUnit, format_balance, from_rems, to_rems

Ss58Address = NewType("Ss58Address", str)
"""Substrate SS58 address.

The `SS58 encoded address format`_ is based on the Bitcoin Base58Check format,
but with a few modification specifically designed to suite Substrate-based
chains.

.. _SS58 encoded address format:
    https://docs.substrate.io/reference/address-formats/
"""


# TODO: replace with dataclasses

# == Burn related
MinBurn = NewType("MinBurn", int)
MaxBurn = NewType("MaxBurn", int)
BurnConfig = NewType("BurnConfig", dict[MinBurn, MaxBurn])


class Rem:
    def __init__(self, value: int):
        self.value = value

    def __str__(self):
        return format_balance(self.value, BalanceUnit.j)

    def __repr__(self):
        return str(self.value)  # format_balance(self.value, BalanceUnit.j)

    def to_torus(self):
        return from_rems(self.value)

    @classmethod
    def from_torus(cls, torus: float):
        return cls(value=to_rems(torus))

    def __add__(self, other: "Rem"):
        return Rem(value=self.value + other.value)

    def __sub__(self, other: "Rem"):
        return Rem(value=self.value - other.value)

    def __mul__(self, other: "Rem | int | float"):
        if isinstance(other, Rem):
            return Rem(value=self.value * other.value)
        return Rem(value=int(self.value * other))

    def __truediv__(self, other: "Rem | int | float"):
        if isinstance(other, Rem):
            return Rem(int(self.value / other.value))
        return Rem(int(self.value / other))

    def __floordiv__(self, other: "Rem | int | float"):
        if isinstance(other, Rem):
            return Rem(self.value // other.value)
        return Rem(int(self.value // other))

    def __mod__(self, other: "Rem | int | float"):
        if isinstance(other, Rem):
            return Rem(self.value % other.value)
        return Rem(int(self.value % other))

    def __pow__(self, other: "Rem | int | float"):
        if isinstance(other, Rem):
            return Rem(self.value**other.value)
        return Rem(self.value**other)


class VoteMode(Enum):
    authority = "Authority"
    vote = "Vote"


class subnetDecryptionInfo(BaseModel):
    node_id: Ss58Address
    node_public_key: bytes
    block_assigned: int


class Fee(BaseModel):
    staking_fee: int
    weight_control_fee: int


class MinFee(BaseModel):
    min_staking_fee: int
    min_weight_control_fee: int


class Agent(BaseModel):
    key: Ss58Address
    name: str
    url: str
    metadata: str
    weight_penalty_factor: int
    registration_block: int
    fees: Fee


class AgentApplication(BaseModel):
    id: int
    payer_key: Ss58Address
    agent_key: Ss58Address
    data: str
    cost: int
    expires_at: int
    action: str
    status: str | dict[str, dict[str, bool]]


class DisplayGovernanceConfiguration(BaseModel):
    proposal_cost: float
    proposal_expiration: float
    vote_mode: VoteMode
    proposal_reward_treasury_allocation: float
    max_proposal_reward_treasury_allocation: float
    proposal_reward_interval: int


class GlobalGovernanceConfig(BaseModel):
    proposal_cost: int
    proposal_expiration: int
    agent_application_cost: int
    agent_application_expiration: int
    proposal_reward_treasury_allocation: int
    max_proposal_reward_treasury_allocation: int
    proposal_reward_interval: int


class DisplayGlobalGovernanceConfig(BaseModel):
    proposal_cost: float
    proposal_expiration: float
    agent_application_cost: float
    agent_application_expiration: float
    proposal_reward_treasury_allocation: float
    max_proposal_reward_treasury_allocation: float
    proposal_reward_interval: float


class BurnConfiguration(TypedDict):
    min_burn: int
    max_burn: int
    adjustment_alpha: int
    target_registrations_interval: int
    target_registrations_per_interval: int
    max_registrations_per_interval: int


def instantiate_rem(value: Any) -> Rem:
    if isinstance(value, int):
        return Rem(value=value)
    elif isinstance(value, Rem):
        return value
    else:
        raise ValidationError(f"Invalid value for Rem field: {value}")


class GlobalParams(BaseModel):
    # max
    max_name_length: int
    max_allowed_agents: int
    max_allowed_weights: int

    # mins
    min_name_length: int
    min_stake_per_weight: int
    min_weight_control_fee: int
    min_staking_fee: int

    dividends_participation_weight: int
    proposal_cost: int
    proposal_expiration: int
    agent_application_cost: int
    agent_application_expiration: int
    proposal_reward_treasury_allocation: int
    max_proposal_reward_treasury_allocation: int
    proposal_reward_interval: int

    to_rem = field_validator(
        "proposal_cost",
        "agent_application_cost",
        "max_proposal_reward_treasury_allocation",
        mode="after",
    )(instantiate_rem)

    @field_serializer(
        "proposal_cost",
        "agent_application_cost",
        "max_proposal_reward_treasury_allocation",
    )
    def from_rem(self, rem_value: Rem) -> int:
        return rem_value.value


# TODO: find a sane way of doing this
class OptionalNetworkParams(BaseModel):
    # max
    max_name_length: int | None
    min_name_length: int | None
    max_allowed_agents: int | None
    max_allowed_weights: int | None

    min_weight_control_fee: int | None
    min_staking_fee: int | None

    dividends_participation_weight: int | None
    proposal_cost: int | None
    proposal_expiration: int | None
    agent_application_cost: int | None
    agent_application_expiration: int | None
    proposal_reward_treasury_allocation: int | None
    max_proposal_reward_treasury_allocation: int | None
    proposal_reward_interval: int | None

    class Config:
        extra = "ignore"


# redundant "TypedDict" inheritance because of pdoc warns.
# see https://github.com/mitmproxy/pdoc/blob/26d40827ddbe1658e8ac46cd092f17a44cf0287b/pdoc/doc.py#L691-L692


class AgentInfo(TypedDict):
    name: str
    key: Ss58Address
    url: str
    stake_from: list[tuple[Ss58Address, int]]
    regblock: int  # block number
    stake: int
    metadata: str | None
    staking_fee: int
    weight_control_fee: int


class AgentInfoWithBalance(AgentInfo):
    balance: int


class AgentInfoWithOptionalBalance(AgentInfo):
    balance: int | None
