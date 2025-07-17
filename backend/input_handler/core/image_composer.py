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
    
    def convert_korean_request_to_prompt(self, korean_request: str, num_images: int, generation_type: str) -> Optional[str]:
        """한글 요청사항을 영문 이미지 생성 프롬프트로 변환"""
        logger.debug(f"🛠️ 프롬프트 변환 시작: {generation_type} 타입")
        
        if not self.openai_client:
            logger.error("❌ OpenAI 클라이언트가 초기화되지 않음")
            return None
        
        # 이미지 참조 번호 생성
        image_refs = ", ".join([f"(#{i+1})" for i in range(num_images)])
        
        if generation_type == "model":
            system_prompt = f"""
당신은 이미지 생성 프롬프트 전문가입니다. 
사용자의 한글 요청사항을 모델과 상품 합성을 위한 영문 이미지 생성 프롬프트로 변환해주세요.

규칙:
1. 자연스럽고 현실적인 이미지 생성을 위한 프롬프트를 작성하세요
2. 이미지 참조는 {image_refs} 형식으로 사용하세요 (첫 번째는 상품, 나머지는 모델/마스크)
3. 텍스트나 글자가 포함되지 않도록 지시하세요
4. "Generate a natural-looking image"로 시작하는 것을 권장합니다

모델과 상품 합성:
- 모델의 신체 비율과 포즈를 유지하도록 지시하세요
- 의상을 입히는 경우 "naturally wearing"과 같은 표현을 사용하세요
- 물건을 들고 있는 경우 "holding"과 같은 표현을 사용하세요
- 상품이 모델에게 자연스럽게 맞도록 지시하세요

예시:
"상품을 모델이 착용하게 해주세요" → "Generate a natural-looking image where the model from (#2) maintains their body proportions and pose, but is naturally wearing the product from (#1) as if they were actually wearing it. Do not include any text or letters in the image."
            """
        else:  # background
            system_prompt = f"""
당신은 이미지 생성 프롬프트 전문가입니다. 
사용자의 한글 요청사항을 상품 배경 합성을 위한 영문 이미지 생성 프롬프트로 변환해주세요.

규칙:
1. 자연스럽고 현실적인 이미지 생성을 위한 프롬프트를 작성하세요
2. 이미지 참조는 {image_refs} 형식으로 사용하세요 (첫 번째는 상품, 두 번째는 배경)
3. 텍스트나 글자가 포함되지 않도록 지시하세요
4. "Generate a natural-looking image"로 시작하는 것을 권장합니다

상품 배경 합성:
- 상품을 자연스러운 배경이나 환경에 배치하도록 지시하세요
- "placed in", "positioned on", "set against" 등의 표현을 사용하세요
- 상품의 원래 형태와 특성을 유지하도록 지시하세요

예시:
"고급 레스토랑 배경에 놓고 싶다" → "Generate a natural-looking image of the product from (#1) elegantly placed in the upscale restaurant setting from (#2). Do not include any text or letters in the image."
            """
        
        try:
            logger.debug("🛠️ OpenAI API 호출 시작")
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": korean_request or "자연스럽게 합성해주세요"}
                ],
                max_tokens=200,
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
        """이미지 합성 메인 함수"""
        logger.debug("🛠️ 이미지 합성 프로세스 시작")
        
        try:
            # 입력 데이터 추출
            user_image_data = composition_data['user_image']
            target_image_data = composition_data['target_image'] 
            mask_image_data = composition_data.get('mask_image')
            generation_options = composition_data['generation_options']
            
            generation_type = generation_options['type']
            custom_prompt = generation_options.get('custom_prompt', '')
            
            logger.debug(f"🛠️ 합성 타입: {generation_type}")
            logger.debug(f"🛠️ 커스텀 프롬프트: {custom_prompt}")
            
            # 이미지 로드
            images = []
            
            # 사용자 이미지 로드 (상품 이미지)
            user_image = self._load_image_safely(user_image_data['path'], 'user', 'RGB')
            if not user_image:
                return None
            images.append(user_image)
            
            # 타겟 이미지 로드 (모델 또는 배경)
            target_image = self._load_image_safely(target_image_data['path'], 'target', 'RGB')
            if not target_image:
                return None
            images.append(target_image)
            
            # 마스크 이미지 로드 (있는 경우)
            if mask_image_data and mask_image_data.get('path'):
                mask_image = self._load_image_safely(mask_image_data['path'], 'mask', 'L')
                if mask_image:
                    images.append(mask_image)
                    logger.debug("🛠️ 마스크 이미지 추가됨")
                else:
                    logger.warning("⚠️ 마스크 이미지 로드 실패, 마스크 없이 진행")
            
            # 프롬프트 변환
            logger.debug("🛠️ 프롬프트 변환 시작")
            english_prompt = self.convert_korean_request_to_prompt(
                custom_prompt, len(images), generation_type
            )
            
            if not english_prompt:
                logger.error("❌ 프롬프트 변환 실패")
                return None
            
            logger.debug(f"🛠️ 변환된 프롬프트: {english_prompt}")
            
            # 이미지 생성
            logger.debug("🛠️ 이미지 생성 시작")
            result_image = self.generate_image_with_gemini(english_prompt, images)
            
            if not result_image:
                logger.error("❌ 이미지 생성 실패")
                return None
            
            # 결과 이미지 저장
            project_root = Path(__file__).parent.parent.parent.parent
            result_dir = project_root / "backend" / "data" / "result"
            result_dir.mkdir(parents=True, exist_ok=True)
            
            result_filename = f"composed_{generation_type}_{uuid.uuid4().hex[:8]}.png"
            result_path = result_dir / result_filename
            
            result_image.save(result_path)
            logger.info(f"✅ 결과 이미지 저장: {result_path}")
            
            # 상대 경로로 변환
            relative_path = os.path.relpath(result_path, project_root)
            
            return {
                'success': True,
                'result_image_path': relative_path,
                'prompt_used': english_prompt,
                'generation_type': generation_type,
                'input_images': len(images)
            }
            
        except Exception as e:
            logger.error(f"❌ 이미지 합성 프로세스 실패: {e}")
            return None