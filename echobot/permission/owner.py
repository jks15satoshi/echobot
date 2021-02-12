import nonebot.adapters.cqhttp.exception as exception
from nonebot.adapters import Bot, Event
from nonebot.log import logger


async def is_owner(bot: Bot, event: Event) -> bool:
    self_id = event.self_id
    group_id = event.group_id

    try:
        info = await bot.get_group_member_info(group_id=group_id,
                                               user_id=self_id)
    except (exception.NetworkError, exception.ActionFailed) as err:
        logger.error(err)
        await bot.send(event, '检查 bot 信息失败')
    else:
        if info.get('role') == 'owner':
            return True
        else:
            await bot.send(event, '该 bot 未被设置为群主，无权执行该命令')
            return False
