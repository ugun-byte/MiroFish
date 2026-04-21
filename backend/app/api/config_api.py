"""
LLM 설정 API
런타임에 LLM 모델/프로바이더를 변경하기 위한 API 엔드포인트
"""

from flask import Blueprint, request, jsonify
from ..config import Config
from ..utils.logger import get_logger

logger = get_logger('mirofish.config')

config_bp = Blueprint('config', __name__)

# ═══════════════════════════════════════════════════════════════
# 프리셋 정의
# ═══════════════════════════════════════════════════════════════

LLM_PRESETS = [
    {
        "id": "openclaw-codex",
        "name": "OpenClaw → GPT-5.4 Codex",
        "icon": "🦞",
        "description": "OpenAI Codex 구독 모델 (OpenClaw OAuth 경유, 무료)",
        "base_url": "http://127.0.0.1:18789/v1",
        "model_name": "openclaw",
        "requires_api_key": False,
        "default_api_key": "925cb4d9d4549638d25dd894c56a9ab.SR0MlQOQHE3rd9V8fKW2geEx"
    },
    {
        "id": "ollama-gemma4",
        "name": "Ollama Gemma4 (로컬)",
        "icon": "🏠",
        "description": "로컬 Ollama 서버에서 Gemma4 추론 (무료)",
        "base_url": "http://127.0.0.1:11434/v1",
        "model_name": "gemma4:e2b",
        "requires_api_key": False,
        "default_api_key": "ollama"
    },
    {
        "id": "openclaw-tuza",
        "name": "OpenClaw → Tuza Agent",
        "icon": "🤖",
        "description": "OpenClaw Tuza 에이전트 (코딩 특화)",
        "base_url": "http://127.0.0.1:18789/v1",
        "model_name": "openclaw/tuza",
        "requires_api_key": False,
        "default_api_key": "925cb4d9d4549638d25dd894c56a9ab.SR0MlQOQHE3rd9V8fKW2geEx"
    },
    {
        "id": "custom",
        "name": "Custom (직접 입력)",
        "icon": "⚡",
        "description": "OpenAI SDK 호환 API 직접 설정",
        "base_url": "",
        "model_name": "",
        "requires_api_key": True,
        "api_key_hint": "your-api-key"
    },
    {
        "id": "openclaw-gpt-5-mini",
        "name": "OpenClaw → GPT-5 Mini",
        "icon": "🚀",
        "description": "GPT-5 Mini 모델 (OpenClaw OAuth 경유)",
        "base_url": "http://127.0.0.1:18789/v1",
        "model_name": "gpt-5-mini",
        "requires_api_key": False,
        "default_api_key": "925cb4d9d4549638d25dd894c56a9ab.SR0MlQOQHE3rd9V8fKW2geEx"
    },
    {
        "id": "openai-codex",
        "name": "OpenAI Codex",
        "icon": "💻",
        "description": "OpenAI Codex 공식 모델",
        "base_url": "https://api.openai.com/v1",
        "model_name": "code-davinci-002",
        "requires_api_key": True,
        "api_key_hint": "sk-..."
    },
    {
        "id": "0auth-model",
        "name": "0auth",
        "icon": "🔐",
        "description": "0auth 기반 인증 모델",
        "base_url": "https://api.openai.com/v1",
        "model_name": "0auth",
        "requires_api_key": True,
        "api_key_hint": "sk-..."
    }
]


@config_bp.route('/llm', methods=['GET'])
def get_llm_config():
    """
    현재 LLM 설정 조회
    
    Returns:
        {
            "success": true,
            "data": {
                "api_key": "sk-or-...",  (마스킹됨)
                "api_key_raw_length": 42,
                "base_url": "https://openrouter.ai/api/v1",
                "model_name": "openai-codex/gpt-5.4",
                "active_preset_id": "openrouter-gpt54"  (자동 감지)
            }
        }
    """
    config = Config.get_llm_config()
    
    # API Key 마스킹 (앞 8자만 표시)
    raw_key = config['api_key'] or ''
    if len(raw_key) > 8:
        masked_key = raw_key[:8] + '...' + raw_key[-4:]
    else:
        masked_key = raw_key
    
    # 현재 설정과 매칭되는 프리셋 자동 감지
    active_preset_id = _detect_active_preset(config)
    
    return jsonify({
        "success": True,
        "data": {
            "api_key": masked_key,
            "api_key_raw_length": len(raw_key),
            "base_url": config['base_url'],
            "model_name": config['model_name'],
            "active_preset_id": active_preset_id
        }
    })


@config_bp.route('/llm', methods=['PUT'])
def update_llm_config():
    """
    LLM 설정 변경 (런타임 + .env 파일 동시 업데이트)
    
    Request Body:
        {
            "api_key": "sk-or-...",
            "base_url": "https://openrouter.ai/api/v1",
            "model_name": "openai-codex/gpt-5.4"
        }
    """
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "요청 본문이 비어있습니다"}), 400
    
    api_key = data.get('api_key')
    base_url = data.get('base_url')
    model_name = data.get('model_name')
    
    if not any([api_key, base_url, model_name]):
        return jsonify({
            "success": False, 
            "error": "api_key, base_url, model_name 중 하나 이상 제공해주세요"
        }), 400
    
    try:
        Config.update_llm_config(
            api_key=api_key,
            base_url=base_url,
            model_name=model_name
        )
        
        updated_config = Config.get_llm_config()
        active_preset_id = _detect_active_preset(updated_config)
        
        logger.info(f"LLM 설정 변경됨: model={updated_config['model_name']}, "
                    f"base_url={updated_config['base_url']}")
        
        return jsonify({
            "success": True,
            "message": "LLM 설정이 업데이트되었습니다",
            "data": {
                "base_url": updated_config['base_url'],
                "model_name": updated_config['model_name'],
                "active_preset_id": active_preset_id
            }
        })
        
    except Exception as e:
        logger.error(f"LLM 설정 변경 실패: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"설정 변경 실패: {str(e)}"
        }), 500


@config_bp.route('/llm/presets', methods=['GET'])
def get_llm_presets():
    """
    프리셋 목록 반환
    """
    current_config = Config.get_llm_config()
    active_preset_id = _detect_active_preset(current_config)
    
    return jsonify({
        "success": True,
        "data": {
            "presets": LLM_PRESETS,
            "active_preset_id": active_preset_id
        }
    })


def _detect_active_preset(config: dict) -> str:
    """현재 설정과 매칭되는 프리셋 ID를 자동 감지"""
    for preset in LLM_PRESETS:
        if preset['id'] == 'custom':
            continue
        if (config.get('base_url') == preset['base_url'] and 
            config.get('model_name') == preset['model_name']):
            return preset['id']
    return 'custom'
