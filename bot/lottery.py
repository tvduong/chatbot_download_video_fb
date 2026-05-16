"""Dò vé & xem KQXS 3 miền — nguồn: xosodaiphat.com"""
from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field
from html import unescape

import httpx

log = logging.getLogger(__name__)

URLS = {
    "mb": "https://xosodaiphat.com/xsmb-xo-so-mien-bac.html",
    "mn": "https://xosodaiphat.com/xsmn-xo-so-mien-nam.html",
    "mt": "https://xosodaiphat.com/xsmt-xo-so-mien-trung.html",
}
NAMES = {"mb": "Miền Bắc", "mn": "Miền Nam", "mt": "Miền Trung"}
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; FBTelegramBot/1.0)"}

_cache: dict[str, tuple[float, DrawResult]] = {}
_CACHE_TTL = 600  # 10 phút


@dataclass
class DrawResult:
    region: str
    date: str
    prizes: dict[str, list[str]] = field(default_factory=dict)
    provinces: dict[str, dict[str, list[str]]] | None = None


class LotteryError(Exception):
    pass


def _fetch_html(region: str) -> str:
    url = URLS.get(region)
    if not url:
        raise LotteryError("Miền không hợp lệ. Dùng: mb, mn, mt")
    try:
        r = httpx.get(url, headers=HEADERS, follow_redirects=True, timeout=25)
        r.raise_for_status()
        return unescape(r.text)
    except httpx.HTTPError as exc:
        log.warning("Lottery fetch failed %s: %s", region, exc)
        raise LotteryError("Không lấy được kết quả. Thử lại sau.") from exc


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
    """block_prefix: '' cho MB, 'mn_' cho MN, 'mt_' cho MT."""
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
    """HTML xosodaiphat thường không đóng </tr> — tách theo <tr>."""
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


def _parse_mb(html: str) -> DrawResult:
    day_id, block = _latest_block(html, "")
    prizes = _parse_prize_rows(block)
    if not prizes:
        raise LotteryError("Không đọc được giải thưởng MB.")
    return DrawResult(region="mb", date=_format_date(day_id), prizes=prizes)


def _parse_multi_province(html: str, block_prefix: str, region: str) -> DrawResult:
    day_id, block = _latest_block(html, block_prefix)
    table_m = re.search(
        r'<table class="[^"]*table-xsm[nt][^"]*"[^>]*>(.*?)</table>',
        block,
        re.S | re.I,
    )
    if not table_m:
        raise LotteryError("Không đọc được bảng kết quả.")
    table = table_m.group(1)
    thead = table.split("<tbody>", 1)[0] if "<tbody>" in table.lower() else table[:800]
    provinces: list[str] = []
    for h in re.split(r"<th[^>]*>", thead, flags=re.I)[1:]:
        name = re.sub(r"<[^>]+>", "", h).strip()
        if name and name.lower() != "giải":
            provinces.append(name)
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
    return DrawResult(
        region=region,
        date=_format_date(day_id),
        provinces=provinces_data,
    )


def get_draw(region: str = "mb") -> DrawResult:
    region = region.lower().strip()
    if region in _cache:
        ts, data = _cache[region]
        if time.time() - ts < _CACHE_TTL:
            return data
    html = _fetch_html(region)
    if region == "mb":
        data = _parse_mb(html)
    elif region == "mn":
        data = _parse_multi_province(html, "mn_", "mn")
    elif region == "mt":
        data = _parse_multi_province(html, "mt_", "mt")
    else:
        raise LotteryError("Miền: mb, mn, mt")
    _cache[region] = (time.time(), data)
    return data


def _all_numbers_mb(draw: DrawResult) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for prize, nums in draw.prizes.items():
        for n in nums:
            out.append((prize, n))
    return out


def _all_numbers_mn_mt(draw: DrawResult) -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    if not draw.provinces:
        return out
    for prov, prizes in draw.provinces.items():
        for prize, nums in prizes.items():
            for n in nums:
                out.append((prov, prize, n))
    return out


def check_numbers(numbers: list[str], region: str = "mb") -> str:
    draw = get_draw(region)
    if not numbers:
        raise LotteryError("Gửi số cần dò. VD: /do 67294 hoặc /do 94 388")

    lines = [f"🎰 Dò vé — {NAMES[region]} ({draw.date})\n"]
    any_hit = False

    if draw.region == "mb":
        pool = _all_numbers_mb(draw)
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
                lines.append(f"❌ Số {raw}: trượt (không khớp giải)")
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
                    lines.append(f"  … và {len(hits) - 15} kết quả khác")
            else:
                lines.append(f"❌ Số {raw}: trượt cả 3 miền tỉnh")

    if any_hit:
        lines.append("\n🎉 Có nhịp trúng — đổi đời chưa biết, nhưng bot chúc mừng!")
    else:
        lines.append("\n🐔 Trượt sạch — gà vàng đồng hành. Mai thử lại!")

    return "\n".join(lines)


def _number_matches(bet: str, drawn: str) -> bool:
    if bet == drawn:
        return True
    if len(bet) == 2 and drawn.endswith(bet):
        return True  # lô 2 số
    if len(bet) == 3 and drawn.endswith(bet):
        return True  # 3 càng
    return False


def _match_number(bet: str, pool: list[tuple[str, str]]) -> list[str]:
    hits = []
    for prize, drawn in pool:
        if _number_matches(bet, drawn):
            kind = "trùng giải" if bet == drawn else f"khớp đuôi ({drawn})"
            hits.append(f"{prize}: {drawn} — {kind}")
    return hits


def format_results(region: str = "mb") -> str:
    draw = get_draw(region)
    lines = [f"📊 KQXS {NAMES[region]} — {draw.date}\n"]

    if draw.region == "mb":
        order = ["G.ĐB", "G.1", "G.2", "G.3", "G.4", "G.5", "G.6", "G.7"]
        for key in order:
            if key in draw.prizes:
                lines.append(f"{key}: {' - '.join(draw.prizes[key])}")
        for key, nums in draw.prizes.items():
            if key not in order:
                lines.append(f"{key}: {' - '.join(nums)}")
    else:
        if not draw.provinces or not any(draw.provinces.values()):
            raise LotteryError("Không có dữ liệu tỉnh.")
        for prov, prizes in draw.provinces.items():
            lines.append(f"\n🏙 {prov}")
            for key in ["G.ĐB", "G.8", "G.1", "G.2"]:
                if key in prizes:
                    lines.append(f"  {key}: {' | '.join(prizes[key])}")

    lines.append("\n/do <số> — dò vé (VD: /do 94 67294)")
    lines.append("/do <số> mn — dò miền Nam")
    return "\n".join(lines)


def parse_bet_numbers(text: str) -> tuple[list[str], str]:
    """Trả về (danh sách số, miền mb|mn|mt)."""
    text = text.strip()
    region = "mb"
    for r in ("mn", "mt", "mb"):
        if re.search(rf"\b{r}\b", text, re.I):
            region = r
            text = re.sub(rf"\b{r}\b", "", text, flags=re.I)
    nums = re.findall(r"\d{2,6}", text)
    return nums, region


HELP_LOTTERY = (
    "🎰 Dò vé số VN\n\n"
    "/xsmb — KQ miền Bắc\n"
    "/xsmn — KQ miền Nam\n"
    "/xsmt — KQ miền Trung\n"
    "/do <số> — dò vé MB\n"
    "  VD: /do 67294\n"
    "  VD: /do 94 388 (lô 2 số)\n"
    "  VD: /do 216215 mn\n\n"
    "Nguồn: xosodaiphat.com — chỉ mang tính tham khảo."
)
