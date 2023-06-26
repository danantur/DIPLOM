import asyncio
import random
from datetime import datetime, timedelta

import googletrans
from bs4 import BeautifulSoup
from langid import langid
from twitchio import Client, Channel
from twitchio.ext.commands import Bot, command

from config.config import config
from db import models
from db.db import async_session
from utils import get


def convert_minutes(num):
    order = ['м', 'ч', 'д']
    counter = [60, 60, 24]
    for x in range(3):
        if num < counter[x]:
            return "%3.1f %s" % (num, order[x])
        num /= counter[x]


class SlonBase(Bot):

    def __init__(self):
        super().__init__(config("OAUTH_TOKEN"), client_secret=config("CLIENT_SECRET"), prefix="!",
                         initial_channels=[], case_insensitive=True)

    async def event_ready(self):
        print("READY")
        async with async_session.begin() as sess:
            for name, cmd in self.commands.items():
                c = models.Command(name=name)
                await sess.merge(c)

    async def event_channel_joined(self, channel: Channel):
        print(channel.name)

    @command()
    async def help(self, ctx):
        await ctx.send(f"Список всех команд: https://slonb0t.site/commands/{ctx.channel.name}")

    @command(name="перевод")
    async def trans(self, ctx, message: str = None):
        if message is None:
            await ctx.send("cсылка со всеми ключами языков: https://pastebin.com/raw/nk1n1KxD")
        else:
            try:
                lang = message.split()[0]
                word = message.replace(f"{lang} ", "")
                lang = lang.split("-")
                if len(lang) > 1:
                    if len(lang) > 2:
                        await ctx.send("Языки описываются либо как {dest}, либо как {src}-{dest}")
                    lang_2, lang = lang
                else:
                    lang_2 = langid.classify(message)[0]
                    lang = lang[0]
                if lang in googletrans.LANGUAGES.keys():
                    result = googletrans.Translator().translate(word, src=lang_2, dest=lang).text
                else:
                    result = googletrans.Translator().translate(message, src=lang_2, dest="ru").text
                await ctx.send(f"{result}")
            except IndexError:
                raise await ctx.send("неправильно указаны параметры. Ссылка со всеми языками: "
                                     "https://pastebin.com/raw/nk1n1KxD")

    @command(name="статистика")
    async def stat(self, ctx, nickname: str):
        messages, time_count = (random.randint(100, 1000), random.randint(100, 1000))
        if nickname:
            await ctx.send(
                f"{nickname} написал всего сообщений: {messages}, проведено времени в чате: {convert_minutes(time_count)}")
        else:
            await ctx.send(
                f"вы написали всего сообщений: {messages}, проведено времени в чате: {convert_minutes(time_count)}")

    @command(name="курс")
    async def curs(self, ctx, count: int = None, user_cur: str = None):
        if user_cur is None:
            try:
                r = (await get("https://free.currconv.com/api/v7/convert?q=USD_RUB,EUR_RUB&compact=ultra&"
                               "apiKey=ac2f70eec83f27836644")).json()
                r2 = (await get("https://free.currconv.com/api/v7/convert?q=BTC_RUB,UAH_RUB&compact=ultra&"
                                "apiKey=ac2f70eec83f27836644")).json()
                today = (datetime.now() + timedelta(hours=3)).strftime("%d.%m")
                kurs = f"Курс валют на {today}: USD = {round(r['USD_RUB'], 2)} RUB | EUR = {round(r['EUR_RUB'], 2)} " \
                       f"RUB | BTC = {round(r2['BTC_RUB'])} RUB | UAH = {round(r2['UAH_RUB'], 2)} RUB"
                await ctx.send(kurs)
            except Exception:
                await ctx.send("не удаётся получить курс валют, попробуйте позже Waiting")
        elif count is not None:
            json_r = (await get(
                f"https://free.currconv.com/api/v7/convert?q={user_cur.replace('-', '_')}&compact=ultra&apiKey"
                f"=ac2f70eec83f27836644")).json()
            if len(json_r) == 0:
                await ctx.send("неправильно введены валюты. Вводите в международном формате (USD-RUB, RUB-JPY)")
            else:
                try:
                    print(json_r)
                    res = user_cur.replace("-", "_").upper()
                    one, two = user_cur.split("-")
                    await ctx.send(f"{count} {one.upper()} = "
                                   f"{round(json_r[res] * float(count), 2)} {two.upper()}")
                except KeyError:
                    await ctx.send(
                        "произошла ошибка конвертации. Скорее всего вы неправильно написали валюты. ~clever~")
                except IndexError:
                    await ctx.send(
                        "произошла ошибка конвертации. Скорее всего вы неправильно написали валюты. ~clever~")
                except Exception:
                    await ctx.send("не удаётся получить курс валют, попробуйте позже Waiting")
        else:
            await ctx.send("Неправильно введена команда!")

    @command()
    async def bban(self, ctx):
        await asyncio.sleep(1)
        await ctx.send(f"Массовый бан завершён, затронуто {random.randint(10, 30)} пользователей. SirMad")

    @command(name="анекдот")
    async def joke(self, ctx):
        url = "http://anecdotica.ru/"
        r = await get(url)
        ankdt = BeautifulSoup(r.content, "lxml").find("div", class_="item_text").get_text()
        await ctx.send(f"{ankdt[:400]} ~laugh~")

    @command(name="цитата")
    async def auf(self, ctx):
        r = await get("https://socratify.net/quotes/random")
        d = BeautifulSoup(r.content, "lxml").find("h1", class_="b-quote__text").get_text()
        while len(d) > 80:
            r = await get("https://socratify.net/quotes/random")
            d = BeautifulSoup(r.content, "lxml").find("h1", class_="b-quote__text").get_text()
        await ctx.send(f"{d} ~clever~")

    @command(name="рецепт")
    async def recipe(self, ctx):
        r = await get("http://culinar.ivest.kz/randomMenu")
        soup = BeautifulSoup(r.content, "lxml")
        recipe_name = soup.find("a", class_="rec_name").get_text()
        recipe_full = soup.find("div", class_="randome_recept_right").get_text()

        recipe_1 = recipe_full.partition("Способ приготовления:")[0]
        recipe_2 = recipe_full.partition("Способ приготовления:")[2]
        await ctx.send(f"{recipe_name} - {recipe_1}")
        await asyncio.sleep(1)
        await ctx.send(f"Способ приготовления: {recipe_2[:450]}")


client = Client.from_client_credentials(config("CLIENT_ID"), config("CLIENT_SECRET"))
bot = SlonBase()
