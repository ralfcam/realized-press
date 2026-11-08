import re
from bs4 import BeautifulSoup

with open('docs/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

print(f"Total HTML length: {len(html)}")
print(f"Title: {soup.title.text if soup.title else 'No title'}")

# Check elements with fixed widths or min-widths in inline styles or classes
for tag in soup.find_all(True):
    style = tag.get('style', '')
    if 'width' in style or 'min-width' in style:
        print(f"Tag <{tag.name}> id={tag.get('id')} class={tag.get('class')}: style='{style}'")
