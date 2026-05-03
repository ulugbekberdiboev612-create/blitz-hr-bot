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
