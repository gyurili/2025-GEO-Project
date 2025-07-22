import requests
import json
from typing import Dict, Any, Optional
import streamlit as st
import sys
from pathlib import Path

# 로거 임포트 추가
sys.path.append(str(Path(__file__).parent.parent))
from utils.logger import get_logger

# 로거 설정
logger = get_logger(__name__)

class APIClient:
    """FastAPI 서버와 통신하는 클라이언트"""
    
    def __init__(self, base_url: str = "http://localhost:8010"):
        logger.debug("🛠️ APIClient 인스턴스 초기화 시작")
        self.base_url = base_url
        self.session = requests.Session()
        logger.debug(f"🛠️ API 기본 URL 설정: {base_url}")
        logger.info("✅ APIClient 인스턴스 초기화 완료")
        
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict[str, Any]]:
        """HTTP 요청 수행"""
        logger.debug(f"🛠️ HTTP 요청 시작: {method} {endpoint}")
        
        try:
            url = f"{self.base_url}{endpoint}"
            logger.debug(f"🛠️ 요청 URL: {url}")
            
            response = self.session.request(method, url, **kwargs)
            logger.debug(f"🛠️ 응답 상태 코드: {response.status_code}")
            
            response.raise_for_status()
            result = response.json()
            logger.info(f"✅ HTTP 요청 성공: {method} {endpoint}")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ API 요청 실패: {str(e)}")
            st.error(f"API 요청 실패: {str(e)}")
            return None
        except json.JSONDecodeError:
            logger.error("❌ API 응답 JSON 파싱 실패")
            st.error("API 응답을 파싱할 수 없습니다.")
            return None
    
    def health_check(self) -> bool:
        """서버 상태 확인"""
        logger.debug("🛠️ 서버 헬스체크 시작")
        
        result = self._make_request("GET", "/health")
        is_healthy = result and result.get("success", False)
        
        if is_healthy:
            logger.info("✅ 서버 헬스체크 성공")
        else:
            logger.warning("⚠️ 서버 헬스체크 실패")
            
        return is_healthy
    
    def process_product_input(self, form_data: Dict[str, Any], image_file=None) -> Optional[Dict[str, Any]]:
        """상품 입력 데이터 처리"""
        logger.debug("🛠️ 상품 입력 데이터 처리 시작")
        logger.debug(f"🛠️ 폼 데이터: {list(form_data.keys())}")
        logger.debug(f"🛠️ 이미지 파일: {'있음' if image_file else '없음'}")
        
        try:
            # 파일 업로드가 있는 경우
            if image_file:
                logger.debug("🛠️ 이미지 파일과 함께 요청")
                files = {"image": image_file}
                data = form_data
                result = self._make_request("POST", "/input/process", files=files, data=data)
            else:
                # JSON 데이터만 전송
                logger.debug("🛠️ JSON 데이터만으로 요청")
                result = self._make_request("POST", "/process-direct", json=form_data)
            
            if result:
                logger.info("✅ 상품 입력 데이터 처리 완료")
            else:
                logger.error("❌ 상품 입력 데이터 처리 실패")
                
            return result
            
        except Exception as e:
            logger.error(f"❌ 상품 입력 처리 중 예외 발생: {str(e)}")
            st.error(f"상품 입력 처리 실패: {str(e)}")
            return None
    
    def get_product_input(self) -> Optional[Dict[str, Any]]:
        """config.yaml에서 상품 입력 데이터 조회"""
        logger.debug("🛠️ 상품 입력 데이터 조회 시작")
        
        result = self._make_request("GET", "/get-product-input")
        
        if result:
            logger.info("✅ 상품 입력 데이터 조회 완료")
        else:
            logger.warning("⚠️ 상품 입력 데이터 조회 실패")
            
        return result
    
    def get_config(self) -> Optional[Dict[str, Any]]:
        """현재 설정 조회"""
        logger.debug("🛠️ 현재 설정 조회 시작")
        
        result = self._make_request("GET", "/input/config")
        
        if result:
            logger.info("✅ 현재 설정 조회 완료")
        else:
            logger.warning("⚠️ 현재 설정 조회 실패")
            
        return result
    
    def validate_config(self) -> Optional[Dict[str, Any]]:
        """설정 파일 유효성 검증"""
        logger.debug("🛠️ 설정 파일 유효성 검증 시작")
        
        result = self._make_request("POST", "/input/config/validate")
        
        if result:
            is_valid = result.get("data", {}).get("is_valid", False)
            if is_valid:
                logger.info("✅ 설정 파일 유효성 검증 완료 - 유효함")
            else:
                logger.warning("⚠️ 설정 파일 유효성 검증 완료 - 유효하지 않음")
        else:
            logger.error("❌ 설정 파일 유효성 검증 실패")
            
        return result


