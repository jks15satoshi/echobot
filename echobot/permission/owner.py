import nonebot.adapters.cqhttp.exception as exception
from nonebot import require
from nonebot.adapters import Bot, Event
from nonebot.log import logger


async def is_owner(bot: Bot, event: Event) -> bool:
    self_id = event.self_id
    group_id = event.group_id

    parser = require('nonebot_plugin_styledstr').parser

    try:
        info = await bot.get_group_member_info(group_id=group_id,
                                               user_id=self_id)
    except (exception.NetworkError, exception.ActionFailed) as err:
        logger.error(err)
        await bot.send(event, parser.parse('permission.owner.check_err'))
    else:
        if info.get('role') == 'owner':
            return True
        else:
            await bot.send(event, parser.parse('permission.owner.check_false'))
            return False
