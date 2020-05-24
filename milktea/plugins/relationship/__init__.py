from nonebot import on_command, CommandSession
from nonebot import on_natural_language, NLPSession, IntentCommand
from nonebot.helpers import render_expression as expr

from . import expressions as e
from .relationship import get_relation

__plugin_name__ = '亲戚关系计算器'


@on_command('relationship')
async def _(session: CommandSession):
    text = session.state.get('text')

    s = 1
    r = False
    t = 'default'

    # 输入关系
    if 'text' not in session.state:
        session.get('text', prompt=expr(e.INPPUT_MESSAGE))

    # 计算结果
    result = '、'.join(
        get_relation({
            'text': text,
            'sex': s,
            'reverse': r,
            'type': t
        }))

    # 输入格式不正确
    if result == '':
        session.finish(expr(e.FAULT_INSERT))

    # 返回结果
    reply = f'{expr(e.NAME)}{result}'
    session.finish(reply)


@on_natural_language(keywords={'亲戚', '称呼', '关系推算', '关系计算'})
async def _(session: NLPSession):
    return IntentCommand(80.0, 'relationship')
