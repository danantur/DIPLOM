import typing

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.authentication import requires
from starlette.exceptions import HTTPException
from starlette.responses import Response
from twitchio import ChannelInfo

from bot.slon_bot import client
from config.config import templates, user_settings

from db.auth import Request
from db.db import async_session
from db.models import User, Channel
from db.settings import get_user, get_channel, get_commands
from utils import retrieve_channel


def req(scopes: typing.Union[str, typing.Sequence[str]]):

    if "USER_MANAGE" not in scopes:
        return requires(scopes, redirect="auth_redirect")
    else:
        return requires(scopes)


async def landing(request: Request):

    return templates.TemplateResponse(
        "pages/landing.html",
        {
            "request": request
        }
    )


async def streamers(request: Request):

    streams = (await client.fetch_streams())[:15]

    for stream in streams:
        stream.thumbnail_url = stream.thumbnail_url.format(width=400, height=175)

    return templates.TemplateResponse(
        "pages/streamers.html",
        {
            "request": request,
            "streamers": streams
        }
    )


async def about(request: Request):
    return templates.TemplateResponse(
        "pages/about.html",
        {
            "request": request
        }
    )


@req(["user:read:email"])
async def profile(request: Request):

    settings = await get_user(request.user)

    return templates.TemplateResponse(
        "app/profile.html",
        {
            "request": request,
            "page": "Профиль",
            "settings": settings
        }
    )


@req(["user:read:email", "USER_MANAGE"])
async def admin(request: Request):

    channel = request.path_params['channel']

    chan = await retrieve_channel(channel)

    if not chan:
        raise HTTPException(status_code=404)

    settings = await get_channel(chan)
    command_settings = await get_commands(chan)

    return templates.TemplateResponse(
        "app/admin.html",
        {
            "request": request,
            "page": "Админ-панель",
            "channel": channel,
            "settings": settings,
            "commands": command_settings
        }
    )


async def commands(request: Request):
    channel = request.path_params['channel']

    chan = await retrieve_channel(channel)

    if not chan:
        raise HTTPException(status_code=404)

    command_settings = await get_commands(chan)

    return templates.TemplateResponse(
        "app/commands.html",
        {
            "request": request,
            "page": "Команды",
            "channel": channel,
            "commands": command_settings
        }
    )
