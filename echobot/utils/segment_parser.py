import re
from typing import Optional, Union


class SegmentParser(object):
    """
    消息段解析器。消息段类型遵循 OneBot v11 标准。

    参数：
    - `pattern: str`：解析器匹配规则。
    - `message: str`：解析消息内容。

    关键字参数：
    - `filter_pattern: str`：解析器匹配规则，用于过滤消息内容中的消息段。默认与
      `pattern` 相同。
    """

    def __init__(self, pattern: str, message: str, /,
                 filter_pattern: str = None) -> None:
        """初始化消息段解析器。"""
        self.__pattern = pattern
        self.__message = message
        self.__filter_pattern = filter_pattern if filter_pattern else pattern

    def get_data(self, *args) -> Optional[Union[str, tuple[str, ...],
                                                dict[str, str]]]:
        """
        获取消息段中的数据。

        参数：
        - `*args`：数据键名。

        返回：
        - `Optional[Union[str, tuple[str, ...], dict[str, str]]]`：消息段数据：
            - 当未获取到数据时无返回值；
            - 当未提供键名时以字典形式返回所有数据；
            - 当提供一个键名时返回该键对应的值；
            - 当提供多个键名时返回以元组形式返回每个键所对应的值，顺序与键名顺
              序一致。
          数据键名遵循 OneBot v11 标准所定义的参数名称。
        """
        data = (re.search(self.__pattern, self.__message).groupdict()
                if re.search(self.__pattern, self.__message)
                else None)

        if data is not None:
            if not args:
                return data
            elif len(args) == 1:
                return data.get(args[0])
            else:
                return (data.get(key) for key in args)

    def filter_segment(self, any_segments: bool = False) -> str:
        """
        过滤消息内容中的消息段。

        关键字参数：
        - `any_segments: bool`：过滤任意消息段，默认为 `False`。

        返回：
        - `str`：已被过滤的消息内容。
        """
        pattern = self.__filter_pattern if not any_segments else r'\[CQ:.*\]'
        return ''.join(re.split(pattern, self.__message))


class AtSegmentParser(SegmentParser):
    """
    提及用户（@用户）数据段解析器。

    参数：
    - `message: str`：解析消息内容。
    """

    def __init__(self, message: str) -> None:
        """初始化消息段解析器。"""
        super(AtSegmentParser, self).__init__(r'\[CQ:at,qq=(?P<qq>\d+|all)\]',
                                              message,
                                              r'\[CQ:at,qq=.*\]')
