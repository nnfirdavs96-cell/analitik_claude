"""Dictionary-based normalization of AI-parsed values."""
from dataclasses import dataclass
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dictionary import Asset, AssetAlias, Channel, ChannelAlias
from app.normalization.fuzzy_match import find_best_match_with_score
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class NormalizationResult:
    channel_id: Optional[int] = None
    channel_name: Optional[str] = None
    asset_id: Optional[int] = None
    asset_name: Optional[str] = None
    channel_match_score: int = 0
    asset_match_score: int = 0
    status: str = "normalized"  # normalized | partial | failed


async def normalize_channel(
    db: AsyncSession,
    raw_name: Optional[str],
) -> tuple[Optional[int], Optional[str], int]:
    """
    Try to match raw_name to a Channel in the database.
    Returns (channel_id, channel_name, match_score).
    """
    if not raw_name:
        return None, None, 0

    # Load all channels + aliases
    channels_result = await db.execute(select(Channel).where(Channel.is_active == True))
    channels = channels_result.scalars().all()

    aliases_result = await db.execute(select(ChannelAlias))
    aliases = aliases_result.scalars().all()

    # Build candidate lookup: display_name -> channel_id
    lookup: dict[str, int] = {}
    for ch in channels:
        lookup[ch.name] = ch.id
        lookup[ch.code] = ch.id
        if ch.name_ru:
            lookup[ch.name_ru] = ch.id

    alias_lookup: dict[str, int] = {}
    for alias in aliases:
        alias_lookup[alias.alias] = alias.channel_id

    # Check alias exact match
    raw_lower = raw_name.lower().strip()
    for alias_text, ch_id in alias_lookup.items():
        if alias_text.lower().strip() == raw_lower:
            ch = next((c for c in channels if c.id == ch_id), None)
            if ch:
                return ch.id, ch.name, 100

    all_candidates = list(lookup.keys()) + list(alias_lookup.keys())
    best, score = find_best_match_with_score(raw_name, all_candidates)

    if best:
        ch_id = lookup.get(best) or alias_lookup.get(best)
        if ch_id:
            ch = next((c for c in channels if c.id == ch_id), None)
            if ch:
                logger.info("channel_matched", raw=raw_name, matched=ch.name, score=score)
                return ch.id, ch.name, score

    logger.warning("channel_not_matched", raw=raw_name)
    return None, None, 0


async def normalize_asset(
    db: AsyncSession,
    raw_name: Optional[str],
) -> tuple[Optional[int], Optional[str], int]:
    """
    Try to match raw_name to an Asset in the database.
    Returns (asset_id, asset_name, match_score).
    """
    if not raw_name:
        return None, None, 0

    assets_result = await db.execute(select(Asset).where(Asset.is_active == True))
    assets = assets_result.scalars().all()

    aliases_result = await db.execute(select(AssetAlias))
    aliases = aliases_result.scalars().all()

    lookup: dict[str, int] = {}
    for asset in assets:
        lookup[asset.name] = asset.id
        lookup[asset.code] = asset.id

    alias_lookup: dict[str, int] = {}
    for alias in aliases:
        alias_lookup[alias.alias] = alias.asset_id

    raw_lower = raw_name.lower().strip()
    for alias_text, asset_id in alias_lookup.items():
        if alias_text.lower().strip() == raw_lower:
            asset = next((a for a in assets if a.id == asset_id), None)
            if asset:
                return asset.id, asset.name, 100

    all_candidates = list(lookup.keys()) + list(alias_lookup.keys())
    best, score = find_best_match_with_score(raw_name, all_candidates)

    if best:
        asset_id = lookup.get(best) or alias_lookup.get(best)
        if asset_id:
            asset = next((a for a in assets if a.id == asset_id), None)
            if asset:
                logger.info("asset_matched", raw=raw_name, matched=asset.name, score=score)
                return asset.id, asset.name, score

    logger.warning("asset_not_matched", raw=raw_name)
    return None, None, 0


async def normalize_event_fields(
    db: AsyncSession,
    channel_name_raw: Optional[str],
    asset_name_raw: Optional[str],
) -> NormalizationResult:
    """
    Normalize both channel and asset fields for a parsed event.
    Returns a NormalizationResult with resolved IDs.
    """
    result = NormalizationResult()

    ch_id, ch_name, ch_score = await normalize_channel(db, channel_name_raw)
    result.channel_id = ch_id
    result.channel_name = ch_name
    result.channel_match_score = ch_score

    asset_id, asset_name, asset_score = await normalize_asset(db, asset_name_raw)
    result.asset_id = asset_id
    result.asset_name = asset_name
    result.asset_match_score = asset_score

    if ch_id and asset_id:
        result.status = "normalized"
    elif ch_id or asset_id:
        result.status = "partial"
    elif channel_name_raw or asset_name_raw:
        result.status = "partial"  # had names but couldn't match
    else:
        result.status = "normalized"  # nothing to normalize

    return result
