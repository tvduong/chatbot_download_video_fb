import random
import re
import unicodedata

# q: cau hoi | a: dap an chap nhan | ans: dap an hien thi | explain: giai thích bựa
RIDDLES: list[dict] = [
    {
        "q": "Con gì đi bằng chân mà không phải động vật?",
        "a": ["cái quạt", "quạt", "fan", "quat"],
        "ans": "Cái quạt",
        "explain": "Quạt có chân đế, quay bằng điện — không phải con vật. Mày đi tìm con vật 4 chân là sao?",
    },
    {
        "q": "Cái gì càng giặt càng bẩn?",
        "a": ["lưỡi", "luoi", "miệng", "mieng", "mồm", "mom"],
        "ans": "Lưỡi / miệng",
        "explain": "Giặt lưỡi = nhai đồ ăn, nó càng bẩn chứ có sạch hơn đâu. Đồ ăn chứ không phải áo quần.",
    },
    {
        "q": "Bố của em gái em gọi em là gì? (không phải 'em')",
        "a": ["chị", "chi", "chị ruột", "chi ruot"],
        "ans": "Chị",
        "explain": "Em gái = em là con gái. Bố em gái = bố mày. Bố mày gọi con gái là «chị» (nếu mày là em trai) hoặc logic ngược — câu bẫy relationship.",
    },
    {
        "q": "2 + 2 nhân chia cho mấy bằng cá?",
        "a": ["5", "nam", "năm", "cá", "ca"],
        "ans": "5 (hoặc «cá» — câu láo)",
        "explain": "Toán thật = 4. Câu này bựa: «bằng cá» = con cá, hoặc 2+2=5 theo kiểu não cá vàng. Mày làm toán thật là dính bẫy.",
    },
    {
        "q": "Con gì ở trên cây mà không phải khỉ?",
        "a": ["lá", "la", "cành", "canh", "nấm", "nam"],
        "ans": "Lá / cành / nấm",
        "explain": "Trên cây không chỉ có khỉ — lá, chim, nấm, trái… Mày fix cứng «con vật» là thua.",
    },
    {
        "q": "Thứ gì người ta cho mà không ai nhận?",
        "a": ["lời khuyên", "loi khuyen", "lời", "loi"],
        "ans": "Lời khuyên",
        "explain": "Cho lời khuyên free mà nghe không? Không ai «nhận» vì ai cũng tưởng mình đúng.",
    },
    {
        "q": "Tại sao gà không chạy marathon?",
        "a": ["ngắn chân", "ngan chan", "không đủ chân", "khong du chan", "gà", "ga"],
        "ans": "Chân ngắn / vì nó là gà",
        "explain": "Gà chân ngắn, sức bền kém — marathon không phải skill tree của gà. Meta joke: mày hỏi gà chạy marathon = mày cũng não gà.",
    },
    {
        "q": "Một con vịt đi trước hai con vịt — có mấy cái chân?",
        "a": ["6", "sau", "4", "bon", "bốn"],
        "ans": "6 chân (3 con vịt × 2 chân)",
        "explain": "«Một con đi trước hai con» = TỔNG 3 CON VỊT. 3×2=6 chân. Mày đếm 1 con hoặc 2 con là não vịt.",
    },
    {
        "q": "Cái gì mày cầm được nhưng không ném được?",
        "a": ["hơi thở", "hoi tho", "hơi", "hoi", "thở", "tho", "cái nhìn"],
        "ans": "Hơi thở / cái nhìn",
        "explain": "Hơi thở «cầm» trong phổi, ném không được. Cái nhìn cũng vậy — nhìn chớp chớp, ném không trúng ai.",
    },
    {
        "q": "Bot này có mấy chân?",
        "a": ["0", "không", "khong", "khong co", "zero"],
        "ans": "0 chân",
        "explain": "Bot = code trên server. Không chân, không tay, chỉ có attitude. Mày hỏi 2 chân là nhầm người với bot.",
    },
    {
        "q": "Cái gì càng cắt càng dài?",
        "a": ["tóc", "toc", "móng tay", "mong tay", "râu", "rau"],
        "ans": "Tóc / móng / râu",
        "explain": "Cắt tóc/râu/móng xong nó MỌC LẠI dài hơn — không phải cắt dây hay bánh. Sinh học cơ bản.",
    },
    {
        "q": "Đêm qua 10 con muỗi, đập chết 3 — còn mấy con?",
        "a": ["3", "ba", "3 con", "ba con"],
        "ans": "3 con (con còn sống)",
        "explain": "Đập CHẾT 3 → còn 10-3=7? Không — câu hỏi «còn mấy con» = còn SỐNG = 3 con chết nằm đó… À không, 10-3=7 sống. \n\nBẫy phổ biến: người ta nghĩ 7. Đáp «3» = 3 con đã chết vẫn «còn» trên sàn. Câu đố não cá — đáp 3 hoặc 7 tùy cách hiểu, bố chấp 3 (bẫy cổ điển).",
    },
    {
        "q": "Con gì ăn cơm nhưng không sống trong bếp?",
        "a": ["người", "nguoi", "con người", "khách", "khach", "bạn", "ban"],
        "ans": "Người",
        "explain": "Người ăn cơm ở phòng khách, công ty, quán — không phải chuột bếp. Mày nghĩ con vật là thiếu tôn trọng loài người.",
    },
    {
        "q": "Cái gì có cánh mà không bay được (trong nhà)?",
        "a": ["cửa sổ", "cua so", "quạt trần", "quat tran", "máy bay giấy"],
        "ans": "Cửa sổ / quạt / máy bay giấy",
        "explain": "Cánh cửa, cánh quạt — có «cánh» nhưng không phải chim. Máy bay giấy bay được nhưng «trong nhà» hên xui.",
    },
    {
        "q": "Tiếng gì kêu to mà không ai sợ trong group chat?",
        "a": ["tin nhắn", "tin nhan", "tag all", "ping", "sticker", "meme"],
        "ans": "Tin nhắn / tag all",
        "explain": "Tag @all kêu to mà không ai sợ — chỉ sợ notification. Đúng vibe group zalo/telegram.",
    },
    {
        "q": "Nếu tao là con mèo, màu tao là gì? (câu bẫy)",
        "a": ["màu mèo", "mau meo", "mèo", "meo", "không có màu", "tùy ý", "tuy y"],
        "ans": "Màu mèo / tùy",
        "explain": "Câu bẫy vô lý — mèo giả thì «màu mèo». Hoặc «không có màu» vì câu hỏi vô nghĩa. Mày trả lời nghiêm túc là dính bẫy.",
    },
    {
        "q": "Cái gì càng nhai càng ngắn?",
        "a": ["kẹo", "keo", "bánh", "banh", "miếng", "mieng"],
        "ans": "Kẹo / bánh",
        "explain": "Nhai kẹo/bánh thì miếng ngắn dần. Không phải cắt tóc — đọc kỹ «nhai».",
    },
    {
        "q": "Máy + máy = ? (kiểu bựa)",
        "a": ["máy", "may", "hai máy", "2 may", "lỗi", "loi"],
        "ans": "Máy (hoặc lỗi)",
        "explain": "Máy + máy = 2 cái máy, hoặc «máy» ghép chữ, hoặc «lỗi» vì não không tính được. Câu láo toán học.",
    },
    {
        "q": "Con gì 4 chân mà đi bằng 2 chân?",
        "a": ["người", "nguoi", "con người", "khách", "ban"],
        "ans": "Người",
        "explain": "Người có 4 chân khi bò, đi thì 2 chân. Hoặc người già chống gậy — vẫn là người, không phải chó.",
    },
    {
        "q": "Cái gì bot không có mà vẫn bắt mày trả lời?",
        "a": ["kiên nhẫn", "kien nhan", "nhân phẩm", "nhan pham", "lòng kiên trì"],
        "ans": "Kiên nhẫn / nhân phẩm",
        "explain": "Bot không có kiên nhẫn với não cá — nhưng bắt mày trả lời vì… mày rảnh. Meta level 999.",
    },
]

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
