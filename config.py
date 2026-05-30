from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

ADMINS = [int(admin_id.strip()) for admin_id in os.getenv("ADMINS", "").split(",") if admin_id.strip()]

TABLE_NAME = os.getenv("TABLE_NAME")

