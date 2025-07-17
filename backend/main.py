from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from contextlib import asynccontextmanager
import sys
from pathlib import Path

# 로거 임포트 추가
sys.path.append(str(Path(__file__).parent.parent))
from utils.logger import get_logger

from input_handler.api.input_router import router as input_router
from input_handler.core.input_main import InputHandler
# from image_generator.api.image_router import router as image_router

# 로거 설정
logger = get_logger(__name__)

# 전역 InputHandler 인스턴스
input_handler = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI 애플리케이션 생명주기 관리"""
    global input_handler
    
    # 시작 시 초기화
    logger.debug("🛠️ FastAPI 애플리케이션 시작 프로세스 시작")
    logger.info("✅ FastAPI 애플리케이션 시작")
    
    try:
        logger.debug("🛠️ InputHandler 초기화 시작")
        input_handler = InputHandler()
        logger.info("✅ InputHandler 초기화 완료")
        
        # 초기화된 핸들러 정보
        if input_handler:
            logger.debug(f"🛠️ 프로젝트 루트: {input_handler.project_root}")
            logger.debug(f"🛠️ 데이터 디렉토리: {input_handler.data_dir}")
        
    except Exception as e:
        logger.error(f"❌ InputHandler 초기화 실패: {e}")
        input_handler = None
    
    yield
    
    # 종료 시 정리
    logger.debug("🛠️ FastAPI 애플리케이션 종료 프로세스 시작")
    if input_handler:
        logger.debug("🛠️ InputHandler 정리 작업 수행")
    logger.info("✅ FastAPI 애플리케이션 종료 완료")

# FastAPI 애플리케이션 생성
logger.debug("🛠️ FastAPI 애플리케이션 인스턴스 생성 시작")
app = FastAPI(
    title="GeoPage Input Handler API",
    description="상품 정보 입력 처리 API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 설정
logger.debug("🛠️ CORS 미들웨어 설정 시작")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발 환경에서만 사용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logger.debug("🛠️ CORS 미들웨어 설정 완료 (모든 origin 허용)")

# 라우터 등록
logger.debug("🛠️ API 라우터 등록 시작")
app.include_router(input_router)
logger.debug("🛠️ input_router 등록 완료")
# 이미지 생성기 등록
# app.include_router(image_router)
logger.debug("🛠️ image_router 등록 완료")

logger.info("✅ FastAPI 애플리케이션 설정 완료")

# 전역 예외 핸들러
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """전역 예외 처리"""
    logger.debug(f"🛠️ 전역 예외 핸들러 호출: {type(exc).__name__}")
    logger.error(f"❌ 전역 예외 발생: {exc}")
    
    # 요청 정보 로그
    if hasattr(request, 'url'):
        logger.debug(f"🛠️ 예외 발생 URL: {request.url}")
    if hasattr(request, 'method'):
        logger.debug(f"🛠️ 예외 발생 메서드: {request.method}")
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "내부 서버 오류가 발생했습니다.",
            "detail": str(exc)
        }
    )

# 루트 엔드포인트
@app.get("/")
async def root():
    """루트 엔드포인트"""
    logger.debug("🛠️ 루트 엔드포인트 호출")
    
    response = {
        "message": "GeoPage Input Handler API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }
    
    logger.debug("🛠️ 루트 엔드포인트 응답 준비 완료")
    logger.info("✅ 루트 엔드포인트 호출 완료")
    
    return response

# 헬스체크 엔드포인트
@app.get("/health")
async def health_check():
    """전체 시스템 상태 확인"""
    logger.debug("🛠️ 헬스체크 시작")
    
    try:
        # InputHandler 상태 확인
        logger.debug("🛠️ InputHandler 상태 확인 중")
        if input_handler is None:
            logger.warning("⚠️ InputHandler가 초기화되지 않음")
            return {
                "success": False,
                "message": "InputHandler가 초기화되지 않았습니다.",
                "status": "unhealthy"
            }
        
        logger.debug("🛠️ InputHandler 상태 정상 확인")
        
        # 디렉토리 상태 확인
        logger.debug("🛠️ 디렉토리 상태 확인 중")
        data_dir = os.path.join(input_handler.project_root, "backend", "data")
        directories_exist = os.path.exists(data_dir)
        
        if directories_exist:
            logger.debug(f"🛠️ 데이터 디렉토리 확인됨: {data_dir}")
            
            # 하위 디렉토리들 확인
            subdirs = ['input', 'output', 'result']
            subdir_status = {}
            for subdir in subdirs:
                subdir_path = os.path.join(data_dir, subdir)
                subdir_exists = os.path.exists(subdir_path)
                subdir_status[subdir] = subdir_exists
                logger.debug(f"🛠️ {subdir} 디렉토리: {'존재' if subdir_exists else '없음'}")
        else:
            logger.warning(f"⚠️ 데이터 디렉토리 없음: {data_dir}")
        
        response = {
            "success": True,
            "message": "시스템 정상 작동 중",
            "status": "healthy",
            "details": {
                "input_handler": "initialized",
                "directories": "created" if directories_exist else "missing",
                "project_root": input_handler.project_root
            }
        }
        
        logger.info("✅ 헬스체크 완료 - 시스템 정상")
        return response
        
    except Exception as e:
        logger.error(f"❌ 헬스체크 실패: {e}")
        return {
            "success": False,
            "message": f"헬스체크 실패: {str(e)}",
            "status": "unhealthy"
        }

# 직접 처리 엔드포인트 (Streamlit에서 사용)
@app.post("/process-direct")
async def process_direct(form_data: dict):
    """
    Streamlit에서 직접 호출하는 처리 엔드포인트
    (API 라우터를 거치지 않고 직접 처리)
    """
    logger.debug("🛠️ 직접 처리 엔드포인트 호출")
    logger.debug(f"🛠️ 받은 폼 데이터 키: {list(form_data.keys())}")
    
    try:
        # InputHandler 상태 확인
        if input_handler is None:
            logger.error("❌ InputHandler 초기화 상태 오류")
            raise HTTPException(
                status_code=500,
                detail="InputHandler가 초기화되지 않았습니다."
            )
        
        logger.debug("🛠️ InputHandler 상태 정상 확인")
        
        # 입력 처리
        logger.debug("🛠️ 폼 데이터 처리 시작")
        result = input_handler.process_form_input(form_data)
        
        response = {
            "success": True,
            "message": "상품 정보 처리 완료",
            "data": result
        }
        
        logger.info("✅ 직접 처리 완료")
        logger.debug(f"🛠️ 응답 데이터 크기: {len(str(response))} bytes")
        
        return response
        
    except HTTPException:
        # HTTPException은 그대로 재발생
        raise
    except Exception as e:
        logger.error(f"❌ 직접 처리 실패: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"처리 중 오류 발생: {str(e)}"
        )

# config.yaml 읽기 전용 엔드포인트
@app.get("/get-product-input")
async def get_product_input():
    """
    config.yaml에서 product_input 딕셔너리 반환
    (FastAPI에서 전처리 후 호출)
    """
    logger.debug("🛠️ 상품 입력 데이터 조회 엔드포인트 호출")
    
    try:
        # InputHandler 상태 확인
        if input_handler is None:
            logger.error("❌ InputHandler 초기화 상태 오류")
            raise HTTPException(
                status_code=500,
                detail="InputHandler가 초기화되지 않았습니다."
            )
        
        logger.debug("🛠️ InputHandler 상태 정상 확인")
        
        # config.yaml에서 product_input 추출
        logger.debug("🛠️ config.yaml에서 상품 데이터 추출 시작")
        product_input = input_handler.get_product_input_dict()
        
        response = {
            "success": True,
            "message": "상품 입력 데이터 로드 완료",
            "data": product_input
        }
        
        logger.info("✅ 상품 입력 데이터 조회 완료")
        
        if isinstance(product_input, dict):
            logger.debug(f"🛠️ 반환된 상품 데이터 키: {list(product_input.keys())}")
        
        return response
        
    except HTTPException:
        # HTTPException은 그대로 재발생
        raise
    except Exception as e:
        logger.error(f"❌ 상품 입력 데이터 로드 실패: {e}")
        raise HTTPException(
            status_code=404,
            detail=f"상품 입력 데이터 로드 실패: {str(e)}"
        )

if __name__ == "__main__":
    logger.debug("🛠️ 메인 스크립트 실행 시작")
    logger.debug("🛠️ uvicorn 서버 설정 중")
    
    import uvicorn
    
    # 서버 설정 정보
    host = "0.0.0.0"
    port = 8010
    
    logger.debug(f"🛠️ 서버 설정: host={host}, port={port}")
    logger.info(f"✅ FastAPI 서버 시작: http://{host}:{port}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )