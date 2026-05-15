import json
import random
import re
import unicodedata
from pathlib import Path

_DATA = Path(__file__).resolve().parent / "data" / "riddles.json"
with _DATA.open(encoding="utf-8") as f:
    RIDDLES: list[dict] = json.load(f)

SKIP_WORDS = {"bo qua", "bỏ qua", "skip", "thoi", "thôi", "khong biet", "không biết", "ko biet", "pass"}

POOL_TAUNT = [
    "Ồ sai rồi kìa 🐔 — nghe bố giảng:",
    "Trả lời thế mà cũng dám cãi? Ngồi xuống nghe:",
    "Sai bét. Bố spoil đáp án cho não cá:",
    "Khiêu khích xong toán sai — embarrassment:",
    "Plot twist: mày sai. Giờ bố explain cho vui:",
]

POOL_GA = [
    "🐔 Gà vậy mà còn chửi bot — cười ụ.",
    "Level gà confirmed. Quay về tutorial đi.",
    "Não gà rang muối — vừa ăn vừa sai đố.",
    "Mày gà thế này mà meta — không ai sợ.",
    "Achievement unlocked: Gà vàng 🏆",
    "Sai xong còn im thì tốt — gà mà sủa nhiều.",
    "Tưởng pro, hóa gà farm. Cãi tiếp không?",
    "IQ gà, ego sư tử — combo hài.",
]

POOL_CORRECT = [
    "Ồ, não mày còn 1% pin — tạm chấp nhận.",
    "Đúng rồi, surprise. Cãi tiếp không?",
    "Ok não có hàng, chửi tiếp đi.",
    "Chuẩn. Mày thông minh 5 giây thôi nhé.",
    "Đúng — rare event, ghi lại ngày giờ.",
]

POOL_AFTER_WRONG = [
    "Câu tiếp — đừng gà tiếp:",
    "Đổi câu, redeem đi gà ơi:",
    "Thử câu khác, còn cứu được:",
]

RIDDLE_CHANCE = 0.45
_HISTORY_SIZE = 80  # khong lap lai trong 80 cau gan nhat


def _strip_accents(s: str) -> str:
    nfd = unicodedata.normalize("NFD", s)
    return "".join(c for c in nfd if unicodedata.category(c) != "Mn")


def normalize(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^\w\s]", "", s)
    s = re.sub(r"\s+", " ", s)
    return _strip_accents(s)


class RiddleSession:
    def __init__(self) -> None:
        self._used: dict[int, list[int]] = {}

    def pick(self, user_id: int) -> dict:
        used = self._used.setdefault(user_id, [])
        available = [i for i in range(len(RIDDLES)) if i not in used[-_HISTORY_SIZE:]]
        if not available:
            used.clear()
            available = list(range(len(RIDDLES)))
        idx = random.choice(available)
        used.append(idx)
        return RIDDLES[idx].copy()

    def check(self, user_text: str, riddle: dict) -> str:
        norm = normalize(user_text)
        if norm in {normalize(w) for w in SKIP_WORDS}:
            return "skip"
        for ans in riddle["a"]:
            a = normalize(ans)
            if norm == a or (len(a) > 2 and a in norm) or (len(norm) > 2 and norm in a):
                return "correct"
        return "wrong"

    def format_question(self, riddle: dict) -> str:
        total = len(RIDDLES)
        return (
            f"🧩 Câu đố ({total} câu trong kho):\n"
            f"{riddle['q']}\n\n"
            "(Trả lời 1 tin — «bỏ qua» đổi câu)"
        )

    def wrong_reply(self, user_id: int, riddle: dict, user_answer: str = "") -> str:
        from bot.trash_talk import generate_reply_with_streak

        taunt = random.choice(POOL_TAUNT)
        ans = riddle.get("ans", riddle["a"][0])
        explain = riddle.get("explain", f"Đáp đúng là: {ans}")
        ga = random.choice(POOL_GA)
        extra = generate_reply_with_streak("sai roi ngu", user_id, 3, cai_mode=True)

        lines = [taunt]
        if user_answer.strip():
            lines.append(f"\n❌ Mày: «{user_answer.strip()[:80]}»")
        lines.append(f"\n✅ Đáp đúng: {ans}")
        lines.append(f"\n📖 Giải thích:\n{explain}")
        lines.append(f"\n{ga}")
        lines.append(f"\n{extra}")
        return "".join(lines)

    def correct_reply(self) -> str:
        return random.choice(POOL_CORRECT)

    def intro_after_wrong(self) -> str:
        return random.choice(POOL_AFTER_WRONG)


session = RiddleSession()


def should_ask_riddle(streak: int, has_active: bool) -> bool:
    if has_active or streak < 1:
        return False
    return random.random() < RIDDLE_CHANCE


def riddle_count() -> int:
    return len(RIDDLES)
