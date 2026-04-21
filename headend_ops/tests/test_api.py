"""API endpoint tests."""
import pytest
import pytest_asyncio


class TestHealthEndpoints:
    @pytest.mark.asyncio
    async def test_health(self, client):
        resp = await client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"

    @pytest.mark.asyncio
    async def test_ready(self, client):
        resp = await client.get("/api/v1/ready")
        assert resp.status_code == 200


class TestEventsEndpoints:
    @pytest.mark.asyncio
    async def test_list_events_empty(self, client):
        resp = await client.get("/api/v1/events")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert data["total"] >= 0

    @pytest.mark.asyncio
    async def test_get_nonexistent_event(self, client):
        resp = await client.get("/api/v1/events/99999")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_list_events_with_filter(self, client):
        resp = await client.get("/api/v1/events?record_type=incident")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_list_events_pagination(self, client):
        resp = await client.get("/api/v1/events?page=1&page_size=10")
        assert resp.status_code == 200
        data = resp.json()
        assert data["page"] == 1
        assert data["page_size"] == 10


class TestDictionariesEndpoints:
    @pytest.mark.asyncio
    async def test_list_channels_empty(self, client):
        resp = await client.get("/api/v1/dictionaries/channels")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    @pytest.mark.asyncio
    async def test_create_channel(self, client):
        payload = {
            "code": "TEST-CH",
            "name": "Test Channel",
            "name_ru": "Тестовый канал",
            "aliases": ["test", "tch"],
        }
        resp = await client.post("/api/v1/dictionaries/channels", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == "TEST-CH"
        assert len(data["aliases"]) == 2

    @pytest.mark.asyncio
    async def test_create_asset(self, client):
        payload = {
            "code": "TEST-ENC",
            "name": "Test Encoder",
            "asset_type": "encoder",
            "aliases": ["tenc", "test encoder"],
        }
        resp = await client.post("/api/v1/dictionaries/assets", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == "TEST-ENC"

    @pytest.mark.asyncio
    async def test_list_assets_empty(self, client):
        resp = await client.get("/api/v1/dictionaries/assets")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestReviewEndpoints:
    @pytest.mark.asyncio
    async def test_pending_reviews_empty(self, client):
        resp = await client.get("/api/v1/review/pending")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestKPIEndpoints:
    @pytest.mark.asyncio
    async def test_kpi_history_empty(self, client):
        resp = await client.get("/api/v1/kpi/history")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    @pytest.mark.asyncio
    async def test_kpi_calculate(self, client):
        resp = await client.post("/api/v1/kpi/calculate")
        assert resp.status_code == 200
        data = resp.json()
        assert "daily" in data
        assert "monthly" in data
        assert "weekly" in data


class TestTelegramIngest:
    @pytest.mark.asyncio
    async def test_ingest_message(self, client):
        """Test that ingest endpoint accepts a message and returns a response."""
        payload = {
            "telegram_message_id": 12345,
            "chat_id": -100123456,
            "chat_type": "group",
            "chat_title": "Test Ops Group",
            "user_telegram_id": 111222333,
            "username": "test_engineer",
            "first_name": "Иван",
            "last_name": "Петров",
            "text": "14:20 пропал звук на канале Мир, encoder-2, перезапустили, восстановлено в 14:32",
            "message_date": "2024-01-15T14:20:00Z",
        }
        resp = await client.post("/api/v1/telegram/ingest", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert "message_id" in data
        assert "status" in data
        assert "confirmation_text" in data
        assert data["status"] in ("parsed", "needs_review", "failed")

    @pytest.mark.asyncio
    async def test_ingest_creates_event(self, client):
        """Ingesting a message should create a ParsedEvent."""
        payload = {
            "telegram_message_id": 99999,
            "chat_id": -100999888,
            "chat_type": "supergroup",
            "chat_title": "Headend Ops",
            "user_telegram_id": 777888999,
            "username": "ops_engineer",
            "first_name": "Анна",
            "last_name": "Сидорова",
            "text": "Выполнено плановое обслуживание mux-2, все системы в норме",
        }
        resp = await client.post("/api/v1/telegram/ingest", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("event_id") is not None

        # Check that the event is retrievable
        event_resp = await client.get(f"/api/v1/events/{data['event_id']}")
        assert event_resp.status_code == 200
