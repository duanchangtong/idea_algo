"""应用配置"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # 数据库配置（FC环境下使用/tmp目录，本地使用项目目录）
    _is_fc = os.getenv("APP_FC_MODE", "") == "true"
    _db_dir = "/tmp" if _is_fc else os.path.dirname(os.path.abspath(__file__))
    DATABASE = os.path.join(_db_dir, "painpoints.db")

    # 百炼API配置
    BAILIAN_API_KEY = os.getenv("BAILIAN_TOKEN_API_KEY", "")
    BAILIAN_BASE_URL = os.getenv("BAILIAN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    MODEL_NAME = "qwen3.8-max"

    # 点赞奖励阶梯配置
    REWARD_TIERS = [
        {"min_likes": 10, "title": "生活观察家", "badge": "🔍"},
        {"min_likes": 50, "title": "痛点猎人", "badge": "🎯"},
        {"min_likes": 100, "title": "脑洞达人", "badge": "💡"},
        {"min_likes": 300, "title": "创意大师", "badge": "🏆"},
        {"min_likes": 500, "title": "生活改造王", "badge": "👑"},
    ]
