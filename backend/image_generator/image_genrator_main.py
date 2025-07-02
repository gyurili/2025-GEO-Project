from utils.logger import get_logger

'''
TODO: 상품명, 카테고리, 특징, 이미지패스, 상품링크, 차별점을 바탕으로 이미지 재구성
TODO: 이미지를 임시로 데이터 아웃풋에 저장 이후 삭제
'''

logger = get_logger(__name__)

def image_generator_main(config, product_info, differences):
    
    image_data = {"image_path": "data/output/example.jpg"}
    return image_data