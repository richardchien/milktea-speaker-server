from nonebot import init, run, load_builtin_plugins
from nonebot import on_command, CommandSession
from nonebot import on_natural_language, NLPSession, IntentCommand

import config

init(config)


@on_command('test')
async def test(session: CommandSession):
    await session.send('wow')


@on_natural_language(keywords={'你好'})
async def hello(session: NLPSession):
    return IntentCommand(100.0, 'echo', current_arg='你也好')


if __name__ == '__main__':
    load_builtin_plugins()
    run()
