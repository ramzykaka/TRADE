import logging

def setup_logger():
    """إعداد نظام التسجيل"""
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )