import re
from bot.lottery import _fetch_html, _latest_block

h = _fetch_html("mn")
day_id, b = _latest_block(h, "mn_")
print("day", day_id, "len", len(b))
m = re.search(r'<table class="[^"]*table-xsmn[^"]*"[^>]*>(.*?)</table>', b, re.S | re.I)
print("table", bool(m))
if m:
    t = m.group(1)[:1500]
    print(t[:800])
    headers = re.split(r"<th[^>]*>", t)
    print("split th", len(headers))
