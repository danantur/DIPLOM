from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.routing import Route, Mount

from bot.slon_bot import bot
from db.auth import *
from db.db import *
from web.backend_views import create_channel, edit_user, edit_channel
from web.front_views import *


async def setup_bot():
    get_event_loop().create_task(bot.start())


app = Starlette(
    routes=[
        Route("/", landing),
        Route("/streamers", streamers),
        Route("/about", about),
        Route("/profile", profile),
        Route("/admin/{channel:str}", admin),
        Route("/commands/{channel:str}", commands),
        Mount("/api", routes=[
            Route("/create_channel", create_channel),
            Route("/edit_user", edit_user, methods=["POST"]),
            Route("/edit_channel/{channel:str}", edit_channel, methods=["POST"])
        ]),
        Mount("/auth", routes=[
            Route("/", auth_redirect),
            Route("/approve", auth_get),
            Route("/approve", auth_post, methods=["POST"]),
            Route("/logout", auth_logout),
        ])
    ],
    on_startup=[on_start, setup_bot], on_shutdown=[on_clean],
    middleware=[
        Middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]),
        Middleware(SessionMiddleware, secret_key="(3QLX*z4yw6%(IR4"),
        Middleware(AuthenticationMiddleware, backend=BasicAuthBackend(), on_error=on_auth_error)
    ]
)
