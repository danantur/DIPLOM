import datetime
import enum

from sqlalchemy import Column, String, ForeignKey, PickleType, DateTime, Enum
from sqlalchemy.orm import relationship

from db.db import Base


# USER


class User(Base):
    __tablename__ = "user_table"
    id = Column(String, primary_key=True)
    name = Column(String)
    settings = relationship("UserSetting", back_populates="user", lazy="selectin")
    channel = relationship("Channel", back_populates="user", uselist=False, lazy="selectin")
    authorized_channels = relationship("UserChannels", back_populates="user", lazy="selectin")


class UserSetting(Base):
    __tablename__ = "user_setting_table"
    user_id = Column(
        String, ForeignKey(
            "user_table.id", ondelete="CASCADE"
        ), primary_key=True
    )
    name = Column(String, primary_key=True)
    value = Column(PickleType)
    user = relationship("User", back_populates="settings", lazy="selectin")


# CHANNEL


class Channel(Base):
    __tablename__ = "channel_table"
    user_id = Column(
        String, ForeignKey(
            "user_table.id", ondelete="CASCADE"
        ), primary_key=True
    )
    started_at = Column(DateTime, default=datetime.datetime.now(
        datetime.timezone(datetime.timedelta(hours=3), name='МСК')
    ))
    user = relationship("User", back_populates="channel", lazy="selectin")
    settings = relationship("Setting", back_populates="channel", lazy="selectin")
    authorized_users = relationship("UserChannels", back_populates="channel", lazy="selectin")
    # cog_settings = relationship("CogSetting", back_populates="channel", lazy="selectin")
    command_settings = relationship("CommandSetting", back_populates="channel", lazy="selectin")


class Setting(Base):
    __tablename__ = "setting_table"
    channel_id = Column(
        String, ForeignKey(
            "channel_table.user_id", ondelete="CASCADE"
        ), primary_key=True
    )
    name = Column(String, primary_key=True)
    value = Column(PickleType)
    channel = relationship("Channel", back_populates="settings", lazy="selectin")


class UserChannels(Base):
    __tablename__ = "user_channel_table"

    class Roles(enum.Enum):
        mod = 2
        vip = 1

    user_id = Column(
        String, ForeignKey(
            "user_table.id", ondelete="CASCADE"
        ), primary_key=True
    )
    channel_id = Column(
        String, ForeignKey(
            "channel_table.user_id", ondelete="CASCADE"
        ), primary_key=True
    )
    type = Column(Enum(Roles))

    user = relationship("User", back_populates="authorized_channels", lazy="selectin")
    channel = relationship("Channel", back_populates="authorized_users", lazy="selectin")


# COMMANDS


# class Cog(Base):
#     __tablename__ = "cog_table"
#     name = Column(String, primary_key=True)
#     commands = relationship("Command", back_populates="cog", lazy="selectin")
#     settings = relationship("CogSetting", back_populates="cog", lazy="selectin")
#
#
# class CogSetting(Base):
#     __tablename__ = "cog_setting_table"
#     cog_id = Column(
#         String, ForeignKey(
#             "cog_table.name", ondelete="CASCADE", onupdate="CASCADE"
#         ), primary_key=True
#     )
#     channel_id = Column(
#         String, ForeignKey(
#             "channel_table.user_id", ondelete="CASCADE"
#         ), primary_key=True
#     )
#     name = Column(String, primary_key=True)
#     value = Column(PickleType)
#     cog = relationship("Cog", back_populates="settings", lazy="selectin")
#     channel = relationship("Channel", back_populates="cog_settings", lazy="selectin")


class Command(Base):
    __tablename__ = "command_table"
    name = Column(String, primary_key=True)
    # cog_id = Column(
    #     String, ForeignKey(
    #         "cog_table.name", ondelete="CASCADE", onupdate="CASCADE"
    #     ), primary_key=True
    # )
    # cog = relationship("Cog", back_populates="commands", lazy="selectin")
    settings = relationship("CommandSetting", back_populates="command", lazy="selectin")


class CommandSetting(Base):
    __tablename__ = "command_setting_table"
    command_id = Column(
        String, ForeignKey(
            "command_table.name", ondelete="CASCADE", onupdate="CASCADE"
        ), primary_key=True
    )
    channel_id = Column(
        String, ForeignKey(
            "channel_table.user_id", ondelete="CASCADE"
        ), primary_key=True
    )
    name = Column(String, primary_key=True)
    value = Column(PickleType)
    command = relationship("Command", back_populates="settings", lazy="selectin")
    channel = relationship("Channel", back_populates="command_settings", lazy="selectin")
