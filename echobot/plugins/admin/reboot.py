'''
重启 Echobot
'''
import nonebot.exception as exception
from echobot.utils import confirm_intent
from nonebot import on_keyword
from nonebot.adapters.cqhttp import Bot, Event
from nonebot.log import logger
from nonebot.permission import SUPERUSER
from nonebot.rule import to_me
from nonebot.typing import T_State

from . import bot, str_parser


reboot = on_keyword('重启', rule=to_me(), permission=SUPERUSER, priority=1)
reboot_cli = bot.command('reboot', permission=SUPERUSER)


# 一般指令事件处理
@reboot.got('confirm', prompt=str_parser.parse('admin.reboot.prompt'))
async def handle(bot: Bot, event: Event, state: T_State) -> None:
    confirm = state.get('confirm').lower()

    if confirm_intent(confirm) == 'confirm':
        await _reboot(bot, event)
    elif confirm_intent(confirm) == 'decline':
        await reboot.finish(str_parser.parse('admin.reboot.cancel'))
    else:
        await reboot.finish(str_parser.parse('admin.reboot.failed'))


# CLI 指令事件处理
@reboot_cli.handle()
async def cli_first_receive(bot: Bot, event: Event) -> None:
    await _reboot(bot, event)


async def _reboot(bot: Bot, event: Event) -> None:
    '''
    执行重启（*需要 CQHTTP 实现提供 API 支持*）。

    参数:
    - `bot: nonebot.adapter.cqhttp.Bot`：Bot 对象
    - `event: nonebot.adapter.cqhttp.Event`：上报事件
    '''
    await bot.send(event, str_parser.parse('admin.reboot.on_reboot'))

    try:
        await bot.set_restart()
    except (exception.NetworkError, exception.ActionFailed) as err:
        logger.error(err)
        await bot.send(event, str_parser.parse('admin.reboot.on_err'))
