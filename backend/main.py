from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import os
from contextlib import asynccontextmanager

from input_handler.api.input_router import router as input_router
from input_handler.core.input_main import InputHandler

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 전역 InputHandler 인스턴스
input_handler = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI 애플리케이션 생명주기 관리"""
    global input_handler
    
    # 시작 시 초기화
    logger.info("FastAPI 애플리케이션 시작")
    try:
        input_handler = InputHandler()
        logger.info("InputHandler 초기화 완료")
    except Exception as e:
        logger.error(f"InputHandler 초기화 실패: {str(e)}")
    
    yield
    
    # 종료 시 정리
    logger.info("FastAPI 애플리케이션 종료")

# FastAPI 애플리케이션 생성
app = FastAPI(
    title="GeoPage Input Handler API",
    description="상품 정보 입력 처리 API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발 환경에서만 사용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(input_router)

# 전역 예외 핸들러
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"전역 예외 발생: {str(exc)}")
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
    return {
        "message": "GeoPage Input Handler API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

# 헬스체크 엔드포인트
@app.get("/health")
async def health_check():
    """전체 시스템 상태 확인"""
    try:
        # InputHandler 상태 확인
        if input_handler is None:
            return {
                "success": False,
                "message": "InputHandler가 초기화되지 않았습니다.",
                "status": "unhealthy"
            }
        
        # 디렉토리 상태 확인
        data_dir = os.path.join(input_handler.project_root, "data")
        directories_exist = os.path.exists(data_dir)
        
        return {
            "success": True,
            "message": "시스템 정상 작동 중",
            "status": "healthy",
            "details": {
                "input_handler": "initialized",
                "directories": "created" if directories_exist else "missing",
                "project_root": input_handler.project_root
            }
        }
        
    except Exception as e:
        logger.error(f"헬스체크 실패: {str(e)}")
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
    try:
        if input_handler is None:
            raise HTTPException(
                status_code=500,
                detail="InputHandler가 초기화되지 않았습니다."
            )
        
        # 입력 처리
        result = input_handler.process_form_input(form_data)
        
        return {
            "success": True,
            "message": "상품 정보 처리 완료",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"직접 처리 실패: {str(e)}")
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
    try:
        if input_handler is None:
            raise HTTPException(
                status_code=500,
                detail="InputHandler가 초기화되지 않았습니다."
            )
        
        # config.yaml에서 product_input 추출
        product_input = input_handler.get_product_input_dict()
        
        return {
            "success": True,
            "message": "상품 입력 데이터 로드 완료",
            "data": product_input
        }
        
    except Exception as e:
        logger.error(f"상품 입력 데이터 로드 실패: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=f"상품 입력 데이터 로드 실패: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8010,
        reload=True,
        log_level="info"
    )