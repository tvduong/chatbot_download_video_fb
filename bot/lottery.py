"""Dò vé & xem KQXS 3 miền — nguồn: xosodaiphat.com"""
from __future__ import annotations

import logging
import re
import time
import unicodedata
from dataclasses import dataclass, field
from html import unescape

import httpx

log = logging.getLogger(__name__)

URLS = {
    "mb": "https://xosodaiphat.com/xsmb-xo-so-mien-bac.html",
    "mn": "https://xosodaiphat.com/xsmn-xo-so-mien-nam.html",
    "mt": "https://xosodaiphat.com/xsmt-xo-so-mien-trung.html",
}
REGION_SLUG = {"mb": "xsmb", "mn": "xsmn", "mt": "xsmt"}
NAMES = {"mb": "Miền Bắc", "mn": "Miền Nam", "mt": "Miền Trung"}
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; FBTelegramBot/1.0)"}

# Tỉnh quay thứ mấy (miền Nam) — tham khảo lịch quay
MN_DRAW_WEEKDAY: dict[str, str] = {
    "binh duong": "Thứ Sáu",
    "bd": "Thứ Sáu",
    "vinh long": "Thứ Sáu",
    "tra vinh": "Thứ Sáu",
    "tphcm": "Thứ Bảy",
    "hcm": "Thứ Bảy",
    "tp hcm": "Thứ Bảy",
}

# Mã tỉnh trên xosodaiphat (trang /xsbd-...-ngay.html)
PROVINCE_DISPLAY: dict[str, str] = {
    "binh duong": "Bình Dương",
    "bd": "Bình Dương",
    "bình dương": "Bình Dương",
    "vinh long": "Vĩnh Long",
    "tra vinh": "Trà Vinh",
    "tphcm": "TP.HCM",
    "hcm": "TP.HCM",
}

PROVINCE_CODE: dict[str, str] = {
    "binh duong": "xsbd",
    "bd": "xsbd",
    "bình dương": "xsbd",
    "vinh long": "xsvl",
    "vĩnh long": "xsvl",
    "vl": "xsvl",
    "tra vinh": "xstv",
    "trà vinh": "xstv",
    "tphcm": "xshcm",
    "hcm": "xshcm",
    "tp hcm": "xshcm",
    "can tho": "xsct",
    "cần thơ": "xsct",
    "dong nai": "xsdn",
    "đồng nai": "xsdn",
    "an giang": "xsag",
    "tay ninh": "xstn",
    "da lat": "xsdl",
    "da nang": "xsdng",
    "đà nẵng": "xsdng",
    "hue": "xshue",
    "huế": "xshue",
}

_cache: dict[str, tuple[float, DrawResult]] = {}
_CACHE_TTL = 600


@dataclass
class DrawResult:
    region: str
    date: str
    prizes: dict[str, list[str]] = field(default_factory=dict)
    provinces: dict[str, dict[str, list[str]]] | None = None
    province_filter: str | None = None


class LotteryError(Exception):
    pass


def _strip_accents(s: str) -> str:
    nfd = unicodedata.normalize("NFD", s)
    return "".join(c for c in nfd if unicodedata.category(c) != "Mn")


def display_province(name: str) -> str:
    return PROVINCE_DISPLAY.get(normalize_province(name), name.strip().title())


def normalize_province(name: str) -> str:
    s = _strip_accents(name.lower())
    s = re.sub(r"^(xs|xổ số)\s*", "", s)
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _fetch_url(url: str) -> str:
    try:
        r = httpx.get(url, headers=HEADERS, follow_redirects=True, timeout=25)
        r.raise_for_status()
        if "/404" in str(r.url) or len(r.text) < 500:
            raise LotteryError(f"Không có trang kết quả: {url}")
        return unescape(r.text)
    except httpx.HTTPError as exc:
        log.warning("Lottery fetch failed %s: %s", url, exc)
        raise LotteryError("Không lấy được kết quả. Thử lại sau.") from exc


def _fetch_html(region: str) -> str:
    url = URLS.get(region)
    if not url:
        raise LotteryError("Miền không hợp lệ. Dùng: mb, mn, mt")
    return _fetch_url(url)


def _province_code(name: str) -> str | None:
    return PROVINCE_CODE.get(normalize_province(name))


def _province_date_url(province: str, date: str) -> str:
    code = _province_code(province)
    if not code:
        raise LotteryError(
            f"Chưa hỗ trợ tỉnh «{province}». Thử: binh duong, vinh long, tphcm, can tho…"
        )
    m = re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})", date.strip())
    if not m:
        raise LotteryError("Ngày sai định dạng. Dùng: 23/05/2026")
    dd, mm, yyyy = m.group(1).zfill(2), m.group(2).zfill(2), m.group(3)
    return f"https://xosodaiphat.com/{code}-{dd}-{mm}-{yyyy}.html"


def _parse_province_page(html: str, province_name: str, date: str) -> DrawResult:
    table_m = re.search(r"<table[^>]*table-[^>]*>(.*?)</table>", html, re.S | re.I)
    if not table_m:
        raise LotteryError(f"Chưa có KQXS {province_name} ngày {date} (chưa quay / chưa cập nhật).")
    prizes = _parse_prize_rows(table_m.group(1))
    if not prizes:
        raise LotteryError(f"Không đọc được KQ {province_name} ngày {date}.")
    return DrawResult(
        region="mn",
        date=date,
        prizes=prizes,
        province_filter=province_name,
    )


def _province_listing_url(province: str) -> str:
    code = _province_code(province)
    if not code:
        return ""
    slug = normalize_province(province).replace(" ", "-")
    return f"https://xosodaiphat.com/{code}-xo-so-{slug}.html"


def _nearest_province_dates(province: str, limit: int = 3) -> list[str]:
    code = _province_code(province)
    url = _province_listing_url(province)
    if not code or not url:
        return []
    try:
        html = _fetch_url(url)
    except Exception:
        return []
    dates = re.findall(rf"/{code}-(\d{{2}}-\d{{2}}-\d{{4}})\.html", html)
    out = []
    for d in dates:
        dd, mm, yyyy = d.split("-")
        out.append(f"{dd}/{mm}/{yyyy}")
    return out[:limit]


def _date_page_url(region: str, date: str) -> str:
    """date: dd/mm/yyyy"""
    m = re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})", date.strip())
    if not m:
        raise LotteryError("Ngày sai định dạng. Dùng: 23/05/2026")
    dd, mm, yyyy = m.group(1).zfill(2), m.group(2).zfill(2), m.group(3)
    slug = REGION_SLUG[region]
    return f"https://xosodaiphat.com/{slug}-{dd}-{mm}-{yyyy}.html"


def _extract_nums(cell_html: str) -> list[str]:
    nums = re.findall(
        r'<span[^>]*class="[^"]*(?:special-prize|number-black-bold)[^"]*"[^>]*>\s*(\d+)\s*<',
        cell_html,
        re.I,
    )
    if not nums:
        nums = re.findall(r"\b(\d{2,6})\b", re.sub(r"<[^>]+>", " ", cell_html))
    return [n.strip() for n in nums if n.strip()]


def _latest_block(html: str, block_prefix: str) -> tuple[str, str]:
    pat = rf"id={block_prefix}kqngay_(\d+)([^>]*)>(.*?)(?=id={block_prefix}kqngay_|$)"
    blocks = re.findall(pat, html, re.S | re.I)
    for day_id, attrs, content in blocks:
        if "display:none" in attrs:
            continue
        if "table-xsmb" in content or "table-xsmn" in content or "table-xsmt" in content:
            return day_id, content
    raise LotteryError("Chưa có kết quả mới trên hệ thống.")


def _format_date(day_id: str) -> str:
    if len(day_id) == 8:
        return f"{day_id[:2]}/{day_id[2:4]}/{day_id[4:]}"
    return day_id


def _parse_prize_rows(block: str) -> dict[str, list[str]]:
    prizes: dict[str, list[str]] = {}
    for seg in re.split(r"<tr[^>]*>", block, flags=re.I):
        parts = [p for p in re.split(r"<td[^>]*>", seg, flags=re.I) if p.strip()]
        if len(parts) < 2:
            continue
        label = re.sub(r"<[^>]+>", "", parts[0]).strip()
        if not label or label.startswith("Mã") or not re.match(r"^G\.", label):
            continue
        nums = _extract_nums(parts[1])
        if nums:
            prizes[label] = nums
    return prizes


def _parse_multi_province_table(html: str, region: str, date_label: str) -> DrawResult:
    table_m = re.search(
        r"<table[^>]*table-xsm[nt][^>]*>(.*?)</table>",
        html,
        re.S | re.I,
    )
    if not table_m:
        raise LotteryError(f"Không có bảng KQXS ngày {date_label}.")
    table = table_m.group(1)
    thead = table.split("<tbody>", 1)[0] if "<tbody>" in table.lower() else table[:800]
    provinces: list[str] = []
    for h in re.split(r"<th[^>]*>", thead, flags=re.I)[1:]:
        name = re.sub(r"<[^>]+>", "", h).strip()
        low = name.lower()
        if name and low not in ("giải", "ngày quay") and "ngày" not in low:
            provinces.append(name)
    if not provinces:
        raise LotteryError(f"Ngày {date_label} chưa có KQ hoặc chưa quay.")
    provinces_data: dict[str, dict[str, list[str]]] = {p: {} for p in provinces}
    for seg in re.split(r"<tr[^>]*>", table, flags=re.I):
        parts = [p for p in re.split(r"<td[^>]*>", seg, flags=re.I) if p.strip()]
        if len(parts) < 2:
            continue
        label = re.sub(r"<[^>]+>", "", parts[0]).strip()
        if not label or not re.match(r"^G\.", label):
            continue
        for i, prov in enumerate(provinces):
            if i + 1 < len(parts):
                nums = _extract_nums(parts[i + 1])
                if nums:
                    provinces_data[prov][label] = nums
    return DrawResult(region=region, date=date_label, provinces=provinces_data)


def _parse_mb(html: str) -> DrawResult:
    day_id, block = _latest_block(html, "")
    prizes = _parse_prize_rows(block)
    if not prizes:
        raise LotteryError("Không đọc được giải thưởng MB.")
    return DrawResult(region="mb", date=_format_date(day_id), prizes=prizes)


def _parse_mb_date(html: str, date_label: str) -> DrawResult:
    if "table-xsmb" in html:
        block_m = re.search(
            r'id=kqngay_\d+[^>]*>(.*?table-xsmb.*?)(?=id=kqngay_|$)',
            html,
            re.S | re.I,
        )
        block = block_m.group(1) if block_m else html
    else:
        block = html
    prizes = _parse_prize_rows(block)
    if not prizes:
        raise LotteryError(f"Không có KQXS MB ngày {date_label}.")
    return DrawResult(region="mb", date=date_label, prizes=prizes)


def _parse_multi_province(html: str, block_prefix: str, region: str) -> DrawResult:
    day_id, block = _latest_block(html, block_prefix)
    draw = _parse_multi_province_table(block, region, _format_date(day_id))
    return draw


def find_province_prizes(draw: DrawResult, province_query: str) -> tuple[str, dict[str, list[str]]] | None:
    if not draw.provinces:
        return None
    q = normalize_province(province_query)
    for name, prizes in draw.provinces.items():
        n = normalize_province(name)
        if q in n or n in q or q.replace(" ", "") in n.replace(" ", ""):
            return name, prizes
    return None


def _no_province_hint(province: str, date: str, draw: DrawResult) -> str:
    listed = ", ".join(draw.provinces.keys()) if draw.provinces else "—"
    sched = MN_DRAW_WEEKDAY.get(normalize_province(province), "")
    lines = [
        f"⚠️ Ngày {date} không có xổ số **{province}**.",
        f"Các đài quay ngày đó: {listed}",
    ]
    if sched:
        lines.append(f"💡 {province} thường quay vào **{sched}** (miền Nam).")
        lines.append(f"Thử: /dove <số> bd {date} hoặc đổi ngày Thứ Sáu gần nhất.")
    return "\n".join(lines)


