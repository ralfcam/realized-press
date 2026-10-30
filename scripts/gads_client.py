#!/usr/bin/env python3
"""Google Ads Keyword Planner adapter for Realized Press Marketing Intelligence (BWE v0.6.0, ARC-73).

Two ways to obtain empirical search demand, both normalised to ``EnrichedKeywordMetric``:

1. ``GoogleAdsKeywordClient`` wraps ``KeywordPlanIdeaService`` (``GenerateKeywordHistoricalMetrics`` to
   enrich exact strings, ``GenerateKeywordIdeas`` to expand seed topics) with batching, retry on
   transient/quota errors only, and keyword sanitising. The ``google-ads`` SDK is imported lazily, so
   this module (and everything that imports it) works without the SDK or credentials installed.
2. ``parse_native_gkp_csv_export`` ingests a CSV exported from the Keyword Planner web UI (UTF-16LE,
   tab-separated, two preamble lines, ``"1K - 10K"`` range strings), which needs no Developer Token.

Provenance matters: ``source_tier`` is ``gads_api`` or ``gkp_csv_export`` for everything produced here.
"""
from __future__ import annotations

import csv
import io
import os
import re
import time
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

TIER_GADS_API = "gads_api"
TIER_GKP_EXPORT = "gkp_csv_export"

HISTORICAL_METRICS_BATCH = 10_000   # GenerateKeywordHistoricalMetrics keyword cap per request
IDEA_SEED_BATCH = 20                # GenerateKeywordIdeas keyword_seed cap per request
IDEA_CALL_SPACING_S = 1.0           # stay under ~1 idea request/second
MAX_KEYWORD_CHARS = 80              # Google Ads keyword text limits
MAX_KEYWORD_WORDS = 10

_MONTHS = {
    "JANUARY": 1, "FEBRUARY": 2, "MARCH": 3, "APRIL": 4, "MAY": 5, "JUNE": 6, "JULY": 7,
    "AUGUST": 8, "SEPTEMBER": 9, "OCTOBER": 10, "NOVEMBER": 11, "DECEMBER": 12,
}
_MONTH_ABBR = {name[:3]: num for name, num in _MONTHS.items()}

# Competition label -> midpoint of Google's 0-100 index bands (LOW 0-33, MEDIUM 34-66, HIGH 67-100).
_COMPETITION_LABEL = {"low": 0.17, "medium": 0.50, "high": 0.83}

_RETRYABLE_MARKERS = (
    "RESOURCE_EXHAUSTED", "RESOURCE_TEMPORARILY_EXHAUSTED", "RATE_EXCEEDED",
    "TRANSIENT_ERROR", "INTERNAL_ERROR", "UNAVAILABLE", "DEADLINE_EXCEEDED",
)


@dataclass
class EnrichedKeywordMetric:
    query: str
    monthly_volume: int
    yoy_trend_pct: float
    competition_index: float          # 0.0-1.0 (Google's 0-100 index / 100)
    cpc_low_usd: float
    cpc_high_usd: float
    monthly_histogram: List[Dict[str, int]] = field(default_factory=list)  # [{"year","month","searches"}]
    volume_range_high: Optional[int] = None   # set when the source only gave a range (UI export, no spend)
    source_tier: str = TIER_GADS_API


@dataclass
class GkpExport:
    metrics: List[EnrichedKeywordMetric]
    warnings: List[str] = field(default_factory=list)
    skipped_rows: int = 0


# ---------------------------------------------------------------------------
# Trend
# ---------------------------------------------------------------------------

