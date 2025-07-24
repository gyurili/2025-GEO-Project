import logging  # 파이썬 표준 로깅(logging) 모듈을 가져옵니다. 로그 기록과 출력에 사용됩니다.

def get_logger(name: str) -> logging.Logger:
    # 이름을 받아 해당 이름의 로거(Logger) 객체를 생성하거나 가져옵니다.
    logger = logging.getLogger(name)

    # 로거의 로그 레벨을 DEBUG로 설정합니다. DEBUG 이상 레벨의 로그를 출력합니다.
    # 적용하는 레벨 이하의 문제는 출력하지 않는다. 
    # 예를 들어 default값인 warning으로 설정 시 DEBUG나 INFO의 로그는 기록되지 않고,
    # WARNING 이상의 로그만 기록된다.
    logger.setLevel(logging.DEBUG)

    # 이미 핸들러(handler)가 설정되어 있는지 확인합니다. 중복 설정을 방지하기 위함입니다.
    # DEBUG: 상세한 정보. 문제 진단 시 필요.
    # INFO: 예상대로 작동하는지에 대한 확인.
    # WARNING(default): 예상치 못한 일의 발생 (소프트웨어는 여전히 예상대로 작동)
    # ERROR: 심각한 문제로 인해 소프트웨어 일부 기능 수행 못함
    # CRITICAL: 심각한 에러로 인해 프로그램 자체가 계속 실행되지 않을 수 있음.
    if not logger.handlers:
        # 콘솔에 로그를 출력할 스트림 핸들러(StreamHandler)를 생성합니다.
        # (streamHandLer: 콘솔 출력용 // fileHandler: 파일 기록용)
        stream_handler = logging.StreamHandler()

        # 로그 출력 형식을 지정합니다. (시간, 로그레벨, 로거이름, 메시지)
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s",
            datefmt="%y%m%d %H:%M:%S"  # 시간 형식을 '년월일 시:분:초'로 설정합니다.
        )

        # 핸들러에 포매터를 연결합니다.
        stream_handler.setFormatter(formatter)

        # 로거에 핸들러를 추가합니다.
        logger.addHandler(stream_handler)

    # 설정된 로거를 반환합니다.
    return logger