def get_draw(
    region: str = "mb",
    date: str | None = None,
    province: str | None = None,
) -> DrawResult:
    region = region.lower().strip()
    cache_key = f"{region}:{date or 'latest'}:{province or ''}"
    if cache_key in _cache:
        ts, data = _cache[cache_key]
        if time.time() - ts < _CACHE_TTL:
            return data

    if date and province:
        prov_norm = normalize_province(province)
        display = display_province(province)
        try:
            html = _fetch_url(_province_date_url(province, date))
            data = _parse_province_page(html, display, date)
        except LotteryError as exc:
            sched = MN_DRAW_WEEKDAY.get(prov_norm, "")
            near = _nearest_province_dates(province)
            extra = []
            if sched:
                extra.append(f"💡 {display} thường quay **{sched}**.")
            if "23/05/2026" in date and prov_norm in ("binh duong", "bd"):
                extra.append(
                    "📅 23/05/2026 là **Thứ Bảy** — không có XS Bình Dương "
                    "(BD quay Thứ Sáu: 16/05, 09/05…)."
                )
            if near:
                extra.append(f"Ngày có KQ gần đây: {', '.join(near)}")
                extra.append(f"Thử: /dove <số> bd {near[0]}")
            if extra:
                raise LotteryError(f"{exc}\n\n" + "\n".join(extra)) from exc
            raise
    elif date:
        html = _fetch_url(_date_page_url(region, date))
        if region == "mb":
            data = _parse_mb_date(html, date)
        else:
            try:
                data = _parse_multi_province_table(html, region, date)
            except LotteryError:
                raise LotteryError(
                    f"Chưa có bảng KQXS miền Nam ngày {date}. "
                    "Thử trang tỉnh: /dove <số> bd 15/05/2026"
                ) from None
    else:
        html = _fetch_html(region)
        if region == "mb":
            data = _parse_mb(html)
        elif region == "mn":
            data = _parse_multi_province(html, "mn_", "mn")
        else:
            data = _parse_multi_province(html, "mt_", "mt")

    if province and data.provinces:
        found = find_province_prizes(data, province)
        if not found:
            raise LotteryError(_no_province_hint(province, data.date, data))
        prov_name, prizes = found
        data = DrawResult(
            region=data.region,
            date=data.date,
            prizes=prizes,
            province_filter=prov_name,
        )

    _cache[cache_key] = (time.time(), data)
    return data


def _all_numbers_mb(draw: DrawResult) -> list[tuple[str, str]]:
    return [(prize, n) for prize, nums in draw.prizes.items() for n in nums]


def _all_numbers_province(draw: DrawResult) -> list[tuple[str, str]]:
    return [(prize, n) for prize, nums in draw.prizes.items() for n in nums]


def _all_numbers_mn_mt(draw: DrawResult) -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    if not draw.provinces:
        return out
    for prov, prizes in draw.provinces.items():
        for prize, nums in prizes.items():
            for n in nums:
                out.append((prov, prize, n))
    return out


def check_numbers(
    numbers: list[str],
    region: str = "mb",
    date: str | None = None,
    province: str | None = None,
) -> str:
    draw = get_draw(region, date=date, province=province)
    if not numbers:
        raise LotteryError("Gửi số cần dò. VD: /dove 67294 hoặc /dove 39 bd 22/05/2026")

    title = NAMES[region]
    if draw.province_filter:
        title = draw.province_filter
    lines = [f"🎰 Dò vé — {title} ({draw.date})\n"]
    any_hit = False

    if draw.region == "mb" or draw.province_filter:
        pool = _all_numbers_province(draw) if draw.province_filter else _all_numbers_mb(draw)
        for raw in numbers:
            n = re.sub(r"\D", "", raw)
            if not n:
                continue
            hits = _match_number(n, pool)
            if hits:
                any_hit = True
                lines.append(f"✅ Số {raw}:")
                lines.extend(f"  • {h}" for h in hits)
            else:
                lines.append(f"❌ Số {raw}: trượt")
    else:
        pool = _all_numbers_mn_mt(draw)
        for raw in numbers:
            n = re.sub(r"\D", "", raw)
            if not n:
                continue
            hits = []
            for prov, prize, drawn in pool:
                if _number_matches(n, drawn):
                    hits.append(f"{prov} — {prize}: {drawn}")
            if hits:
                any_hit = True
                lines.append(f"✅ Số {raw}:")
                lines.extend(f"  • {h}" for h in hits[:15])
                if len(hits) > 15:
                    lines.append(f"  … +{len(hits) - 15} kết quả")
            else:
                lines.append(f"❌ Số {raw}: trượt")

    lines.append(
        "\n🎉 Trúng rồi!" if any_hit else "\n🐔 Trượt — gà đồng hành."
    )
    return "\n".join(lines)


def _number_matches(bet: str, drawn: str) -> bool:
    if bet == drawn:
        return True
    if len(bet) in (2, 3) and drawn.endswith(bet):
        return True
    return False


