import json
import math
import re
import urllib.error
import urllib.request

from config import (
    DEEPSEEK_API_KEY,
    DEEPSEEK_BASE_URL,
    DEEPSEEK_MODEL,
    DEEPSEEK_TIMEOUT,
)


INTENT_KEYWORDS = {
    "产品咨询": ["买", "购买", "推荐", "配置", "续航", "区别", "适合", "价格", "优惠", "车型"],
    "订单查询": ["订单", "物流", "发货", "自提", "提车", "什么时候到", "快递"],
    "退换货": ["退货", "换货", "退款", "七天", "不想要", "质量问题"],
    "故障排查": ["坏", "故障", "启动不了", "无法启动", "续航变短", "连接不上", "蓝牙", "报警"],
    "保修政策": ["保修", "质保", "保修多久", "免费维修", "电池保"],
    "发票凭证": ["发票", "税号", "抬头", "凭证", "报销"],
    "投诉安抚": ["投诉", "生气", "不满意", "太慢", "失望", "差评", "人工"],
}

HANDOFF_KEYWORDS = [
    "转人工",
    "人工客服",
    "真人客服",
    "客服介入",
    "人工处理",
    "人工接入",
    "联系人工",
    "找人工",
    "找客服",
    "升级人工",
]

EMOTION_WORDS = {
    "angry": ["生气", "差评", "投诉", "太差", "垃圾", "不满意", "离谱", "烦"],
    "anxious": ["着急", "急用", "马上", "尽快", "怎么办", "担心"],
}

ORDER_NO_PATTERN = re.compile(r"\bYX\d{12,16}\b", re.IGNORECASE)


def tokenize(text):
    text = (text or "").lower()
    latin = re.findall(r"[a-z0-9]+", text)
    cjk = re.findall(r"[\u4e00-\u9fff]", text)
    bigrams = [text[i : i + 2] for i in range(max(len(text) - 1, 0))]
    bigrams = [token for token in bigrams if re.search(r"[\u4e00-\u9fff]", token)]
    return latin + cjk + bigrams


def split_keywords(keywords):
    return [item.strip().lower() for item in re.split(r"[,，、\s]+", keywords or "") if item.strip()]


def classify_intent(message):
    score_by_intent = {}
    for intent, words in INTENT_KEYWORDS.items():
        score = sum(1 for word in words if word in message)
        if score:
            score_by_intent[intent] = score
    if not score_by_intent:
        return "综合咨询"
    return max(score_by_intent, key=score_by_intent.get)


def extract_order_no(message):
    match = ORDER_NO_PATTERN.search(message or "")
    return match.group(0).upper() if match else ""


def is_handoff_request(message):
    compact = re.sub(r"\s+", "", message or "")
    if "人工智能" in compact:
        return False
    return any(keyword in compact for keyword in HANDOFF_KEYWORDS)


def detect_emotion(message):
    for emotion, words in EMOTION_WORDS.items():
        if any(word in message for word in words):
            return emotion
    return "neutral"


def entry_text(entry):
    return " ".join(
        [
            str(entry.get("category", "")),
            str(entry.get("title", "")),
            str(entry.get("question", "")),
            str(entry.get("answer", "")),
            str(entry.get("keywords", "")),
        ]
    )


def score_entry(message, entry):
    message_tokens = tokenize(message)
    entry_tokens = tokenize(entry_text(entry))
    if not message_tokens or not entry_tokens:
        return 0.0

    message_set = set(message_tokens)
    entry_set = set(entry_tokens)
    overlap = len(message_set & entry_set)
    union = len(message_set | entry_set)
    jaccard = overlap / union if union else 0

    keyword_bonus = 0.0
    for keyword in split_keywords(entry.get("keywords", "")):
        if keyword and keyword in message.lower():
            keyword_bonus += 0.35

    title_bonus = 0.25 if str(entry.get("title", "")).lower() in message.lower() else 0
    length_penalty = 1 / math.sqrt(max(len(entry_tokens), 1))
    return jaccard + keyword_bonus + title_bonus + length_penalty * overlap * 0.03


def retrieve_knowledge(message, knowledge, top_k=3):
    scored = []
    for entry in knowledge:
        score = score_entry(message, entry)
        if score > 0:
            item = dict(entry)
            item["score"] = round(score, 4)
            scored.append(item)
    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored[:top_k]


def empathy_prefix(emotion):
    if emotion == "angry":
        return "非常抱歉给您带来不好的体验，我先帮您把问题拆清楚并给出下一步处理方案。"
    if emotion == "anxious":
        return "我理解您现在比较着急，我会优先给出最快能执行的处理步骤。"
    return ""


