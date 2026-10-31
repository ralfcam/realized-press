import re
from pathlib import Path

def analyze_contrast_tokens():
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    templates_dir = repo_root / "bwe" / "templates"

    # Low contrast text tokens on dark backgrounds (stone-950, stone-900, stone-800)
    # stone-500 has ~3.65:1 - 4.12:1 ratio (fails WCAG AA 4.5:1 for normal text)
    # stone-600 has ~2.29:1 - 2.59:1 ratio (fails even 3.0:1)
    low_contrast_pattern = re.compile(r"\btext-(stone|zinc|gray|slate)-(500|600|700)\b")

    print("=== Low Contrast Text Tokens in Templates (WCAG AA Risk) ===")
    for html_file in sorted(templates_dir.rglob("*.html")):
        lines = html_file.read_text(encoding="utf-8").splitlines()
        hits = []
        for idx, line in enumerate(lines, 1):
            matches = low_contrast_pattern.findall(line)
            if matches:
                hits.append((idx, line.strip()))
        rel_path = html_file.relative_to(templates_dir)
        print(f"\n{rel_path}: {len(hits)} occurrences of low-contrast text tokens")
        for line_no, content in hits[:4]:
            print(f"  Line {line_no}: {content[:80]}")

if __name__ == "__main__":
    analyze_contrast_tokens()
