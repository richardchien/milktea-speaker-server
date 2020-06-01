from nonebot import IntentCommand, NLPSession, on_natural_language


@on_natural_language(keywords={'你是谁'})
async def who(session: NLPSession):
    return IntentCommand(100.0, 'echo', current_arg='我是奶茶！')
