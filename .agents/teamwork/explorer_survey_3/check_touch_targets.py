import re
from pathlib import Path
from bs4 import BeautifulSoup

def analyze_templates():
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    templates_dir = repo_root / "bwe" / "templates"
    interactive_tags = {"a", "button", "input", "select", "textarea"}

    print("=== Interactive Elements & 44px Touch Target Analysis ===")
    pattern_44 = re.compile(r"min-h-\[44px\]|min-w-\[44px\]|\b(?:h-11|w-11|h-12|w-12|h-14|h-16)\b|min-height:\s*44px|height:\s*44px")

    for html_file in sorted(templates_dir.rglob("*.html")):
        text = html_file.read_text(encoding="utf-8")
        soup = BeautifulSoup(text, "html.parser")
        elements = soup.find_all(
            lambda tag: tag.name in interactive_tags
            or tag.get("role") in ("button", "tab", "slider")
            or tag.get("onclick")
        )
        total = len(elements)
        non_compliant = []
        for el in elements:
            cls = " ".join(el.get("class", []))
            style = el.get("style", "")
            combined = f"{cls} {style}"
            if not pattern_44.search(combined):
                non_compliant.append((el.name, cls[:60], el.get("role", "")))

        rel_path = html_file.relative_to(templates_dir)
        print(f"\n{rel_path}: {total} interactive elements | {len(non_compliant)} missing explicit 44px target")
        for tag_name, cls_snippet, role in non_compliant[:4]:
            print(f"  - <{tag_name}> (role={role}): class='{cls_snippet}'")

if __name__ == "__main__":
    analyze_templates()
