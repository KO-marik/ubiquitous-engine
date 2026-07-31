import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from aiogram import Bot

# Вшиваем твои данные по умолчанию (при желании их можно переопределить через Render Environment)
BOT_TOKEN = os.getenv("BOT_TOKEN", "8897929456:AAGcoM4VSvOnEWKG29Wt_GDufSnVf4s9bXI")
DB_CHANNEL_ID = int(os.getenv("DB_CHANNEL_ID", "-1004302302856"))

bot = Bot(token=BOT_TOKEN)
app = FastAPI()

# Настройка CORS, чтобы игра (index.html) могла делать запросы с любого сайта/хостинга
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Кэш прямо в памяти сервера: ID игрока -> ID его сообщения в Telegram-канале
USER_MSG_MAP = {}

# Структура всех данных игрока
class FullSaveData(BaseModel):
    user_id: int
    username: str
    balance: float
    level: int
    hasPC: bool
    warehouseSlots: int
    unclaimedMining: float
    seedsInventory: dict
    plots: list
    inventory: list

@app.get("/")
def root():
    return {"status": "CyberVerse DB Backend is running!", "channel": DB_CHANNEL_ID}

@app.post("/api/save")
async def save_progress(data: FullSaveData):
    try:
        player_dict = data.dict()
        json_str = json.dumps(player_dict, ensure_ascii=False, indent=2)
        
        # Оформление карточки игрока в Telegram-канале
        text = (
            f"👤 <b>ИГРОК:</b> @{data.username} (ID: <code>{data.user_id}</code>)\n"
            f"💰 <b>Баланс:</b> {round(data.balance, 2)}$\n"
            f"💻 <b>ПК:</b> {'Есть ✅' if data.hasPC else 'Нет ❌'}\n"
            f"🌿 <b>Грядок:</b> {len(data.plots)} шт.\n"
            f"📦 <b>Предметов в инвентаре:</b> {len(data.inventory)} шт.\n\n"
            f"⚙️ <b>ПОЛНЫЙ JSON СОХРАНЕНИЯ:</b>\n"
            f"<pre><code class=\"language-json\">{json_str}</code></pre>"
        )

        # Если этот игрок уже сохранялся во время работы сервера — обновляем его прошлый пост
        if data.user_id in USER_MSG_MAP:
            msg_id = USER_MSG_MAP[data.user_id]
            await bot.edit_message_text(
                chat_id=DB_CHANNEL_ID,
                message_id=msg_id,
                text=text,
                parse_mode="HTML"
            )
        else:
            # Новый игрок — создаём новый пост в закрытом канале
            msg = await bot.send_message(
                chat_id=DB_CHANNEL_ID,
                text=text,
                parse_mode="HTML"
            )
            # Запоминаем ID сообщения для этого игрока
            USER_MSG_MAP[data.user_id] = msg.message_id

        return {"status": "ok", "saved_id": data.user_id}

    except Exception as e:
        print(f"Ошибка при сохранении в Telegram: {e}")
        raise HTTPException(status_code=500, detail=str(e))
      
