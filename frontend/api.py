import requests
import json
from typing import Dict, Any, Optional
import streamlit as st

class APIClient:
    """FastAPI 서버와 통신하는 클라이언트"""
    
    def __init__(self, base_url: str = "http://localhost:8010"):
        self.base_url = base_url
        self.session = requests.Session()
        
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict[str, Any]]:
        """HTTP 요청 수행"""
        try:
            url = f"{self.base_url}{endpoint}"
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            st.error(f"API 요청 실패: {str(e)}")
            return None
        except json.JSONDecodeError:
            st.error("API 응답을 파싱할 수 없습니다.")
            return None
    
    def health_check(self) -> bool:
        """서버 상태 확인"""
        result = self._make_request("GET", "/health")
        return result and result.get("success", False)
    
    def process_product_input(self, form_data: Dict[str, Any], image_file=None) -> Optional[Dict[str, Any]]:
        """상품 입력 데이터 처리"""
        try:
            # 파일 업로드가 있는 경우
            if image_file:
                files = {"image": image_file}
                data = form_data
                result = self._make_request("POST", "/api/input/process", files=files, data=data)
            else:
                # JSON 데이터만 전송
                result = self._make_request("POST", "/process-direct", json=form_data)
            
            return result
            
        except Exception as e:
            st.error(f"상품 입력 처리 실패: {str(e)}")
            return None
    
    def get_product_input(self) -> Optional[Dict[str, Any]]:
        """config.yaml에서 상품 입력 데이터 조회"""
        result = self._make_request("GET", "/get-product-input")
        return result
    
    def get_config(self) -> Optional[Dict[str, Any]]:
        """현재 설정 조회"""
        result = self._make_request("GET", "/api/input/config")
        return result
    
    def validate_config(self) -> Optional[Dict[str, Any]]:
        """설정 파일 유효성 검증"""
        result = self._make_request("POST", "/api/input/config/validate")
        return result


# 전역 API 클라이언트 인스턴스
api_client = APIClient()

# Streamlit에서 사용할 수 있는 함수들
def check_server_connection() -> bool:
    """서버 연결 상태 확인"""
    return api_client.health_check()

def process_product_via_api(form_data: Dict[str, Any], image_file=None) -> Optional[Dict[str, Any]]:
    """API를 통한 상품 정보 처리"""
    return api_client.process_product_input(form_data, image_file)

def get_product_data() -> Optional[Dict[str, Any]]:
    """API를 통한 상품 데이터 조회"""
    return api_client.get_product_input()

def get_current_config() -> Optional[Dict[str, Any]]:
    """API를 통한 현재 설정 조회"""
    return api_client.get_config()

def validate_current_config() -> Optional[Dict[str, Any]]:
    """API를 통한 설정 유효성 검증"""
    return api_client.validate_config()

# 사용 예시 함수
def example_usage():
    """API 사용 예시"""
    st.header("🔌 API 연결 테스트")
    
    # 서버 상태 확인
    if st.button("서버 상태 확인"):
        if check_server_connection():
            st.success("✅ 서버가 정상적으로 작동 중입니다.")
        else:
            st.error("❌ 서버에 연결할 수 없습니다.")
    
    # 현재 설정 조회
    if st.button("현재 설정 조회"):
        config = get_current_config()
        if config:
            st.json(config)
        else:
            st.error("설정을 불러올 수 없습니다.")
    
    # 상품 데이터 조회
    if st.button("상품 데이터 조회"):
        product_data = get_product_data()
        if product_data:
            st.json(product_data)
        else:
            st.error("상품 데이터를 불러올 수 없습니다.")
    
    # 설정 유효성 검증
    if st.button("설정 유효성 검증"):
        validation_result = validate_current_config()
        if validation_result:
            st.json(validation_result)
        else:
            st.error("설정 검증을 수행할 수 없습니다.")

if __name__ == "__main__":
    example_usage()