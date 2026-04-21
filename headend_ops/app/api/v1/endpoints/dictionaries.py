"""Dictionary management endpoints."""
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.dictionary import AssetCreate, AssetRead, ChannelCreate, ChannelRead
from app.services.dictionary_service import create_asset, create_channel, list_assets, list_channels

router = APIRouter(prefix="/dictionaries", tags=["Dictionaries"])


@router.get("/channels", response_model=List[ChannelRead], summary="List all channels")
async def get_channels(db: AsyncSession = Depends(get_db)):
    channels = await list_channels(db)
    return [
        ChannelRead(
            id=ch.id, code=ch.code, name=ch.name, name_ru=ch.name_ru,
            description=ch.description, is_active=ch.is_active,
            aliases=[a.alias for a in ch.aliases],
        )
        for ch in channels
    ]


@router.post("/channels", response_model=ChannelRead, summary="Create channel")
async def create_channel_endpoint(data: ChannelCreate, db: AsyncSession = Depends(get_db)):
    ch = await create_channel(db, data)
    return ChannelRead(
        id=ch.id, code=ch.code, name=ch.name, name_ru=ch.name_ru,
        description=ch.description, is_active=ch.is_active,
        aliases=[a.alias for a in ch.aliases],
    )


@router.get("/assets", response_model=List[AssetRead], summary="List all assets")
async def get_assets(db: AsyncSession = Depends(get_db)):
    assets = await list_assets(db)
    return [
        AssetRead(
            id=a.id, code=a.code, name=a.name, asset_type=a.asset_type,
            location=a.location, description=a.description, is_active=a.is_active,
            aliases=[al.alias for al in a.aliases],
        )
        for a in assets
    ]


@router.post("/assets", response_model=AssetRead, summary="Create asset")
async def create_asset_endpoint(data: AssetCreate, db: AsyncSession = Depends(get_db)):
    a = await create_asset(db, data)
    return AssetRead(
        id=a.id, code=a.code, name=a.name, asset_type=a.asset_type,
        location=a.location, description=a.description, is_active=a.is_active,
        aliases=[al.alias for al in a.aliases],
    )
