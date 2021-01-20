import json
import time
from pathlib import Path
from typing import Dict, Union

import nonebot
from fastapi_utils.tasks import repeat_every
from nonebot.adapters.cqhttp import Bot
from nonebot.log import logger

from . import styled_string as styledstr


driver = nonebot.get_driver()
config = driver.config

_cooldown_events = {}

log = logger.opt(colors=True)
_LABEL = '<le><u>cooldown</u></le>'

# 备份文件路径。
# 默认配置文件备份于 .cache/cooldown.json 文件中，可以通过在 .env.* 文件中配置
# CD_BACKUP 配置项进行自定义。
_root = Path(f'{__file__}').parent.parent.parent.parent

try:
    _backup = config.cd_backup
    assert _backup
except AssertionError:
    BACKUP_FILE = _root / '.cache' / 'cooldown.json'
else:
    BACKUP_FILE = Path(f'{_root}/{_backup}')

if not BACKUP_FILE.parent.is_dir():
    BACKUP_FILE.parent.mkdir()

log.debug(f'{_LABEL} | Backup file path has been set as '
          f'{BACKUP_FILE.absolute()}')

# 自动移除过期事件时间。
# 默认自动移除时间为 3600 秒，可以通过在 .env.* 文件中配置
# CD_AUTOREMOVE_PERIOD 配置项进行自定义。
AUTOREMOVE_PERIOD = (config.cd_autoremove_period
                     if config.cd_autoremove_period
                     else 3600)
log.debug(f'{_LABEL} | Removing expired events every {AUTOREMOVE_PERIOD} '
          f'{"seconds" if AUTOREMOVE_PERIOD != 1 else "second"}')

# 自动备份数据时间。
# 默认自动移除时间为 180 秒，可以通过在 .env.* 文件中配置
# CD_AUTO_BACKUP_PERIOD 配置项进行自定义。
AUTO_BACKUP_PERIOD = (config.cd_auto_backup_period
                      if config.cd_auto_backup_period
                      else 180)
log.debug(f'{_LABEL} | Backing up data every {AUTO_BACKUP_PERIOD} '
          f'{"seconds" if AUTOREMOVE_PERIOD != 1 else "second"}')


@driver.on_startup
def restore() -> None:
    '''
    驱动启动时从备份文件恢复数据。
    '''
    global _cooldown_events

    if BACKUP_FILE.exists():
        with open(BACKUP_FILE) as file:
            _cooldown_events = json.load(file)

        log.debug(f'{_LABEL} | Restored data from file '
                  f'{BACKUP_FILE.absolute()}.')
    else:
        log.warning(f'{_LABEL} | Backup file {BACKUP_FILE.absolute()} does '
                    'not exist, skip restoring.')


@driver.on_startup
@repeat_every(wait_first=True, seconds=AUTOREMOVE_PERIOD)
def remove_expired_events() -> None:
    '''
    自动移除过期事件。

    自动移除时间间隔可通过配置项 `CD_AUTOREMOVE_PERIOD` 自定义，默认时间为 3600
    秒。
    '''
    global _cooldown_events
    events = _cooldown_events.values()

    count = 0
    current_time = int(time.time())

    for sub in events:
        for i, event in enumerate(sub):
            if event.get('expire_time') - current_time <= 0:
                sub.pop(i)
                count += 1

    _cooldown_events = {k: v for k, v in _cooldown_events.items() if v}

    log.info(f'{_LABEL} | Automatically removed expired cooldown events: '
             f'{count} {"events" if count != 1 else "event"} removed.')


@driver.on_startup
@repeat_every(wait_first=True, seconds=AUTO_BACKUP_PERIOD)
def auto_backup() -> None:
    '''
    自动备份数据。

    自动备份时间间隔可通过配置项 `CD_AUTO_BACKUP_PERIOD` 自定义，默认时间为 180
    秒。
    '''
    _backup()


@driver.on_bot_disconnect
async def backup_on_disconnect(bot: Bot) -> None:
    '''
    Bot 断开连接时备份数据。

    参数：
    - `bot: nonebot.adapters.cqhttp.Bot`：Bot 对象。
    '''
    _backup()


