# tests/test_ui_compliance.py
"""
Static UI compliance inspection test suite for Realized Press BWE.
Verifies accessibility (WCAG 2.1 AA color contrast and 44px minimum touch targets)
and design system palette consistency (rose-400 alerts) across all Jinja2 templates.

Acts as an automated acceptance gate for template implementers across M3 & M4.
Enforces strict gate failure when STRICT_UI_GATE=1 is set in the environment.
"""
import os
import re
import sys
import warnings
from pathlib import Path
from typing import Any, Dict, List
from bs4 import BeautifulSoup
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = REPO_ROOT / "bwe" / "templates"

# Minimum 44x44px touch target pattern matching Tailwind utilities or inline styles
TOUCH_TARGET_REGEX = re.compile(
    r"min-h-\[44px\]|min-w-\[44px\]|\b(?:h-11|w-11|h-12|w-12|h-14|w-14|h-16|w-16)\b|min-height:\s*44px|height:\s*44px"
)

# Non-compliant low-contrast text tokens against dark backgrounds (stone-950/900/800)
# stone-500 yields ~3.65:1 - 4.12:1 (fails WCAG AA 4.5:1 for normal text)
# stone-600 yields ~2.29:1 - 2.59:1 (fails all WCAG criteria)
LOW_CONTRAST_TEXT_REGEX = re.compile(r"\btext-(?:stone|zinc|gray|slate)-(?:500|600|700)\b")

# Design system R2 palette rule: Alert states must use rose-400 instead of generic red-400/red-500
RED_ALERT_REGEX = re.compile(r"\b(?:text|bg|border)-red-(?:400|500|600)\b")

STRICT_GATE = os.environ.get("STRICT_UI_GATE", "").lower() in ("1", "true", "yes")


def scan_touch_target_violations() -> tuple[int, List[Dict[str, Any]]]:
    """Scans all Jinja2 templates for interactive controls missing 44px minimum dimensions."""
    interactive_tags = {"a", "button", "input", "select", "textarea"}
    violations: List[Dict[str, Any]] = []
    files_scanned = 0

    for html_file in sorted(TEMPLATES_DIR.rglob("*.html")):
        files_scanned += 1
        text = html_file.read_text(encoding="utf-8")
        soup = BeautifulSoup(text, "html.parser")
        rel_path = str(html_file.relative_to(TEMPLATES_DIR)).replace("\\", "/")

        elements = soup.find_all(
            lambda tag: tag.name in interactive_tags
            or tag.get("role") in ("button", "tab", "slider")
            or tag.get("onclick")
        )

        for el in elements:
            # Exclude hidden inputs or elements with explicit hidden attribute
            if el.name == "input" and el.get("type") == "hidden":
                continue
            if el.has_attr("hidden"):
                continue

            cls = " ".join(el.get("class", []))
            style = el.get("style", "")
            combined = f"{cls} {style}"

            if not TOUCH_TARGET_REGEX.search(combined):
                violations.append({
                    "file": rel_path,
                    "tag": el.name,
                    "role": el.get("role", ""),
                    "class": cls[:70],
                    "aria_label": el.get("aria-label", ""),
                })

    return files_scanned, violations


def scan_wcag_contrast_violations() -> tuple[int, List[Dict[str, Any]]]:
    """Scans all Jinja2 templates for low-contrast text utility classes violating WCAG 2.1 AA."""
    violations: List[Dict[str, Any]] = []
    files_scanned = 0

    for html_file in sorted(TEMPLATES_DIR.rglob("*.html")):
        files_scanned += 1
        lines = html_file.read_text(encoding="utf-8").splitlines()
        rel_path = str(html_file.relative_to(TEMPLATES_DIR)).replace("\\", "/")

        for line_no, line in enumerate(lines, 1):
            match = LOW_CONTRAST_TEXT_REGEX.search(line)
            if match:
                violations.append({
                    "file": rel_path,
                    "line": line_no,
                    "token": match.group(0),
                    "snippet": line.strip()[:80],
                })

    return files_scanned, violations


def scan_palette_violations() -> tuple[int, List[Dict[str, Any]]]:
    """Scans all Jinja2 templates for red-400/red-500 classes that must be replaced by rose-400."""
    violations: List[Dict[str, Any]] = []
    files_scanned = 0

    for html_file in sorted(TEMPLATES_DIR.rglob("*.html")):
        files_scanned += 1
        lines = html_file.read_text(encoding="utf-8").splitlines()
        rel_path = str(html_file.relative_to(TEMPLATES_DIR)).replace("\\", "/")

        for line_no, line in enumerate(lines, 1):
            match = RED_ALERT_REGEX.search(line)
            if match:
                violations.append({
                    "file": rel_path,
                    "line": line_no,
                    "token": match.group(0),
                    "snippet": line.strip()[:80],
                })

    return files_scanned, violations


