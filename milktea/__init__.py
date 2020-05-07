from nonebot import *


@before_handle_message
async def stt(bot: NoneBot, event: Event):
    event.message.append(MessageSegment.text('\n\n----处理前'))


@before_send_message
async def tts(bot: NoneBot, event: Event, message: Message):
    message.append(MessageSegment.text('\n\n----发送前'))


@on_command('test')
async def test(session: CommandSession):
    await session.send('wow')


@on_natural_language(keywords={'你好'})
async def hello(session: NLPSession):
    return IntentCommand(100.0, 'echo', current_arg='你也好')


def main(config):
    init(config)
    load_builtin_plugins()
    run()
