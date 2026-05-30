import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Загружаем переменные окружения
load_dotenv()

url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")

# Инициализируем клиент Supabase
supabase: Client = create_client(url, key)

# Название твоей таблицы в Supabase
TABLE_NAME = "dresses"

async def add_product(name: str, price: int, photo_id: str, category: str, sizes: dict = None) -> dict:
    try:
        # Базовые данные товара
        product_data = {
            "name": name,
            "price": price,
            "photo": photo_id,
            "category": category
        }
        
        # Если размеры переданы, добавляем их в общий словарь
        if sizes:
            product_data.update(sizes)
            
        # Отправляем запрос в Supabase
        response = supabase.table(TABLE_NAME).insert(product_data).execute()
        
        # Если данные успешно записались, возвращаем первую (и единственную) добавленную строку
        if response.data:
            return response.data[0]
        return None
        
    except Exception as e:
        print(f"Ошибка при добавлении товара '{name}': {e}")
        return None