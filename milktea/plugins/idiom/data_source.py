import httpx

from nonebot import NoneBot


async def get_info_of_word(bot: NoneBot, word: str) -> str:
    async with httpx.AsyncClient() as client:
        resp = await client.post('http://v.juhe.cn/chengyu/query',
                                 data={
                                     'word': word,
                                     'key': bot.config.JUHE_IDIOM_API_KEY,
                                 })
    payload = resp.json()

    if not payload or not isinstance(payload, dict):  # 返回数据不正确
        return '抱歉，暂时无法查询哦'

    info = ''
    if payload['error_code'] == 0:
        try:
            info = payload['result']['chengyujs']
        except (KeyError, TypeError):
            pass

    return info or '哎呀，查询失败了'
