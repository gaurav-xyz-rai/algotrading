import asyncio
import telegram

TOKEN = "7818824422:AAGBPE3-XWj04Oc-CQz8rETaFeAWg7u9GaE"
chat_id = '-4516284607'

# Channel ID Sample: -1001829542722

bot = telegram.Bot(token=TOKEN)

async def send_message(text, chat_id):
    async with bot:
        await bot.send_message(text=text, chat_id=chat_id)


async def send_document(document, chat_id):
    async with bot:
        await bot.send_document(document=document, chat_id=chat_id)


async def send_photo(photo, chat_id):
    async with bot:
        await bot.send_photo(photo=photo, chat_id=chat_id)


async def send_video(video, chat_id):
    async with bot:
        await bot.send_video(video=video, chat_id=chat_id)


async def main():
    # Sending a message
    await send_message(text='Test Message', chat_id=chat_id)

        # Sending a document
    # await send_document(document=open('/path/to/document.pdf', 'rb'), chat_id=chat_id)

    # Sending a photo
    # await send_photo(photo=open('/Users/gaurav_rai/codebase/repos/telegram/stockalert.png', 'rb'), chat_id=chat_id)

    # Sending a video
    # await send_video(video=open('path/to/video.mp4', 'rb'), chat_id=chat_id)


if __name__ == '__main__':
    asyncio.run(main())