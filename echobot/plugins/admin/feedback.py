'''
用户反馈
'''
import argparse

from echobot.utils import argv_parse, confirm_intent
from nonebot import on_keyword, require
from nonebot.adapters.cqhttp import Bot, Event
from nonebot.rule import to_me
from nonebot.typing import T_State

from . import bot, str_parser


feedback = on_keyword({'反馈'}, rule=to_me(), priority=1)
feedback_cli = bot.command('feedback')


# 一般指令事件处理
@feedback.handle()
async def first_receive(bot: Bot, event: Event, state: T_State) -> None:
    message = str(event.message).split('反馈')
    contents = message[1].strip()

    if contents:
        state['contents'] = contents


@feedback.got('contents', prompt=str_parser.parse('admin.feedback.prompt'))
async def handle(bot: Bot, event: Event, state: T_State) -> None:
    contents = state.get('contents')
    if confirm_intent(contents) == 'decline':
        await feedback.finish(str_parser.parse('admin.feedback.cancel'))

    report = await _feedback_report(contents, bot, event)
    await _report_send(bot, report)
    await feedback.finish(str_parser.parse('admin.feedback.finish'))


# CLI 指令事件处理
@feedback_cli.handle()
async def cli_first_receive(bot: Bot, event: Event) -> None:
    argv = argv_parse(str(event.message))

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('contents', type=str, nargs='?')
    args = parser.parse_args(argv)

    if args.contents:
        await feedback_cli.finish(str_parser.parse('admin.feedback.failed'))
    else:
        report = await _feedback_report(args.contents, bot, event)
        await _report_send(bot, report)
        await feedback_cli.finish(str_parser.parse('admin.feedback.finish'))


async def _feedback_report(contents: str, bot: Bot, event: Event) -> str:
    '''
    格式化反馈报告。

    参数:
    - `contents: str`：反馈内容。
    - `bot: nonebot.adapter.cqhttp.Bot`：Bot 对象
    - `event: nonebot.adapter.cqhttp.Event`：上报事件

    返回:
    - `str`：格式化后的反馈报告
    '''
    feedback_info = ''
    feedback_method = ''

    user_id = str(event.user_id)
    user_name = event.sender.nickname
    message_type = event.message_type
    sub_type = event.sub_type
    group_id = ''
    group_name = ''

    if message_type == 'group':
        group_id = str(event.group_id)
        _info = await bot.get_group_info(group_id=group_id)
        group_name = _info.get('group_name')

    if sub_type != 'anonymous':
        feedback_info = f'{user_name} ({user_id})'

    if message_type == 'private':
        feedback_method = '私信'
    elif message_type == 'group':
        if sub_type == 'anonymous':
            feedback_method = '匿名'
        elif sub_type == 'normal':
            feedback_method = f'群 {group_name} (ID: {group_id}) '

    return f'''收到一则用户反馈：
    反馈内容：{contents}
    反馈者：{feedback_info}，通过{feedback_method}发送
    '''.strip()


async def _report_send(bot: Bot, report: str) -> None:
    '''
    将反馈报告发送给全体 bot 管理员。

    参数:
    - `bot: nonebot.adapter.cqhttp.Bot`：Bot 对象
    - `report: str`：报告内容
    '''
    for user in bot.config.superusers:
        await bot.send_private_msg(user_id=user, message=report)
