"""
설정 관리
프로젝트 루트 디렉토리의 .env 파일에서 하나로 통합하여 설정 로드
"""

import os
from dotenv import load_dotenv

# 프로젝트 루트 디렉토리의 .env 파일 로드
# 경로: MiroFish/.env (backend/app/config.py 기준 상대경로)
project_root_env = os.path.join(os.path.dirname(__file__), '../../.env')

if os.path.exists(project_root_env):
    load_dotenv(project_root_env, override=True)
else:
    # 루트 디렉토리에 .env가 없으면 환경변수 로드 시도 (프로덕션 환경용)
    load_dotenv(override=True)


class Config:
    """Flask 설정 클래스"""
    
    # Flask 설정
    SECRET_KEY = os.environ.get('SECRET_KEY', 'mirofish-secret-key')
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    # JSON 설정 - ASCII 이스케이프 비활성화, 한글을 \uXXXX가 아닌 그대로 표시
    JSON_AS_ASCII = False
    
    # LLM 설정（OpenAI 포맷으로 통일)
    LLM_API_KEY = os.environ.get('LLM_API_KEY')
    LLM_BASE_URL = os.environ.get('LLM_BASE_URL', 'https://api.openai.com/v1')
    LLM_MODEL_NAME = os.environ.get('LLM_MODEL_NAME', 'gpt-4o-mini')
    
    # Zep 설정
    ZEP_API_KEY = os.environ.get('ZEP_API_KEY')
    
    # 파일 업로드 설정
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '../uploads')
    ALLOWED_EXTENSIONS = {'pdf', 'md', 'txt', 'markdown'}
    
    # 텍스트 처리 설정
    DEFAULT_CHUNK_SIZE = 500  # 기본 청크 크기
    DEFAULT_CHUNK_OVERLAP = 50  # 기본 겹침 크기
    
    # OASIS 시뮬레이션 설정
    OASIS_DEFAULT_MAX_ROUNDS = int(os.environ.get('OASIS_DEFAULT_MAX_ROUNDS', '10'))
    OASIS_SIMULATION_DATA_DIR = os.path.join(os.path.dirname(__file__), '../uploads/simulations')
    
    # OASIS 플랫폼 가용 액션 설정
    OASIS_TWITTER_ACTIONS = [
        'CREATE_POST', 'LIKE_POST', 'REPOST', 'FOLLOW', 'DO_NOTHING', 'QUOTE_POST'
    ]
    OASIS_REDDIT_ACTIONS = [
        'LIKE_POST', 'DISLIKE_POST', 'CREATE_POST', 'CREATE_COMMENT',
        'LIKE_COMMENT', 'DISLIKE_COMMENT', 'SEARCH_POSTS', 'SEARCH_USER',
        'TREND', 'REFRESH', 'DO_NOTHING', 'FOLLOW', 'MUTE'
    ]
    
    # Report Agent 설정
    REPORT_AGENT_MAX_TOOL_CALLS = int(os.environ.get('REPORT_AGENT_MAX_TOOL_CALLS', '5'))
    REPORT_AGENT_MAX_REFLECTION_ROUNDS = int(os.environ.get('REPORT_AGENT_MAX_REFLECTION_ROUNDS', '2'))
    REPORT_AGENT_TEMPERATURE = float(os.environ.get('REPORT_AGENT_TEMPERATURE', '0.5'))
    
    @classmethod
    def validate(cls):
        """필수 설정 검증"""
        errors = []
        if not cls.LLM_API_KEY:
            errors.append("LLM_API_KEY가 구성되지 않음")
        if not cls.ZEP_API_KEY:
            errors.append("ZEP_API_KEY가 구성되지 않음")
        return errors
    
    @classmethod
    def update_llm_config(cls, api_key: str = None, base_url: str = None, model_name: str = None):
        """
        런타임에 LLM 설정을 업데이트하고 .env 파일도 동시 갱신
        
        Args:
            api_key: 새 API Key (None이면 변경하지 않음)
            base_url: 새 Base URL (None이면 변경하지 않음)
            model_name: 새 Model Name (None이면 변경하지 않음)
        """
        # 1. 클래스 변수 업데이트 (런타임 즉시 반영)
        if api_key is not None:
            cls.LLM_API_KEY = api_key
            os.environ['LLM_API_KEY'] = api_key
        if base_url is not None:
            cls.LLM_BASE_URL = base_url
            os.environ['LLM_BASE_URL'] = base_url
        if model_name is not None:
            cls.LLM_MODEL_NAME = model_name
            os.environ['LLM_MODEL_NAME'] = model_name
        
        # 2. .env 파일 업데이트 (영구 저장)
        env_path = os.path.join(os.path.dirname(__file__), '../../.env')
        cls._update_env_file(env_path)
    
    @classmethod
    def _update_env_file(cls, env_path: str):
        """
        .env 파일의 LLM 관련 설정을 현재 클래스 변수 값으로 업데이트
        """
        if not os.path.exists(env_path):
            return
        
        with open(env_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 업데이트할 키-값 맵
        updates = {
            'LLM_API_KEY': cls.LLM_API_KEY,
            'LLM_BASE_URL': cls.LLM_BASE_URL,
            'LLM_MODEL_NAME': cls.LLM_MODEL_NAME,
        }
        
        updated_keys = set()
        new_lines = []
        for line in lines:
            stripped = line.strip()
            matched = False
            for key, value in updates.items():
                if stripped.startswith(f'{key}=') or stripped.startswith(f'# {key}='):
                    new_lines.append(f'{key}={value}\n')
                    updated_keys.add(key)
                    matched = True
                    break
            if not matched:
                new_lines.append(line)
        
        # 파일에 없던 키는 끝에 추가
        for key, value in updates.items():
            if key not in updated_keys and value:
                new_lines.append(f'{key}={value}\n')
        
        with open(env_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
    
    @classmethod
    def get_llm_config(cls):
        """현재 LLM 설정을 딕셔너리로 반환"""
        return {
            'api_key': cls.LLM_API_KEY,
            'base_url': cls.LLM_BASE_URL,
            'model_name': cls.LLM_MODEL_NAME,
        }

