"""
Seed script — populates master dictionaries with realistic TV headend data.
Run: python scripts/seed_data.py
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.dictionary import (
    Asset, AssetAlias, Channel, ChannelAlias,
    Department, IncidentCategory, RootCauseCategory, Shift, StaffMember,
)

engine = create_engine(settings.DATABASE_URL_SYNC)
Session = sessionmaker(bind=engine)


CHANNELS = [
    {"code": "MIR", "name": "МИР", "name_ru": "МИР", "aliases": ["Мир", "MIR", "мир", "mir"]},
    {"code": "RUSSIA1", "name": "Россия 1", "name_ru": "Россия 1", "aliases": ["Россия", "р1", "R1", "russia1"]},
    {"code": "NTV", "name": "НТВ", "name_ru": "НТВ", "aliases": ["НТВ", "ntv", "нтв"]},
    {"code": "PERVIY", "name": "Первый канал", "name_ru": "Первый канал", "aliases": ["Первый", "1", "first"]},
    {"code": "TNT", "name": "ТНТ", "name_ru": "ТНТ", "aliases": ["ТНТ", "тнт", "tnt"]},
    {"code": "RENTV", "name": "РЕН ТВ", "name_ru": "РЕН ТВ", "aliases": ["РЕН", "ren", "рен"]},
    {"code": "STS", "name": "СТС", "name_ru": "СТС", "aliases": ["стс", "sts"]},
    {"code": "MATCH", "name": "Матч!", "name_ru": "Матч!", "aliases": ["Матч", "match", "матч"]},
    {"code": "SPAS", "name": "СПАС", "name_ru": "СПАС", "aliases": ["спас", "spas"]},
    {"code": "RUSSIA24", "name": "Россия 24", "name_ru": "Россия 24", "aliases": ["р24", "r24", "russia24"]},
    {"code": "OTR", "name": "ОТР", "name_ru": "ОТР", "aliases": ["отр", "otr"]},
    {"code": "EURONEWS", "name": "Euronews", "name_ru": "Евроньюс", "aliases": ["euronews", "евроньюс"]},
]

ASSETS = [
    # Encoders
    {"code": "ENC-01", "name": "Encoder-1", "type": "encoder", "aliases": ["encoder1", "энк1", "кодер 1", "enc1"]},
    {"code": "ENC-02", "name": "Encoder-2", "type": "encoder", "aliases": ["encoder2", "энк2", "кодер 2", "enc2"]},
    {"code": "ENC-03", "name": "Encoder-3", "type": "encoder", "aliases": ["encoder3", "энк3", "кодер 3", "enc3"]},
    {"code": "ENC-04", "name": "Encoder-4", "type": "encoder", "aliases": ["encoder4", "энк4", "кодер 4", "enc4"]},
    # Transcoders
    {"code": "TC-01", "name": "Transcoder-1", "type": "transcoder", "aliases": ["transcoder1", "транскодер 1", "tc1", "tc-1"]},
    {"code": "TC-02", "name": "Transcoder-2", "type": "transcoder", "aliases": ["transcoder2", "транскодер 2", "tc2", "tc-2"]},
    {"code": "TC-03", "name": "Transcoder-3", "type": "transcoder", "aliases": ["transcoder3", "транскодер 3", "tc3"]},
    # Muxes
    {"code": "MUX-01", "name": "Mux-1", "type": "mux", "aliases": ["mux1", "мукс 1", "мультиплексор 1", "mux-1"]},
    {"code": "MUX-02", "name": "Mux-2", "type": "mux", "aliases": ["mux2", "мукс 2", "мультиплексор 2", "mux-2"]},
    {"code": "MUX-03", "name": "Mux-3", "type": "mux", "aliases": ["mux3", "мукс 3", "мультиплексор 3"]},
    # Playout
    {"code": "PLY-01", "name": "Playout-1", "type": "playout", "aliases": ["playout1", "плейаут 1", "ply1"]},
    {"code": "PLY-02", "name": "Playout-2", "type": "playout", "aliases": ["playout2", "плейаут 2", "ply2"]},
    # Uplinks
    {"code": "UPL-01", "name": "Uplink-01", "type": "uplink", "aliases": ["uplink", "uplink1", "аплинк", "аплинк 1", "uplink-01"]},
    {"code": "UPL-02", "name": "Uplink-02", "type": "uplink", "aliases": ["uplink2", "аплинк 2", "uplink-02"]},
    # Servers
    {"code": "SRV-01", "name": "Server-1", "type": "server", "aliases": ["server1", "сервер 1", "srv1"]},
    {"code": "SRV-02", "name": "Server-2", "type": "server", "aliases": ["server2", "сервер 2", "srv2"]},
    {"code": "SRV-NMS", "name": "NMS-Server", "type": "server", "aliases": ["nms", "nms-server", "мониторинг сервер"]},
    # Storage
    {"code": "STR-01", "name": "Storage-1", "type": "storage", "aliases": ["storage1", "хранилище 1", "stor1", "storage-1"]},
    {"code": "STR-02", "name": "Storage-2", "type": "storage", "aliases": ["storage2", "хранилище 2", "stor2"]},
    # Network
    {"code": "SW-CORE", "name": "Core-Switch", "type": "network", "aliases": ["core switch", "коммутатор", "свитч"]},
    {"code": "RTR-01", "name": "Router-1", "type": "network", "aliases": ["router", "роутер", "маршрутизатор"]},
]

DEPARTMENTS = [
    {"code": "OPS", "name": "Отдел эксплуатации"},
    {"code": "NOC", "name": "Центр управления сетью"},
    {"code": "TECH", "name": "Технический отдел"},
]

SHIFTS = [
    {"code": "MORNING", "name": "Утренняя смена (08:00–16:00)"},
    {"code": "DAY", "name": "Дневная смена (12:00–20:00)"},
    {"code": "NIGHT", "name": "Ночная смена (20:00–08:00)"},
    {"code": "DUTY", "name": "Дежурная смена"},
]

INCIDENT_CATEGORIES = [
    {"code": "SIGNAL_LOSS", "name": "Потеря сигнала", "type": "incident"},
    {"code": "AUDIO_FAULT", "name": "Неисправность звука", "type": "incident"},
    {"code": "VIDEO_FAULT", "name": "Неисправность видео", "type": "incident"},
    {"code": "HW_FAULT", "name": "Аппаратная неисправность", "type": "incident"},
    {"code": "SW_FAULT", "name": "Программный сбой", "type": "incident"},
    {"code": "NETWORK", "name": "Проблема сети", "type": "incident"},
    {"code": "POWER", "name": "Проблема электропитания", "type": "incident"},
    {"code": "PLANNED_MAINTENANCE", "name": "Плановое обслуживание", "type": "work"},
    {"code": "HW_REPLACEMENT", "name": "Замена оборудования", "type": "work"},
    {"code": "SW_UPDATE", "name": "Обновление ПО", "type": "work"},
    {"code": "CAPACITY_RISK", "name": "Риск переполнения", "type": "risk"},
    {"code": "HW_AGE_RISK", "name": "Риск устаревшего оборудования", "type": "risk"},
]

ROOT_CAUSE_CATEGORIES = [
    {"code": "HW_FAILURE", "name": "Аппаратный отказ"},
    {"code": "SW_BUG", "name": "Программная ошибка"},
    {"code": "CONFIG_ERROR", "name": "Ошибка конфигурации"},
    {"code": "NETWORK_ISSUE", "name": "Проблема сети"},
    {"code": "POWER_ISSUE", "name": "Проблема питания"},
    {"code": "OVERLOAD", "name": "Перегрузка ресурсов"},
    {"code": "TEMP_FIX", "name": "Временное решение (требует доработки)"},
    {"code": "HUMAN_ERROR", "name": "Ошибка персонала"},
    {"code": "EXTERNAL", "name": "Внешние факторы"},
    {"code": "UNKNOWN", "name": "Не установлено"},
]


def seed(session) -> None:
    print("Seeding channels...")
    for ch_data in CHANNELS:
        existing = session.query(Channel).filter_by(code=ch_data["code"]).first()
        if not existing:
            ch = Channel(code=ch_data["code"], name=ch_data["name"], name_ru=ch_data.get("name_ru"))
            session.add(ch)
            session.flush()
            for alias in ch_data.get("aliases", []):
                session.add(ChannelAlias(channel_id=ch.id, alias=alias))
    session.commit()
    print(f"  {len(CHANNELS)} channels seeded")

    print("Seeding assets...")
    for a_data in ASSETS:
        existing = session.query(Asset).filter_by(code=a_data["code"]).first()
        if not existing:
            a = Asset(code=a_data["code"], name=a_data["name"], asset_type=a_data["type"])
            session.add(a)
            session.flush()
            for alias in a_data.get("aliases", []):
                session.add(AssetAlias(asset_id=a.id, alias=alias))
    session.commit()
    print(f"  {len(ASSETS)} assets seeded")

    print("Seeding departments and shifts...")
    for d_data in DEPARTMENTS:
        if not session.query(Department).filter_by(code=d_data["code"]).first():
            session.add(Department(code=d_data["code"], name=d_data["name"]))
    for s_data in SHIFTS:
        if not session.query(Shift).filter_by(code=s_data["code"]).first():
            session.add(Shift(code=s_data["code"], name=s_data["name"]))
    session.commit()

    print("Seeding categories...")
    for cat in INCIDENT_CATEGORIES:
        if not session.query(IncidentCategory).filter_by(code=cat["code"]).first():
            session.add(IncidentCategory(code=cat["code"], name=cat["name"], record_type=cat["type"]))
    for rc in ROOT_CAUSE_CATEGORIES:
        if not session.query(RootCauseCategory).filter_by(code=rc["code"]).first():
            session.add(RootCauseCategory(code=rc["code"], name=rc["name"]))
    session.commit()
    print("Seed complete.")


if __name__ == "__main__":
    with Session() as session:
        seed(session)
