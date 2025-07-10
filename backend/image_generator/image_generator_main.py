import yaml
import os
import sys
from PIL import Image

from utils.logger import get_logger
from .core.image_loader import ImageLoader
from .core.background_handler import Txt2ImgGenerator, BackgroundHandler, Img2ImgGenerator
from .core.prompt_builder import generate_prompts

'''
TODO: 상품명, 카테고리, 특징, 이미지패스, 상품링크, 차별점을 바탕으로 이미지 재구성
TODO: 이미지를 임시로 데이터 아웃풋에 저장 이후 삭제
'''

logger = get_logger(__name__)

def image_generator_main(
    product: dict,
    input_image_path: str, 
    model_pipeline,
    output_dir_path: str = "backend/data/output/",
    background_image_path: str = None,
)-> dict | bool:
    """
    이미지 제너레이터 메인
    """
    # 1. 이미지 로더
    logger.debug(f"🛠️ 이미지 로드 시작")
    image_loader = ImageLoader()
    loaded_image, filename = image_loader.load_image(image_path=input_image_path, target_size=None)

    if loaded_image is None:
        logger.error("❌ 이미지 로드에 실패했습니다. 처리를 중단합니다.")
        return False

    logger.info("✅ 이미지 로드 성공.")

    # 2. 배경 제거
    logger.debug(f"🛠️ 배경 제거 시작")
    background_handler = BackgroundHandler()

    processed_image = background_handler.remove_background(
        input_image=loaded_image,
        original_filename=filename,
        output_dir=output_dir_path
    )

    if processed_image is None:
        logger.error("❌ 배경 제거에 실패했습니다. 처리를 중단합니다.")
        return False

    logger.info("✅ 배경 제거 및 저장 성공.")

    # 3. 프롬프트 생성
    logger.debug("🛠️ 프롬프트 생성 시작")
    prompts = generate_prompts(product)

    if prompts:
        logger.info("✅ 프롬프트 생성 완료")
    else:
        logger.error("❌ 프롬프트 생성 실패")

    # 제품에 배경 이미지 생성하기
    logger.debug("🛠️ 모델 파이프라인으로 이미지 생성 시작")
    try:
        img_2_img_gen = Img2ImgGenerator(model_pipeline)
        gen_image, image_path = img_2_img_gen.generate_img(
            prompt=prompts["background_prompt"],
            init_image=processed_image,
            negative_prompt=prompts["negative_prompt"]
        )
        logger.info("✅ 이미지 생성 성공")
    except Exception as e:
        logger.error(f"❌ 이미지 생성 중 에러 발생: {e}")

    return {"image": gen_image}


    # # 4. 배경 이미지 생성
    # logger.debug("🛠️ 파이프라인 생성 시작")
    # text_to_img_gen = Txt2ImgGenerator(model_pipeline)
    # background_image, background_image_path = text_to_img_gen.generate_background(prompt=prompts["background_prompt"],
    #                                                  negative_prompt=prompts["negative_prompt"])


    # # 5. 이미지 배경 추가
    # logger.debug(f"🛠️ 이미지 배경 추가 시작")
    # bg_image, bg_filename = image_loader.load_image(
    #     image_path=background_image_path,
    # )

    # if bg_image is None:
    #     logger.error("❌ 배경 이미지 로드에 실패했습니다. 배경 합성을 건너뜁니다.")
    # else:
    #     image_with_bg = background_handler.add_image_background(
    #         foreground_image=processed_image,
    #         background_image=bg_image,
    #         original_filename=filename,
    #         background_filename=bg_filename,
    #         output_dir=output_dir_path
    #     )
    #     if image_with_bg is None:
    #         logger.error("❌ 이미지 배경 추가에 실패했습니다. 처리를 중단합니다.")
    #     logger.info("✅ 이미지 배경 추가 및 저장 성공.")

    # return {"image": image_with_bg}