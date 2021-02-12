"""用户反馈"""
import nonebot.adapters.cqhttp.event as cqevent
from echobot.utils import confirm_intent
from nonebot.adapters.cqhttp import Bot, Event
from nonebot.typing import T_State

from .glob import bot, str_parser

feedback = bot.on_keyword({'反馈'})


@feedback.handle()
async def first_receive(bot: Bot, event: Event, state: T_State) -> None:
    message = str(event.message).split('反馈')
    contents = message[1].strip()

    if contents:
        state['contents'] = contents


@feedback.got('contents', prompt=str_parser.parse('bot.feedback.prompt'))
async def handle(bot: Bot, event: Event, state: T_State) -> None:
    contents = state.get('contents')
    if confirm_intent(contents) == 'decline':
        await feedback.finish(str_parser.parse('bot.feedback.cancel'))

    await send_report(bot, event, contents)
    await feedback.finish(str_parser.parse('bot.feedback.finish'))


async def send_report(bot: Bot, event: Event, contents: str) -> None:
    """
    发送反馈报告。

    参数：
    - `bot: nonebot.adapter.cqhttp.Bot`：Bot 对象。
    - `event: nonebot.adapter.cqhttp.Event`：上报事件。
    - `contents: str`：反馈内容。
    """
    info = await _get_feedback_info(bot, event)

    report = ''.join([
        '收到一则用户反馈：\n',
        f'“{contents}”\n'
        '\n'
        f'反馈者：{info.get("user")}\n'
        f'反馈途径：{info.get("method")}'
    ])

    for user in bot.config.superusers:
        await bot.send_private_msg(user_id=user, message=report)


async def _get_feedback_info(bot: Bot, event: Event) -> dict[str, str]:
    """
    获取反馈者信息

    参数：
    - `bot: nonebot.adapter.cqhttp.Bot`：Bot 对象。
    - `event: nonebot.adapter.cqhttp.Event`：上报事件。

    返回：
    - `dict[str, str]`：反馈者信息，包含两个字段 `user` 与 `method`，分别表示反
      馈者用户信息与反馈途径。
    """
    user_id = str(event.user_id)
    user_name = event.sender.nickname

    method = ''
    method_detail = ''
    if isinstance(event, cqevent.PrivateMessageEvent):
        method = '私聊消息'
    elif isinstance(event, cqevent.GroupMessageEvent):
        method = '群聊消息'

        group_id = event.group_id
        group_info = await bot.get_group_info(group_id=group_id)
        group_name = group_info.get('group_name')

        method_detail = f'，发送自 {group_name} ({group_id})'

    return {
        'user': f'{user_name} ({user_id})',
        'method': f'{method}{method_detail}'
    }
