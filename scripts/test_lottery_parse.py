import re
import httpx
from html import unescape

html = unescape(
    httpx.get(
        "https://xosodaiphat.com/xsmb-xo-so-mien-bac.html",
        headers={"User-Agent": "Mozilla/5.0"},
        follow_redirects=True,
        timeout=20,
    ).text
)

# latest result block (not display:none)
blocks = re.findall(
    r'<motion[^>]*id=kqngay_(\d+)[^>]*>(.*?)</motion',
    html,
    re.S,
)
if not blocks:
    blocks = re.findall(r'id=kqngay_(\d+)"[^>]*>(.*?)(?=<motion|</motion)', html, re.S)

print("blocks", len(blocks))
for day_id, content in blocks[:2]:
    if "display:none" in content[:200]:
        continue
    print("--- day", day_id)
    # prize rows
    for row in re.findall(r"<tr[^>]*>(.*?)</tr>", content, re.S):
        cells = re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)
        if len(cells) < 2:
            continue
        label = re.sub(r"<[^>]+>", "", cells[0]).strip()
        nums = re.findall(r"\b(\d{2,6})\b", re.sub(r"<[^>]+>", " ", cells[1]))
        if label and nums:
            print(label, nums)
