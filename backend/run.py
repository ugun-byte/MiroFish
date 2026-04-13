"""
MiroFish Backend 실행 엔트리포인트
"""

import os
import sys

# Windows 콘솔 한글 깨짐 문제 해결: 모든 패키지 임포트 전 UTF-8 인코딩 설정
if sys.platform == 'win32':
    # Python이 UTF-8을 사용하도록 환경변수 설정
    os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
    # 표준 출력 스트림을 UTF-8로 재설정
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# 프로젝트 루트 디렉토리를 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.config import Config


def main():
    """메인 함수"""
    # 설정 검증
    errors = Config.validate()
    if errors:
        print("설정 오류:")
        for err in errors:
            print(f"  - {err}")
        print("\n.env 파일 내의 설정을 확인해주세요")
        sys.exit(1)
    
    # 앱 생성
    app = create_app()
    
    # 실행 설정 가져오기
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5001))
    debug = Config.DEBUG
    
    # 서비스 시작
    app.run(host=host, port=port, debug=debug, threaded=True)


if __name__ == '__main__':
    main()

