"""Generate ~500 Vietnamese riddles -> bot/data/riddles.json"""
import json
import random
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "bot" / "data" / "riddles.json"
TARGET = 500

# --- handcrafted premium ---
HANDCRAFTED = [
    {"q": "Con gì đi bằng chân mà không phải động vật?", "a": ["cái quạt", "quạt", "fan"], "ans": "Cái quạt", "explain": "Quạt có chân đế — không phải con vật."},
    {"q": "Cái gì càng giặt càng bẩn?", "a": ["lưỡi", "miệng", "mồm"], "ans": "Lưỡi/miệng", "explain": "Giặt = nhai đồ ăn, càng nhai càng bẩn."},
    {"q": "Bố của em gái em gọi em là gì?", "a": ["chị", "chi"], "ans": "Chị", "explain": "Câu bẫy quan hệ — em gái thì bố gọi theo vai."},
    {"q": "2 + 2 nhân chia cho mấy bằng cá?", "a": ["5", "năm", "cá"], "ans": "5 hoặc cá", "explain": "Toán thật = 4. «Bằng cá» = câu láo."},
    {"q": "Bot này có mấy chân?", "a": ["0", "không", "zero"], "ans": "0", "explain": "Bot là code — không chân."},
    {"q": "10 con muỗi, đập 3, còn mấy con?", "a": ["7", "bảy", "3", "ba"], "ans": "7 sống / 3 chết (bẫy)", "explain": "10-3=7 còn sống. Một số bẫy đáp 3 = con chết."},
    {"q": "Một con vịt trước hai con vịt — mấy chân?", "a": ["6", "sau"], "ans": "6 chân", "explain": "3 con vịt × 2 chân = 6."},
    {"q": "Cái gì cầm được mà không ném được?", "a": ["hơi thở", "cái nhìn"], "ans": "Hơi thở", "explain": "Không ném được hơi thở."},
    {"q": "Thứ gì cho mà không ai nhận?", "a": ["lời khuyên", "lời"], "ans": "Lời khuyên", "explain": "Ai cũng nghe, không ai «nhận»."},
    {"q": "Cái gì càng cắt càng dài?", "a": ["tóc", "râu", "móng"], "ans": "Tóc/râu", "explain": "Cắt xong mọc lại dài."},
    {"q": "Cái gì càng nhai càng ngắn?", "a": ["kẹo", "bánh"], "ans": "Kẹo/bánh", "explain": "Nhai thì ngắn dần."},
    {"q": "Con gì 4 chân mà đi bằng 2?", "a": ["người"], "ans": "Người", "explain": "Người bò 4 chân, đi 2 chân."},
    {"q": "Tại sao gà không marathon?", "a": ["ngắn chân", "gà"], "ans": "Chân ngắn", "explain": "Gà không skill marathon."},
    {"q": "Tiếng gì group chat không ai sợ?", "a": ["tag all", "tin nhắn", "ping"], "ans": "Tag all", "explain": "Chỉ sợ notification."},
    {"q": "Máy + máy = ?", "a": ["máy", "lỗi", "2 máy"], "ans": "Máy/lỗi", "explain": "Câu láo toán."},
]

ANIMALS = ["gà", "vịt", "chó", "mèo", "cá", "muỗi", "kiến", "voi", "khỉ", "rắn", "ếch", "bò", "heo"]
OBJECTS = ["bàn", "ghế", "điện thoại", "nồi", "chảo", "bút", "sách", "gương", "đồng hồ", "tủ lạnh"]
PLACES = ["bếp", "nhà tắm", "công ty", "trường", "chợ", "quán net", "group zalo"]
ACTIONS = ["ăn", "ngủ", "cãi", "scroll", "spam sticker", "tag all", "ghost", "flex"]