# 전역 API 클라이언트 인스턴스
logger.debug("🛠️ 전역 API 클라이언트 인스턴스 생성")
api_client = APIClient()

# Streamlit에서 사용할 수 있는 함수들
def check_server_connection() -> bool:
    """서버 연결 상태 확인"""
    logger.debug("🛠️ 서버 연결 상태 확인 함수 호출")
    result = api_client.health_check()
    logger.debug(f"🛠️ 서버 연결 결과: {result}")
    return result

def process_product_via_api(form_data: Dict[str, Any], image_file=None) -> Optional[Dict[str, Any]]:
    """API를 통한 상품 정보 처리"""
    logger.debug("🛠️ API를 통한 상품 정보 처리 함수 호출")
    result = api_client.process_product_input(form_data, image_file)
    return result

def get_product_data() -> Optional[Dict[str, Any]]:
    """API를 통한 상품 데이터 조회"""
    logger.debug("🛠️ API를 통한 상품 데이터 조회 함수 호출")
    result = api_client.get_product_input()
    return result

def get_current_config() -> Optional[Dict[str, Any]]:
    """API를 통한 현재 설정 조회"""
    logger.debug("🛠️ API를 통한 현재 설정 조회 함수 호출")
    result = api_client.get_config()
    return result

def validate_current_config() -> Optional[Dict[str, Any]]:
    """API를 통한 설정 유효성 검증"""
    logger.debug("🛠️ API를 통한 설정 유효성 검증 함수 호출")
    result = api_client.validate_config()
    return result

# 사용 예시 함수
def example_usage():
    """API 사용 예시"""
    logger.debug("🛠️ API 사용 예시 함수 시작")
    st.header("🔌 API 연결 테스트")
    
    # 서버 상태 확인
    if st.button("서버 상태 확인"):
        logger.debug("🛠️ 서버 상태 확인 버튼 클릭")
        if check_server_connection():
            st.success("✅ 서버가 정상적으로 작동 중입니다.")
        else:
            st.error("❌ 서버에 연결할 수 없습니다.")
    
    # 현재 설정 조회
    if st.button("현재 설정 조회"):
        logger.debug("🛠️ 현재 설정 조회 버튼 클릭")
        config = get_current_config()
        if config:
            st.json(config)
        else:
            st.error("설정을 불러올 수 없습니다.")
    
    # 상품 데이터 조회
    if st.button("상품 데이터 조회"):
        logger.debug("🛠️ 상품 데이터 조회 버튼 클릭")
        product_data = get_product_data()
        if product_data:
            st.json(product_data)
        else:
            st.error("상품 데이터를 불러올 수 없습니다.")
    
    # 설정 유효성 검증
    if st.button("설정 유효성 검증"):
        logger.debug("🛠️ 설정 유효성 검증 버튼 클릭")
        validation_result = validate_current_config()
        if validation_result:
            st.json(validation_result)
        else:
            st.error("설정 검증을 수행할 수 없습니다.")

def analyze_product(product_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """상품 분석 및 이미지 생성 API 호출"""
    logger.debug("🛠️ 상품 분석 API 호출 함수")
    result = api_client._make_request("POST", "/process/analyze-product", json=product_data)
    return result

def compose_images(composition_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """이미지 합성 API 호출"""
    logger.debug("🛠️ 이미지 합성 API 호출 함수")
    result = api_client._make_request("POST", "/input/compose", json=composition_data)
    return result

def generate_detail_page(generation_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """상세페이지 생성 API 호출"""
    logger.debug("🛠️ 상세페이지 생성 API 호출 함수")
    result = api_client._make_request("POST", "/output/create-page", json=generation_data)
    return result

if __name__ == "__main__":
    logger.debug("🛠️ API 모듈 직접 실행")
    example_usage()