from dotenv import load_dotenv
import os

load_dotenv()  # одноразово, тільки тут

BOT_TOKEN    = os.getenv("BOT_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
TABLE_NAME   = os.getenv("TABLE_NAME", "dresses")
ADMINS       = [
    int(x.strip())
    for x in os.getenv("ADMINS", "").split(",")
    if x.strip().isdigit()
]
