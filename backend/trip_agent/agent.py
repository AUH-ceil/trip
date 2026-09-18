"""
TripAgent 主类
统一注册所有 Skill 工具，大模型可自主调度完成多步骤行程任务
"""
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage
from backend.trip_agent.prompt_template import TRIP_AGENT_SYSTEM_PROMPT, build_trip_prompt
from backend.app.services.weather_service import get_weather_forecast
from backend.app.services.map_service import search_pois
from backend.app.services.wardrobe_recommend import recommend_wardrobe
from backend.utils.env_loader import get_deepseek_api_key


class TripAgent:
    """旅行规划智能体，集成多个 Skill 工具，生成完整行程方案"""

    def __init__(self):
        self.llm = self._init_llm()
        self.agent = self._build_agent()

    def _init_llm(self) -> ChatOpenAI:
        """初始化大语言模型（DeepSeek Chat）"""
        api_key = get_deepseek_api_key()
        return ChatOpenAI(
            model='deepseek-chat',
            openai_api_key=api_key,
            openai_api_base='https://api.deepseek.com/v1',
            temperature=0.7,
            max_tokens=4096,
        )
#aaad
    def _register_tools(self) -> list:
        """注册所有 Agent Skill 工具（使用 @tool 装饰器）"""

        @tool
        async def weather_forecast(city: str) -> str:
            """查询目的地天气预报，输入城市名称，返回多日天气预报"""
            return await get_weather_forecast(city, 3)

        @tool
        async def search_places(keyword: str, city: str = '') -> str:
            """搜索景点、餐厅、购物地点信息，输入关键词和城市名"""
            return await search_pois(keyword, city)

        @tool
        async def wardrobe_recommendation(city: str) -> str:
            """根据目的地天气推荐穿搭，输入城市名称"""
            return await recommend_wardrobe(city)

        return [weather_forecast, search_places, wardrobe_recommendation]

    def _build_agent(self):
        """构建 LangGraph 模式的 Agent"""
        tools = self._register_tools()
        return create_agent(
            model=self.llm,
            tools=tools,
            system_prompt=TRIP_AGENT_SYSTEM_PROMPT,
        )

    async def generate_trip(self, destination: str, days: int, preferences: str = '') -> str:
        """
        生成完整行程方案

        参数:
            destination: 目的地
            days: 行程天数
            preferences: 偏好说明

        返回:
            格式化的行程方案文本
        """
        user_input = build_trip_prompt(destination, days, preferences)
        result = await self.agent.ainvoke({
            'messages': [HumanMessage(content=user_input)],
        })
        # 提取最终输出
        messages = result.get('messages', [])
        if messages:
            return messages[-1].content if hasattr(messages[-1], 'content') else str(messages[-1])
        return '行程生成失败，请稍后重试'


# 全局单例
trip_agent = TripAgent()

