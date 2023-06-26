from starlette.config import Config
from starlette.templating import Jinja2Templates

import yaml

config = Config(".env")
templates = Jinja2Templates(directory="web/templates")

with open('config/settings.yaml', 'r', encoding="utf-8") as file:
    settings = yaml.safe_load(file)
user_settings: dict = settings['user']
channel_settings: dict = settings['channel']
commands_settings: dict = settings['commands']