def _match_number(bet: str, pool: list[tuple[str, str]]) -> list[str]:
    hits = []
    for prize, drawn in pool:
        if _number_matches(bet, drawn):
            kind = "trùng giải" if bet == drawn else f"khớp đuôi ({drawn})"
            hits.append(f"{prize}: {drawn} — {kind}")
    return hits


def format_results(
    region: str = "mb",
    date: str | None = None,
    province: str | None = None,
) -> str:
    draw = get_draw(region, date=date, province=province)
    if draw.province_filter:
        lines = [f"📊 {draw.province_filter} — {draw.date}\n"]
        for key in ["G.ĐB", "G.8", "G.1", "G.2", "G.3", "G.4", "G.5", "G.6", "G.7"]:
            if key in draw.prizes:
                lines.append(f"{key}: {' - '.join(draw.prizes[key])}")
        lines.append("\n/dove <số> bd " + draw.date)
        return "\n".join(lines)

    lines = [f"📊 KQXS {NAMES[region]} — {draw.date}\n"]
    if draw.region == "mb":
        for key in ["G.ĐB", "G.1", "G.2", "G.3", "G.4", "G.5", "G.6", "G.7"]:
            if key in draw.prizes:
                lines.append(f"{key}: {' - '.join(draw.prizes[key])}")
    elif draw.provinces:
        for prov, prizes in draw.provinces.items():
            lines.append(f"\n🏙 {prov}")
            for key in ["G.ĐB", "G.8", "G.1", "G.2"]:
                if key in prizes:
                    lines.append(f"  {key}: {' | '.join(prizes[key])}")
    lines.append("\n/dove <số> bd 23/05/2026 — dò theo tỉnh + ngày")
    return "\n".join(lines)


_DATE_RE = re.compile(
    r"\b(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})\b"
)
_PROVINCE_WORDS = (
    r"binh duong|bình dương|bd|"
    r"vinh long|vĩnh long|"
    r"tra vinh|trà vinh|"
    r"tphcm|tp hcm|hcm|sài gòn|sai gon|"
    r"can tho|cần thơ|"
    r"dong nai|đồng nai|"
    r"da nang|đà nẵng|"
    r"hue|huế|"
    r"ha noi|hà nội|hn"
)


def parse_bet_text(text: str) -> tuple[list[str], str, str | None, str | None]:
    """(số, miền, ngày dd/mm/yyyy, tỉnh)."""
    text = text.strip()
    region = "mn"  # tỉnh thường là MN/MT
    province = None
    date = None

    dm = _DATE_RE.search(text)
    if dm:
        date = f"{dm.group(1).zfill(2)}/{dm.group(2).zfill(2)}/{dm.group(3)}"
        text = text[: dm.start()] + text[dm.end() :]

    pm = re.search(_PROVINCE_WORDS, text, re.I)
    if pm:
        province = pm.group(0)
        text = text[: pm.start()] + text[pm.end() :]
        region = "mn"

    for r in ("mn", "mt", "mb"):
        if re.search(rf"\b{r}\b", text, re.I):
            region = r
            text = re.sub(rf"\b{r}\b", "", text, flags=re.I)

    nums = re.findall(r"\d{2,6}", text)
    return nums, region, date, province


# alias cũ
def parse_bet_numbers(text: str) -> tuple[list[str], str]:
    nums, region, _, _ = parse_bet_text(text)
    return nums, region


HELP_LOTTERY = (
    "🎰 Dò vé số VN\n\n"
    "/xsmb — KQ miền Bắc hôm nay\n"
    "/xsmn — KQ miền Nam hôm nay\n"
    "/xsmt — KQ miền Trung hôm nay\n\n"
    "/dove <số> — dò vé\n"
    "  /dove 67294\n"
    "  /dove 39 bd 22/05/2026\n"
    "  /dove 39 bd 15/05/2026\n"
    "  /dove 12345 binh duong 15/05/2026\n\n"
    "📌 **Bình Dương quay Thứ Sáu** — 23/05/2026 (Thứ Bảy) "
    "**không có** XS Bình Dương.\n"
    "Dùng ngày Thứ Sáu có KQ, VD: /dove 39 bd 15/05/2026\n\n"
    "Nguồn: xosodaiphat.com — tham khảo."
)
