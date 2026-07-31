import os
import json
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from aiogram import Bot

BOT_TOKEN = os.getenv("BOT_TOKEN", "8897929456:AAGcoM4VSvOnEWKG29Wt_GDufSnVf4s9bXI")
DB_CHANNEL_ID = int(os.getenv("DB_CHANNEL_ID", "-1004302302856"))

bot = Bot(token=BOT_TOKEN)
app = FastAPI()

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Кэш: ID игрока -> ID его сообщения в Telegram-канале
USER_MSG_MAP = {}

# НОВАЯ СТРУКТУРА: Точно совпадает с тем, что шлет фронтенд
class SaveRequest(BaseModel):
    userId: str
    playerData: Dict[str, Any]  # Гибкий словарь, примет любые данные из игры

@app.get("/")
def root():
    return {"status": "Tycoon DB Backend is running!", "channel": DB_CHANNEL_ID}

@app.post("/api/save")
async def save_progress(data: SaveRequest):
    try:
        player_dict = data.playerData
        json_str = json.dumps(player_dict, ensure_ascii=False, indent=2)
        
        # Безопасно достаем данные для красивого отображения (если их нет, ставим 0 или False)
        balance = player_dict.get("balance", 0)
        has_pc = player_dict.get("hasPC", False)
        seeds = player_dict.get("seeds", 0)
        harvest = player_dict.get("harvest", 0)
        nft_count = len(player_dict.get("nftList", []))
        
        # Оформление карточки игрока в Telegram-канале
        text = (
            f"👤 <b>ИГРОК</b> (ID: <code>{data.userId}</code>)\n"
            f"💰 <b>Баланс:</b> {round(balance, 2)} ₽\n"
            f"💻 <b>ПК:</b> {'Есть ✅' if has_pc else 'Нет ❌'}\n"
            f"🌱 <b>Семена:</b> {seeds} шт.\n"
            f"🌾 <b>Урожай:</b> {harvest} шт.\n"
            f"📦 <b>Кейсы/NFT:</b> {nft_count} шт.\n\n"
            f"⚙️ <b>ПОЛНЫЙ JSON СОХРАНЕНИЯ:</b>\n"
            f"<pre><code class=\"language-json\">{json_str}</code></pre>"
        )

        # Обновляем пост, если игрок уже сохранялся в эту сессию работы сервера
        if data.userId in USER_MSG_MAP:
            msg_id = USER_MSG_MAP[data.userId]
            await bot.edit_message_text(
                chat_id=DB_CHANNEL_ID,
                message_id=msg_id,
                text=text,
                parse_mode="HTML"
            )
        else:
            # Новый игрок — создаём новый пост
            msg = await bot.send_message(
                chat_id=DB_CHANNEL_ID,
                text=text,
                parse_mode="HTML"
            )
            USER_MSG_MAP[data.userId] = msg.message_id

        return {"status": "ok", "saved_id": data.userId}

    except Exception as e:
        print(f"Ошибка при сохранении в Telegram: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/load")
async def load_progress(userId: str):
    # Эта функция нужна, чтобы фронтенд не падал при загрузке (если ты сделаешь чтение из базы)
    # Пока мы просто возвращаем статус, что бэкенд жив.
    return {"status": "ok", "message": "Чтение из Telegram пока не реализовано, используем кэш браузера"}
          
