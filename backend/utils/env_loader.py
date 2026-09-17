"""
环境变量加载工具
从 .env 文件读取 DeepSeek、高德、和风天气 API Key
"""
import os
from dotenv import load_dotenv

# 项目根目录的 .env 文件路径
load_dotenv(r"E:\trip\.env")


def get_deepseek_api_key() -> str:
    """获取 DeepSeek API 密钥"""
    return os.getenv('DEEPSEEK_API_KEY', '')


def get_gaode_api_key() -> str:
    """获取高德地图 API 密钥"""
    return os.getenv('GAODE_API_KEY', '')


def get_weather_api_key() -> str:
    """获取和风天气 API 密钥"""
    return os.getenv('HEFENG_API_KEY', '')

