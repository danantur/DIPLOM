import uuid
from typing import Annotated
from urllib import parse
from uuid import UUID

import deta
from fastapi import HTTPException, FastAPI, Request, Body, Depends
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi_sessions.backends.session_backend import SessionBackend, BackendError
from fastapi_sessions.frontends.implementations import CookieParameters, SessionCookie
from fastapi_sessions.session_verifier import SessionVerifier
from pydantic import BaseModel

from functions import get_data_by_token


class SessionData(BaseModel):
    key: str
    nickname: str
    token: str
    scopes: list
    session_id: UUID
    whispers: bool = True
    tag_random: bool = True


cookie_params = CookieParameters()

cookie = SessionCookie(
    cookie_name="cookie",
    identifier="general_verifier",
    auto_error=False,
    secret_key="somesecretkey",
    cookie_params=cookie_params,
)


class TokensStorage(SessionBackend[str, SessionData]):

    def __init__(self) -> None:
        self.data = deta.Base("tokens")

    async def create(self, _, data: SessionData):

        if len(self.data.fetch({"session_id": str(data.session_id)}).items) > 0:
            raise BackendError("create can't overwrite an existing session")

        data = data.copy(deep=True).dict()
        data["session_id"] = str(data["session_id"])

        self.data.put(data)

    async def read(self, session_id: UUID):
        data = self.data.fetch({"session_id": str(session_id)}).items
        if len(data) == 0:
            return

        return SessionData.parse_obj(data[0])

    async def update(self, _, data: SessionData) -> None:
        if self.data.get(data.key):
            data = data.copy(deep=True).dict()
            data["session_id"] = str(data["session_id"])
            self.data.put(data)
        else:
            raise BackendError("session does not exist, cannot update")

    async def delete(self, data: SessionData) -> None:
        self.data.update({"session_id": ""}, data.key)


backend = TokensStorage()


class BasicVerifier(SessionVerifier[UUID, SessionData]):
    def __init__(
        self,
        *,
        identifier: str,
        auto_error: bool,
        back: TokensStorage,
        auth_http_exception: HTTPException,
    ):
        self._identifier = identifier
        self._auto_error = auto_error
        self._backend = back
        self._auth_http_exception = auth_http_exception

    @property
    def identifier(self):
        return self._identifier

    @property
    def backend(self):
        return self._backend

    @property
    def auto_error(self):
        return self._auto_error

    @property
    def auth_http_exception(self):
        return self._auth_http_exception

    def verify_session(self, model: SessionData) -> bool:
        return model or False


verifier = BasicVerifier(
    identifier="general_verifier",
    auto_error=True,
    back=backend,
    auth_http_exception=HTTPException(status_code=403, detail="invalid session"),
)

verifier_none = BasicVerifier(
    identifier="general_verifier",
    auto_error=False,
    back=backend,
    auth_http_exception=HTTPException(status_code=403, detail="invalid session"),
)


auth_app = FastAPI()
templates = Jinja2Templates(directory="templates")


@auth_app.get("/approve")
async def auth_get(request: Request):
    return templates.TemplateResponse("app/auth.html", {"request": request})


@auth_app.get("/logout", dependencies=[Depends(cookie)])
async def auth_logout(request: Request, session_data: SessionData = Depends(verifier)):
    await backend.delete(session_data)
    response = RedirectResponse("/")
    cookie.delete_from_response(response)
    return response


@auth_app.post("/approve")
async def auth_post(auth_data: Annotated[str, Body(embed=True)]):
    auth_data = dict(parse.parse_qsl(auth_data))
    user = (await get_data_by_token(auth_data['access_token']))

    user_id = str(user["id"])
    nickname = user["login"]
    scopes = user["scopes"]

    response = JSONResponse({})

    if len(user_id) > 0:

        data = SessionData(key=user_id, nickname=nickname, token=auth_data['access_token'], scopes=scopes, session_id=uuid.uuid4())

        await backend.create(None, data)
        cookie.attach_to_response(response, data.session_id)

        return response

    else:

        response.status_code = 401
        return response