def compute_trend_from_histogram(volumes: Sequence[Dict[str, int]]) -> float:
    """Percent change of the latest 3 months' mean against the earliest 3 months' mean.

    Keyword Planner returns at most 12 months, so the two windows sit ~9 months apart; this is a
    window trend, not a strict year-over-year figure (a UI export's own ``YoY change`` column is
    preferred when present). The API does not guarantee chronological order, so points are sorted
    first. Returns 0.0 with fewer than 6 usable points.
    """
    points = [
        v for v in volumes
        if v.get("searches") is not None and v.get("year") is not None and v.get("month") is not None
    ]
    points.sort(key=lambda v: (int(v["year"]), int(v["month"])))
    values = [int(v["searches"]) for v in points]
    if len(values) < 6:
        return 0.0
    early = sum(values[:3]) / 3.0
    recent = sum(values[-3:]) / 3.0
    if early <= 0:
        return 100.0 if recent > 0 else 0.0
    return round((recent - early) / early * 100.0, 1)


# ---------------------------------------------------------------------------
# Value parsing (Keyword Planner UI export)
# ---------------------------------------------------------------------------

_RANGE_RE = re.compile(
    r"^\s*([\d.,]+)\s*([kKmM]?)\s*(?:[\u2013\u2014\-]|to)\s*([\d.,]+)\s*([kKmM]?)\s*$"
)
_NUMBER_RE = re.compile(r"^\s*([\d.,]+)\s*([kKmM]?)\s*$")


def _scaled(number: str, suffix: str) -> int:
    value = float(number.replace(",", "").replace(" ", ""))
    value *= {"": 1, "k": 1_000, "m": 1_000_000}[suffix.lower()]
    return int(round(value))


def parse_volume_value(text: Optional[str]) -> Tuple[int, Optional[int]]:
    """Parse ``"12500"``, ``"1K"``, ``"1K - 10K"``; returns (low, high_or_None). Blank/-/-- gives (0, None).

    Without active ad spend Google shows ranges instead of exact counts; the low bound is returned as
    the conservative volume and the high bound is kept for reference.
    """
    if text is None:
        return 0, None
    value = str(text).strip()
    if not value or value.lower() in {"-", "\u2013", "\u2014", "--", "nan", "none", "null"}:
        return 0, None
    value = re.sub(r"(?<=\d)\s+(?=\d)", "", value)
    m = _RANGE_RE.match(value)
    if m:
        low, high = _scaled(m.group(1), m.group(2)), _scaled(m.group(3), m.group(4))
        return (low, high) if high >= low else (high, low)
    m = _NUMBER_RE.match(value)
    if m:
        return _scaled(m.group(1), m.group(2)), None
    return 0, None


def parse_percent(text: Optional[str]) -> Optional[float]:
    """``"-12%"`` -> -12.0; blank or non-numeric (e.g. an infinity glyph) -> None."""
    if text is None:
        return None
    val_str = str(text).strip().lower()
    if val_str in {"nan", "none", "null", "", "-", "--"}:
        return None
    cleaned = str(text).strip().replace(",", "").replace("+", "").rstrip("%").strip()
    if not cleaned:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def parse_money(text: Optional[str]) -> float:
    if text is None:
        return 0.0
    val_str = str(text).strip().lower()
    if val_str in {"nan", "none", "null", "", "-", "--"}:
        return 0.0
    cleaned = re.sub(r"[^\d.\-]", "", str(text or "").replace(",", ""))
    try:
        return round(float(cleaned), 2) if cleaned not in {"", "-", "."} else 0.0
    except ValueError:
        return 0.0


def decode_export_bytes(raw: bytes) -> str:
    """Decode a Keyword Planner export: UTF-16 (BOM or BOM-less LE), UTF-8 (BOM), else cp1252."""
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        return raw.decode("utf-16")
    if raw.startswith(b"\xef\xbb\xbf"):
        return raw.decode("utf-8-sig")
    if len(raw) >= 4 and raw[1:2] == b"\x00" and raw[3:4] == b"\x00":
        return raw.decode("utf-16-le")
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("cp1252", errors="replace")


