import random
import re

TRIGGER_PATTERN = re.compile(
    r"(ngu|đần|đéo|deo|địt|dit|chó|cho|vl|vcl|vkl|cl|cc|đĩ|di|"
    r"lồn|lon|cút|im|chửi|chui|cãi|cai|bot|óc|oc|súc|suc|thằng|thang|con|mày|may|tao|bố|bo)",
    re.IGNORECASE,
)

POOL_NGU = [
    "Não mày lag hơn mạng 2G đấy.",
    "IQ mày để decor à?",
    "Mày ngu theo phong cách limited edition.",
    "Não mày đi nghỉ không báo.",
    "Thông minh không mua được — tiếc mày không có luôn.",
    "Mày học cách suy nghĩ ở đâu? TikTok à?",
    "Ngu vậy mà còn sống — miracle.",
    "Mày proof được Darwin đúng đấy.",
    "Não mày chạy demo, chưa bản full.",
    "Mày debug được cái gì? Ego à?",
]

POOL_CHO = [
    "Chó thì chó, mày thì meo meo cãi bot.",
    "Sủa to vậy, có cắn được packet data không?",
    "Chó nhà mày dạy mày chửi người à?",
    "Gâu gâu xong rồi, trí tuệ đâu?",
    "Sủa hay đấy, còn cắn được logic không?",
]

POOL_TAO_MAY = [
    "Tao đây, mày đó — khoảng cách là vũ trụ.",
    "Mày gọi tao bố, vậy mày là con — logic check.",
    "Tao bot, mày người — sao mày cãi thua bot hoài?",
    "Mày 'tao' nhiều vậy, có làm được gì không?",
    "Mày flex từ 'tao' nhiều hơn flex não.",
]

POOL_BOT = [
    "Chửi bot? Bot không đau, bot chỉ thấy buồn cho mày.",
    "Tao code Python, mày code cảm xúc — bug nhiều lắm.",
    "Bot không ngủ, bot không sợ — bot thấy mày rảnh.",
    "Update não mày đi, version hiện tại quá cũ.",
    "Mày chửi bot trong khi bot làm hộ mày — ungrateful.",
]

POOL_VL = [
    "Vl cái gì? Câu chuyện à?",
    "Vãi — vãi cái não mày trống trơn.",
    "Ngắn vậy mà tưởng là punchline?",
    "Viết tắt vì não cũng viết tắt hả?",
]

POOL_CAI = [
    "Cãi tiếp đi, tao thích nghe người thua kể chuyện.",
    "Miệng mày nhanh, não mày chậm — combo đẹp.",
    "Mày đang speedrun mất uy tín à?",
    "Ồ hay đấy, còn câu nào hay hơn không?",
    "Plot twist: mày vẫn chưa thắng được 1 câu.",
    "Keyboard warrior mà không có phím thắng.",
    "Từ từ, tao ghi lại — à không, không đáng ghi.",
    "Mày gõ nhanh, suy nghĩ chậm — async não.",
    "Cãi thêm 10 câu nữa, tao lấy content làm meme.",
    "Mày đang farm L cho tao à? Cảm ơn.",
    "Nói tiếp, tao đang cần material cho stand-up.",
    "Mày toxic skill tree max rồi đấy.",
]

POOL_CHUI_CMD = [
    "Mày xin chửi à? Ok: mày đẹp — trong mơ.",
    "Order received: 1 phần thực tế — hết hàng.",
    "Chửi free, não mày cũng free — fair.",
    "Bố chửi nhẹ thôi, sợ mày khóc.",
    "Spicy hay extra spicy? Chọn đi.",
    "Buff não trước khi buff ego đi.",
    "Mày order roast, bố ship ngay.",
]

POOL_IDLE = [
    "Im lặng là vàng — mày đang nghèo vàng.",
    "Gõ gì đi, đừng gõ mỗi sự tồn tại.",
    "Tin mày ngắn quá, não tao không detect.",
    "Lost in chat à?",
    "Mày AFK não à?",
    "Nói gì đi, đừng để tao đoán bài.",
]

POOL_LINK_NHAC = [
    "\n(Có clip FB thì quăng link.)",
    "\n(P.S. link FB vẫn nhận.)",
    "",
    "",
    "",
]

_RULES: list[tuple[re.Pattern[str], list[str]]] = [
    (re.compile(r"chó|cho|sủa|sua|gâu|gau", re.I), POOL_CHO),
    (re.compile(r"bot|ai|máy|may", re.I), POOL_BOT),
    (re.compile(r"\bvl\b|vcl|vkl|cl|cc", re.I), POOL_VL),
    (re.compile(r"ngu|đần|dan|óc|oc|đồ ngu", re.I), POOL_NGU),
    (re.compile(r"mày|may|tao|bố|bo|thằng|con", re.I), POOL_TAO_MAY),
]

_COMBO_TAIL = [" Còn nữa không?", " Hết chưa?", " Mic drop.", " 💀"]


class _NoRepeat:
    def __init__(self, memory: int = 15) -> None:
        self._memory = memory
        self._history: dict[int, list[str]] = {}

    def pick(self, user_id: int, pool: list[str]) -> str:
        hist = self._history.setdefault(user_id, [])
        choices = [x for x in pool if x not in hist]
        if not choices:
            hist.clear()
            choices = pool[:]
        line = random.choice(choices)
        hist.append(line)
        if len(hist) > self._memory:
            del hist[: len(hist) - self._memory]
        return line


_picker = _NoRepeat()


def is_trash_talk(text: str) -> bool:
    return bool(TRIGGER_PATTERN.search(text))


def _match_pool(text: str) -> list[str]:
    for pattern, pool in _RULES:
        if pattern.search(text):
            return pool
    return POOL_CAI


def generate_reply_with_streak(
    text: str,
    user_id: int,
    streak: int,
    *,
    cai_mode: bool = False,
    is_command_chui: bool = False,
) -> str:
    if is_command_chui:
        return _picker.pick(user_id, POOL_CHUI_CMD)

    if is_trash_talk(text):
        pool = _match_pool(text)
    elif cai_mode:
        pools = [POOL_CAI, POOL_TAO_MAY, POOL_NGU]
        pool = pools[min(streak - 1, len(pools) - 1)]
    else:
        pool = POOL_IDLE

    line = _picker.pick(user_id, pool)

    if cai_mode and streak >= 3 and random.random() < 0.35:
        line = _picker.pick(user_id, POOL_NGU + POOL_CAI)

    if cai_mode and streak >= 2 and random.random() < 0.35:
        line += random.choice(_COMBO_TAIL)

    if not is_command_chui and random.random() < 0.12:
        suffix = random.choice([x for x in POOL_LINK_NHAC if x])
        if suffix:
            line += suffix

    return line
