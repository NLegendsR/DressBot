# 🤖 DressBot

<div align="center">

**Choose language / Wybierz język:**

[🇬🇧 English](#english) · [🇵🇱 Polski](#polski)

---

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)
![aiogram](https://img.shields.io/badge/aiogram-3.x-2CA5E0?logo=telegram&logoColor=white)
![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL-3ECF8E?logo=supabase&logoColor=white)
![Railway](https://img.shields.io/badge/Deploy-Railway-purple?logo=railway&logoColor=white)

</div>

---

> ⚠️ **IMPORTANT / WAŻNE**
>
> 🔴 **The server is currently offline.**
> Even if you run the bot locally — nothing will work, because the database and hosting have been disconnected. The bot is no longer connected to Railway or Supabase — both services are inactive.
>
> 🔴 **Serwer jest obecnie wyłączony.**
> Nawet jeśli uruchomisz bota lokalnie — nic nie zadziała, ponieważ baza danych i hosting zostały odłączone. Bot nie jest już połączony z Railway ani Supabase — oba serwisy są nieaktywne.

---

<br>

---

## English

<a name="english"></a>

### 📌 What is this project?

**DressBot** is a Telegram bot for an online dress boutique. It serves two audiences:

- **Customers** — browse a photo catalog, filter dresses by price and EU size, and contact a manager to place an order.
- **Admins** — manage the entire product catalog directly from Telegram: add, edit, and delete dresses without ever opening a database UI.

The bot uses a memory-efficient architecture: the FSM (finite-state machine) stores only lightweight identifiers per user session, while every catalog page fetches a fresh row from Supabase — keeping RAM usage minimal even with a large product catalog.

---

### 🏗️ Architecture

```
Customer (Telegram)
├── /start                →  Welcome screen + main menu
└── 📂 Catalog            →  Category selection
                                      ↓
                          ┌─────────────────────┐
                          │    Filter panel      │
                          │  • Price range       │
                          │  • EU size  40–66    │
                          └─────────────────────┘
                                      ↓
                           get_filtered_products()
                                      ↓
                          Supabase (PostgreSQL)   ←  REST API
                                      ↓
                           Product card (photo)
                           name · price · sizes
                                      ↓
                      ◀ prev     1 of N     next ▶
                                      ↓
                           Order → contact manager

Admin (Telegram)
├── /admin                →  Admin panel
├── 📂 Browse catalog     →  View cards → Edit / Delete
├── ➕ Add product         →  FSM: photo → name → price → category → sizes
└── 🔍 Search             →  by ID / name / price
                                      ↓
                          Supabase CRUD operations
                                      ↓
                           Refreshed product card
```

---

### 🛠️ Tech stack

| Tool | Purpose |
|------|---------|
| **aiogram 3.x** | Telegram Bot API framework with FSM support |
| **Supabase** | PostgreSQL cloud database accessed via REST API |
| **python-dotenv** | Environment variable management |
| **Railway** | Cloud deployment platform (worker process) |
| **asyncio** | Async I/O — all DB calls are non-blocking |

---

### 🗄️ Database schema (Supabase)

Single table: `dresses`

| Column | Type | Description |
|--------|------|-------------|
| `id` | bigint PK | Auto-generated product ID |
| `name` | text | Product name |
| `price` | integer | Price in UAH |
| `photo` | text | Telegram `file_id` of the product photo |
| `category` | text | `eve_dresses` / `prom_dresses` / `casual_dresses` |
| `size_40` – `size_66` | smallint | Stock per EU size — `1` = available, `0` = out of stock |

> **Size note:** The store uses EU sizing. EU size = Ukrainian size + 6 (e.g. size 36 on the label → displayed as 42).

---

### 📁 Project structure

```
DressBot/
├── bot.py              # Entry point — Bot, Dispatcher, router registration
├── config.py           # Reads all environment variables
├── db.py               # Supabase client + CRUD helpers
├── handlers/
│   ├── admin.py        # All admin FSM flows (add, edit, delete, search, browse)
│   └── users.py        # Customer flows (start, catalog, filters, navigation)
├── keyboards/
│   ├── admin.py        # Inline keyboards for admin panels
│   └── users.py        # Inline keyboards for customer views
├── .env.example        # Environment variable template
├── Procfile            # Railway process definition
└── requirements.txt    # Python dependencies
```

---

### 🚀 How to deploy (Railway)

#### Prerequisites
- Telegram bot token from [@BotFather](https://t.me/BotFather)
- Supabase account with a project and the `dresses` table created
- GitHub account
- Railway account ([railway.app](https://railway.app))

#### Step 1 — Create the Supabase table

In your Supabase project → **SQL Editor**, run:

```sql
create table dresses (
  id       bigint generated always as identity primary key,
  name     text     not null,
  price    integer  not null,
  photo    text     not null,
  category text     not null,
  size_40  smallint default 0,
  size_42  smallint default 0,
  size_44  smallint default 0,
  size_46  smallint default 0,
  size_48  smallint default 0,
  size_50  smallint default 0,
  size_52  smallint default 0,
  size_54  smallint default 0,
  size_56  smallint default 0,
  size_58  smallint default 0,
  size_60  smallint default 0,
  size_62  smallint default 0,
  size_64  smallint default 0,
  size_66  smallint default 0
);
```

Copy the **Project URL** and **anon key** from **Settings → API**.

#### Step 2 — Push code to GitHub

```bash
git init
git add .
git commit -m "initial deploy"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/DressBot.git
git push -u origin main
```

> ⚠️ Make sure `.env` is in `.gitignore` — never push credentials to GitHub!

#### Step 3 — Create a Railway project

1. Go to [railway.app](https://railway.app)
2. Click **New Project → Deploy from GitHub repo**
3. Select your repository
4. Railway will detect `Procfile` and `requirements.txt` automatically

#### Step 4 — Add environment variables

In Railway → your service → **Variables**, add:

| Variable | Value |
|----------|-------|
| `BOT_TOKEN` | Your Telegram bot token from @BotFather |
| `ADMINS` | Comma-separated Telegram user IDs of admins (e.g. `123456,789012`) |
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_KEY` | Your Supabase anon/public API key |
| `TABLE_NAME` | `dresses` (or whatever you named the table) |

To find your Telegram user ID, message [@userinfobot](https://t.me/userinfobot).

#### Step 5 — Deploy

Railway will automatically start the process defined in `Procfile`:

```
worker: python bot.py
```

The bot connects via long-polling — no HTTP server or domain is needed.

---

### ⚙️ Running locally (development only)

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/DressBot.git
cd DressBot

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Fill in all values in .env

# 5. Start the bot
python bot.py
```

> ⚠️ Local run requires an active Supabase project with the `dresses` table. Without it, all catalog actions will return errors.

---

<br>

---

## Polski

<a name="polski"></a>

### 📌 Czym jest ten projekt?

**DressBot** to bot Telegram dla butiku sukienek online. Obsługuje dwie grupy użytkowników:

- **Klientki** — przeglądają katalog ze zdjęciami, filtrują sukienki według ceny i rozmiaru EU, a następnie kontaktują się z menedżerem, aby złożyć zamówienie.
- **Administratorzy** — zarządzają całym katalogiem produktów bezpośrednio przez Telegram: dodają, edytują i usuwają sukienki bez konieczności otwierania interfejsu bazy danych.

Bot używa architektury oszczędzającej pamięć: maszyna stanów (FSM) przechowuje wyłącznie lekkie identyfikatory dla każdej sesji użytkownika, a każde odświeżenie katalogu pobiera nowy wiersz z Supabase — dzięki czemu zużycie RAM pozostaje minimalne nawet przy dużym katalogu produktów.

---

### 🏗️ Architektura

```
Klientka (Telegram)
├── /start                →  Ekran powitalny + główne menu
└── 📂 Katalog            →  Wybór kategorii
                                      ↓
                          ┌─────────────────────┐
                          │    Panel filtrów     │
                          │  • Zakres cen        │
                          │  • Rozmiar EU 40–66  │
                          └─────────────────────┘
                                      ↓
                           get_filtered_products()
                                      ↓
                          Supabase (PostgreSQL)   ←  REST API
                                      ↓
                           Karta produktu (foto)
                           nazwa · cena · rozmiary
                                      ↓
                      ◀ poprz.   1 z N   następny ▶
                                      ↓
                           Zamówienie → kontakt z menedżerem

Administrator (Telegram)
├── /admin                →  Panel admina
├── 📂 Przeglądaj katalog →  Karty → Edytuj / Usuń
├── ➕ Dodaj produkt       →  FSM: foto → nazwa → cena → kategoria → rozmiary
└── 🔍 Wyszukaj           →  po ID / nazwie / cenie
                                      ↓
                          Operacje CRUD na Supabase
                                      ↓
                           Odświeżona karta produktu
```

---

### 🛠️ Stos technologiczny

| Narzędzie | Zastosowanie |
|-----------|-------------|
| **aiogram 3.x** | Framework Telegram Bot API z obsługą FSM |
| **Supabase** | Chmurowa baza PostgreSQL dostępna przez REST API |
| **python-dotenv** | Zarządzanie zmiennymi środowiskowymi |
| **Railway** | Platforma deploymentu w chmurze (proces worker) |
| **asyncio** | Asynchroniczne I/O — wszystkie wywołania DB są nieblokujące |

---

### 🗄️ Schemat bazy danych (Supabase)

Jedna tabela: `dresses`

| Kolumna | Typ | Opis |
|---------|-----|------|
| `id` | bigint PK | Automatycznie generowane ID produktu |
| `name` | text | Nazwa produktu |
| `price` | integer | Cena w UAH |
| `photo` | text | Telegram `file_id` zdjęcia produktu |
| `category` | text | `eve_dresses` / `prom_dresses` / `casual_dresses` |
| `size_40` – `size_66` | smallint | Stan na rozmiar EU — `1` = dostępny, `0` = brak |

> **Uwaga o rozmiarach:** Sklep używa rozmiarówki EU. Rozmiar EU = rozmiar ukraiński + 6 (np. rozmiar 36 na metce → wyświetlany jako 42).

---

### 📁 Struktura projektu

```
DressBot/
├── bot.py              # Punkt wejścia — Bot, Dispatcher, rejestracja routerów
├── config.py           # Odczyt wszystkich zmiennych środowiskowych
├── db.py               # Klient Supabase + helpery CRUD
├── handlers/
│   ├── admin.py        # Wszystkie przepływy FSM admina (dodaj, edytuj, usuń, szukaj, przeglądaj)
│   └── users.py        # Przepływy klientek (start, katalog, filtry, nawigacja)
├── keyboards/
│   ├── admin.py        # Klawiatury inline dla paneli admina
│   └── users.py        # Klawiatury inline dla widoków klientek
├── .env.example        # Szablon zmiennych środowiskowych
├── Procfile            # Definicja procesu dla Railway
└── requirements.txt    # Zależności Python
```

---

### 🚀 Jak zadepłojować (Railway)

#### Wymagania wstępne
- Token bota Telegram od [@BotFather](https://t.me/BotFather)
- Konto Supabase z projektem i stworzoną tabelą `dresses`
- Konto GitHub
- Konto Railway ([railway.app](https://railway.app))

#### Krok 1 — Stwórz tabelę w Supabase

W projekcie Supabase → **SQL Editor**, uruchom:

```sql
create table dresses (
  id       bigint generated always as identity primary key,
  name     text     not null,
  price    integer  not null,
  photo    text     not null,
  category text     not null,
  size_40  smallint default 0,
  size_42  smallint default 0,
  size_44  smallint default 0,
  size_46  smallint default 0,
  size_48  smallint default 0,
  size_50  smallint default 0,
  size_52  smallint default 0,
  size_54  smallint default 0,
  size_56  smallint default 0,
  size_58  smallint default 0,
  size_60  smallint default 0,
  size_62  smallint default 0,
  size_64  smallint default 0,
  size_66  smallint default 0
);
```

Skopiuj **Project URL** i **anon key** z zakładki **Settings → API**.

#### Krok 2 — Wgraj kod na GitHub

```bash
git init
git add .
git commit -m "initial deploy"
git branch -M main
git remote add origin https://github.com/TWOJ_LOGIN/DressBot.git
git push -u origin main
```

> ⚠️ Upewnij się, że `.env` jest w `.gitignore` — nigdy nie wgrywaj poświadczeń na GitHub!

#### Krok 3 — Stwórz projekt na Railway

1. Wejdź na [railway.app](https://railway.app)
2. Kliknij **New Project → Deploy from GitHub repo**
3. Wybierz swoje repozytorium
4. Railway automatycznie wykryje `Procfile` i `requirements.txt`

#### Krok 4 — Dodaj zmienne środowiskowe

Railway → twój serwis → **Variables**, dodaj:

| Zmienna | Wartość |
|---------|---------|
| `BOT_TOKEN` | Token bota Telegram od @BotFather |
| `ADMINS` | ID użytkowników Telegram oddzielone przecinkami (np. `123456,789012`) |
| `SUPABASE_URL` | URL twojego projektu Supabase |
| `SUPABASE_KEY` | Klucz anon/public API Supabase |
| `TABLE_NAME` | `dresses` (lub inna nazwa tabeli) |

Aby poznać swoje ID użytkownika Telegram, napisz do [@userinfobot](https://t.me/userinfobot).

#### Krok 5 — Deploy

Railway automatycznie uruchomi proces zdefiniowany w `Procfile`:

```
worker: python bot.py
```

Bot działa na long-pollingu — serwer HTTP ani domena nie są potrzebne.

---

### ⚙️ Uruchomienie lokalne (tylko do developmentu)

```bash
# 1. Sklonuj repozytorium
git clone https://github.com/TWOJ_LOGIN/DressBot.git
cd DressBot

# 2. Utwórz i aktywuj środowisko wirtualne
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 3. Zainstaluj zależności
pip install -r requirements.txt

# 4. Skonfiguruj środowisko
cp .env.example .env
# Uzupełnij wszystkie wartości w pliku .env

# 5. Uruchom bota
python bot.py
```

> ⚠️ Lokalne uruchomienie wymaga aktywnego projektu Supabase z tabelą `dresses`. Bez niego wszystkie akcje katalogu będą zwracać błędy.

---

<div align="center">
<sub>Built with ❤️ using Python · aiogram · Supabase</sub>
</div>
