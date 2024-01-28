import asyncio
from db.db import DB
from bot import TG_Bot
from db.storage import UserStorage
from config_reader import config
import aioschedule as schedule


async def init_db():
    db = DB(
        host=config.host.get_secret_value(),
        port=config.port.get_secret_value(),
        login=config.login.get_secret_value(),
        password=config.password.get_secret_value(),
        database=config.database.get_secret_value(),
    )
    await db.init()
    user_storage = UserStorage(db)
    await user_storage.init()
    return user_storage


async def check_schedule():
    while True:
        await schedule.run_pending()
        await asyncio.sleep(1)


async def main():
    user_storage = await init_db()
    tg_bot = TG_Bot(user_storage)
    await tg_bot.init()
    await tg_bot.start()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(check_schedule())
    loop.run_until_complete(main())