def gen_math() -> dict | None:
    templates = [
        (
            "{a} + {b} × 0 + {c} = ?",
            lambda a, b, c: str(c),
            lambda a, b, c: [str(c), str(c)],
            "Nhân 0 = 0. Còn {c}.",
        ),
        (
            "1 + 1 × 0 + {n} = ?",
            lambda n: str(n),
            lambda n: [str(n)],
            "Thứ tự phép tính: nhân trước. 1+0+{n}={n}.",
        ),
        (
            "{a} chia {a} nhân 0 cộng {c} = ?",
            lambda a, c: str(c),
            lambda a, c: [str(c), "0"],
            "{a}/{a}=1, ×0=0, +{c}={c}.",
        ),
        (
            "Có {n} quả táo, ăn {e} — còn mấy quả trên cây?",
            lambda n, e: "0",
            lambda n, e: ["0", "không", "khong"],
            "Ăn rồi thì trên cây còn 0 — không phải {n}-{e}.",
        ),
        (
            "{n} - {n} + {k} = ?",
            lambda n, k: str(k),
            lambda k: [str(k)],
            "Hủy nhau hết, còn {k}.",
        ),
    ]
    t = random.choice(templates)
    a, b, c = random.randint(2, 19), random.randint(2, 9), random.randint(1, 15)
    n, e, k = random.randint(5, 20), random.randint(1, 4), random.randint(1, 9)
    q_tpl, ans_fn, alts_fn, ex_tpl = t
    if "{a}" in q_tpl and "{b}" in q_tpl:
        q = q_tpl.format(a=a, b=b, c=c)
        ans = ans_fn(a, b, c)
        alts = alts_fn(a, b, c)
        ex = ex_tpl.format(a=a, b=b, c=c)
    elif "{n}" in q_tpl and "ăn" in q_tpl:
        q = q_tpl.format(n=n, e=e)
        ans = ans_fn(n, e)
        alts = alts_fn(n, e)
        ex = ex_tpl.format(n=n, e=e)
    elif "{n}" in q_tpl and "{k}" in q_tpl:
        q = q_tpl.format(n=n, k=k)
        ans = ans_fn(n, k)
        alts = alts_fn(k)
        ex = ex_tpl.format(n=n, k=k)
    else:
        q = q_tpl.format(n=k)
        ans = ans_fn(k)
        alts = alts_fn(k)
        ex = ex_tpl.format(n=k)
    return {"q": q, "a": list(set(alts + [ans])), "ans": ans, "explain": ex}


def gen_con_gi() -> dict:
    pairs = [
        ("Con gì biết bay mà không phải chim?", ["máy bay", "may bay", "tên lửa"], "Máy bay", "Có cánh mà là đồ chế tạo."),
        ("Con gì sống dưới nước mà không phải cá?", ["người", "tàu ngầm", "đá"], "Người/tàu", "Người bơi, tàu ngầm — không phải cá."),
        ("Con gì có 4 chân nhưng hay đứng 2 chân?", ["chó", "gấu", "khỉ", "người"], "Chó/gấu/khỉ", "Nhiều động vật đứng 2 chân."),
        ("Con gì sáng đi tối về?", ["con tim", "tim", "người đi làm"], "Con tim/người", "Tim hoặc người đi làm."),
        ("Con gì càng nuôi càng lớn nhưng không ăn?", ["nợ", "no", "khoản vay"], "Nợ", "Nợ càng nuôi càng to."),
        ("Con gì mà ai cũng nuôi trong đầu?", ["ý tưởng", "y tuong", "tưởng tượng"], "Ý tưởng", "Meta — trong đầu."),
        ("Con gì nói nhiều mà không mở miệng?", ["sách", "chat bot", "bot"], "Sách/bot", "Đọc hoặc bot chat."),
    ]
    q, a, ans, ex = random.choice(pairs)
    return {"q": q, "a": a, "ans": ans, "explain": ex}


