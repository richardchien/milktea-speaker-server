from milktea.ai_vendor import tencent_ai
from nonebot import on_command, CommandSession, IntentCommand
from nonebot import on_natural_language, NLPSession
from nonebot.helpers import context_id, render_expression as expr
from nonebot.log import logger
from nonebot.message import Message, escape
from . import expressions as e

__plugin_name__ = '智能聊天'


@on_command('ai_chat', aliases=('聊天', '对话'))
async def ai_chat(session: CommandSession):
    message = session.get('message', prompt=expr(e.I_AM_READY))

    ctx_id = context_id(session.event)

    tmp_msg = Message(message)
    text = tmp_msg.extract_plain_text()

    # call ai_chat api
    reply = await tencent_ai.chat(text, ctx_id)
    logger.debug(f'Got AI reply: {reply}')

    if reply:
        session.finish(escape(reply))
    else:
        session.finish(expr(e.I_DONT_UNDERSTAND))


@ai_chat.args_parser
async def _(session: CommandSession):
    if session.current_key == 'message':
        text = session.current_arg_text.strip()
        if ('拜拜' in text or '再见' in text) and len(text) <= 4:
            session.finish(expr(e.BYE_BYE))
            return
        session.state[session.current_key] = session.current_arg


@on_natural_language()
async def _(session: NLPSession):
    return IntentCommand(60.1, 'ai_chat', args={'message': session.msg})


@on_natural_language()
async def anything(session: NLPSession):
    return IntentCommand(60.0, 'echo', current_arg='你在说什么？')
