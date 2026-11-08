import re

with open('docs/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

m = re.search(r'<style>(.*?)</style>', html, re.DOTALL)
if m:
    css = m.group(1)
    lines = css.splitlines()
    for idx, line in enumerate(lines, 1):
        if any(k in line for k in ['width', 'min-width', 'max-width', 'padding', 'margin', 'grid-template', 'flex', 'overflow']):
            print(f"Line {idx}: {line.strip()}")