def gen_cai_gi() -> dict:
    items = [
        ("Cái gì càng dùng càng hỏng?", ["ắc quy", "pin", "tuổi thọ"], "Pin/ắc quy", "Hao mòn."),
        ("Cái gì đi mà không đi?", ["thời gian", "thoi gian", "năm"], "Thời gian", "Trôi mà không chân."),
        ("Cái gì đánh mà không đau?", ["cờ", "co", "bài"], "Cờ/bài", "Đánh bài cờ."),
        ("Cái gì có mắt mà không nhìn?", ["kim", "khoai tây", "cây kim"], "Kim/khoai", "Kim may, khoai có «mắt»."),
        ("Cái gì càng sạch càng bẩn?", ["nước rửa", "xà phòng", "khăn lau"], "Nước rửa", "Rửa đồ bẩn thì nước bẩn."),
        ("Cái gì mở mà không đóng được?", ["miệng khi ngạc", "quảng cáo", "popup"], "Miệng/popup", "Bựa thật."),
        ("Cái gì càng chia càng to?", ["tin đồn", "drama", "nợ"], "Tin đồn/drama", "Lan truyền."),
        ("Cái gì ai cũng có nhưng không ai thấy?", ["mùi hôi", "hơi thở", "wifi yếu"], "Hơi/mùi", "Cảm nhận chứ không thấy."),
    ]
    q, a, ans, ex = random.choice(items)
    return {"q": q, "a": a, "ans": ans, "explain": ex}


def gen_bay() -> dict:
    traps = [
        ("Câu hỏi: màu của tuyết? (bẫy)", ["trắng", "trang", "không có màu"], "Trắng", "Tuyết trắng — đừng overthink."),
        ("Có phải cá heo sống trên cạn không?", ["không", "khong", "có"], "Không", "Heo biển — trên cạn thì… stress."),
        ("Thứ ba sau thứ hai là thứ mấy?", ["ba", "3", "thứ ba"], "Thứ ba", "Đọc kỹ."),
        ("1 phút có mấy giây?", ["60", "sáu mươi"], "60", "Toán lớp 1."),
        ("Nước sôi ở 100°C (nước nguyên chất)?", ["đúng", "dung", "co"], "Đúng", "Vật lý cơ bản."),
        ("Số 0 chia được cho 0 không?", ["không", "vo cuc", "lỗi"], "Không/lỗi", "Toán học nói không."),
    ]
    q, a, ans, ex = random.choice(traps)
    return {"q": q, "a": a, "ans": ans, "explain": ex}


def gen_viet_wordplay() -> dict:
    w = random.choice(ANIMALS)
    o = random.choice(OBJECTS)
    templates = [
        (
            f"Tại sao {w} không dùng {o}?",
            ["vì không biết", "không có tay", "không cần"],
            "Không cần / bựa",
            f"Câu vô tri — {w} không cần {o}.",
        ),
        (
            f"Nếu {o} biết nói, nói gì đầu tiên?",
            ["đừng dùng tao sai", "cứu", "help"],
            "Đừng dùng sai",
            f"{o.capitalize()} than vì bị dùng sai cách.",
        ),
        (
            f"Đi {random.choice(PLACES)} mà quên mang gì thì ngại nhất?",
            ["tiền", "điện thoại", "mặt"],
            "Tiền/điện thoại",
            "Thực tế xã hội.",
        ),
    ]
    q, a, ans, ex = random.choice(templates)
    return {"q": q, "a": a, "ans": ans, "explain": ex}


def gen_number_word() -> dict:
    n = random.randint(10, 99)
    digit_sum = sum(int(d) for d in str(n))
    return {
        "q": f"Số {n} — tổng các chữ số bằng mấy?",
        "a": [str(digit_sum), str(digit_sum)],
        "ans": str(digit_sum),
        "explain": f"{n} → {'+'.join(str(n))} = {digit_sum}.",
    }


