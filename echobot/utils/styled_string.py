from functools import reduce
from pathlib import Path

import nonebot
from nonebot.log import logger
import yaml


PATH = Path(__file__).parent.parent / 'assets' / 'strings' / 'styles'


def _get_style_preset() -> str:
    preset = nonebot.get_driver().config.style_preset

    if not preset:
        logger.warning('Cannot get the preset from configuration, use neutral '
                       'instead.')
        preset = 'neutral'

    return preset


def styledstr(tag: str) -> str:
    preset = _get_style_preset()
    with open(f'{PATH}/{preset}.yaml') as file:
        strings = yaml.safe_load(file)

    result = ''
    try:
        result = reduce(lambda key, val: key[val], tag.split('.'), strings)
    except KeyError as err:
        logger.error(err)
    else:
        logger.debug(f'Tag "{tag}" parsed as expected')

    return result
