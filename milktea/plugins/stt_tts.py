from milktea.ai_vendor import tencent_ai
from nonebot import (NoneBot, Event, Message, before_handle_message,
                     before_send_message)


@before_handle_message
async def stt(bot: NoneBot, event: Event):
    print('before_handle_message')
    for seg in event.message:
        if seg.type != 'record':
            continue
        speech_base64 = seg.data.get('base64')
        if speech_base64:
            text = await tencent_ai.stt(speech_base64)
            if text:
                seg.type = 'text'
                seg.data = {'text': text}
    event.message.reduce()
    print('converted msg:', event.message)


@before_send_message
async def tts(bot: NoneBot, event: Event, message: Message):
    print('before_send_message')
    for seg in message:
        if seg.type != 'text':
            continue
        text = seg.data.get('text')
        if text:
            speech_base64 = await tencent_ai.tts(text)
            if speech_base64:
                seg.type = 'record'
                seg.data = {'base64': speech_base64}
    message.reduce()
