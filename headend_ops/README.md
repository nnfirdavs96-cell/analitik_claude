# Headend Ops Platform

AI-powered operational reporting platform for TV headend / broadcast operations departments.

---

## What it does

The team writes operational updates in a Telegram group chat in natural language. The system:

1. **Ingests** Telegram messages via bot
2. **Parses** them with OpenAI (or rule-based fallback)
3. **Validates** structured JSON output
4. **Normalizes** channel/asset names against master dictionaries
5. **Detects** duplicate and repeat incidents
6. **Calculates** KPI metrics (daily / weekly / monthly)
7. **Generates** management reports (JSON, Excel, PDF)
8. **Exposes** dashboard-ready REST API
9. **Queues** low-confidence records for human review

---

## Quick Start (Docker Compose)

```bash
# 1. Clone and configure
cp .env.example .env
# Edit .env: set OPENAI_API_KEY and TELEGRAM_BOT_TOKEN

# 2. Start all services
docker compose up -d

# 3. Apply database migrations + seed data
docker compose run --rm migrate

# 4. Open API documentation
open http://localhost:8000/docs

# 5. Open dashboard
open http://localhost:8000/static/dashboard.html
```

---

## Start Telegram Bot

```bash
# Bot runs as a separate service
docker compose --profile bot up -d bot
```

---

## Architecture

```
Telegram Group Chat
    ↓
Telegram Bot (aiogram 3.x)
    ↓
FastAPI  /api/v1/telegram/ingest
    ↓
AI Parser (OpenAI gpt-4o-mini | Rule-based fallback)
    ↓
Schema Validation (Pydantic v2)
    ↓
Dictionary Normalization (fuzzy match channels/assets)
    ↓
Duplicate Detection + Recurrence Counter
    ↓
PostgreSQL (SQLAlchemy 2.x + Alembic)
    ↓
KPI Engine (weighted composite score)
    ↓
Report Generator (JSON + Excel + PDF)
    ↓
Dashboard API + HTML Dashboard
```

---

## Project Structure

```
headend_ops/
├── app/
│   ├── ai/                  # AI provider abstraction
│   │   ├── base.py          # Abstract AIProvider interface
│   │   ├── openai_provider.py
│   │   ├── fallback_parser.py
│   │   ├── provider_factory.py
│   │   └── schemas.py       # AIParseResult schema
│   ├── api/
│   │   └── v1/endpoints/    # FastAPI route handlers
│   ├── bot/
│   │   ├── handlers/        # Telegram command + message handlers
│   │   ├── texts.py         # All Russian user-facing text
│   │   └── main.py          # Bot entry point
│   ├── core/                # Config, logging, exceptions
│   ├── db/                  # SQLAlchemy session + base
│   ├── kpi/                 # KPI engine + formulas
│   ├── models/              # SQLAlchemy ORM models
│   ├── normalization/       # Fuzzy matching + dict normalization
│   ├── reports/             # Excel + PDF exporters
│   ├── schemas/             # Pydantic v2 schemas
│   ├── services/            # Business logic services + pipeline
│   └── main.py              # FastAPI application
├── alembic/                 # DB migrations
├── scripts/
│   └── seed_data.py         # Seed channels, assets, categories
├── tests/
│   ├── test_parser.py
│   ├── test_kpi.py
│   ├── test_normalization.py
│   ├── test_api.py
│   └── test_reports.py
├── static/
│   └── dashboard.html       # Standalone dashboard UI
├── docker/
│   ├── Dockerfile.app
│   └── Dockerfile.bot
├── docker-compose.yml
├── .env.example
├── Makefile
└── requirements.txt
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/telegram/ingest` | Ingest Telegram message |
| GET | `/api/v1/events` | List events with filters |
| GET | `/api/v1/events/{id}` | Get event by ID |
| PATCH | `/api/v1/events/{id}` | Update event |
| GET | `/api/v1/kpi/snapshot` | Current KPI snapshot |
| POST | `/api/v1/kpi/calculate` | Recalculate KPI |
| GET | `/api/v1/kpi/history` | KPI trend history |
| POST | `/api/v1/reports/generate` | Generate report |
| GET | `/api/v1/reports/{id}/download/excel` | Download Excel |
| GET | `/api/v1/reports/{id}/download/pdf` | Download PDF |
| GET | `/api/v1/dictionaries/channels` | List channels |
| POST | `/api/v1/dictionaries/channels` | Create channel |
| GET | `/api/v1/dictionaries/assets` | List assets |
| POST | `/api/v1/dictionaries/assets` | Create asset |
| GET | `/api/v1/review/pending` | Review queue |
| POST | `/api/v1/review/{id}/approve` | Approve review |
| POST | `/api/v1/review/{id}/correct` | Correct + approve |
| GET | `/api/v1/dashboard/summary` | Dashboard data |
| GET | `/api/v1/health` | Healthcheck |
| GET | `/api/v1/ready` | Readiness check |

