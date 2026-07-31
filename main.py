import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from aiogram import Bot

# Данные подтягиваются из настроек Render (Environment Variables)
BOT_TOKEN = os.getenv("BOT_TOKEN", "8897929456:AAGcoM4VSvOnEWKG29Wt_GDufSnVf4s9bXI")
DB_CHANNEL_ID = int(os.getenv("DB_CHANNEL_ID", "0"))

bot = Bot(token=BOT_TOKEN)
app = FastAPI()

# Разрешаем веб-приложению (JS) делать запросы к нашему бэкенду без CORS-ошибок
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Кеш в памяти сервера: ID игрока -> ID его сообщения в закрытом канале
USER_MSG_MAP = {}

# Полная модель сохранения игрока
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
    return {"status": "CyberVerse DB Backend is running!"}

@app.post("/api/save")
async def save_progress(data: FullSaveData):
    try:
        player_dict = data.dict()
        json_str = json.dumps(player_dict, ensure_ascii=False, indent=2)
        
        # Визуальное оформление поста в Telegram-канале
        text = (
            f"👤 <b>ИГРОК:</b> @{data.username} (ID: <code>{data.user_id}</code>)\n"
            f"💰 <b>Баланс:</b> {round(data.balance, 2)}$\n"
            f"💻 <b>ПК:</b> {'Есть ✅' if data.hasPC else 'Нет ❌'}\n"
            f"🌿 <b>Грядки:</b> {len(data.plots)} шт.\n"
            f"📦 <b>Инвентарь:</b> {len(data.inventory)} предметов\n\n"
            f"⚙️ <b>ПОЛНЫЙ JSON СОХРАНЕНИЯ:</b>\n"
            f"<pre><code class=\"language-json\">{json_str}</code></pre>"
        )

        # Если игрок уже сохранялся в этой сессии — редактируем его существующий пост
        if data.user_id in USER_MSG_MAP:
            msg_id = USER_MSG_MAP[data.user_id]
            await bot.edit_message_text(
                chat_id=DB_CHANNEL_ID,
                message_id=msg_id,
                text=text,
                parse_mode="HTML"
            )
        else:
            # Новый игрок — публикуем новый пост
            msg = await bot.send_message(
                chat_id=DB_CHANNEL_ID,
                text=text,
                parse_mode="HTML"
            )
            USER_MSG_MAP[data.user_id] = msg.message_id

        return {"status": "ok", "saved_id": data.user_id}

    except Exception as e:
        print(f"Ошибка сохранения в Telegram: {e}")
        raise HTTPException(status_code=500, detail=str(e))
  
