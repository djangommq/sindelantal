import csv
import json
import logging
import traceback
from bs4 import BeautifulSoup

from time import sleep

import os

from get_restaurants_list import check_element_by_xpath, wait_to_display, update_restaurant, find_todo_restaurant, \
    mark_restaurant_done, restaurants_collection, unmark_doing
from utils import VERSION, launch_driver

from mongodb_utils import get_db

# 获取链接数据库的对象那个
client_mongo=get_db()

# 存储评论数据的表名称
table_name=VERSION+'comment'



# 主方法
def get_restaurant_info(r):
    driver = launch_driver()

    try:
        # 请求链接
        url = r.get('url')
        logging.info(url)
        driver.get(url)

        # 重定向判定
        if driver.current_url == url:
            pass
        else:
            logging.info('该网页进行了重定向,稍后再请求.')
            return -1

        # 首先分析信息,更新到new_info
        # 从script中解析出新信息
        new_info = parse_new_info(driver)
        new_info['state'] = r.get('state')
        new_info['rid'] = r.get('rid')

        # 统计评论
        if new_info.get('count_rating') is None or int(new_info.get('count_rating', 0)) == 0:
            logging.info('餐馆评论为0, 可以直接跳过')
            update_restaurant(new_info)
            return 0
        else:
            # 加载评论
            load_comments(driver)
            source_page = BeautifulSoup(driver.page_source, 'html.parser')
            comments = parse_comments(source_page, new_info)
            save_comments(comments, r)
            update_restaurant(new_info)
            return 0

    except Exception as e:
        logging.info(traceback.format_exc())
        return -1
    finally:
        driver.close()


def parse_new_info(driver):
    try:
        source_page = BeautifulSoup(driver.page_source, 'html.parser')
        # geo_content = source_page.find('script', type='application/ld+json')
        geo_content = source_page.find_all('script', type='application/ld+json')[-1]
        # 异常修复5次，还不行就跳过
        r = geo_content.text.strip()
        loop_mark = 5
        r_info = None
        while loop_mark > 0:
            try:
                r_info = json.loads(r)
                break
            except Exception as e1:
                logging.info('修复json数据')
                code = int(str(e1).split(' ')[-1].replace(')', ''))
                error_c_index = r.rfind(',', 0, code)
                r = r[:error_c_index] + r[error_c_index + 1:]
                loop_mark -= 1
                ...

        if r_info is None:
            new_info = None
            pass
        else:
            new_info = {
                'url': driver.current_url,
                'name': r_info.get('name'),
                'cuisine': r_info.get('servesCuisine'),
                'rating_summary': r_info.get('aggregateRating').get('ratingValue'),
                'price': r_info.get('priceRange'),
                'latitude': r_info.get('geo').get('latitude'),
                'longitude': r_info.get('geo').get('longitude'),
                'address_locality': r_info.get('address').get('addressLocality'),
                'address_region': r_info.get('address').get('addressRegion'),
                'address_street': r_info.get('address').get('streetAddress'),
                'postalcode': r_info.get('address').get('postalCode'),
                'count_rating': r_info.get('aggregateRating').get('ratingCount'),
                'max_rating_date': None,
                'min_rating_date': None,
            }
            # 增加log,和下面统计的评论进行比对

        return new_info
    except Exception as e:
        logging.info('获取餐馆坐标出错')
        logging.info(traceback.format_exc())
        raise e


def load_comments(driver):
    driver.execute_script("$('.button.load-more.hide').removeClass('hide')")
    sleep(1)
    driver.execute_script("$('#menuContent').remove()")
    sleep(1)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    print('开始拉取评论')
    # 加载带内容的评论
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        more_comments = driver.find_element_by_xpath('//*[@id="ratingContent"]/div[2]/div[2]')
        if more_comments.get_attribute('style') == 'display: none;':
            break
        else:
            ab_close_button(driver)
            more_comments.click()
            sleep(2)

    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        more_comments = driver.find_element_by_xpath('//*[@id="ratingContent"]/div[3]/div')
        if more_comments.get_attribute('style') == 'display: none;':
            break
        else:
            ab_close_button(driver)
            more_comments.click()
            sleep(2)
    print('加载出所有评论')


def ab_close_button(driver):
    try:
        ab_close_button = driver.find_element_by_xpath('/html/body/div[7]/div[2]/i')
        ab_close_button.click()
        print(ab_close_button)
        print('找到了图片按钮')
        sleep(2)
    except:
        print('没有弹出图片')