def parse_native_gkp_csv_export(source: "Path | str | bytes") -> GkpExport:
    """Parse a Google Ads Keyword Planner UI export (English column headers).

    Handles UTF-16LE/UTF-8 encodings, tab or comma delimiters, the two preamble lines above the header
    row, ``"1K - 10K"`` volume ranges, ``Three month change`` / ``YoY change`` percentages,
    ``Competition (indexed value)``, top-of-page bids and ``Searches: Mon YYYY`` monthly columns.
    Rows without any volume are skipped and counted.
    """
    if isinstance(source, bytes):
        raw = source
    elif isinstance(source, Path):
        raw = source.read_bytes()
    elif isinstance(source, str):
        if "\n" in source or "\r" in source or "\t" in source:
            raw = source.encode("utf-8")
        else:
            p = Path(source)
            raw = p.read_bytes() if p.exists() else source.encode("utf-8")
    else:
        raw = Path(source).read_bytes()
    lines = decode_export_bytes(raw).splitlines()

    header_idx = next(
        (
            i for i, line in enumerate(lines[:15])
            if ("avg. monthly searches" in line.lower() or "avgmonthlysearches" in line.lower())
            and re.search(r"(^|[\t,\"])\s*keyword\b", line.lower())
        ),
        None,
    )
    if header_idx is None:
        raise ValueError("not a Keyword Planner export: no 'Keyword' / 'Avg. monthly searches' header row found")

    delimiter = "\t" if "\t" in lines[header_idx] else ","
    rows = list(csv.reader(io.StringIO("\n".join(lines[header_idx:])), delimiter=delimiter))
    header = [c.strip().lower().lstrip("\ufeff") for c in rows[0]]

    def col(*names: str) -> Optional[int]:
        return next((header.index(n) for n in names if n in header), None)

    c_kw = col("keyword")
    c_vol = col("avg. monthly searches", "avgmonthlysearches")
    c_3m = col("three month change")
    c_yoy = col("yoy change")
    c_label = col("competition")
    c_idx = col("competition (indexed value)", "competitionindex")
    c_low = col("top of page bid (low range)", "lowtopofpagebid")
    c_high = col("top of page bid (high range)", "hightopofpagebid")
    c_cur = col("currency")
    month_cols = []
    for i, name in enumerate(header):
        m = re.fullmatch(r"searches:\s*([a-z]{3})[a-z]*\s+(\d{4})", name)
        if m and m.group(1).upper() in _MONTH_ABBR:
            month_cols.append((i, int(m.group(2)), _MONTH_ABBR[m.group(1).upper()]))

    def cell(row: List[str], idx: Optional[int]) -> str:
        return row[idx].strip() if idx is not None and idx < len(row) else ""

    result = GkpExport(metrics=[])
    non_usd = set()
    for row in rows[1:]:
        keyword = cell(row, c_kw).lower()
        if not keyword:
            continue
        low, high = parse_volume_value(cell(row, c_vol))
        if low == 0 and high is None:
            result.skipped_rows += 1
            continue

        histogram = []
        for idx, year, month in month_cols:
            searches, _ = parse_volume_value(cell(row, idx))
            if cell(row, idx):
                histogram.append({"year": year, "month": month, "searches": searches})

        trend = parse_percent(cell(row, c_yoy))
        if trend is None and len(histogram) >= 6:
            trend = compute_trend_from_histogram(histogram)
        if trend is None:
            trend = parse_percent(cell(row, c_3m))
        trend = round(trend or 0.0, 1)

        comp_raw = cell(row, c_idx)
        if comp_raw:
            comp = round(min(max(parse_percent(comp_raw) or 0.0, 0.0), 100.0) / 100.0, 2)
        else:
            comp = _COMPETITION_LABEL.get(cell(row, c_label).lower(), 0.0)

        currency = cell(row, c_cur).upper()
        bid_low, bid_high = parse_money(cell(row, c_low)), parse_money(cell(row, c_high))
        if currency and currency != "USD" and (bid_low or bid_high):
            non_usd.add(currency)

        result.metrics.append(
            EnrichedKeywordMetric(
                query=keyword,
                monthly_volume=low,
                yoy_trend_pct=trend,
                competition_index=comp,
                cpc_low_usd=bid_low,
                cpc_high_usd=bid_high,
                monthly_histogram=histogram,
                volume_range_high=high,
                source_tier=TIER_GKP_EXPORT,
            )
        )

    if non_usd:
        result.warnings.append(
            f"bids exported in {', '.join(sorted(non_usd))}, not USD; cpc_*_usd columns are unconverted"
        )
    return result


