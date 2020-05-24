import random

import httpx

from nonebot import NoneBot


async def get_joke(bot: NoneBot):
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            'http://v.juhe.cn/joke/content/text.php',
            # 注：这里请使用 POST 请求，官网上说的 GET 请求无效
            data={
                'key': bot.config.JUHE_JOKE_API_KEY,
                'page': 1,
                'pagesize': 20,
            })

    payload = resp.json()
    if not payload or not isinstance(payload, dict):
        return '抱歉，没有新段子了～'

    info = ''
    if payload['error_code'] == 0:
        try:
            jokes = [j['content'] for j in payload['result']['data']]
            if jokes:
                info = random.choice(jokes)
                info = info.replace('&nbsp;', '').strip()
        except KeyError:
            pass

    return info or '暂时没有笑话可以讲哦'
