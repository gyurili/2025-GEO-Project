from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
from openai import OpenAI
import base64
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import uuid
from dotenv import load_dotenv

# 로거 임포트 추가
sys.path.append(str(Path(__file__).parent.parent.parent.parent))
from utils.logger import get_logger

# 로거 설정
logger = get_logger(__name__)

class ImageComposer:
    """이미지 합성 클래스"""
    
    def __init__(self):
        logger.debug("🛠️ ImageComposer 인스턴스 초기화 시작")
        
        # 프로젝트 루트에서 .env 파일 로드
        project_root = Path(__file__).parent.parent.parent.parent
        env_path = project_root / ".env"
        
        if env_path.exists():
            load_dotenv(env_path)
            logger.debug(f"🛠️ .env 파일 로드: {env_path}")
        else:
            logger.warning(f"⚠️ .env 파일을 찾을 수 없습니다: {env_path}")
        
        # API 키 설정
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "")
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        
        # API 키 확인 (보안상 길이만 표시)
        if self.gemini_api_key:
            logger.debug(f"🛠️ Gemini API 키 로드됨: {len(self.gemini_api_key)}자")
        else:
            logger.warning("⚠️ Gemini API 키가 설정되지 않았습니다")
            
        if self.openai_api_key:
            logger.debug(f"🛠️ OpenAI API 키 로드됨: {len(self.openai_api_key)}자")
        else:
            logger.warning("⚠️ OpenAI API 키가 설정되지 않았습니다")
        
        if not self.gemini_api_key or not self.openai_api_key:
            logger.error("❌ 필수 API 키가 설정되지 않았습니다")
        
        # 클라이언트 초기화
        try:
            self.openai_client = OpenAI(api_key=self.openai_api_key) if self.openai_api_key else None
            self.gemini_client = genai.Client(api_key=self.gemini_api_key) if self.gemini_api_key else None
            logger.info("✅ ImageComposer 클라이언트 초기화 완료")
        except Exception as e:
            logger.error(f"❌ 클라이언트 초기화 실패: {e}")
            self.openai_client = None
            self.gemini_client = None
    
    def _load_image_safely(self, image_path: str, image_type: str, target_mode: str = 'RGB') -> Optional[Image.Image]:
        """
        이미지를 안전하게 로드하는 헬퍼 함수
        
        Args:
            image_path: 이미지 파일 경로
            image_type: 이미지 타입 (로깅용) - 'user', 'target', 'mask'
            target_mode: 변환할 이미지 모드 (기본값: 'RGB')
        
        Returns:
            PIL Image 객체 또는 None
        """
        logger.debug(f"🛠️ {image_type} 이미지 로드 시작: {image_path}")
        
        if not os.path.exists(image_path):
            logger.error(f"❌ {image_type} 이미지 파일 없음: {image_path}")
            return None
        
        try:
            # 이미지 로드
            image = Image.open(image_path)
            original_mode = image.mode
            
            # 지정된 모드로 변환
            if image.mode != target_mode:
                image = image.convert(target_mode)
                logger.debug(f"🛠️ {image_type} 이미지 모드 변환: {original_mode} → {target_mode}")
            
            logger.debug(f"🛠️ {image_type} 이미지 로드 성공: {image.size}, 모드: {image.mode}")
            return image
            
        except Exception as e:
            logger.error(f"❌ {image_type} 이미지 로드 실패: {e}")
            return None
    
    def convert_korean_request_to_prompt(self, korean_request: str, num_images: int, generation_type: str, num_products: int = 1) -> Optional[str]:
        """한글 요청사항을 영문 이미지 생성 프롬프트로 변환 (다중 상품 이미지 지원)"""
        logger.debug(f"🛠️ 프롬프트 변환 시작: {generation_type} 타입, {num_products}개 상품")
        
        if not self.openai_client:
            logger.error("❌ OpenAI 클라이언트가 초기화되지 않음")
            return None
        
        # 이미지 참조 번호 생성 (다중 상품 지원)
        if num_products > 1:
            product_refs = ", ".join([f"(#{i+1})" for i in range(num_products)])
            target_ref = f"(#{num_products + 1})"
            mask_ref = f"(#{num_products + 2})" if num_images > num_products + 1 else ""
        else:
            product_refs = "(#1)"
            target_ref = "(#2)"
            mask_ref = "(#3)" if num_images > 2 else ""
        
        if generation_type == "model":
            system_prompt = f"""
    당신은 이미지 생성 프롬프트 전문가입니다. 
    사용자의 한글 요청사항을 모델과 상품 합성을 위한 영문 이미지 생성 프롬프트로 변환해주세요.

    규칙:
    1. 자연스럽고 현실적인 이미지 생성을 위한 프롬프트를 작성하세요
    2. 상품 이미지 참조: {product_refs}, 모델 이미지: {target_ref}{', 마스크: ' + mask_ref if mask_ref else ''}
    3. 텍스트나 글자가 포함되지 않도록 지시하세요
    4. "Generate a natural-looking image"로 시작하는 것을 권장합니다

    다중 상품과 모델 합성:
    - 모델의 신체 비율과 포즈를 유지하도록 지시하세요
    - 여러 상품이 있는 경우 자연스럽게 배치하도록 지시하세요
    - 의상을 입히는 경우 "naturally wearing"과 같은 표현을 사용하세요
    - 물건을 들고 있는 경우 "holding" 또는 "using"과 같은 표현을 사용하세요

    예시:
    - 단일 상품: "Generate a natural-looking image where the model from {target_ref} maintains their body proportions and pose, but is naturally wearing the product from {product_refs}."
    - 다중 상품: "Generate a natural-looking image where the model from {target_ref} maintains their body proportions and pose, naturally interacting with all products from {product_refs} in a cohesive and realistic way."
            """
        else:  # background
            system_prompt = f"""
    당신은 이미지 생성 프롬프트 전문가입니다. 
    사용자의 한글 요청사항을 상품 배경 합성을 위한 영문 이미지 생성 프롬프트로 변환해주세요.

    규칙:
    1. 자연스럽고 현실적인 이미지 생성을 위한 프롬프트를 작성하세요
    2. 상품 이미지 참조: {product_refs}, 배경 이미지: {target_ref}
    3. 텍스트나 글자가 포함되지 않도록 지시하세요
    4. "Generate a natural-looking image"로 시작하는 것을 권장합니다

    다중 상품과 배경 합성:
    - 여러 상품이 있는 경우 배경에 자연스럽게 배치하도록 지시하세요
    - "placed in", "positioned on", "arranged in" 등의 표현을 사용하세요
    - 상품들의 원래 형태와 특성을 유지하도록 지시하세요

    예시:
    - 단일 상품: "Generate a natural-looking image of the product from {product_refs} elegantly placed in the setting from {target_ref}."
    - 다중 상품: "Generate a natural-looking image with all products from {product_refs} beautifully arranged in the setting from {target_ref}, maintaining their individual characteristics."
            """
        
        try:
            logger.debug("🛠️ OpenAI API 호출 시작")
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": korean_request or "자연스럽게 합성해주세요"}
                ],
                max_tokens=300,  # 다중 상품용으로 토큰 수 증가
                temperature=0.7
            )
            
            prompt = response.choices[0].message.content.strip()
            logger.info(f"✅ 프롬프트 변환 완료: {len(prompt)}자")
            return prompt
            
        except Exception as e:
            logger.error(f"❌ OpenAI API 호출 실패: {e}")
            return None
    
    def generate_image_with_gemini(self, prompt: str, images: List[Image.Image]) -> Optional[Image.Image]:
        """Gemini API를 사용하여 이미지 생성"""
        logger.debug(f"🛠️ Gemini 이미지 생성 시작: {len(images)}개 이미지")
        
        if not self.gemini_client:
            logger.error("❌ Gemini 클라이언트가 초기화되지 않음")
            return None
        
        try:
            # 이미지 정보 로깅
            for i, img in enumerate(images):
                logger.debug(f"🛠️ 이미지 {i+1}: {img.size}, 모드: {img.mode}")
            
            # 프롬프트와 이미지들을 함께 전달
            contents = [prompt] + images
            logger.debug(f"🛠️ Gemini API 호출: 프롬프트 길이={len(prompt)}, 이미지 수={len(images)}")
            
            response = self.gemini_client.models.generate_content(
                model="gemini-2.0-flash-preview-image-generation",
                contents=contents,
                config=types.GenerateContentConfig(
                    response_modalities=['TEXT', 'IMAGE']
                )
            )
            
            # 결과 이미지 추출 부분 수정
            for part in response.candidates[0].content.parts:
                if part.text is not None:
                    logger.debug(f"🛠️ Gemini 응답 텍스트: {part.text}")
                elif part.inline_data is not None:
                    try:
                        # 🔍 추가 디버깅
                        logger.debug(f"🛠️ inline_data 타입: {type(part.inline_data)}")
                        logger.debug(f"🛠️ inline_data.data 타입: {type(part.inline_data.data)}")
                        logger.debug(f"🛠️ inline_data.data 길이: {len(part.inline_data.data)}")
                        
                        # bytes를 문자열로 변환 (base64 디코딩을 위해)
                        if isinstance(part.inline_data.data, bytes):
                            base64_string = part.inline_data.data.decode('utf-8')
                        else:
                            base64_string = part.inline_data.data
                            
                        # base64 디코딩
                        image_data = base64.b64decode(base64_string)
                        logger.debug(f"🛠️ 디코딩된 이미지 데이터 길이: {len(image_data)}")
                        
                        # BytesIO 객체 생성 및 이미지 로드
                        image_bytes = BytesIO(image_data)
                        image_bytes.seek(0)
                        
                        result_image = Image.open(image_bytes)
                        logger.info(f"✅ 이미지 생성 완료: {result_image.size}")
                        return result_image
                        
                    except Exception as e:
                        logger.error(f"❌ 이미지 변환 실패: {e}")
                        logger.debug(f"🛠️ 이미지 데이터 처음 100바이트: {part.inline_data.data[:100]}")
                        return None
                        
                    except Exception as e:
                        logger.error(f"❌ 이미지 변환 실패: {e}")
                        logger.debug(f"🛠️ 이미지 데이터 처음 100바이트: {part.inline_data.data[:100]}")
                        return None
            
            logger.warning("⚠️ 생성된 이미지를 찾을 수 없음")
            return None
            
        except Exception as e:
            logger.error(f"❌ Gemini API 호출 실패: {e}")
            return None
    
    def compose_images(self, composition_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        이미지 합성 메인 함수
        - 모델합성: 상품 + 모델(+마스크)
        - 배경합성: 상품 + 프롬프트(카테고리/소분류) (실제 배경이미지 없음)
        """
        logger.debug("🛠️ 이미지 합성 프로세스 시작")
        try:
            user_images_data = composition_data.get('user_images', [])
            target_image_data = composition_data.get('target_image')
            mask_image_data = composition_data.get('mask_image')
            generation_options = composition_data.get('generation_options', {})
            generation_type = generation_options.get('type', 'background')
            logger.debug(f"🛠️ 합성 타입: {generation_type}")

            images = []

            # 1. 공통: 유저 상품 이미지 로드
            for i, user_image_data in enumerate(user_images_data):
                user_image = self._load_image_safely(user_image_data['path'], f'user_{i+1}', 'RGB')
                if not user_image:
                    logger.error(f"❌ 사용자 이미지 {i+1} 로드 실패")
                    return None
                images.append(user_image)
                logger.debug(f"🛠️ 사용자 이미지 {i+1} 추가됨")

            # 2. 분기: 모델 합성 vs 배경(프롬프트) 합성
            if generation_type == 'model':
                # (1) 모델 이미지 로드 (필수)
                if not target_image_data or 'path' not in target_image_data:
                    logger.error("❌ 모델 이미지 정보 없음")
                    return None
                model_image = self._load_image_safely(target_image_data['path'], 'model', 'RGB')
                if not model_image:
                    logger.error("❌ 모델 이미지 로드 실패")
                    return None
                images.append(model_image)

                # (2) 마스크 이미지 로드 (선택)
                if mask_image_data and 'path' in mask_image_data:
                    mask_image = self._load_image_safely(mask_image_data['path'], 'mask', 'L')
                    if mask_image:
                        images.append(mask_image)
                        logger.debug("🛠️ 마스크 이미지 추가됨")

                # (3) 프롬프트(한글→영문 변환)
                prompt = self.convert_korean_request_to_prompt(
                    generation_options.get('custom_prompt', ''),
                    num_images=len(images),
                    generation_type='model',
                    num_products=len(user_images_data)
                )
                if not prompt:
                    logger.error("❌ 모델 합성 프롬프트 변환 실패")
                    return None

            elif generation_type == 'background':
                # (1) 배경 프롬프트 기반으로 상품 이미지 참조 프롬프트 생성
                if not (target_image_data and 'prompt' in target_image_data):
                    logger.error("❌ 배경 프롬프트 정보 없음")
                    return None
                
                base_prompt = target_image_data['prompt']
                # 기본 프롬프트를 기반으로 상품 이미지 참조 프롬프트 생성
                prompt = self.convert_korean_request_to_prompt(
                    f"다음 배경에 상품을 자연스럽게 배치해주세요: {base_prompt}",
                    num_images=len(images),
                    generation_type='background',
                    num_products=len(user_images_data)
                )
                if not prompt:
                    logger.error("❌ 배경 합성 프롬프트 변환 실패")
                    return None
                # images는 오직 상품이미지만!

            else:
                logger.error(f"❌ 알 수 없는 합성 타입: {generation_type}")
                return None

            # 3. Gemini 등 이미지 생성
            logger.debug("🛠️ 이미지 생성 시작")
            result_image = self.generate_image_with_gemini(prompt, images)
            if not result_image:
                logger.error("❌ 이미지 생성 실패")
                return None

            # 4. 결과 저장
            project_root = Path(__file__).parent.parent.parent.parent
            result_dir = project_root / "backend" / "data" / "result"
            result_dir.mkdir(parents=True, exist_ok=True)
            result_filename = f"composed_{generation_type}_{uuid.uuid4().hex[:8]}.png"
            result_path = result_dir / result_filename
            result_image.save(result_path)
            logger.info(f"✅ 결과 이미지 저장: {result_path}")

            relative_path = os.path.relpath(result_path, project_root)
            return {
                'success': True,
                'result_image_path': relative_path,
                'prompt_used': prompt,
                'generation_type': generation_type,
                'input_images': len(images),
                'product_images_count': len(user_images_data)
            }
        except Exception as e:
            logger.error(f"❌ 이미지 합성 프로세스 실패: {e}")
            return None
