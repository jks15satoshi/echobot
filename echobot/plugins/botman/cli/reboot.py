"""重启 Echobot (CLI)"""
from nonebot.adapters.cqhttp import Bot, Event
from nonebot.permission import SUPERUSER

from .glob import bot
from ..reboot import run_reboot


reboot = bot.command('reboot', permission=SUPERUSER)


@reboot.handle()
async def first_receive(bot: Bot, event: Event) -> None:
    await run_reboot(bot, event)