# ---------------------------------------------------------------------------
# Keyword hygiene
# ---------------------------------------------------------------------------

def sanitize_keyword(query: str) -> Optional[str]:
    """Make a query safe for Google Ads keyword endpoints, or None if it cannot be.

    Google Ads rejects an entire request when one keyword has disallowed symbols, exceeds 80
    characters, or has more than 10 words, so unsuitable strings are filtered before batching.
    """
    cleaned = re.sub(r"[^\w\s'&-]", " ", query.lower().replace("_", " "))
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if not cleaned or len(cleaned) > MAX_KEYWORD_CHARS or len(cleaned.split()) > MAX_KEYWORD_WORDS:
        return None
    return cleaned


def cluster_to_seed_phrases(text: str) -> List[str]:
    """Split a topic-cluster sentence into short keyword-seed phrases (2-6 words each)."""
    parts = re.split(r",|;|\(|\)|/|\bvs\.?\b|\band\b|:", text, flags=re.IGNORECASE)
    phrases = []
    for part in parts:
        phrase = sanitize_keyword(part)
        if phrase and 2 <= len(phrase.split()) <= 6:
            phrases.append(phrase)
    return list(dict.fromkeys(phrases))


def is_retryable_error(exc: BaseException) -> bool:
    """True for quota / transient Google Ads and gRPC failures; auth and argument errors are not."""
    texts: List[str] = [type(exc).__name__]
    failure = getattr(exc, "failure", None)
    if failure is not None:
        for err in getattr(failure, "errors", None) or []:
            texts.append(str(getattr(err, "error_code", "")))
    code_fn = getattr(exc, "code", None)
    if callable(code_fn):
        try:
            texts.append(str(code_fn()))
        except Exception:  # noqa: BLE001 - defensive: a broken exc.code() must not mask the real error
            pass
    joined = " ".join(texts).upper()
    return any(marker in joined for marker in _RETRYABLE_MARKERS)


def _month_number(value: Any) -> int:
    name = getattr(value, "name", None)
    if isinstance(name, str) and name.upper() in _MONTHS:
        return _MONTHS[name.upper()]
    if isinstance(value, str) and value.upper() in _MONTHS:
        return _MONTHS[value.upper()]
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


# ---------------------------------------------------------------------------
# Google Ads API client
# ---------------------------------------------------------------------------

