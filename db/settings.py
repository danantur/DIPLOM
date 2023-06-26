from copy import deepcopy

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from twitchio import PartialUser

from config.config import user_settings, channel_settings, commands_settings
from db.db import async_session
from db.models import User, UserSetting, Channel, Setting, Command, CommandSetting


async def get_user(user: PartialUser):
    sets = deepcopy(user_settings)

    async with async_session.begin() as sess:
        sess: AsyncSession = sess

        u: User = await sess.get(User, user.id)

        if u.settings:
            for sett in u.settings:
                if sett.name in sets.keys():
                    sets[sett.name]["default"] = sett.value
                    print(sets[sett.name]["default"])

    if sets["calling"]["default"] == "nickname":
        sets["calling"]["default"] = user.name

    return sets


async def save_user(user: PartialUser, setts: dict):
    async with async_session.begin() as sess:
        sess: AsyncSession = sess

        for sett, value in setts.items():
            if sett in user_settings.keys():
                await sess.merge(
                    UserSetting(user_id=user.id, name=sett, value=type(user_settings[sett]["default"])(value))
                )


async def get_channel(channel: Channel):
    sets = deepcopy(channel_settings)

    async with async_session.begin() as sess:
        sess: AsyncSession = sess

        c: Channel = await sess.get(Channel, channel.user_id)

        if c.settings:
            for sett in c.settings:
                if sett.name in sets.keys():
                    sets[sett.name]["default"] = sett.value

    return sets


async def save_channel(channel: Channel, setts: dict):
    async with async_session.begin() as sess:
        sess: AsyncSession = sess

        for sett, value in setts.items():
            if sett in channel_settings.keys():
                await sess.merge(
                    Setting(channel_id=channel.user_id, name=sett, value=type(channel_settings[sett]["default"])(value))
                )


async def get_commands(channel: Channel):
    sets = deepcopy(commands_settings)

    async with async_session.begin() as sess:
        sess: AsyncSession = sess

        commands = (await sess.scalars(select(Command))).all()

        for cmd in commands:
            if cmd.settings:
                for sett in cmd.settings:
                    sets[cmd.name][sett.name] = sett.value

    return sets


async def save_commands(channel: Channel, setts: dict):

    async with async_session.begin() as sess:
        sess: AsyncSession = sess

        for k in setts.keys():
            if sess[k].get("description"):
                del setts[k]["description"]
            if sess[k].get("result"):
                del setts[k]["result"]

        for name, cmd in setts.items():

            for sett, value in cmd.items():
                if sett in ["enabled"]:
                    value = bool(value)
                if sett in ["kd"]:
                    value = int(value)
                await sess.merge(CommandSetting(
                    channel_id=channel.user_id, command_id=name, name=sett, value=value
                ))
