import os

from fastapi import FastAPI, Depends
from fastapi.exceptions import HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi.responses import JSONResponse
from twitchio import Client

from auth import SessionData, cookie, verifier, auth_app, verifier_none

app = FastAPI()
app.mount("/auth", auth_app)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

client_secret = "b1n93u9hsi0vasv846stof65fm63v4"
client_id = "xmz75z68brtc2sommryre8m2i3vpet"

token = "xn1zzexlzl4184rgeov6zmdtj75a1m"

client = Client(token, client_secret="b1n93u9hsi0vasv846stof65fm63v4")

url = 'http://localhost:4200' \
    if 'localhost' in os.getenv('DETA_SPACE_APP_HOSTNAME', 'localhost') \
    else 'https://' + os.getenv('DETA_SPACE_APP_HOSTNAME')


@app.exception_handler(HTTPException)
async def auth_validation_error_handler(request: Request, exc: HTTPException):
    if exc.detail == "invalid session":
        return RedirectResponse(f"https://id.twitch.tv/oauth2/authorize?client_id={client_id}"
                                f"&redirect_uri={url}/auth/approve&response_type=token&scope=user"
                                f":read:email")
    else:
        return JSONResponse(*exc.args)


@app.get("/", dependencies=[Depends(cookie)])
async def landing(request: Request, session_data: SessionData = Depends(verifier_none)):
    if session_data:
        user = await client.create_user(int(session_data.key), session_data.nickname).fetch(force=True)
    else:
        user = None
    return templates.TemplateResponse("pages/landing.html",
                                      {"request": request,
                                       "user": user})


@app.get("/streamers", dependencies=[Depends(cookie)])
async def streamers(request: Request, session_data: SessionData = Depends(verifier_none)):
    streams = (await client.fetch_streams())[:15]
    for stream in streams:
        stream.thumbnail_url = stream.thumbnail_url.format(width=400, height=175)
    if session_data:
        user = await client.create_user(int(session_data.key), session_data.nickname).fetch(force=True)
    else:
        user = None
    return templates.TemplateResponse("pages/streamers.html",
                                      {"request": request,
                                       "streamers": streams,
                                       "user": user})


@app.get("/about", dependencies=[Depends(cookie)])
async def about(request: Request, session_data: SessionData = Depends(verifier_none)):
    if session_data:
        user = await client.create_user(int(session_data.key), session_data.nickname).fetch(force=True)
    else:
        user = None
    return templates.TemplateResponse("pages/about.html",
                                      {"request": request,
                                       "user": user})


@app.get("/profile", dependencies=[Depends(cookie)])
async def profile(request: Request, session_data: SessionData = Depends(verifier)):
    user = await client.create_user(int(session_data.key), session_data.nickname).fetch(force=True)
    return templates.TemplateResponse("app/profile.html",
                                      {"request": request,
                                       "page": "Профиль",
                                       "user": user})


@app.get("/admin", dependencies=[Depends(cookie)])
async def admin(request: Request, session_data: SessionData = Depends(verifier)):
    user = await client.create_user(int(session_data.key), session_data.nickname).fetch(force=True)
    return templates.TemplateResponse("app/admin.html",
                                      {"request": request,
                                       "page": "Админ-панель",
                                       "user": user})


@app.get("/commands", dependencies=[Depends(cookie)])
async def commands(request: Request, session_data: SessionData = Depends(verifier_none)):
    if session_data:
        user = await client.create_user(int(session_data.key), session_data.nickname).fetch(force=True)
    else:
        user = None
    return templates.TemplateResponse("app/commands.html",
                                      {"request": request,
                                       "user": user,
                                       "page": "Команды",
                                       "channel": "slonb0t"})