class GoogleAdsKeywordClient:
    """Fault-tolerant wrapper around ``KeywordPlanIdeaService``.

    Credentials come from ``google-ads.yaml`` (``GOOGLE_ADS_CONFIGURATION_FILE_PATH`` or the repo root)
    or ``GOOGLE_ADS_*`` environment variables; the customer id from ``GOOGLE_ADS_CUSTOMER_ID``. When
    the SDK or credentials are missing ``is_available`` is False and callers fall back to cached or
    seed data. Tokens are never logged.
    """

    def __init__(
        self,
        customer_id: Optional[str] = None,
        login_customer_id: Optional[str] = None,
        geo_target_id: Optional[str] = None,
        language_id: Optional[str] = None,
        client: Any = None,
        sleep_fn: Callable[[float], None] = time.sleep,
        config_path: Optional[Path] = None,
    ) -> None:
        self.customer_id = re.sub(r"\D", "", customer_id or os.getenv("GOOGLE_ADS_CUSTOMER_ID", ""))
        self.login_customer_id = re.sub(r"\D", "", login_customer_id or os.getenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID", ""))
        self.geo_target_id = geo_target_id or os.getenv("GOOGLE_ADS_GEO_TARGET_ID", "2840")  # 2840 = United States
        self.language_id = language_id or os.getenv("GOOGLE_ADS_LANGUAGE_ID", "1000")        # 1000 = English
        self._sleep = sleep_fn
        self._config_path = config_path
        self._client = client if client is not None else self._init_sdk_client(config_path, self.login_customer_id)
        if self._client is not None and self.login_customer_id:
            try:
                self._client.login_customer_id = self.login_customer_id
            except Exception:
                pass

    @staticmethod
    def _init_sdk_client(config_path: Optional[Path] = None, login_customer_id: Optional[str] = None) -> Any:
        try:
            from google.ads.googleads.client import GoogleAdsClient
        except ImportError:
            return None

        candidates = []
        if config_path is not None:
            candidates.append(Path(config_path))
        if os.getenv("GOOGLE_ADS_CONFIGURATION_FILE_PATH"):
            candidates.append(Path(os.environ["GOOGLE_ADS_CONFIGURATION_FILE_PATH"]))
        candidates += [Path("google-ads.yaml"), Path(__file__).resolve().parent.parent / "google-ads.yaml"]
        try:
            for path in candidates:
                if path.is_file():
                    c = GoogleAdsClient.load_from_storage(str(path))
                    if login_customer_id and hasattr(c, "login_customer_id"):
                        c.login_customer_id = login_customer_id
                    return c
            if os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN"):
                c = GoogleAdsClient.load_from_env()
                if login_customer_id and hasattr(c, "login_customer_id"):
                    c.login_customer_id = login_customer_id
                return c
        except Exception as exc:  # noqa: BLE001 - bad creds must degrade to the fallback tiers
            print(f"[WARN] Google Ads client init skipped ({type(exc).__name__}); using fallback tier.")
        return None

    @property
    def is_available(self) -> bool:
        return self._client is not None and bool(self.customer_id)

    @property
    def is_configured(self) -> bool:
        return self.is_available

    # -- API calls ---------------------------------------------------------

    def fetch_historical_metrics(self, queries: Iterable[str]) -> Dict[str, EnrichedKeywordMetric]:
        """Enrich exact query strings with 12-month Google Ads search metrics.

        Returns a dict keyed by the lower-cased input query. Queries Google cannot accept (see
        ``sanitize_keyword``) are omitted. A returned metric with volume 0 is a real answer (no
        measurable searches) and is worth caching.
        """
        by_sanitized: Dict[str, List[str]] = {}
        for q in dict.fromkeys(x.strip().lower() for x in queries if x and x.strip()):
            s = sanitize_keyword(q)
            if s:
                by_sanitized.setdefault(s, []).append(q)
        if not by_sanitized or not self.is_available:
            return {}

        idea_service = self._client.get_service("KeywordPlanIdeaService")
        ga_service = self._client.get_service("GoogleAdsService")

        keywords = list(by_sanitized)
        exact: Dict[str, EnrichedKeywordMetric] = {}
        variants: Dict[str, EnrichedKeywordMetric] = {}
        for start in range(0, len(keywords), HISTORICAL_METRICS_BATCH):
            request = self._client.get_type("GenerateKeywordHistoricalMetricsRequest")
            request.customer_id = self.customer_id
            request.keywords.extend(keywords[start:start + HISTORICAL_METRICS_BATCH])
            request.geo_target_constants.append(ga_service.geo_target_constant_path(self.geo_target_id))
            request.language = ga_service.language_constant_path(self.language_id)
            request.keyword_plan_network = self._client.enums.KeywordPlanNetworkEnum.GOOGLE_SEARCH

            response = self._call_with_backoff(idea_service.generate_keyword_historical_metrics, request)
            for item in response.results:
                metric = self._extract_metric(item.text, item.keyword_metrics)
                exact[metric.query] = metric
                for variant in getattr(item, "close_variants", []) or []:
                    variants.setdefault(variant.strip().lower(), metric)

        results: Dict[str, EnrichedKeywordMetric] = {}
        for sanitized, originals in by_sanitized.items():
            metric = exact.get(sanitized) or variants.get(sanitized)
            if metric is None:
                continue
            for original in originals:
                results[original] = replace(metric, query=original)
        return results

    def generate_keyword_ideas(
        self, seed_phrases: Sequence[str], max_results: int = 100, min_volume: int = 0
    ) -> List[EnrichedKeywordMetric]:
        """Expand seed phrases into adjacent queries, highest volume first."""
        seeds = list(dict.fromkeys(s for s in (sanitize_keyword(p) for p in seed_phrases) if s))
        if not seeds or not self.is_available:
            return []

        idea_service = self._client.get_service("KeywordPlanIdeaService")
        ga_service = self._client.get_service("GoogleAdsService")

        ideas: Dict[str, EnrichedKeywordMetric] = {}
        for n, start in enumerate(range(0, len(seeds), IDEA_SEED_BATCH)):
            if n:
                self._sleep(IDEA_CALL_SPACING_S)
            request = self._client.get_type("GenerateKeywordIdeasRequest")
            request.customer_id = self.customer_id
            request.language = ga_service.language_constant_path(self.language_id)
            request.geo_target_constants.append(ga_service.geo_target_constant_path(self.geo_target_id))
            request.keyword_plan_network = self._client.enums.KeywordPlanNetworkEnum.GOOGLE_SEARCH
            request.keyword_seed.keywords.extend(seeds[start:start + IDEA_SEED_BATCH])
            request.page_size = min(max_results, 1000)

            response = self._call_with_backoff(idea_service.generate_keyword_ideas, request)
            taken = 0
            for idea in response:
                metric = self._extract_metric(idea.text, idea.keyword_idea_metrics)
                if metric.monthly_volume >= min_volume:
                    ideas.setdefault(metric.query, metric)
                taken += 1
                if taken >= max_results:
                    break
        return sorted(ideas.values(), key=lambda m: (-m.monthly_volume, m.query))[:max_results]

    # -- helpers -----------------------------------------------------------

    @staticmethod
    def _extract_metric(text: str, m: Any) -> EnrichedKeywordMetric:
        histogram = [
            {
                "year": int(v.year),
                "month": _month_number(v.month),
                "searches": int(getattr(v, "monthly_searches", 0) or 0),
            }
            for v in (getattr(m, "monthly_search_volumes", None) or [])
        ]
        histogram.sort(key=lambda p: (p["year"], p["month"]))
        return EnrichedKeywordMetric(
            query=text.strip().lower(),
            monthly_volume=int(getattr(m, "avg_monthly_searches", 0) or 0),
            yoy_trend_pct=compute_trend_from_histogram(histogram),
            competition_index=round(int(getattr(m, "competition_index", 0) or 0) / 100.0, 2),
            cpc_low_usd=round(int(getattr(m, "low_top_of_page_bid_micros", 0) or 0) / 1_000_000, 2),
            cpc_high_usd=round(int(getattr(m, "high_top_of_page_bid_micros", 0) or 0) / 1_000_000, 2),
            monthly_histogram=histogram,
            source_tier=TIER_GADS_API,
        )

    def _call_with_backoff(self, fn: Callable[..., Any], request: Any, max_attempts: int = 4) -> Any:
        """Call fn(request=...), retrying only quota/transient failures with exponential backoff."""
        for attempt in range(1, max_attempts + 1):
            try:
                return fn(request=request)
            except Exception as exc:  # noqa: BLE001 - classified below, re-raised if not retryable
                if attempt == max_attempts or not is_retryable_error(exc):
                    raise
                delay = min(2 ** attempt, 60) + 0.5
                print(f"[WARN] Google Ads API transient error ({type(exc).__name__}); retry {attempt}/{max_attempts - 1} in {delay:.1f}s")
                self._sleep(delay)
        raise AssertionError("unreachable")  # pragma: no cover


# ---------------------------------------------------------------------------
# Diagnostics & CLI
# ---------------------------------------------------------------------------

def check_environment(
    config_path: Optional[Path] = None,
    customer_id: Optional[str] = None,
    login_customer_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Inspect environment, SDK presence, and configuration files for Google Ads."""
    sdk_installed = False
    try:
        import google.ads.googleads.client  # noqa: F401
        sdk_installed = True
    except ImportError:
        pass

    resolved_config = None
    candidates = []
    if config_path is not None:
        candidates.append(Path(config_path))
    if os.getenv("GOOGLE_ADS_CONFIGURATION_FILE_PATH"):
        candidates.append(Path(os.environ["GOOGLE_ADS_CONFIGURATION_FILE_PATH"]))
    candidates += [Path("google-ads.yaml"), Path(__file__).resolve().parent.parent / "google-ads.yaml"]

    for p in candidates:
        if p.is_file():
            resolved_config = p
            break

    client = GoogleAdsKeywordClient(
        customer_id=customer_id,
        login_customer_id=login_customer_id,
        config_path=config_path,
    )
    return {
        "sdk_installed": sdk_installed,
        "config_file": str(resolved_config) if resolved_config else None,
        "customer_id": client.customer_id or None,
        "login_customer_id": client.login_customer_id or None,
        "is_available": client.is_available,
    }


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Google Ads API Keyword Planner CLI & Diagnostic Tool (BWE v0.6.0)")
    parser.add_argument("--check", action="store_true", help="Run diagnostic health check on SDK and credentials")
    parser.add_argument("--query", nargs="+", help="Enrich specific keywords via Google Ads API")
    parser.add_argument("--ideas", nargs="+", help="Generate keyword ideas from seed phrases")
    parser.add_argument("--customer-id", help="Operating customer ID (10 digits without dashes)")
    parser.add_argument("--login-customer-id", help="Manager customer ID (MCC, 10 digits without dashes)")
    parser.add_argument("--config", type=Path, help="Path to google-ads.yaml")
    args = parser.parse_args()

    if args.check or (not args.query and not args.ideas):
        report = check_environment(
            config_path=args.config,
            customer_id=args.customer_id,
            login_customer_id=args.login_customer_id,
        )
        print("=== Google Ads API Diagnostic Health Check ===")
        print(f"SDK Installed:         {'PASS' if report['sdk_installed'] else 'FAIL (run: pip install google-ads>=25.1.0)'}")
        print(f"Config File:           {report['config_file'] or 'None found (copy from google-ads.yaml.example)'}")
        print(f"Customer ID:           {report['customer_id'] or 'Not configured (set GOOGLE_ADS_CUSTOMER_ID)'}")
        print(f"Login Customer ID:     {report['login_customer_id'] or 'None (optional MCC id)'}")
        print(f"Client Ready:          {'PASS (API operational)' if report['is_available'] else 'DISABLED (fallback tiers will be used)'}")
        if not report["is_available"]:
            print("\nTo enable live Google Ads API demand telemetry:")
            print("  1. Copy google-ads.yaml.example to google-ads.yaml")
            print("  2. Fill in developer_token, client_id, client_secret, refresh_token, and customer_id")
            print("  3. Run: python scripts/gads_client.py --check")
        return 0 if report["is_available"] else 1

    client = GoogleAdsKeywordClient(
        customer_id=args.customer_id,
        login_customer_id=args.login_customer_id,
        config_path=args.config,
    )
    if not client.is_available:
        print("[ERROR] Google Ads client is not configured. Run with --check to diagnose.")
        return 1

    if args.query:
        queries = [item.strip() for q in args.query for item in q.split(",") if item.strip()]
        metrics = client.fetch_historical_metrics(queries)
        print(f"Fetched {len(metrics)} metric(s):")
        for q, m in metrics.items():
            print(f"  - {q}: {m.monthly_volume}/mo (YoY {m.yoy_trend_pct:+g}%, Comp: {m.competition_index}, CPC: ${m.cpc_low_usd:.2f}-${m.cpc_high_usd:.2f})")

    if args.ideas:
        seeds = [item.strip() for s in args.ideas for item in s.split(",") if item.strip()]
        ideas = client.generate_keyword_ideas(seeds)
        print(f"Generated {len(ideas)} idea(s):")
        for m in ideas:
            print(f"  - {m.query}: {m.monthly_volume}/mo (YoY {m.yoy_trend_pct:+g}%, Comp: {m.competition_index})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
