import asyncio
import logging
import os
import json

import google.generativeai as genai
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, Document
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
HR_CHAT_ID = os.getenv("HR_CHAT_ID")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

class CandidateFlow(StatesGroup):
    waiting_name = State()
    waiting_position = State()
    waiting_cv = State()

async def analyze_cv(file_path, position):
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")
    with open(file_path, "rb") as f:
        pdf_bytes = f.read()
    prompt = f'Siz HR mutaxassisisiz. CV ni "{position}" uchun baholang. FAQAT JSON: {{"score": 0-100, "summary": "baho", "strengths": "kuchli", "weaknesses": "zaif", "recommendation": "xulosa"}}'
    response = model.generate_content([{"mime_type": "application/pdf", "data": pdf_bytes}, prompt])
    raw = response.text.strip().replace("```json","").replace("```","").strip()
    return json.loads(raw)
    async def write_to_sheets(name, position, username, result):
    scopes = ["https://www.googleapis.com/auth/spreadsheets","https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(json.loads(GOOGLE_CREDENTIALS_JSON), scopes=scopes)
    sheet = gspread.authorize(creds).open_by_key(GOOGLE_SHEET_ID).sheet1
    if sheet.cell(1,1).value != "Sana":
        sheet.insert_row(["Sana","Ism","Lavozim","Telegram","Ball","Xulosa","Kuchli","Zaif","Tavsiya"],1)
    sheet.append_row([datetime.now().strftime("%d.%m.%Y %H:%M"),name,position,f"@{username}",result.get("score",0),result.get("summary",""),result.get("strengths",""),result.get("weaknesses",""),result.get("recommendation","")])

@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await message.answer("👋 *Blitz HR Bot*ga xush kelibsiz!\n\nIsmingiz va familiyangizni kiriting:", parse_mode="Markdown")
    await state.set_state(CandidateFlow.waiting_name)

@dp.message(CandidateFlow.waiting_name)
async def get_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer(f"✅ Salom *{message.text}*!\n\nQaysi lavozimga ariza topshiryapsiz?", parse_mode="Markdown")
    await state.set_state(CandidateFlow.waiting_position)

@dp.message(CandidateFlow.waiting_position)
async def get_position(message: Message, state: FSMContext):
    await state.update_data(position=message.text)
    await message.answer(f"📄 CV ni yuboring.\n\n⚠️ Faqat *PDF*!", parse_mode="Markdown")
    await state.set_state(CandidateFlow.waiting_cv)

@dp.message(CandidateFlow.waiting_cv, F.document)
async def get_cv(message: Message, state: FSMContext):
    document = message.document
    if not document.file_name.lower().endswith(".pdf"):
        await message.answer("❌ Faqat *PDF* yuboring!", parse_mode="Markdown")
        return
    await message.answer("⏳ CV tahlil qilinmoqda, 20-30 sekund kuting...")
    data = await state.get_data()
    file = await bot.get_file(document.file_id)
    file_path = f"/tmp/{document.file_name}"
    await bot.download_file(file.file_path, file_path)
    try:
        result = await analyze_cv(file_path, data["position"])
        await write_to_sheets(data["name"], data["position"], message.from_user.username or "noma'lum", result)
        e = "🟢" if result["score"]>=70 else "🟡" if result["score"]>=40 else "🔴"
        await message.answer(f"✅ *Natija*\n\n👤 {data['name']}\n💼 {data['position']}\n{e} *{result['score']}%*\n\n📊 {result['summary']}\n\n💪 {result['strengths']}\n\n📈 {result['weaknesses']}\n\n🏁 {result['recommendation']}", parse_mode="Markdown")
        if HR_CHAT_ID:
            await bot.send_message(int(HR_CHAT_ID), f"🔔 *Yangi ariza!*\n👤 {data['name']}\n💼 {data['position']}\n{e} *{result['score']}%*\n📱 @{message.from_user.username or 'yoq'}", parse_mode="Markdown")
    except Exception as ex:
        logging.error(f"Xato: {ex}")
        await message.answer("❌ Xatolik yuz berdi.")
    await state.clear()

@dp.message(CandidateFlow.waiting_cv)
async def wrong_format(message: Message):
    await message.answer("📎 PDF fayl yuboring!")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
