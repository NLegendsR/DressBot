# 🤖 DressBot

<div align="center">

**Select language / Виберіть мову:**

[🇬🇧 English](#english) &nbsp;|&nbsp; [🇵🇱 Polski](#polski)

</div>

---

> [!WARNING]
> **⚠️ The server is currently offline.**
> The bot is disconnected from both Railway and Supabase. Running the bot locally or attempting to deploy it as-is will not work until new Railway and Supabase instances are configured with valid credentials in the `.env` file.

---

<a name="english"></a>

## 🇬🇧 English

### About

**DressBot** is a Telegram bot for an online dress boutique. It serves two audiences:

- **Customers** — browse a photo catalog, filter dresses by price and size, and reach out to a manager to place an order.
- **Admins** — manage the entire product catalog directly from Telegram: add, edit, and delete dresses without touching any database UI.

The bot was built with a memory-efficient architecture: the FSM (finite-state machine) stores only lightweight identifiers, while each page refresh fetches a fresh row from Supabase — keeping RAM usage minimal even with a large catalog.

---

### Features

#### For customers
| Feature | Description |
|---|---|
| 📂 Category browsing | Evening dresses, Prom dresses, Casual dresses |
| 🔍 Price filter | Preset ranges or enter a custom max price |
| 📏 Size filter | EU sizes 40–66 (even numbers) |
| 🖼 Product cards | Photo, name, price, available sizes |
| 📞 Contact | Quick link to managers via Telegram handles |

#### For admins
| Feature | Description |
|---|---|
| ➕ Add product | Upload photo → name → price → category → sizes |
| ✏️ Edit product | Change name, price, photo, **category**, add or zero-out sizes |
| 🗑 Delete product | Full removal from the database |
| 🔍 Search | Find by ID, name (partial match), or exact price |

---

### Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11+ |
| Telegram framework | [aiogram 3.x](https://docs.aiogram.dev/) |
| Database | [Supabase](https://supabase.com/) (PostgreSQL via REST API) |
| Hosting | [Railway](https://railway.app/) |
| Config | python-dotenv |

---

### Project Structure

```
DressBot/
├── bot.py              # Entry point — creates Bot, Dispatcher, registers routers
├── config.py           # Reads environment variables
├── db.py               # Supabase client + all DB helpers (CRUD)
├── handlers/
│   ├── admin.py        # All admin FSM flows (add, edit, delete, search, browse)
│   └── users.py        # Customer flows (start, catalog, filters, navigation)
├── keyboards/
│   ├── admin.py        # Inline keyboards for admin panels
│   └── users.py        # Inline keyboards for customer views
├── .env.example        # Template for environment variables
├── Procfile            # Railway process definition
└── requirements.txt    # Python dependencies
```

---

### Database Setup (Supabase)

1. Create a new project at [supabase.com](https://supabase.com/).
2. Go to **SQL Editor** and run the following query to create the products table:

```sql
create table dresses (
  id       bigint generated always as identity primary key,
  name     text        not null,
  price    integer     not null,
  photo    text        not null,  -- Telegram file_id
  category text        not null,  -- eve_dresses | prom_dresses | casual_dresses
  size_40  smallint    default 0,
  size_42  smallint    default 0,
  size_44  smallint    default 0,
  size_46  smallint    default 0,
  size_48  smallint    default 0,
  size_50  smallint    default 0,
  size_52  smallint    default 0,
  size_54  smallint    default 0,
  size_56  smallint    default 0,
  size_58  smallint    default 0,
  size_60  smallint    default 0,
  size_62  smallint    default 0,
  size_64  smallint    default 0,
  size_66  smallint    default 0
);
```

3. Copy the **Project URL** and **anon/public API key** from **Settings → API** — you will need them for the `.env` file.

---

### Getting a Bot Token

1. Open Telegram and start a chat with [@BotFather](https://t.me/BotFather).
2. Send `/newbot` and follow the prompts.
3. Copy the token you receive (format: `123456789:ABC-DEF...`).
4. To get your Telegram **user ID**, message [@userinfobot](https://t.me/userinfobot).

---

### Environment Variables

Create a `.env` file in the project root (copy `.env.example` as a starting point):

```env
BOT_TOKEN=your_telegram_bot_token_here
ADMINS=123456789,987654321        # Comma-separated Telegram user IDs
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_KEY=your_supabase_anon_key_here
TABLE_NAME=dresses
```

| Variable | Required | Description |
|---|---|---|
| `BOT_TOKEN` | ✅ | Telegram Bot API token from @BotFather |
| `ADMINS` | ✅ | Comma-separated list of admin Telegram user IDs |
| `SUPABASE_URL` | ✅ | Your Supabase project URL |
| `SUPABASE_KEY` | ✅ | Supabase anon/public API key |
| `TABLE_NAME` | ✅ | Database table name (default: `dresses`) |

---

### Running Locally

```bash
# 1. Clone the repository
git clone https://github.com/your-username/DressBot.git
cd DressBot

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env and fill in all values

# 5. Run the bot
python bot.py
```

---

### Deploying to Railway

1. Push the project to a GitHub repository.
2. Create a new project on [railway.app](https://railway.app/) and connect the repository.
3. Go to **Variables** and add all keys from the `.env` file.
4. Railway will detect the `Procfile` and use `worker: python bot.py` as the start command.
5. Click **Deploy** — the bot starts automatically.

> **Note:** No web server is needed. The bot uses long-polling, so Railway's HTTP health-check can be ignored or disabled.

---

<a name="polski"></a>

## 🇵🇱 Polski

### O projekcie

**DressBot** to bot Telegram dla butiku sukienek online. Obsługuje dwie grupy użytkowników:

- **Klientki** — przeglądają katalog ze zdjęciami, filtrują sukienki według ceny i rozmiaru, a następnie kontaktują się z menedżerem, aby złożyć zamówienie.
- **Administratorzy** — zarządzają całym katalogiem produktów bezpośrednio przez Telegram: dodają, edytują i usuwają sukienki bez konieczności korzystania z interfejsu bazy danych.

Bot został zbudowany z myślą o oszczędnym zarządzaniu pamięcią: maszyna stanów (FSM) przechowuje tylko lekkie identyfikatory, a każde odświeżenie strony pobiera nowe dane z Supabase — dzięki czemu zużycie RAM pozostaje minimalne nawet przy dużym katalogu.

---

### Funkcjonalności

#### Dla klientek
| Funkcja | Opis |
|---|---|
| 📂 Przeglądanie kategorii | Sukienki wieczorowe, na bal maturalny, casualowe |
| 🔍 Filtr ceny | Gotowe zakresy lub własna maksymalna cena |
| 📏 Filtr rozmiaru | Rozmiary EU 40–66 (parzyste) |
| 🖼 Karty produktów | Zdjęcie, nazwa, cena, dostępne rozmiary |
| 📞 Kontakt | Szybki link do menedżerów przez Telegram |

#### Dla administratorów
| Funkcja | Opis |
|---|---|
| ➕ Dodaj produkt | Zdjęcie → nazwa → cena → kategoria → rozmiary |
| ✏️ Edytuj produkt | Zmiana nazwy, ceny, zdjęcia, **kategorii**, dodawanie lub zerowanie rozmiarów |
| 🗑 Usuń produkt | Całkowite usunięcie z bazy danych |
| 🔍 Wyszukiwanie | Wyszukaj po ID, nazwie (dopasowanie częściowe) lub dokładnej cenie |

---

### Stos technologiczny

| Warstwa | Technologia |
|---|---|
| Język | Python 3.11+ |
| Framework Telegram | [aiogram 3.x](https://docs.aiogram.dev/) |
| Baza danych | [Supabase](https://supabase.com/) (PostgreSQL przez REST API) |
| Hosting | [Railway](https://railway.app/) |
| Konfiguracja | python-dotenv |

---

### Struktura projektu

```
DressBot/
├── bot.py              # Punkt wejścia — tworzy Bot, Dispatcher, rejestruje routery
├── config.py           # Odczytuje zmienne środowiskowe
├── db.py               # Klient Supabase + helpery bazy danych (CRUD)
├── handlers/
│   ├── admin.py        # Wszystkie przepływy FSM dla admina (dodawanie, edycja, usuwanie, wyszukiwanie, przeglądanie)
│   └── users.py        # Przepływy dla klientek (start, katalog, filtry, nawigacja)
├── keyboards/
│   ├── admin.py        # Klawiatury inline dla paneli admina
│   └── users.py        # Klawiatury inline dla widoków klientek
├── .env.example        # Szablon zmiennych środowiskowych
├── Procfile            # Definicja procesu dla Railway
└── requirements.txt    # Zależności Pythona
```

---

### Konfiguracja bazy danych (Supabase)

1. Utwórz nowy projekt na [supabase.com](https://supabase.com/).
2. Przejdź do **SQL Editor** i uruchom poniższe zapytanie, aby utworzyć tabelę produktów:

```sql
create table dresses (
  id       bigint generated always as identity primary key,
  name     text        not null,
  price    integer     not null,
  photo    text        not null,  -- Telegram file_id
  category text        not null,  -- eve_dresses | prom_dresses | casual_dresses
  size_40  smallint    default 0,
  size_42  smallint    default 0,
  size_44  smallint    default 0,
  size_46  smallint    default 0,
  size_48  smallint    default 0,
  size_50  smallint    default 0,
  size_52  smallint    default 0,
  size_54  smallint    default 0,
  size_56  smallint    default 0,
  size_58  smallint    default 0,
  size_60  smallint    default 0,
  size_62  smallint    default 0,
  size_64  smallint    default 0,
  size_66  smallint    default 0
);
```

3. Skopiuj **Project URL** i **anon/public API key** z zakładki **Settings → API** — będą potrzebne do pliku `.env`.

---

### Uzyskanie tokena bota

1. Otwórz Telegram i rozpocznij rozmowę z [@BotFather](https://t.me/BotFather).
2. Wyślij `/newbot` i postępuj zgodnie z instrukcjami.
3. Skopiuj otrzymany token (format: `123456789:ABC-DEF...`).
4. Aby poznać swoje **ID użytkownika Telegram**, napisz do [@userinfobot](https://t.me/userinfobot).

---

### Zmienne środowiskowe

Utwórz plik `.env` w głównym katalogu projektu (skopiuj `.env.example` jako punkt wyjścia):

```env
BOT_TOKEN=twój_token_bota_telegram
ADMINS=123456789,987654321        # ID użytkowników Telegram oddzielone przecinkami
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_KEY=twój_klucz_anon_supabase
TABLE_NAME=dresses
```

| Zmienna | Wymagana | Opis |
|---|---|---|
| `BOT_TOKEN` | ✅ | Token Telegram Bot API od @BotFather |
| `ADMINS` | ✅ | Lista ID adminów w Telegramie (przecinki jako separator) |
| `SUPABASE_URL` | ✅ | URL projektu Supabase |
| `SUPABASE_KEY` | ✅ | Klucz anon/public API Supabase |
| `TABLE_NAME` | ✅ | Nazwa tabeli w bazie danych (domyślnie: `dresses`) |

---

### Uruchamianie lokalnie

```bash
# 1. Sklonuj repozytorium
git clone https://github.com/twoja-nazwa-użytkownika/DressBot.git
cd DressBot

# 2. Utwórz i aktywuj środowisko wirtualne
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 3. Zainstaluj zależności
pip install -r requirements.txt

# 4. Skonfiguruj środowisko
cp .env.example .env
# Edytuj plik .env i uzupełnij wszystkie wartości

# 5. Uruchom bota
python bot.py
```

---

### Wdrożenie na Railway

1. Wypchnij projekt do repozytorium GitHub.
2. Utwórz nowy projekt na [railway.app](https://railway.app/) i podłącz repozytorium.
3. Przejdź do zakładki **Variables** i dodaj wszystkie klucze z pliku `.env`.
4. Railway wykryje `Procfile` i użyje `worker: python bot.py` jako komendy startowej.
5. Kliknij **Deploy** — bot uruchomi się automatycznie.

> **Uwaga:** Serwer HTTP nie jest potrzebny. Bot używa long-pollingu, więc health-check HTTP Railway można zignorować lub wyłączyć.

---

<div align="center">
<sub>Built with ❤️ using Python + aiogram + Supabase</sub>
</div>
