from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, HttpUrl, ConfigDict, field_serializer


class WorkplaceType(str, Enum):
    REMOTE = "remote"
    HYBRID = "hybrid"
    ON_SITE = "on_site"
    UNKNOWN = "unknown"


class InternshipType(str, Enum):
    PFE = "pfe"
    SUMMER = "summer"
    OFF_GRADUATE = "off_graduate"
    GENERAL = "general"


class NormalizedInternshipOffer(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    source_name: str = Field(..., description="Unique slug for the source adapter")
    source_item_id: Optional[str] = Field(None, description="Native identifier provided by source")
    canonical_url: HttpUrl = Field(..., description="Canonical link to the listing")

    title: str = Field(..., description="Raw listing title")
    normalized_title: str = Field(..., description="Lowercased, sanitized title")
    company: str = Field(..., description="Company or organization offering the internship")

    location_raw: str = Field(..., description="Unparsed location string from source")
    city: Optional[str] = None
    country: str = Field("Europe", description="Country name or ISO code")
    workplace_type: WorkplaceType = Field(default=WorkplaceType.UNKNOWN)

    internship_type: InternshipType = Field(default=InternshipType.PFE)
    description: str = Field(..., description="Sanitized clean HTML or plain text description")
    required_skills: List[str] = Field(default_factory=list, description="Extracted AI/Data skill keywords")
    languages: List[str] = Field(default_factory=list, description="Extracted language requirements")

    published_at: Optional[datetime] = None
    application_deadline: Optional[datetime] = None
    first_seen_at: datetime = Field(default_factory=datetime.utcnow)
    last_seen_at: datetime = Field(default_factory=datetime.utcnow)

    fingerprint: Optional[str] = Field(None, description="SHA256 fingerprint for fall-back deduplication")

    @field_serializer('canonical_url')
    def serialize_url(self, url: HttpUrl, _info):
        return str(url)

    @field_serializer('published_at', 'application_deadline', 'first_seen_at', 'last_seen_at')
    def serialize_dt(self, dt: Optional[datetime], _info):
        return dt.isoformat() if dt else None