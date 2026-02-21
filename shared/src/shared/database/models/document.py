from sqlmodel import SQLModel, Field, Column
from sqlalchemy import Index, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from typing import Optional, Dict, Any
from uuid import uuid4, UUID as PyUUID

class Document(SQLModel, table=True):
    id: PyUUID = Field(
        sa_column=Column(UUID(as_uuid=True), primary_key=True),
        default_factory=uuid4
    )

    crawl_id: str = Field(nullable=False)

    # maps to the meta description, empty by default
    description: Optional[str] = Field(default="")
    
    # maps to the meta title, (page title or meta title)
    title: Optional[str] = Field(nullable=False, default="")

    # url, unique
    url: str = Field(nullable=False, unique=True)

    headings: list[str] = Field(
        sa_column=Column(ARRAY(Text), nullable=False),
        default_factory=list
    )

    links: list[str] = Field(
        sa_column=Column(ARRAY(Text), nullable=False),
        default_factory=list
    )

    # text
    text: str = Field(nullable=False)

    meta_info: Dict[str, Any] = Field(
        sa_column=Column(JSONB, nullable=False)
    )