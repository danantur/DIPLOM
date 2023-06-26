from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.datastructures import FormData
from starlette.exceptions import HTTPException
from starlette.responses import RedirectResponse, Response

from bot.slon_bot import bot
from db.auth import Request
from db.db import async_session
from db.models import User, Channel, UserChannels
from db.settings import save_user, save_channel
from utils import retrieve_channel
from web.front_views import req


def process_form(f: FormData):
    data = {}
    for key, value in dict(f).items():
        if value in ['true', 'false']:
            data[key] = True if value == 'true' else False
        else:
            data[key] = value
    return data


async def edit_user(request: Request):
    async with request.form() as f:
        await save_user(request.user, process_form(f))
    return Response()


async def edit_channel(request: Request):

    channel = request.path_params['channel']

    chan = await retrieve_channel(channel)
    if chan:
        async with request.form() as f:
            await save_channel(chan, process_form(f))
    else:
        raise HTTPException(status_code=401)

    return Response()


@req(["user:read:email"])
async def create_channel(request: Request):
    async with async_session.begin() as sess:

        sess: AsyncSession = sess

        u: User = await sess.get(User, request.user.user_id)

        if not u.channel:

            chan = Channel(user_id=u.id)

            if "moderation:read" in request.user.scopes and "channel:read:vips" in request.user.scopes:

                authorized_users = \
                    [UserChannels(user=User(id=str(usr.id), name=usr.name), channel=chan, type=UserChannels.Roles.mod)
                     for usr in (await request.user.fetch_moderators(request.user.token))] + \
                    [UserChannels(user=User(id=str(usr.id), name=usr.name), channel=chan, type=UserChannels.Roles.vip)
                     for usr in (await request.user.fetch_channel_vips(request.user.token))]

                chan.authorized_users = authorized_users

            u.channel = chan

            await bot.join_channels([u.name])

        await sess.merge(u)

    return RedirectResponse(f"/admin/{request.user.name}")
