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
        logger.debug(f"🛠️ 프롬프트 변환: {generation_type}, {num_products}개 상품, {num_images}개 이미지")
        
        if not self.openai_client:
            logger.error("❌ OpenAI 클라이언트가 초기화되지 않음")
            return None
        
        # ✅ 이미지 참조 번호 생성 (실제 전달되는 이미지 순서와 일치)
        if num_products > 1:
            product_refs = ", ".join([f"(#{i+1})" for i in range(num_products)])
            target_ref = f"(#{num_products + 1})"
            mask_ref = f"(#{num_products + 2})" if num_images > num_products + 1 else ""
        else:
            product_refs = "(#1)"
            target_ref = "(#2)"
            mask_ref = "(#3)" if num_images > 2 else ""
        
        logger.debug(f"🛠️ 참조 번호 - 상품: {product_refs}, 타겟: {target_ref}, 마스크: {mask_ref}")
        
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
    
    def analyze_combination_intent(self, korean_request: str, num_products: int) -> Dict[str, Any]:
        """사용자 요청사항을 분석하여 상품 조합 의도 파악"""
        logger.debug(f"🛠️ 조합 의도 분석 시작: {num_products}개 상품")
        
        if num_products <= 1:
            return {
                'combine_products': False,
                'description': '단일 상품'
            }
        
        if not korean_request or korean_request.strip() == "":
            return {
                'combine_products': False,
                'description': '요청사항 없음 - 개별 착용'
            }
        
        if not self.openai_client:
            logger.error("❌ OpenAI 클라이언트가 초기화되지 않음")
            return {
                'combine_products': False,
                'description': '기본값 - 개별 착용'
            }
        
        system_prompt = f"""
당신은 패션 의상 조합 요청을 분석하는 전문가입니다.
사용자가 {num_products}개의 상품에 대해 요청한 내용을 분석해주세요.

판단 기준:
1. "combine_products": true - 여러 상품을 동시에 착용하라는 의도가 명확한 경우
   예시: 
   - "바지와 티셔츠를 입고 있는"
   - "상의와 하의를 함께"
   - "세트로 착용한"
   - "모든 옷을 입은"
   - 복수의 의류 아이템을 동시에 언급

2. "combine_products": false - 개별 착용을 원하거나 명확하지 않은 경우
   예시:
   - "바지를 입은 모델" (단일 아이템만 언급)
   - "자연스럽게" (구체적 언급 없음)
   - 빈 문자열 또는 일반적인 요청

응답은 반드시 다음 JSON 형식으로만 해주세요:
{{
    "combine_products": true 또는 false,
    "reasoning": "판단 근거"
}}
"""
    
        try:
            logger.debug("🛠️ OpenAI API 호출로 조합 의도 분석")
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": korean_request}
                ],
                max_tokens=150,
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            combine_products = result.get('combine_products', False)
            reasoning = result.get('reasoning', '')
            
            logger.info(f"✅ 조합 의도 분석: {'동시 착용' if combine_products else '개별 착용'} - {reasoning}")
            
            return {
                'combine_products': combine_products,
                'description': f"{'동시 착용' if combine_products else '개별 착용'} - {reasoning}"
            }
            
        except Exception as e:
            logger.error(f"❌ 조합 의도 분석 실패: {e}")
            return {
                'combine_products': False,
                'description': '분석 실패 - 개별 착용 (기본값)'
            }
    
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
        - 항상 선택한 상품 수만큼 결과물 생성
        - 요청사항에 따라 각 결과물의 조합 방식 결정
        """
        logger.debug("🛠️ 이미지 합성 프로세스 시작")
        try:
            user_images_data = composition_data.get('user_images', [])
            target_image_data = composition_data.get('target_image')
            mask_image_data = composition_data.get('mask_image')
            generation_options = composition_data.get('generation_options', {})
            generation_type = generation_options.get('type', 'background')
            
            num_products = len(user_images_data)
            logger.debug(f"🛠️ 합성 타입: {generation_type}, 상품 수: {num_products}")

            # 조합 의도 분석
            combination_info = self.analyze_combination_intent(
                generation_options.get('custom_prompt', ''), 
                num_products
            )
            
            logger.info(f"🎯 조합 전략: {combination_info['description']}")
            
            # 항상 상품 수만큼 결과 생성
            results = []
            project_root = Path(__file__).parent.parent.parent.parent
            result_dir = project_root / "backend" / "data" / "output"
            result_dir.mkdir(parents=True, exist_ok=True)
            
            for i in range(num_products):
                logger.debug(f"🛠️ 결과물 {i+1}/{num_products} 생성 시작")
                
                if combination_info['combine_products']:
                    # 모든 상품을 함께 착용한 이미지 생성
                    result = self._generate_combined_image_for_result(
                        user_images_data, target_image_data, mask_image_data,
                        generation_options, generation_type, i + 1
                    )
                else:
                    # 개별 상품만 착용한 이미지 생성
                    result = self._generate_individual_image_for_result(
                        user_images_data[i], target_image_data, mask_image_data,
                        generation_options, generation_type, i + 1
                    )
                
                if result:
                    results.append(result)
                    logger.info(f"✅ 결과물 {i+1} 생성 완료")
                else:
                    logger.error(f"❌ 결과물 {i+1} 생성 실패")
            
            if not results:
                logger.error("❌ 모든 결과물 생성 실패")
                return None
            
            return {
                'success': True,
                'results': results,
                'generation_type': generation_type,
                'total_images': len(results),
                'product_images_count': num_products,
                'combination_strategy': combination_info['description']
            }
                
        except Exception as e:
            logger.error(f"❌ 이미지 합성 프로세스 실패: {e}")
            return None

    def _generate_combined_image_for_result(self, user_images_data, target_image_data, mask_image_data, 
                                      generation_options, generation_type, result_index) -> Optional[Dict[str, Any]]:
        """모든 상품을 함께 착용한 이미지 생성 (단일 결과물용)"""
        logger.debug(f"🛠️ 통합 착용 이미지 생성: 결과물 {result_index}")
        
        images = []
        
        # ✅ 모든 상품 이미지를 순서대로 로드
        logger.debug(f"🛠️ 모든 상품 이미지 로드 시작: {len(user_images_data)}개")
        for i, user_image_data in enumerate(user_images_data):
            user_image = self._load_image_safely(user_image_data['path'], f'상품_{i+1}', 'RGB')
            if not user_image:
                logger.error(f"❌ 상품 이미지 {i+1} 로드 실패: {user_image_data['path']}")
                return None
            images.append(user_image)
            logger.debug(f"✅ 상품 이미지 {i+1} 추가: {user_image.size}")
        
        # 타겟 이미지 처리
        if generation_type == 'model':
            if not target_image_data or 'path' not in target_image_data:
                logger.error("❌ 모델 이미지 정보 없음")
                return None
            model_image = self._load_image_safely(target_image_data['path'], 'model', 'RGB')
            if not model_image:
                return None
            images.append(model_image)
            logger.debug(f"✅ 모델 이미지 추가: {model_image.size}")
            
            # 마스크 이미지 (선택)
            if mask_image_data and 'path' in mask_image_data:
                mask_image = self._load_image_safely(mask_image_data['path'], 'mask', 'L')
                if mask_image:
                    images.append(mask_image)
                    logger.debug(f"✅ 마스크 이미지 추가: {mask_image.size}")
        
        # ✅ 실제 이미지 순서에 맞는 프롬프트 생성
        total_images = len(images)
        logger.debug(f"🛠️ 총 전달할 이미지 수: {total_images}")
        logger.debug(f"🛠️ 이미지 구성: 상품 {len(user_images_data)}개 + 모델/배경 1개" + 
                    (f" + 마스크 1개" if generation_type == 'model' and mask_image_data else ""))
        
        # 통합 착용용 프롬프트 생성
        if generation_type == 'model':
            prompt = self.convert_korean_request_to_prompt(
                generation_options.get('custom_prompt', ''),
                num_images=total_images,
                generation_type='model',
                num_products=len(user_images_data)
            )
        else:  # background
            base_prompt = target_image_data.get('prompt', '')
            prompt = self.convert_korean_request_to_prompt(
                f"다음 배경에 모든 상품을 자연스럽게 배치해주세요: {base_prompt}",
                num_images=total_images,
                generation_type='background',
                num_products=len(user_images_data)
            )
        
        if not prompt:
            logger.error("❌ 프롬프트 변환 실패")
            return None
        
        logger.debug(f"🛠️ 생성된 프롬프트: {prompt}")
        
        # ✅ 이미지 생성 (모든 상품 이미지 + 모델/배경 이미지 전달)
        result_image = self.generate_image_with_gemini(prompt, images)
        if not result_image:
            logger.error("❌ Gemini 이미지 생성 실패")
            return None
        
        # 결과 저장
        project_root = Path(__file__).parent.parent.parent.parent
        result_dir = project_root / "backend" / "data" / "output"
        result_filename = f"composed_{generation_type}_combined_{result_index}_{uuid.uuid4().hex[:8]}.png"
        result_path = result_dir / result_filename
        result_image.save(result_path)
        
        relative_path = os.path.relpath(result_path, project_root)
        logger.info(f"✅ 통합 착용 이미지 저장: {relative_path}")
        
        return {
            'result_image_path': relative_path,
            'prompt_used': prompt,
            'result_index': result_index,
            'combination_type': '모든 상품 동시 착용',
            'images_used': f"상품 {len(user_images_data)}개 + 모델/배경 1개"
        }

    def _generate_individual_image_for_result(self, user_image_data, target_image_data, mask_image_data,
                                        generation_options, generation_type, result_index) -> Optional[Dict[str, Any]]:
        """개별 상품만 착용한 이미지 생성 (단일 결과물용)"""
        logger.debug(f"🛠️ 개별 착용 이미지 생성: 결과물 {result_index}")
        
        images = []
        
        # ✅ 현재 상품 이미지만 로드
        logger.debug(f"🛠️ 상품 {result_index} 이미지 로드: {user_image_data['path']}")
        user_image = self._load_image_safely(user_image_data['path'], f'상품_{result_index}', 'RGB')
        if not user_image:
            logger.error(f"❌ 상품 {result_index} 이미지 로드 실패: {user_image_data['path']}")
            return None
        images.append(user_image)
        logger.debug(f"✅ 상품 {result_index} 이미지 추가: {user_image.size}")
        
        # 타겟 이미지 처리
        if generation_type == 'model':
            if not target_image_data or 'path' not in target_image_data:
                logger.error("❌ 모델 이미지 정보 없음")
                return None
            model_image = self._load_image_safely(target_image_data['path'], 'model', 'RGB')
            if not model_image:
                return None
            images.append(model_image)
            logger.debug(f"✅ 모델 이미지 추가: {model_image.size}")
            
            # 마스크 이미지 (선택)
            if mask_image_data and 'path' in mask_image_data:
                mask_image = self._load_image_safely(mask_image_data['path'], 'mask', 'L')
                if mask_image:
                    images.append(mask_image)
                    logger.debug(f"✅ 마스크 이미지 추가: {mask_image.size}")
        
        # ✅ 실제 이미지 순서에 맞는 프롬프트 생성
        total_images = len(images)
        logger.debug(f"🛠️ 총 전달할 이미지 수: {total_images}")
        logger.debug(f"🛠️ 이미지 구성: 상품 1개 + 모델/배경 1개" + 
                    (f" + 마스크 1개" if generation_type == 'model' and mask_image_data else ""))
        
        # 개별 착용용 프롬프트 생성
        if generation_type == 'model':
            prompt = self.convert_korean_request_to_prompt(
                generation_options.get('custom_prompt', ''),
                num_images=total_images,
                generation_type='model',
                num_products=1  # ✅ 개별 생성이므로 1개
            )
        else:  # background
            base_prompt = target_image_data.get('prompt', '')
            prompt = self.convert_korean_request_to_prompt(
                f"다음 배경에 상품을 자연스럽게 배치해주세요: {base_prompt}",
                num_images=total_images,
                generation_type='background',
                num_products=1
            )
        
        if not prompt:
            logger.error(f"❌ 상품 {result_index} 프롬프트 변환 실패")
            return None
        
        logger.debug(f"🛠️ 생성된 프롬프트: {prompt}")
        
        # ✅ 이미지 생성 (단일 상품 이미지 + 모델/배경 이미지 전달)
        result_image = self.generate_image_with_gemini(prompt, images)
        if not result_image:
            logger.error(f"❌ 상품 {result_index} Gemini 이미지 생성 실패")
            return None
        
        # 결과 저장
        project_root = Path(__file__).parent.parent.parent.parent
        result_dir = project_root / "backend" / "data" / "output"
        result_filename = f"composed_{generation_type}_individual_{result_index}_{uuid.uuid4().hex[:8]}.png"
        result_path = result_dir / result_filename
        result_image.save(result_path)
        
        relative_path = os.path.relpath(result_path, project_root)
        logger.info(f"✅ 개별 착용 이미지 저장: {relative_path}")
        
        return {
            'result_image_path': relative_path,
            'prompt_used': prompt,
            'result_index': result_index,
            'combination_type': f'상품 {result_index} 개별 착용',
            'product_name': user_image_data.get('relative_path', f'상품_{result_index}'),
            'images_used': f"상품 1개 + 모델/배경 1개"
        }
