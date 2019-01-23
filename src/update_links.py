from bs4 import BeautifulSoup

from mongodb_utils import Mongodb, get_db
from utils import VERSION, launch_driver


def update_links_to_db(links):
    db = get_db()
    links_collection = 'links_{}'.format(VERSION)
    db.insert_many(links_collection, links, ['url'])


def get_links_from_web():
    driver = launch_driver()
    url = 'https://www.sindelantal.mx'
    driver.get(url)
    # 解析页面
    # selenium stores th source HTML in the driver's page_source attribute
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    cities_rests = soup.find("div", {"class": "cities-rests"})
    lis = cities_rests.find_all("li", {"class": "internal-link"})
    links = []
    for li in lis:
        tag_a = li.a
        link = {
            "title": tag_a['title'],
            "url": url + tag_a['href'],
        }
        links.append(link)
    return links


if __name__ == "__main__":
    links = get_links_from_web()
    update_links_to_db(links)