def gen_logic() -> dict:
    logics = [
        {
            "q": "Anh trai em có 1 em trai. Em có mấy anh trai?",
            "a": ["1", "mot", "một"],
            "ans": "1",
            "explain": "Anh trai của anh = 1 người. Em có 1 anh.",
        },
        {
            "q": "Bạn đi vào quán. Có 1 người ngồi. Hỏi có mấy người trong quán?",
            "a": ["2", "hai"],
            "ans": "2",
            "explain": "1 + bạn = 2.",
        },
        {
            "q": "Tên tôi là gì? (trong câu đố này)",
            "a": ["không biết", "khong biet", "tên bạn", "ten ban"],
            "ans": "Không biết",
            "explain": "Bot không biết tên mày — bẫy.",
        },
        {
            "q": "Có 2 đồng xu, 1 ẩn mặt sấp. Xác suất đồng ẩn là ngửa?",
            "a": ["50", "50%", "mot nua", "một nửa"],
            "ans": "50%",
            "explain": "Ngẫu nhiên 1/2.",
        },
    ]
    return random.choice(logics)


def gen_meta_bot() -> dict:
    metas = [
        {
            "q": "Bot có ngủ không?",
            "a": ["không", "khong", "không ngủ"],
            "ans": "Không",
            "explain": "Polling 24/7 — ngủ là mày.",
        },
        {
            "q": "Gõ /stop thì bot im. Vậy bot sợ gì?",
            "a": ["lệnh stop", "stop", "mày"],
            "ans": "Lệnh /stop",
            "explain": "Hoặc sợ mày spam.",
        },
        {
            "q": "yt-dlp là gì? (trong bot này)",
            "a": ["tải video", "tai video", "tool"],
            "ans": "Tool tải video",
            "explain": "Engine tải clip FB.",
        },
    ]
    return random.choice(metas)


def gen_absurd() -> dict:
    a, b = random.randint(1, 9), random.randint(1, 9)
    absurd = [
        {
            "q": f"{a} + {b} bằng mấy (theo kiểu tình cảm)?",
            "a": ["69", "520", "1314", str(a + b)],
            "ans": "520/1314 hoặc tổng",
            "explain": "Toán tình cảm ≠ toán thật.",
        },
        {
            "q": "Mày + bot = ?",
            "a": ["drama", "clip fb", "gà", "chaos"],
            "ans": "Drama/chaos",
            "explain": "Tùy session.",
        },
        {
            "q": f"Có {random.randint(3,8)} người trong thang máy. Thang hỏi mấy người?",
            "a": ["0", "không", "thang máy không hỏi"],
            "ans": "Thang không hỏi",
            "explain": "Thang máy không biết nói — bựa.",
        },
    ]
    return random.choice(absurd)


GENERATORS = [
    gen_math,
    gen_con_gi,
    gen_cai_gi,
    gen_bay,
    gen_viet_wordplay,
    gen_number_word,
    gen_logic,
    gen_meta_bot,
    gen_absurd,
]


def build() -> list[dict]:
    seen: set[str] = set()
    out: list[dict] = []

    for r in HANDCRAFTED:
        k = r["q"].lower().strip()
        if k not in seen:
            seen.add(k)
            out.append(r)

    attempts = 0
    while len(out) < TARGET and attempts < TARGET * 20:
        attempts += 1
        gen = random.choice(GENERATORS)
        try:
            r = gen()
        except Exception:
            continue
        if not r:
            continue
        k = r["q"].lower().strip()
        if k in seen:
            continue
        seen.add(k)
        if "a" not in r or not r["a"]:
            continue
        if "ans" not in r:
            r["ans"] = r["a"][0]
        if "explain" not in r:
            r["explain"] = f"Đáp: {r['ans']}"
        out.append(r)

    return out[:TARGET]


def main() -> None:
    random.seed(42)
    riddles = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(riddles, ensure_ascii=False, indent=0), encoding="utf-8")
    print(f"Wrote {len(riddles)} riddles -> {OUT}")


if __name__ == "__main__":
    main()