def local_reply(message, intent, emotion, sources):
    prefix = empathy_prefix(emotion)
    if sources:
        best = sources[0]
        answer = best["answer"]
        next_step = ""
        if intent == "订单查询":
            next_step = "如果需要继续查询，请补充订单号或下单手机号后四位。"
        elif intent == "故障排查":
            next_step = "如果排查后仍未恢复，请补充车型、仪表提示和故障照片，我可以继续帮您定位。"
        elif intent == "投诉安抚":
            next_step = "若问题已经影响使用，我建议同步转人工客服并保留订单、维修单或照片凭证。"
        else:
            next_step = "如果您告诉我所在城市、车型或订单状态，我可以继续细化建议。"
        parts = [part for part in [prefix, answer, next_step] if part]
        return "\n\n".join(parts)

    fallback = "我暂时没有在知识库中找到完全匹配的信息。为了避免误导您，请补充车型、订单号、故障现象或所在城市，我会继续帮您缩小范围；也可以为您转接人工客服。"
    return "\n\n".join([part for part in [prefix, fallback] if part])


def format_order_reply(order):
    if not order:
        return (
            "我还没有查到这个订单号。请确认订单号是否以 YX 开头，或者重新发送完整订单号。"
            "\n\n如果您是在课堂演示，可以先点击“生成演示订单”，再把生成的订单号发给我查询。"
        )

    return "\n\n".join(
        [
            f"已为您查询到订单 {order['order_no']}：",
            (
                f"商品：{order['product_name']}\n"
                f"城市：{order['city']}\n"
                f"实付金额：{order['amount']:.2f} 元"
            ),
            (
                f"付款状态：{order['payment_status']}\n"
                f"订单状态：{order['status']}\n"
                f"物流进度：{order['logistics_status']}\n"
                f"售后状态：{order['aftersale_status']}"
            ),
            "下一步建议：如果您要催发货、申请退换货、预约门店检测或转人工，请直接告诉我您的诉求，我会按当前订单状态继续处理。",
        ]
    )


def format_handoff_reply(ticket):
    return "\n\n".join(
        [
            f"已为您转接人工客服，并创建人工工单 {ticket['ticket_no']}。",
            (
                f"当前状态：{ticket['status']}\n"
                f"优先级：{ticket['priority']}\n"
                f"处理小组：{ticket['assigned_team']}\n"
                f"预计响应：{ticket['expected_response']}"
            ),
            "您可以继续补充订单号、车型、故障现象或照片说明。人工客服接入后，会优先查看本次会话记录，不需要您重复说明全部问题。",
        ]
    )


def build_system_prompt(context_text):
    return f"""你是“悦行智能电动车”的销售与售后服务 AI 助手。

服务目标：
1. 回答产品咨询、订单查询、退换货、保修、故障排查、发票和投诉安抚问题。
2. 优先依据知识库回答，不确定时主动说明并引导用户补充信息或转人工客服。
3. 语气专业、耐心、简洁，面对负面情绪先安抚再处理。
4. 不编造订单状态、价格、门店库存、保修结论或检测结果。
5. 遇到安全风险、质量争议、多次维修、用户强烈不满时，建议升级人工客服。

可参考知识库：
{context_text}
"""


def call_deepseek(messages):
    if not DEEPSEEK_API_KEY:
        return None

    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": messages,
        "temperature": 0.35,
        "top_p": 0.85,
        "max_tokens": 900,
    }
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        DEEPSEEK_BASE_URL,
        data=data,
        method="POST",
        headers={
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=DEEPSEEK_TIMEOUT) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    return body["choices"][0]["message"]["content"].strip()


def generate_reply(message, knowledge, history, order=None, order_no=""):
    message = (message or "").strip()
    intent = classify_intent(message)
    emotion = detect_emotion(message)
    detected_order_no = order_no or extract_order_no(message)

    if detected_order_no:
        metadata = {
            "intent": "订单查询",
            "emotion": emotion,
            "sources": [],
            "order_no": detected_order_no,
            "model_mode": "order-workflow",
        }
        return {
            "answer": format_order_reply(order),
            "intent": "订单查询",
            "emotion": emotion,
            "sources": [],
            "model_mode": "order-workflow",
            "metadata": metadata,
        }

    sources = retrieve_knowledge(message, knowledge)

    context_text = "\n".join(
        f"- [{item['category']}] {item['title']}：{item['answer']}"
        for item in sources
    ) or "暂无匹配知识库片段。"

    conversation = [
        {"role": "system", "content": build_system_prompt(context_text)}
    ]
    for item in history[-6:]:
        role = "assistant" if item["role"] == "assistant" else "user"
        conversation.append({"role": role, "content": item["content"]})
    conversation.append({"role": "user", "content": message})

    metadata = {
        "intent": intent,
        "emotion": emotion,
        "sources": [
            {
                "id": item["id"],
                "title": item["title"],
                "category": item["category"],
                "score": item["score"],
            }
            for item in sources
        ],
    }

    try:
        llm_answer = call_deepseek(conversation)
    except (urllib.error.URLError, TimeoutError, KeyError, json.JSONDecodeError) as exc:
        llm_answer = None
        metadata["llm_error"] = str(exc)

    if llm_answer:
        metadata["model_mode"] = "deepseek"
        answer = llm_answer
    else:
        metadata["model_mode"] = "local-retrieval"
        answer = local_reply(message, intent, emotion, sources)

    return {
        "answer": answer,
        "intent": intent,
        "emotion": emotion,
        "sources": metadata["sources"],
        "model_mode": metadata["model_mode"],
        "metadata": metadata,
    }
