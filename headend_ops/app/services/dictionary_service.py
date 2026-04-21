"""CRUD service for master dictionaries (channels, assets, etc.)."""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.dictionary import Asset, AssetAlias, Channel, ChannelAlias
from app.schemas.dictionary import AssetCreate, ChannelCreate


async def list_channels(db: AsyncSession, active_only: bool = True) -> list[Channel]:
    query = select(Channel).options(selectinload(Channel.aliases))
    if active_only:
        query = query.where(Channel.is_active == True)
    result = await db.execute(query.order_by(Channel.name))
    return list(result.scalars().all())


async def create_channel(db: AsyncSession, data: ChannelCreate) -> Channel:
    channel = Channel(
        code=data.code,
        name=data.name,
        name_ru=data.name_ru,
        description=data.description,
        is_active=data.is_active,
    )
    db.add(channel)
    await db.flush()

    for alias_text in data.aliases:
        db.add(ChannelAlias(channel_id=channel.id, alias=alias_text))
    await db.flush()
    return channel


async def list_assets(db: AsyncSession, active_only: bool = True) -> list[Asset]:
    query = select(Asset).options(selectinload(Asset.aliases))
    if active_only:
        query = query.where(Asset.is_active == True)
    result = await db.execute(query.order_by(Asset.name))
    return list(result.scalars().all())


async def create_asset(db: AsyncSession, data: AssetCreate) -> Asset:
    asset = Asset(
        code=data.code,
        name=data.name,
        asset_type=data.asset_type,
        location=data.location,
        description=data.description,
        is_active=data.is_active,
    )
    db.add(asset)
    await db.flush()

    for alias_text in data.aliases:
        db.add(AssetAlias(asset_id=asset.id, alias=alias_text))
    await db.flush()
    return asset
