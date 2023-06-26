import json
from urllib import parse

import twitchio
import typing

from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import requests
from starlette.authentication import AuthenticationBackend, AuthCredentials
from starlette.responses import JSONResponse, RedirectResponse

from bot.slon_bot import client
from config.config import config, templates
from db.db import async_session
from db.models import User
from utils import get_data_by_token


class SessionUser:

    def __init__(self, user_id: str, name: str, token: str, scopes: list):
        self.user_id = user_id
        self.name = name
        self.token = token
        self.scopes = scopes

    @property
    def is_authenticated(self) -> bool:
        return True


class SlonBotUser(SessionUser, twitchio.User):

    def __init__(self, user: SessionUser, twitch_user: twitchio.User, model: User,
                 is_channel: bool, managing: typing.List[User]):
        SessionUser.__init__(self, **user.__dict__)
        data = {
            prop.replace("image", "image_url")
            if prop != "name" else "login":
                getattr(twitch_user, prop)
                if prop != "created_at" else twitch_user.created_at.isoformat()
            for prop in twitch_user.__slots__}
        twitchio.User.__init__(self, twitch_user._http, data)
        self.model = model
        self.is_channel = is_channel
        self.managing = managing


class Request(requests.Request):
    @property
    def user(self) -> SlonBotUser:
        assert (
                "user" in self.scope
        ), "AuthenticationMiddleware must be installed to access request.user"
        return self.scope["user"]


def on_auth_error(request, exc: Exception):
    return JSONResponse({"error": str(exc)}, status_code=401)


class BasicAuthBackend(AuthenticationBackend):
    async def authenticate(self, conn) -> typing.Tuple["AuthCredentials", "SlonBotUser"]:

        scopes = []

        if not conn.session.get("token"):
            session = None
        else:
            session = SessionUser(**conn.session)

            is_channel = False
            managing = []

            async with async_session.begin() as sess:
                sess: AsyncSession = sess

                u: User = await sess.get(User, session.user_id)
                if not u:
                    u = User(id=session.user_id, name=session.name)
                    await sess.merge(u)

                if inspect(u).persistent:

                    if u.channel or u.authorized_channels:

                        scopes.append("USER_MANAGE")

                        if u.channel:
                            is_channel = True

                        if u.authorized_channels:
                            managing = u.authorized_channels

            user = (await client.create_user(int(session.user_id), session.name).fetch(session.token))
            session = SlonBotUser(session, user, u, is_channel, managing)
            scopes = scopes + conn.session["scopes"]

        return AuthCredentials(scopes), session


async def auth_get(request: Request):
    return templates.TemplateResponse("app/auth.html", {"request": request})


async def auth_logout(request: Request):
    request.session.clear()
    response = RedirectResponse("/")
    return response


async def auth_post(request: Request):
    auth_data = dict(parse.parse_qsl((await request.json())["auth_data"]))

    token = auth_data['access_token']

    user = (await get_data_by_token(token))

    user_id = str(user["id"])
    nickname = user["login"]
    scopes = user["scopes"]

    if len(user_id) > 0:

        data = SessionUser(user_id=user_id, name=nickname, token=token, scopes=scopes)

        request.session.update(**data.__dict__)

        redirect = "/profile"

        async with async_session.begin() as sess:
            sess: AsyncSession = sess

            u = await sess.get(User, data.user_id)
            if not u:
                u = User(id=data.user_id, name=data.name)

            if not u.channel and "moderation:read" in scopes and "channel:read:vips" in scopes:
                redirect = "/api/create_channel"

            await sess.merge(u)

        return JSONResponse({"redirect": redirect})

    else:

        return JSONResponse({}, 401)


async def auth_redirect(request: Request):
    scopes = request.query_params.get("scopes")
    if not scopes:
        scopes = "user:read:email"
    else:
        scopes = json.loads(scopes)
        scopes = "+".join(scopes + ["user:read:email"])
    return RedirectResponse(f"https://id.twitch.tv/oauth2/authorize?client_id={config('CLIENT_ID')}"
                            f"&redirect_uri={config('REDIRECT_URL')}&response_type=token&scope={scopes}")
