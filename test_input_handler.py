#!/usr/bin/env python3
"""
GeoPage Input Handler 테스트 예시
전체 파이프라인을 테스트합니다.
"""

import os
import sys
import json
from pathlib import Path

# 프로젝트 루트 추가
PROJECT_ROOT = Path(__file__).parent
sys.path.append(str(PROJECT_ROOT))

def test_input_handler():
    """InputHandler 직접 테스트"""
    print("🧪 InputHandler 직접 테스트")
    print("-" * 50)
    
    try:
        from backend.input_handler.core.input_main import InputHandler
        
        # InputHandler 인스턴스 생성
        handler = InputHandler()
        print("✅ InputHandler 인스턴스 생성 완료")
        
        # 테스트 데이터
        test_data = {
            "name": "우일 여성 여름 인견 7부 블라우스",
            "category": "블라우스",
            "price": 18000,
            "brand": "우일",
            "features": "인견 소재, 우수한 흡수성과 통기성, 부드러운 촉감",
            "product_link": "https://www.coupang.com/vp/products/example_id"
        }
        
        # 입력 처리
        print("📝 입력 데이터 처리 중...")
        result = handler.process_form_input(test_data)
        print("✅ 입력 처리 완료")
        
        # 결과 출력
        print("\n📋 처리 결과:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        # config.yaml 확인
        config_path = os.path.join(handler.project_root, "config.yaml")
        if os.path.exists(config_path):
            print(f"✅ config.yaml 생성 완료: {config_path}")
        else:
            print("❌ config.yaml 생성 실패")
        
        # product_input 추출 테스트
        print("\n🔍 product_input 추출 테스트...")
        product_input = handler.get_product_input_dict()
        print("✅ product_input 추출 완료")
        print(json.dumps(product_input, ensure_ascii=False, indent=2))
        
        return True
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_client():
    """API 클라이언트 테스트"""
    print("\n🌐 API 클라이언트 테스트")
    print("-" * 50)
    
    try:
        import requests
        
        # 서버 상태 확인
        print("🔍 서버 상태 확인 중...")
        response = requests.get("http://localhost:8010/health", timeout=5)
        
        if response.status_code == 200:
            print("✅ 서버 정상 작동 중")
            print(f"응답: {response.json()}")
        else:
            print(f"⚠️ 서버 상태 이상: {response.status_code}")
            return False
        
        # API 테스트
        print("\n📡 API 테스트 중...")
        test_data = {
            "name": "테스트 상품",
            "category": "테스트 카테고리",
            "price": 10000,
            "brand": "테스트 브랜드",
            "features": "테스트 특징"
        }
        
        response = requests.post("http://localhost:8010/process-direct", json=test_data)
        
        if response.status_code == 200:
            print("✅ API 테스트 성공")
            result = response.json()
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"❌ API 테스트 실패: {response.status_code}")
            print(f"에러: {response.text}")
            return False
        
        # product_input 조회 테스트
        print("\n📋 product_input 조회 테스트...")
        response = requests.get("http://localhost:8010/get-product-input")
        
        if response.status_code == 200:
            print("✅ product_input 조회 성공")
            result = response.json()
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"❌ product_input 조회 실패: {response.status_code}")
            print(f"에러: {response.text}")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ 서버에 연결할 수 없습니다.")
        print("FastAPI 서버가 실행 중인지 확인하세요: python backend/main.py")
        return False
    except Exception as e:
        print(f"❌ API 테스트 실패: {e}")
        return False

def test_data_validation():
    """데이터 검증 테스트"""
    print("\n🔍 데이터 검증 테스트")
    print("-" * 50)
    
    try:
        from backend.input_handler.schemas.input_schema import ProductInputSchema
        
        # 유효한 데이터 테스트
        print("✅ 유효한 데이터 테스트...")
        valid_data = {
            "name": "테스트 상품",
            "category": "테스트 카테고리",
            "price": 10000,
            "brand": "테스트 브랜드",
            "features": "테스트 특징"
        }
        
        schema = ProductInputSchema(**valid_data)
        print("✅ 유효한 데이터 검증 통과")
        
        # 잘못된 데이터 테스트
        print("\n❌ 잘못된 데이터 테스트...")
        
        invalid_tests = [
            {"name": "", "category": "카테고리", "price": 1000, "brand": "브랜드", "features": "특징"},  # 빈 이름
            {"name": "상품", "category": "카테고리", "price": -1000, "brand": "브랜드", "features": "특징"},  # 음수 가격
            {"name": "상품", "category": "", "price": 1000, "brand": "브랜드", "features": "특징"},  # 빈 카테고리
        ]
        
        for i, invalid_data in enumerate(invalid_tests):
            try:
                ProductInputSchema(**invalid_data)
                print(f"❌ 테스트 {i+1}: 예상과 다르게 검증 통과")
            except Exception as e:
                print(f"✅ 테스트 {i+1}: 예상대로 검증 실패 - {str(e)}")
        
        return True
        
    except Exception as e:
        print(f"❌ 데이터 검증 테스트 실패: {e}")
        return False

def test_form_parser():
    """폼 파서 테스트"""
    print("\n📝 폼 파서 테스트")
    print("-" * 50)
    
    try:
        from backend.input_handler.core.form_parser import FormParser
        
        parser = FormParser()
        print("✅ FormParser 인스턴스 생성 완료")
        
        # 테스트 데이터
        test_data = {
            "name": "  테스트 상품  ",  # 공백 포함
            "category": "테스트 카테고리",
            "price": "10,000",  # 문자열 가격
            "brand": "테스트 브랜드",
            "features": "테스트 특징입니다. 매우 좋은 상품입니다."
        }
        
        # 파싱 테스트
        print("📋 폼 데이터 파싱 중...")
        result = parser.parse_form_data(test_data)
        print("✅ 폼 데이터 파싱 완료")
        
        # 결과 확인
        print("\n📋 파싱 결과:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        # 특정 검증 테스트
        assert result["name"] == "테스트 상품"  # 공백 제거 확인
        assert result["price"] == 10000  # 문자열 -> 숫자 변환 확인
        print("✅ 특정 검증 테스트 통과")
        
        return True
        
    except Exception as e:
        print(f"❌ 폼 파서 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """메인 테스트 실행"""
    print("=" * 60)
    print("🧪 GeoPage Input Handler 테스트 실행")
    print("=" * 60)
    
    test_results = []
    
    # 1. InputHandler 직접 테스트
    test_results.append(("InputHandler 직접 테스트", test_input_handler()))
    
    # 2. 데이터 검증 테스트
    test_results.append(("데이터 검증 테스트", test_data_validation()))
    
    # 3. 폼 파서 테스트
    test_results.append(("폼 파서 테스트", test_form_parser()))
    
    # 4. API 클라이언트 테스트 (선택사항)
    if input("\nAPI 서버 테스트를 실행하시겠습니까? (y/n): ").lower() == 'y':
        test_results.append(("API 클라이언트 테스트", test_api_client()))
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("📊 테스트 결과 요약")
    print("=" * 60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ 통과" if result else "❌ 실패"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n총 {total}개 테스트 중 {passed}개 통과 ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 모든 테스트가 성공했습니다!")
    else:
        print("⚠️ 일부 테스트가 실패했습니다.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)