from typing import Generic

import deta
from fastapi_sessions.backends.session_backend import SessionModel, SessionBackend, BackendError
from fastapi_sessions.frontends.session_frontend import ID
from pydantic import BaseModel
from fastapi import HTTPException, FastAPI, Response, Depends
from uuid import UUID, uuid4

from fastapi_sessions.backends.implementations import InMemoryBackend
from fastapi_sessions.session_verifier import SessionVerifier
from fastapi_sessions.frontends.implementations import SessionCookie, CookieParameters


class SessionData(BaseModel):
    token: str


cookie_params = CookieParameters()

cookie = SessionCookie(
    cookie_name="cookie",
    identifier="general_verifier",
    auto_error=True,
    secret_key="DONOTUSE",
    cookie_params=cookie_params,
)


class TokensStorage(Generic[ID, SessionModel], SessionBackend[ID, SessionModel]):

    def __init__(self) -> None:
        self.data = deta.Base("tokens")

    async def create(self, session_id: ID, data: SessionModel):

        if self.data.get(str(session_id)):
            raise BackendError("create can't overwrite an existing session")

        self.data.put(data.copy(deep=True).dict(), str(session_id))

    async def read(self, session_id: ID):
        data = self.data.get(str(session_id))
        if not data:
            return

        return data

    async def update(self, session_id: ID, data: SessionModel) -> None:
        if self.data.get(str(session_id)):
            self.data.put(data.dict(), str(session_id))
        else:
            raise BackendError("session does not exist, cannot update")

    async def delete(self, session_id: ID) -> None:
        self.data.delete(str(session_id))


backend = TokensStorage[UUID, SessionData]()


class BasicVerifier(SessionVerifier[UUID, SessionData]):
    def __init__(
        self,
        *,
        identifier: str,
        auto_error: bool,
        back: TokensStorage[UUID, SessionData],
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
        return True


verifier = BasicVerifier(
    identifier="general_verifier",
    auto_error=True,
    back=backend,
    auth_http_exception=HTTPException(status_code=403, detail="invalid session"),
)

app = FastAPI()


@app.get("/create_session/{name}")
async def create_session(name: str, response: Response):

    session = uuid4()
    data = SessionData(token=name)

    await backend.create(session, data)
    cookie.attach_to_response(response, session)

    return f"created session for {name}"


@app.get("/whoami", dependencies=[Depends(cookie)])
async def whoami(session_data: SessionData = Depends(verifier)):
    return session_data


@app.post("/delete_session")
async def del_session(response: Response, session_id: UUID = Depends(cookie)):
    await backend.delete(session_id)
    cookie.delete_from_response(response)
    return "deleted session"