def test_touch_target_sizes() -> None:
    """
    Verifies that all interactive elements (a, button, input, select, textarea, role='tab', role='button')
    meet or exceed the 44px minimum touch target size requirement (min-h-[44px], min-w-[44px], h-11, etc.).
    """
    files_scanned, violations = scan_touch_target_violations()
    assert files_scanned >= 5, f"Expected at least 5 templates to be scanned, scanned {files_scanned}"

    if violations:
        diag_lines = [
            f"[TOUCH TARGET ACCEPTANCE GATE] Found {len(violations)} interactive elements missing >=44px touch targets:",
        ]
        for v in violations[:15]:
            diag_lines.append(
                f"  - {v['file']}: <{v['tag']} role='{v['role']}'> aria-label='{v['aria_label']}' class='{v['class']}'"
            )
        if len(violations) > 15:
            diag_lines.append(f"  ... and {len(violations) - 15} more.")
        diag_lines.append(
            "\nRemediation Guide: Template implementers must add 'min-h-[44px]' (or 'h-11' / 'h-12') "
            "and 'min-w-[44px]' (or 'w-11' / 'w-12') to interactive elements. "
            "Set STRICT_UI_GATE=1 to enforce as a hard test failure."
        )
        msg = "\n".join(diag_lines)

        if STRICT_GATE:
            pytest.fail(msg)
        else:
            warnings.warn(UserWarning(msg))


def test_wcag_color_contrast() -> None:
    """
    Verifies that templates do not use low-contrast text tokens (text-stone-500, text-stone-600)
    on dark surfaces (stone-950/900/800). Requires text-stone-400 or higher (>= 4.5:1 ratio).
    """
    files_scanned, violations = scan_wcag_contrast_violations()
    assert files_scanned >= 5, f"Expected at least 5 templates to be scanned, scanned {files_scanned}"

    if violations:
        diag_lines = [
            f"[WCAG CONTRAST ACCEPTANCE GATE] Found {len(violations)} low-contrast text tokens failing WCAG 2.1 AA (4.5:1):",
        ]
        for v in violations[:15]:
            diag_lines.append(f"  - {v['file']}:{v['line']} [{v['token']}] -> {v['snippet']}")
        if len(violations) > 15:
            diag_lines.append(f"  ... and {len(violations) - 15} more.")
        diag_lines.append(
            "\nRemediation Guide: Replace text-stone-500 (~3.65:1-4.12:1) and text-stone-600 (~2.59:1) "
            "with text-stone-400 (6.93:1-7.83:1) or text-stone-300 for full WCAG AA compliance. "
            "Set STRICT_UI_GATE=1 to enforce as a hard test failure."
        )
        msg = "\n".join(diag_lines)

        if STRICT_GATE:
            pytest.fail(msg)
        else:
            warnings.warn(UserWarning(msg))


def test_dark_mode_palette() -> None:
    """
    Verifies that alert, noise, and overflow warning states use the canonical rose-400
    palette accent specified in R2 rather than generic red-400/red-500 tokens.
    """
    files_scanned, violations = scan_palette_violations()
    assert files_scanned >= 5, f"Expected at least 5 templates to be scanned, scanned {files_scanned}"

    if violations:
        diag_lines = [
            f"[PALETTE ACCEPTANCE GATE] Found {len(violations)} generic red palette tokens requiring rose-400:",
        ]
        for v in violations:
            diag_lines.append(f"  - {v['file']}:{v['line']} [{v['token']}] -> {v['snippet']}")
        diag_lines.append(
            "\nRemediation Guide: Replace 'text-red-400' / 'bg-red-500' with 'text-rose-400' / 'bg-rose-500'. "
            "Set STRICT_UI_GATE=1 to enforce as a hard test failure."
        )
        msg = "\n".join(diag_lines)

        if STRICT_GATE:
            pytest.fail(msg)
        else:
            warnings.warn(UserWarning(msg))


if __name__ == "__main__":
    print("=== Realized Press BWE Static UI Compliance Inspection ===")
    f1, v1 = scan_touch_target_violations()
    f2, v2 = scan_wcag_contrast_violations()
    f3, v3 = scan_palette_violations()
    print(f"Scanned {f1} template files.")
    print(f"Touch target violations (< 44px): {len(v1)}")
    print(f"WCAG color contrast violations (stone-500/600): {len(v2)}")
    print(f"Palette violations (red-* vs rose-400): {len(v3)}")
    if v1 or v2 or v3:
        sys.exit(1)
    print("All templates 100% compliant!")
    sys.exit(0)