---

## Telegram Bot Commands (Russian UI)

| Command | Description |
|---------|-------------|
| `/start` | Начать работу |
| `/help` | Список команд |
| `/incident` | Зафиксировать инцидент |
| `/work` | Зафиксировать работу |
| `/risk` | Зафиксировать риск |
| `/equipment` | Состояние оборудования |
| `/note` | Добавить заметку |
| `/report_day` | Ежедневный отчёт |
| `/report_week` | Еженедельный отчёт |
| `/report_month` | Ежемесячный отчёт |
| `/kpi` | Текущие KPI |
| `/channels` | Список каналов |
| `/assets` | Список оборудования |
| `/pending_review` | Записи на проверке |

---

## KPI Formula

```
department_kpi_score =
    0.40 × incident_score
  + 0.20 × resolution_score
  + 0.20 × work_completion_score
  + 0.10 × repeat_issue_score
  + 0.10 × ai_quality_score
```

Weights are configurable via environment variables:
```
KPI_WEIGHT_INCIDENT=0.40
KPI_WEIGHT_RESOLUTION=0.20
KPI_WEIGHT_WORK=0.20
KPI_WEIGHT_REPEAT=0.10
KPI_WEIGHT_AI_QUALITY=0.10
```

---

## Sample Input Messages

The system handles natural Russian operational messages:

```
14:20 пропал звук на канале Мир, encoder-2, перезапустили, восстановлено в 14:32
Проверили playout-1, диск заполнен на 92%, нужно очистить архив
Заменили блок питания на mux-1, работа завершена
Повторно завис сервер transcoder-1, временно перезапущен сервис
На uplink наблюдаются потери, ведем мониторинг
Нагрузка на storage-1 остается высокой, риск переполнения
Выполнено плановое обслуживание mux-2
```

---

## Review Queue

Records go to review queue when:
- AI confidence < 0.65 (configurable via `AI_CONFIDENCE_THRESHOLD`)
- Rule-based fallback parser was used
- Channel not found in dictionary
- Asset not found in dictionary
- Incident has no severity

Review via API: `GET /api/v1/review/pending`

---

## Environment Variables

See `.env.example` for full list. Required:

```
OPENAI_API_KEY=sk-...
TELEGRAM_BOT_TOKEN=...
DATABASE_URL=postgresql+asyncpg://...
```

---

## Development

```bash
# Install dependencies locally
pip install -r requirements.txt

# Run API in development mode
uvicorn app.main:app --reload --port 8000

# Run Telegram bot
python -m app.bot.main

# Apply migrations
alembic upgrade head

# Seed data
python scripts/seed_data.py

# Run tests
pytest tests/ -v

# Generate monthly report (via API)
curl -X POST http://localhost:8000/api/v1/reports/generate \
  -H "Content-Type: application/json" \
  -d '{"report_type": "monthly", "period_start": "2024-01-01"}'
```

---

## Seeded Master Data

The seed script populates:

**Channels (12):** MIR, Россия 1, НТВ, Первый канал, ТНТ, РЕН ТВ, СТС, Матч!, СПАС, Россия 24, ОТР, Euronews

**Assets (21):**
- Encoders: ENC-01 through ENC-04
- Transcoders: TC-01 through TC-03
- Muxes: MUX-01 through MUX-03
- Playout: PLY-01, PLY-02
- Uplinks: UPL-01, UPL-02
- Servers: SRV-01, SRV-02, SRV-NMS
- Storage: STR-01, STR-02
- Network: SW-CORE, RTR-01

**All assets have Russian and English aliases** for robust normalization.

---

## License

Internal platform — all rights reserved.
