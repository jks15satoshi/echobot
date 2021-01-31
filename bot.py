from pathlib import Path

import nonebot
from nonebot.adapters.cqhttp import Bot as CQHTTPBot
from nonebot.log import default_format, logger


LOG_PATH = Path(__file__).parent / 'logs'
if not LOG_PATH.is_dir():
    LOG_PATH.mkdir()

logger.add(f'{LOG_PATH}/error.log', rotation='00:00', diagnose=False,
           level='ERROR', format=default_format)

# Configurations
config = {
    'styledstr_respath': Path(__file__).parent / 'assets' / 'strings'
}

nonebot.init(**config)
app = nonebot.get_asgi()

driver = nonebot.get_driver()
driver.register_adapter('cqhttp', CQHTTPBot)

nonebot.load_plugins('echobot/plugins')
nonebot.load_plugin('nonebot_plugin_cooldown')
nonebot.load_plugin('nonebot_plugin_styledstr')
# Testing
# nonebot.load_plugins('echobot/test')

if __name__ == '__main__':
    nonebot.run(app='bot:app')
