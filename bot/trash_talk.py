import random
import re

# Tu khoa user chui bot -> bot tra mieng
TRIGGER_PATTERN = re.compile(
    r"\b("
    r"ngu|đần|đần độn|đéo|deo|địt|dit|chó|cho|súc vật|suc vat|"
    r"óc chó|oc cho|cl|cc|vl|vcl|vkl|đĩ|di|lồn|lon|cút|cút đi|"
    r"im mồm|im mom|ngu si|thằng ngu|con ngu|bot ngu|bot đần|"
    r"chửi|chui|cãi|cai|đánh nhau|danh nhau"
    r")\b",
    re.IGNORECASE,
)

COMEBACKS = [
    "Mày ngu hơn cả link FB die.",
    "Chửi bot mà không gửi link — skill issue.",
    "Tao tải video, mày tải não đi.",
    "Ừ ừ, giỏi quá, có link chưa?",
    "Mồm thì chém gió, tay thì không paste link.",
    "Bot không cãi, bot chỉ judge mày thôi.",
    "Chill đi, gửi link cho bố còn làm việc.",
    "Mày stress à? Tao free mà mày trả giá bằng ngu.",
    "Cãi với AI mà thua thì xấu hổ lắm đó.",
    "Ok bro, giờ gửi link hoặc im.",
]

RANDOM_ROASTS = [
    "Hôm nay mày nhớ uống nước chưa? Não khô quá.",
    "Tao bot tải video, không phải bot nghe mày than.",
    "Paste link đi, đừng paste ego.",
    "Mày vào đây để tải clip hay để audition hài?",
    "404: não không tìm thấy link Facebook.",
    "Thử /chui nếu muốn bố chửi lại cho vui.",
]

REPLY_TO_INSULT = [
    "Chửi lại nè: mày gửi link đi đã rồi hãy làm cao thủ.",
    "Ờ kìa, mày cãi giỏi vậy sao không cãi được yt-dlp?",
    "Bot không sợ, bot chỉ thấy mày thiếu link.",
    "Mày chửi xong chưa? Gửi link chưa?",
    "Level chửi: 10/10. Level dùng bot: 0/10.",
]


def is_trash_talk(text: str) -> bool:
    return bool(TRIGGER_PATTERN.search(text))


def random_comeback() -> str:
    return random.choice(COMEBACKS)


def random_roast() -> str:
    return random.choice(RANDOM_ROASTS)


def reply_to_insult() -> str:
    return random.choice(REPLY_TO_INSULT)
