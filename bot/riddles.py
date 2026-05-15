import random
import re
import unicodedata

RIDDLES: list[dict] = [
    {
        "q": "Con gì đi bằng chân mà không phải động vật?",
        "a": ["cái quạt", "quạt", "fan", "quat"],
    },
    {
        "q": "Cái gì càng giặt càng bẩn?",
        "a": ["lưỡi", "luoi", "miệng", "mieng", "mồm", "mom"],
    },
    {
        "q": "Bố của em gái em gọi em là gì? (không phải 'em')",
        "a": ["chị", "chi", "chị ruột", "chi ruot"],
    },
    {
        "q": "2 + 2 nhân chia cho mấy bằng cá?",
        "a": ["5", "nam", "năm", "cá", "ca"],
    },
    {
        "q": "Con gì ở trên cây mà không phải khỉ?",
        "a": ["lá", "la", "cành", "canh", "nấm", "nam"],
    },
    {
        "q": "Thứ gì người ta cho mà không ai nhận?",
        "a": ["lời khuyên", "loi khuyen", "lời", "loi"],
    },
    {
        "q": "Tại sao gà không chạy marathon?",
        "a": ["ngắn chân", "ngan chan", "không đủ chân", "khong du chan", "gà", "ga"],
    },
    {
        "q": "Một con vịt đi trước hai con vịt — có mấy cái chân?",
        "a": ["6", "sau", "4", "bon", "bốn"],
    },
    {
        "q": "Cái gì mày cầm được nhưng không ném được?",
        "a": ["hơi thở", "hoi tho", "hơi", "hoi", "thở", "tho", "cái nhìn"],
    },
    {
        "q": "Bot này có mấy chân?",
        "a": ["0", "không", "khong", "khong co", "zero"],
    },
    {
        "q": "Cái gì càng cắt càng dài?",
        "a": ["tóc", "toc", "móng tay", "mong tay", "râu", "rau"],
    },
    {
        "q": "Đêm qua 10 con muỗi, đập chết 3 — còn mấy con?",
        "a": ["3", "ba", "3 con", "ba con"],
    },
    {
        "q": "Con gì ăn cơm nhưng không sống trong bếp?",
        "a": ["người", "nguoi", "con người", "khách", "khach", "bạn", "ban"],
    },
    {
        "q": "Cái gì có cánh mà không bay được (trong nhà)?",
        "a": ["cửa sổ", "cua so", "quạt trần", "quat tran", "máy bay giấy"],
    },
    {
        "q": "Tiếng gì kêu to mà không ai sợ trong group chat?",
        "a": ["tin nhắn", "tin nhan", "tag all", "ping", "sticker", "meme"],
    },
    {
        "q": "Nếu tao là con mèo, màu tao là gì? (câu bẫy)",
        "a": ["màu mèo", "mau meo", "mèo", "meo", "không có màu", "tùy ý", "tuy y"],
    },
    {
        "q": "Cái gì càng nhai càng ngắn?",
        "a": ["kẹo", "keo", "bánh", "banh", "miếng", "mieng"],
    },
    {
        "q": "Máy + máy = ? (kiểu bựa)",
        "a": ["máy", "may", "hai máy", "2 may", "lỗi", "loi"],
    },
    {
        "q": "Con gì 4 chân mà đi bằng 2 chân?",
        "a": ["người", "nguoi", "con người", "khách", "ban"],
    },
    {
        "q": "Cái gì bot không có mà vẫn bắt mày trả lời?",
        "a": ["kiên nhẫn", "kien nhan", "nhân phẩm", "nhan pham", "lòng kiên trì"],
    },
]

SKIP_WORDS = {"bo qua", "bỏ qua", "skip", "thoi", "thôi", "khong biet", "không biết", "ko biet", "pass"}

POOL_WRONG = [
    "Sai bét nhè — não mày đi du lịch à?",
    "Đáp án sai như dự đoán chứng khoán của mày.",
    "Wrong. Mày học lại lớp câu đố đi.",
    "Sai rồi con vợ, cãi giỏi mà đố dở.",
    "Ôi trời, sai thế mà còn chửi tao?",
    "Fail. IQ mày âm rồi.",
    "Sai — mày nên xin lỗi cả toán lẫn văn.",
    "Đáp sai, miệng vẫn to — talent.",
    "Não lag rồi, thử lại hoặc im.",
    "Sai bét. Mày giỏi cãi hơn giải đố nhiều.",
]

POOL_CORRECT = [
    "Ồ, não mày còn 1% pin — tạm chấp nhận.",
    "Đúng rồi, surprise. Cãi tiếp không?",
    "Ok não có hàng, chửi tiếp đi.",
    "Chuẩn. Mày thông minh 5 giây thôi nhé.",
    "Đúng — rare event, ghi lại ngày giờ.",
]

POOL_AFTER_WRONG = [
    "Câu tiếp, đừng làm tao thất vọng tiếp:",
    "Đổi câu, não refresh đi:",
    "Thử câu khác, còn cơ hội cứu não:",
]

RIDDLE_CHANCE = 0.45


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
        available = [i for i in range(len(RIDDLES)) if i not in used[-20:]]
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
        return f"🧩 Câu đố:\n{riddle['q']}\n\n(Trả lời 1 tin — gõ «bỏ qua» để đổi)"

    def wrong_reply(self, user_id: int, riddle: dict) -> str:
        from bot.trash_talk import generate_reply_with_streak

        insult = generate_reply_with_streak("sai roi ngu", user_id, 3, cai_mode=True)
        roast = random.choice(POOL_WRONG)
        return f"{roast}\n{insult}"

    def correct_reply(self) -> str:
        return random.choice(POOL_CORRECT)

    def intro_after_wrong(self) -> str:
        return random.choice(POOL_AFTER_WRONG)


session = RiddleSession()


def should_ask_riddle(streak: int, has_active: bool) -> bool:
    if has_active or streak < 1:
        return False
    return random.random() < RIDDLE_CHANCE
