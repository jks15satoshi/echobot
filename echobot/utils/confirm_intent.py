from typing import Optional


def confirm_intent(reply: str) -> Optional[str]:
    _reply = reply.lower()

    POSITIVE = {'确认', '确定', '是', 'yes', 'y'}
    NEGATIVE = {'取消', '不', '否', 'no', 'n'}

    if _reply in POSITIVE:
        return 'confirm'
    elif _reply in NEGATIVE:
        return 'decline'
