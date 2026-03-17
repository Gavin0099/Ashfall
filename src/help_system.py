from .difficulty import get_difficulty_profile

HELP_TOPICS = {
    "radiation": {
        "title": "輻射 (Radiation)",
        "content": "輻射是荒廢世界中最致命的隱形威脅。\n- 每一點輻射都會在每次移動時讓你失去 1 點 HP。\n- 目前只有少數裝備（如防毒面具）可以減緩這種消耗。\n- 醫療包無法移除輻射，只能暫時修補受損的身體。"
    },
    "travel_mode": {
        "title": "旅行模式 (Travel Mode)",
        "content": "你可以根據當前物資選擇行進方式：\n- 常規 (Normal)：標準消耗。\n- 衝刺 (Rush)：食物消耗 -1，但發生事件時的戰鬥機率 +20%。\n- 謹慎 (Careful)：食物消耗 +1，但戰鬥機率 -20%。"
    },
    "resources": {
        "title": "物資與生存 (Resources)",
        "content": "- HP: 生命值，歸零即結束冒險。\n- 食物 (Food): 移動的基本消耗，耗盡會導致生命迅速流失。\n- 彈藥 (Ammo): 戰鬥的必需品，沒有彈藥將難以在廢土生存。\n- 醫療包 (Medkit): 回復 HP 的唯一手段。\n- 零件 (Scrap): 交易與 Meta 商店的通用貨幣。"
    }
}

def get_help_text(topic_id: str) -> str | None:
    topic = HELP_TOPICS.get(topic_id)
    if not topic:
        return None
    return f"【 {topic['title']} 】\n{topic['content']}"

def list_topics() -> list[str]:
    return list(HELP_TOPICS.keys())
