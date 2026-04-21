"""
LLM客户端封装
统一使用OpenAI格式调用
"""

import json
import re
from typing import Optional, Dict, Any, List
from openai import OpenAI

from ..config import Config
import logging

logger = logging.getLogger(__name__)

class LLMClient:
    """LLM客户端"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None
    ):
        self.api_key = api_key or Config.LLM_API_KEY
        self.base_url = base_url or Config.LLM_BASE_URL
        self.model = model or Config.LLM_MODEL_NAME
        
        if not self.api_key:
            raise ValueError("LLM_API_KEY 未配置")
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: Optional[Dict] = None
    ) -> str:
        """
        发送聊天请求
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数
            response_format: 响应格式（如JSON模式）
            
        Returns:
            模型响应文本
        """
        # OpenClaw proxy requires 'openclaw' or 'openclaw/{model}'
        request_model = self.model
        if "18789" in self.base_url and not request_model.startswith("openclaw"):
            if request_model == "gpt-5-mini":
                request_model = "openclaw/gpt-5-mini"
            else:
                request_model = "openclaw"

        kwargs = {
            "model": request_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        if response_format:
            kwargs["response_format"] = response_format
        
        import time
        max_retries = 3
        retry_delay = 1.0

        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    **kwargs,
                    timeout=120.0 # 2분 타임아웃
                )
                content = response.choices[0].message.content
                if not content or content.strip() == "":
                     if attempt < max_retries - 1:
                        logger.warning(f"LLM 응답이 비어있음 (시도 {attempt+1}/{max_retries}). 재시도 중...")
                        time.sleep(retry_delay * (2 ** attempt))
                        continue
                     return "No response from OpenClaw."
                
                # 부분 모델（如MiniMax M2.5）会在content中包含<think>思考内容，需要移除
                content = re.sub(r'<think>[\s\S]*?</think>', '', content).strip()
                return content
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"LLM 호출 실패 (시도 {attempt+1}/{max_retries}): {str(e)}. 재시도 중...")
                    time.sleep(retry_delay * (2 ** attempt))
                else:
                    logger.error(f"LLM 호출 최종 실패: {str(e)}")
                    return f"Error: {str(e)}"
        
        return "No response from OpenClaw."
    
    def chat_json(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 4096
    ) -> Dict[str, Any]:
        """
        发送聊天请求并返回JSON
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数
            
        Returns:
            解析后的JSON对象
        """
        response = self.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        # 清理markdown代码块标记
        cleaned_response = response.strip()
        cleaned_response = re.sub(r'^```(?:json)?\s*\n?', '', cleaned_response, flags=re.IGNORECASE)
        cleaned_response = re.sub(r'\n?```\s*$', '', cleaned_response)
        cleaned_response = cleaned_response.strip()

        try:
            return json.loads(cleaned_response)
        except json.JSONDecodeError:
            raise ValueError(f"LLM返回的JSON格式无效: {cleaned_response}")

