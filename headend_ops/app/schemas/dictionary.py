"""Schemas for master dictionaries."""
from typing import List, Optional

from pydantic import BaseModel, Field


class ChannelBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    name_ru: Optional[str] = None
    description: Optional[str] = None
    is_active: bool = True


class ChannelCreate(ChannelBase):
    aliases: List[str] = Field(default_factory=list)


class ChannelRead(ChannelBase):
    id: int
    aliases: List[str] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class AssetBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=200)
    asset_type: str = Field(..., min_length=1, max_length=50)
    location: Optional[str] = None
    description: Optional[str] = None
    is_active: bool = True


class AssetCreate(AssetBase):
    aliases: List[str] = Field(default_factory=list)


class AssetRead(AssetBase):
    id: int
    aliases: List[str] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class StaffMemberRead(BaseModel):
    id: int
    name: str
    telegram_username: Optional[str] = None
    department_id: Optional[int] = None
    is_active: bool

    model_config = {"from_attributes": True}