def set_event(token: str, duration: int, group=0, user=0) -> None:
    '''
    设置冷却事件。当同一事件组中存在较高优先级事件或存在重复事件正在生效时设置
    无效。

    参数：
    - `token: str`：事件组名称。
    - `duration: int`：冷却事件持续时间（秒）。

    关键字参数：
    - `group: int`：群组 ID。默认为 0，表示所有群组。
    - `user: int`：用户 ID。默认为 0，表示所有用户。
    '''
    global _cooldown_events

    current_time = int(time.time())

    # 存在全局事件
    is_exist_global = get_event(token).get('status')
    # 存在特定群组事件
    is_exist_group = get_event(token, group).get('status')
    # 存在重复事件
    is_exist_dubplicate = get_event(token, group, user).get('status')

    if not is_exist_global or not is_exist_group or not is_exist_dubplicate:
        if not _cooldown_events.get(token):
            _cooldown_events[token] = []

        event = {
            'group': group,
            'user': user,
            'expire_time': (current_time + duration
                            if duration >= 0 else -1)
        }
        _cooldown_events[token].append(event)
        log.debug(f'Cooldown event {token}({event}) added.')
    elif is_exist_global:
        log.warning(f'{_LABEL} | A valid global cooldown event is found, '
                    'setup interrupted')
    elif is_exist_group:
        log.warning(f'{_LABEL} | A valid cooldown event for entire specified '
                    'group is found, setup interrupted')
    elif is_exist_dubplicate:
        log.warning(f'{_LABEL} | A dubplicate valid global cooldown event is '
                    'found, setup interrupted')


def get_event(token: str, group=0, user=0) -> Dict[str, Union[bool, int]]:
    '''
    获取冷却事件状态。当存在较高优先级的事件正在生效时，返回较高优先级的事件状
    态。

    参数：
    - `token: str`：事件组名称。

    关键字参数：
    - `group: int`：群组 ID。默认为 0，表示所有群组。
    - `user: int`：用户 ID。默认为 0，表示所有用户。

    返回：
    - `Dict[str, Union[bool, int]]`：事件状态。包含两个字段：
        * `status: bool`：冷却状态，其中 `True` 表示冷却正在生效，反之则为
          `False`；
        * `remaining: int`：冷却剩余时间（秒），其中当 `status` 字段值为 
          `False` 时该字段值为 0。
    '''
    global _cooldown_events
    status = False
    remaining = 0

    current_time = int(time.time())

    if _cooldown_events.get(token):
        for event in _cooldown_events.get(token):
            event_group = event.get('group')
            event_user = event.get('user')
            expire_time = event.get('expire_time')

            # 冷却事件正在生效
            is_valid = expire_time - current_time >= 0
            # 冷却事件对全局有效
            is_global_effective = not event_group and not event_user
            # 冷却事件对指定群组有效
            is_group_effective = event_group == group and not event_user
            # 冷却事件对指定用户有效
            is_user_effective = event_group == group and event_user == user

            if ((is_global_effective or is_group_effective or
                 is_user_effective) and is_valid):
                status = True
                remaining = expire_time - current_time

    return {
        'status': status,
        'remaining': remaining
    }


def time_format(timestamp: int, format='std') -> str:
    '''
    格式化输出剩余时间信息。

    参数：
    - `timestamp: int`：时间戳。

    关键字参数：
    - `format: str`：格式名称，可用的格式名称有：
        * `std`：标准格式，以冒号分隔日、时、分、秒，例如 `05:04:03:02`；
        * `zh`：中文格式，例如 `5天4小时3分2秒`。
      默认值为 `std`。

    返回：
    - `str`：格式化的时间信息
    '''
    days = abs(timestamp) // 86400
    hours = (abs(timestamp) - days * 86400) // 3600
    minutes = (abs(timestamp) - days * 86400 - hours * 3600) // 60
    seconds = abs(timestamp) - days * 86400 - hours * 3600 - minutes * 60

    if format == 'std':
        return (f'{str(days).zfill(2)}:{str(hours).zfill(2)}:'
                f'{str(minutes).zfill(2)}:{str(seconds).zfill(2)}')
    elif format == 'zh':
        result = []
        if days:
            result.append(f'{days}天')
        if hours:
            result.append(f'{hours}小时')
        if minutes:
            result.append(f'{minutes}分')
        if seconds or (not days and not hours and not minutes):
            result.append(f'{seconds}秒')

        return ''.join(result)


def remove_event(token: str, group=0, user=0) -> None:
    '''
    移除冷却事件。

    参数：
    - `token: str`：事件组名称。

    关键字参数：
    - `group: int`：群组 ID。默认为 0，表示所有群组。
    - `user: int`：用户 ID。默认为 0，表示所有用户。
    '''
    global _cooldown_events
    events = _cooldown_events.get(token)

    for i, event in enumerate(events):
        if event.get('group') == group and event.get('user') == user:
            events.pop(i)
            log.info(f'{_LABEL} | Event {token}({event}) has been removed '
                     'manually.')


def _backup() -> None:
    '''
    备份冷却事件数据
    '''
    global _cooldown_events

    with open(BACKUP_FILE, 'w') as file:
        json.dump(_cooldown_events, file, indent=4)

    log.debug(f'{_LABEL} | Backed up cooldown data to file '
              f'{BACKUP_FILE.absolute()}.')
