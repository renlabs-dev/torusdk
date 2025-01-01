"""
Server for Commune modules.
"""

import inspect
import random
from functools import partial
from typing import Any

import fastapi
from fastapi import APIRouter
from pydantic import BaseModel
from torustrateinterface import Keypair

from torus.key import check_ss58_address
from torus.module import _signer as signer
from torus.module._rate_limiters.limiters import (
    IpLimiterParams,
    StakeLimiterParams,
)
from torus.module.module import EndpointDefinition, Module, endpoint
from torus.module.routers.module_routers import (
    InputHandlerVerifier,
    IpLimiterVerifier,
    ListVerifier,
    StakeLimiterVerifier,
    build_route_class,
)
from torus.types import Ss58Address
from torus.util.memo import TTLDict


class ModuleServer:
    def __init__(
        self,
        module: Module,
        key: Keypair,
        max_request_staleness: int = 120,
        whitelist: list[Ss58Address] | None = None,
        blacklist: list[Ss58Address] | None = None,
        lower_ttl: int = 600,
        upper_ttl: int = 700,
        limiter: StakeLimiterParams | IpLimiterParams = StakeLimiterParams(),
        ip_blacklist: list[str] | None = None,
        use_testnet: bool = False,
    ) -> None:
        self._module = module
        self._app = fastapi.FastAPI()
        self.key = key
        self.max_request_staleness = max_request_staleness
        ttl = random.randint(lower_ttl, upper_ttl)
        self._blockchain_cache = TTLDict[str, list[Ss58Address]](ttl)
        self._ip_blacklist = ip_blacklist

        # to keep reference to add_to_blacklist and add_to_whitelist
        whitelist_: list[Ss58Address] = [] if whitelist is None else whitelist
        blacklist_: list[Ss58Address] = [] if blacklist is None else blacklist

        self._whitelist = whitelist_
        self._blacklist = blacklist_

        self._build_routers(use_testnet, limiter)

    def _build_routers(
        self, use_testnet: bool, limiter: StakeLimiterParams | IpLimiterParams
    ):
        input_handler = InputHandlerVerifier(
            check_ss58_address(self.key.ss58_address),
            self.max_request_staleness,
            self._blockchain_cache,
            self.key,
            use_testnet,
        )
        check_lists = ListVerifier(
            self._blacklist, self._whitelist, self._ip_blacklist
        )
        if isinstance(limiter, StakeLimiterParams):
            limiter_verifier = StakeLimiterVerifier(limiter)
        else:
            limiter_verifier = IpLimiterVerifier(limiter)

        # order of verifiers is extremely important
        verifiers = [check_lists, input_handler, limiter_verifier]
        route_class = build_route_class(verifiers)
        self._router = APIRouter(route_class=route_class)
        self.register_endpoints(self._router)
        self._app.include_router(self._router)

    def get_fastapi_app(self):
        return self._app

    def register_endpoints(self, router: APIRouter):
        endpoints = self._module.get_endpoints()
        for name, endpoint_def in endpoints.items():

            class Body(BaseModel):
                params: endpoint_def.params_model  # type: ignore

            async def async_handler(
                end_def: EndpointDefinition[Any, ...], body: Body
            ):
                return await end_def.fn(
                    self._module,
                    **body.params.model_dump(),  # type: ignore
                )

            def handler(end_def: EndpointDefinition[Any, ...], body: Body):
                return end_def.fn(self._module, **body.params.model_dump())  # type: ignore

            if inspect.iscoroutinefunction(endpoint_def.fn):
                defined_handler = partial(async_handler, endpoint_def)
            else:
                defined_handler = partial(handler, endpoint_def)
            router.post(f"/method/{name}")(defined_handler)

    def add_to_blacklist(self, ss58_address: Ss58Address):
        self._blacklist.append(ss58_address)

    def add_to_whitelist(self, ss58_address: Ss58Address):
        self._whitelist.append(ss58_address)


def main():
    class Amod(Module):
        @endpoint
        def do_the_thing(self, awesomness: int = 43):
            if awesomness > 60:
                msg = f"You're super awesome: {awesomness} awesomness"
            else:
                msg = f"You're not that awesome: {awesomness} awesomness"
            return {"msg": msg}

    a_mod = Amod()
    keypair = Keypair.create_from_mnemonic(signer.TESTING_MNEMONIC)
    server = ModuleServer(
        a_mod,
        keypair,
        blacklist=None,
    )
    app = server.get_fastapi_app()

    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)  # type: ignore


if __name__ == "__main__":
    main()
