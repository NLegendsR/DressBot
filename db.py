"""
Single Supabase client shared across the entire app.
Import `supabase` and `TABLE_NAME` from here — never create a second client.
"""
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY, TABLE_NAME

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ── Колонки, которые реально используются в UI ────────────────────────────────
# Не тянем все поля — только нужные (экономит трафик к Supabase и RAM)
_SIZE_COLS = ",".join(f"size_{s}" for s in range(40, 68, 2))
PRODUCT_COLS = f"id,name,price,photo,category,{_SIZE_COLS}"


# ── Helpers ───────────────────────────────────────────────────────────────────

async def get_products_by_category(category: str) -> list:
    r = (supabase.table(TABLE_NAME)
         .select(PRODUCT_COLS)
         .eq("category", category)
         .order("id")
         .execute())
    return r.data


async def get_filtered_products(
    category: str | None,
    min_price: int,
    max_price: int,
    target_size: int | None,
) -> list:
    """Return products matching price/size filters. No FSMContext dependency."""
    q = supabase.table(TABLE_NAME).select(PRODUCT_COLS)
    if category:
        q = q.eq("category", category)
    q = q.gte("price", min_price).lte("price", max_price).order("id")
    all_products = q.execute().data

    result = []
    for p in all_products:
        if target_size:
            if int(p.get(f"size_{target_size}", 0) or 0) > 0:
                result.append(p)
        else:
            total = sum(int(p.get(f"size_{s}", 0) or 0) for s in range(40, 68, 2))
            if total > 0:
                result.append(p)
    return result


async def get_product_by_id(product_id: int) -> dict | None:
    r = (supabase.table(TABLE_NAME)
         .select(PRODUCT_COLS)
         .eq("id", product_id)
         .limit(1)
         .execute())
    return r.data[0] if r.data else None


async def add_product(
    name: str, price: int, photo_id: str, category: str, sizes: dict
) -> dict | None:
    data = {"name": name, "price": price, "photo": photo_id, "category": category}
    data.update(sizes)
    r = supabase.table(TABLE_NAME).insert(data).execute()
    return r.data[0] if r.data else None


async def update_product(product_id: int, fields: dict) -> None:
    supabase.table(TABLE_NAME).update(fields).eq("id", product_id).execute()


async def delete_product(product_id: int) -> bool:
    try:
        r = supabase.table(TABLE_NAME).delete().eq("id", product_id).execute()
        return len(r.data) > 0
    except Exception as e:
        print(f"Delete error: {e}")
        return False


async def search_products(criterion: str, value: str) -> list:
    q = supabase.table(TABLE_NAME).select(PRODUCT_COLS)
    if criterion == "id" and value.isdigit():
        q = q.eq("id", int(value))
    elif criterion == "price" and value.isdigit():
        q = q.eq("price", int(value))
    elif criterion == "name":
        q = q.ilike("name", f"%{value}%")
    else:
        return []
    return q.execute().data
