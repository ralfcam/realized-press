# bwe/schema.py
from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
from typing import Any, List, Optional
import yaml
from pydantic import BaseModel, Field, field_validator, model_validator

KDP_BACKEND_BOX_COUNT = 7
KDP_BACKEND_BOX_MAX_BYTES = 50


class EpistemicLens(str, Enum):
    TECHNICAL = "technical"
    ORGANIZATIONAL = "organizational"
    PHILOSOPHICAL = "philosophical"
    BIOLOGICAL = "biological"
    ECOLOGICAL = "ecological"
    SCIENCE = "science"
    INTERPRETATION = "interpretation"
    ART = "art"


class ReadabilityTargets(BaseModel):
    """ARC-71 / ARC-72: Split-Register Bestseller Readability Targets (body prose above ## Notes)."""

    max_flesch_kincaid_grade: float = Field(default=10.5, le=12.0)
    target_flesch_kincaid_grade: float = Field(default=9.5, le=11.0)
    max_avg_sentence_words: float = Field(default=19.0, le=22.0)
    max_single_sentence_words: int = Field(default=35, le=50)
    max_jargon_density_pct: float = Field(
        default=1.5, description="Max % of 4+ syllable clinical terms in body prose"
    )


class KdpMarketingMetadata(BaseModel):
    """ARC-72: Search-Intent & Amazon KDP Metadata Specification."""

    primary_subtitle: str
    bisac_categories: List[str] = Field(default_factory=list, max_length=3)
    backend_keywords: List[str] = Field(
        default_factory=list,
        max_length=KDP_BACKEND_BOX_COUNT,
        description="7 KDP backend search boxes, each at most 50 UTF-8 bytes",
    )
    target_search_clusters: List[str] = Field(default_factory=list)

    @field_validator("backend_keywords")
    @classmethod
    def _boxes_fit_kdp_limit(cls, boxes: List[str]) -> List[str]:
        """Each box is capped at 50 bytes (stricter than 50 characters for non-ASCII text)."""
        too_long = [b for b in boxes if len(b.encode("utf-8")) > KDP_BACKEND_BOX_MAX_BYTES]
        if too_long:
            raise ValueError(
                f"KDP backend keyword box(es) exceed {KDP_BACKEND_BOX_MAX_BYTES} UTF-8 bytes: {too_long}"
            )
        return boxes


class MovementSpec(BaseModel):
    id: str
    title: str


class ChapterSpec(BaseModel):
    slug: str = Field(..., pattern=r"^\d{2}-[a-z0-9-]+$")
    title: str
    subtitle: Optional[str] = Field(
        default=None, description="High-intent search subtitle paired with literary title (ARC-71)"
    )
    audio_blocks: Optional[int] = Field(default=None, ge=1)
    footnotes_migrated: bool = True


class OKFSpec(BaseModel):
    version: str = "0.2"
    total_cards: int = Field(default=6, ge=0)
    stable_cards: int = Field(default=0, ge=0)
    locked_dois: int = Field(default=0, ge=0)
    retractions: int = Field(default=0, ge=0)
    genetically_informed_triangulation: bool = False
    scaffolding_policy: str = (
        "Purged harness prose; calibrated verbs in text; all OKF metadata and clinical jargon isolated in chapter-local ## Notes."
    )


class AudioSpec(BaseModel):
    sample_rate_bytes_per_sec: int = 48000
    pcm_cache_dir: str = ".cache/tts_pcm"
    total_semantic_blocks: Optional[int] = None
    auto_scroll_grace_timer_ms: int = 5000
    tts_model_chain: List[str] = Field(
        default=[
            "gemini-2.5-pro-preview-tts",
            "gemini-3.8-flash-tts",
            "gemini-3.1-flash-tts-preview",
            "gemini-2.5-flash-preview-tts",
        ]
    )


class KDPPrintSpec(BaseModel):
    trim_size: str = "6x9"
    wrap_cover_dimensions_in: Optional[str] = None
    spine_width_in: Optional[float] = None
    spine_width_mm: Optional[float] = None
    interior_pdf: Optional[str] = None
    cover_pdf: Optional[str] = None


class BookSpec(BaseModel):
    id: str = Field(..., pattern=r"^book-\d{2}-[a-z0-9-]+$")
    path: str = Field(
        default=".",
        description="Relative directory path inside series/<slug>/ ('.' for single-volume series, or 'book-01-...' for multi-book series).",
    )
    title: str
    subtitle: Optional[str] = None
    status: str = Field(
        default="outline", pattern=r"^(outline|outlined|draft|drafting|research-seeded|rc|complete)$"
    )
    target_words: int = Field(default=19500, ge=1000)
    min_okf_cards: int = Field(default=6, ge=1)
    total_footnotes: Optional[int] = None
    readability_targets: ReadabilityTargets = Field(default_factory=ReadabilityTargets)
    movements: List[MovementSpec] = Field(default_factory=list)
    chapters: List[ChapterSpec] = Field(default_factory=list)


class SeriesManifest(BaseModel):
    """ARC-57 / ARC-72: Unified declarative series.yaml schema for all Realized Press series."""

    slug: str = Field(..., pattern=r"^[a-z0-9-]+$")
    title: str
    subtitle: Optional[str] = None
    linear_project_id: Optional[str] = None
    version: str = "v0.1"
    epistemic_contract: str = "Science -> Interpretation -> Art"
    governing_principle: Optional[str] = None
    lenses: List[EpistemicLens]
    okf_spec: OKFSpec = Field(default_factory=OKFSpec)
    audio_spec: AudioSpec = Field(default_factory=AudioSpec)
    readability_targets: ReadabilityTargets = Field(default_factory=ReadabilityTargets)
    kdp_marketing: Optional[KdpMarketingMetadata] = None
    kdp_print_spec: Optional[KDPPrintSpec] = None
    books: List[BookSpec] = Field(..., min_length=1)

    @model_validator(mode="before")
    @classmethod
    def normalize_manifest(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        # Fallback slug from series_id
        if "slug" not in data and "series_id" in data:
            data["slug"] = data["series_id"]

        # Normalize epistemic_contract if structured
        raw_contract = data.get("epistemic_contract")
        if isinstance(raw_contract, dict):
            if "lenses" not in data and "three_lenses" in raw_contract:
                data["lenses"] = [l.get("id", "").lower() for l in raw_contract["three_lenses"] if "id" in l]
            data["epistemic_contract"] = "Technical -> Organizational -> Philosophical"

        if "lenses" not in data or not data["lenses"]:
            data["lenses"] = ["technical", "organizational", "philosophical"]

        # Populate kdp_marketing from monetization.kdp + marketing_intelligence if not explicitly set
        if "kdp_marketing" not in data:
            mon_kdp = (data.get("monetization") or {}).get("kdp") or {}
            mi = data.get("marketing_intelligence") or {}
            if mon_kdp or mi:
                data["kdp_marketing"] = {
                    "primary_subtitle": data.get("subtitle") or "",
                    "bisac_categories": (mon_kdp.get("bisac_categories") or [])[:3],
                    "backend_keywords": (mon_kdp.get("backend_keywords") or [])[:7],
                    "target_search_clusters": mi.get("high_intent_topic_clusters") or [],
                }

        return data


def export_json_schema(output_path: Path) -> None:
    schema = SeriesManifest.model_json_schema()
    output_path.write_text(json.dumps(schema, indent=2), encoding="utf-8")


def validate_series_yaml(yaml_path: Path) -> SeriesManifest:
    raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    return SeriesManifest.model_validate(raw)
