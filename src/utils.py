import datetime
import json
import time
import traceback
import os

from selenium import webdriver
import logging
import config

VERSION = '20190117'
# MONGODB_SERVER = 'localhost'
MONGODB_SERVER = config.MONGODB_SERVER
MONGODB_PORT = config.MONGODB_PORT
USER = config.USER
PASSWORD = config.PASSWORD
MONGODB_DATABASE = 'sindelantal'
MONGODB_COLLECTION = 'restaurants_{}'.format(VERSION)
CHARSET = 'utf-8'


def save_file(data_input, file_path):
    try:
        tmp_dir = os.path.split(file_path)[0]
        if not os.path.exists(tmp_dir):
            os.makedirs(tmp_dir)
        with open(file_path, 'w', encoding='utf-8') as fw:
            s = json.dumps(data_input)
            fw.write(s)
            logging.info('文件{}保存正常'.format(file_path))
    except Exception as e:
        logging.info(e)
        logging.info(traceback.format_exc())


def launch_driver():
    # Chrome配置
    # ===================================================================
    option = webdriver.ChromeOptions()
    option.add_argument('headless')
    prefs = {"profile.managed_default_content_settings.images": 2}
    option.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(chrome_options=option)
    driver.implicitly_wait(10)

    return driver


date = datetime.datetime.now().strftime("%Y-%m-%d")

log_path = './{}.log'.format(date)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s  %(filename)s : %(levelname)s  %(message)s',    # 定义输出log的格式
    datefmt='%Y-%m-%d %A %H:%M:%S',
    handlers=[logging.FileHandler(log_path, 'a', 'utf-8')],
)
logger_name = 'sindelantal_log'
logger = logging.getLogger(logger_name)