def parse_comments(source_page, new_info):  # 11
    logging.info('解析评论中。。。')
    # 先找出含有内容的评论
    count = 0
    comments = {}
    comments_container_tag = source_page.find('div', {'class': 'ratting-comments-container'})
    tags = comments_container_tag.find_all('li')
    for tag in tags:
        count += 1
        # 有描述的为C
        source = 'C'
        comment_name = tag.find('div', {'class': 'user-name'}).text
        comment_rating = tag.find('div', {'class': 'rest-score'}).text
        comment_date = tag.find('div', {'class': 'comment-date'}).text
        comment_desc = tag.find('div', {'class': 'user-comment'}).text.replace('\n', ' ')
        try:
            # 店家没有评论，返回None
            comment_reply = tag.find('div', {'class': 'restaurant-comment'}).text
        except:
            comment_reply = None
        tmp_r = {
            'source': source,
            'comment_name': comment_name,
            'comment_date': comment_date,
            'comment_rating': comment_rating,
            'comment_desc': comment_desc,
            'comment_reply': comment_reply,
        }
        comments[count] = tmp_r

    # 加载不含内容的评论
    no_comments_container_tag = source_page.find('div', {'class': 'ratting-no-comments-container'})
    tags = no_comments_container_tag.find_all('li')
    for tag in tags:
        count += 1
        # 无描述的为R
        source = 'R'
        rating_name = tag.find('div', {'class': 'user-name'}).text
        rating_value = tag.find('div', {'class': 'user-score'}).text
        rating_date = tag.find('div', {'class': 'comment-date'}).text
        if new_info.get('max_rating_date') is None:
            new_info['max_rating_date'] = rating_date
        new_info['min_rating_date'] = rating_date
        tmp_r = {
            'source': source,
            'rating_name': rating_name,
            'rating_value': rating_value,
            'rating_date': rating_date,
        }
        comments[count] = tmp_r

    logging.info('解析评论结束')
    return comments


def save_comments(comments, r):
    # 访问餐馆的url:https://www.sindelantal.mx/delivery/aguascalientes-agu/burger-king-colosio-jardines-de-la-concepcion-ii
    rest_url = r.get('url')
    rest_list=rest_url.split('/')
    # 餐馆评论文件的文件名
    name=rest_list[-2]+'_'+rest_list[-1]

    file_path = '../data/{}/comments/{}.csv'.format(VERSION, name)
    header = [
        'source',
        'comment_name',
        'comment_date',
        'comment_rating',
        'comment_desc',
        'comment_reply',
        'rating_name',
        'rating_value',
        'rating_date'
    ]
    file_dir = os.path.split(file_path)[0]
    if not os.path.exists(file_dir):
        os.makedirs(file_dir)
    # with open(file_path, 'w', newline='', encoding='utf-8') as f:
    #     csv_f = csv.writer(f)
    #     csv_f.writerow(header)
    comment_info_list = []
    for comment in comments.values():
        tmp_row = []
        for h in header:
            tmp_content = comment.get(h)
            if tmp_content is None:
                pass
            elif type(tmp_content) == str:
                tmp_content = tmp_content.encode("gbk", 'ignore').decode("gbk", "ignore")
            tmp_row.append(tmp_content)
        # csv_f.writerow(tmp_row)
        comment_info_list.append(tmp_row)
    comment_info_strb = json.dumps(comment_info_list)
    comment_dict = {
        'comment_name': name + '.csv',
        'comment_content': comment_info_strb
    }
    client_mongo.insert_one(table_name, comment_dict, condition=['comment_name'])


def get_all_restaurants_info():
    while True:
        r = find_todo_restaurant()
        if r is None:
            logging.info('所有餐馆处理完毕')
            new_todo = unmark_doing(restaurants_collection)
            print('标记restaurant数目:{}'.format(new_todo))
            if new_todo == 0:
                # 运行完了, 尽可能等待1小时,
                sleep(3600)
            break
        return_code = get_restaurant_info(r)
        if return_code == 0:
            mark_restaurant_done(r)
        else:
            logging.error("{}餐馆出现错误".format(r))


# 分段统计数据, 后两个参数是起始和末尾id
# 包含start, 不包含end
if __name__ == '__main__':
    get_all_restaurants_info()
    ...