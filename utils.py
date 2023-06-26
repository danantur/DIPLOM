from typing import Union

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette.exceptions import HTTPException

from db.db import async_session
from db.models import User, Channel


async def get(*args, **kwargs):
    async with httpx.AsyncClient() as client:
        result = await client.get(*args, **kwargs)
    return result


async def get_data_by_token(token: str):
    result = (await get("https://id.twitch.tv/oauth2/validate", headers={"Authorization": f"Bearer {token}"})).json()
    return {"id": result.get("user_id", ""), "login": result.get("login", ""), "scopes": result.get("scopes", [])}


async def retrieve_channel(channel: str) -> Union[Channel, None]:

    async with async_session.begin() as sess:
        sess: AsyncSession = sess

        u = (await sess.scalars(select(User).where(User.name == channel))).one()

        print(u.__dict__)

        if not u.channel:
            return None
        else:
            return u.channel

