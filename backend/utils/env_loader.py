"""
环境变量加载工具
从 .env 文件读取 DeepSeek、高德、和风天气 API Key
"""
import os
from dotenv import load_dotenv

# 项目根目录的 .env 文件路径
# 基于本文件位置动态定位（backend/utils/env_loader.py -> backend/utils -> backend -> 项目根目录）
# 项目克隆到任意目录都能正确读取，无需改代码
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENV_PATH = os.path.join(PROJECT_ROOT, '.env')

load_dotenv(ENV_PATH)


def get_deepseek_api_key() -> str:
    """获取 DeepSeek API 密钥"""
    return os.getenv('DEEPSEEK_API_KEY', '')


def get_gaode_api_key() -> str:
    """获取高德地图 API 密钥"""
    return os.getenv('GAODE_API_KEY', '')


def get_weather_api_key() -> str:
    """获取和风天气 API 密钥"""
    return os.getenv('HEFENG_API_KEY', '')

