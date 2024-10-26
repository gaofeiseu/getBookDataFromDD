import requests
from bs4 import BeautifulSoup
import re
import pymysql
import json


db_config = {
    'host': 'xxxxxxxxxxxxxxxxxxxxxxx.mysql.rds.aliyuncs.com',  # 替换为你的数据库链接
    'user': 'xxxxxxxxxxxxx',  # 替换为你的数据库用户名
    'password': 'xxxxxxxxxxxxxxxxxxxxx',  # 替换为你的数据库密码
    'db': 'xxxxxxxxxxxxxxx',  # 替换为你的数据库名
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor,  # 返回字典类型的游标
}


# 初始化数据库连接
def init_db():
    return pymysql.connect(**db_config)


# 插入数据到数据库
def insert_book(conn, ISBN, name, publisher, author, category, description, sell_price, original_price, imgs, site, biz_id):
    with conn.cursor() as cursor:
        sql = "INSERT INTO books (ISBN, name, publisher, author, category, description, sell_price, original_price, " \
              "imgs, site, biz_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) "
        cursor.execute(sql, (ISBN, name, publisher, author, category, description, sell_price, original_price, imgs, site, biz_id))
    conn.commit()


def parse_book_page(url):
    try:
        # 请求网页内容
        response = requests.get(url, timeout=3)
        response.raise_for_status()
    except requests.RequestException as e:
        # print(f"Error fetching {url}: {e}")
        return None

    # 开始解析
    soup = BeautifulSoup(response.text, 'html.parser')

    description_div = soup.find('meta', {'name': 'description'})
    if not description_div:
        return None
    description = description_div['content']

    isbn_pattern = r'ISBN：\s*(\d{13}|\d{10})'
    match = re.search(isbn_pattern, description)
    if match:
        ISBN = match.group(1)
    else:
        print("ISBN not found")
        return None

    category_div = soup.find('span', class_='linkto_value category_text')
    if not category_div:
        return None
    category = category_div.get_text(strip=True)

    author_div = soup.find('a', {'dd_name': '作者查看作品'})
    if not author_div:
        return None
    author_value_div = author_div.find('span', class_='linkto_value')
    if not author_value_div:
        return None
    author = author_value_div.get_text(strip=True)

    publisher_div = soup.find('a', {'dd_name': '出版社查看作品'})
    if not publisher_div:
        return None
    publisher_value_div = publisher_div.find('span', class_='linkto_value')
    if not publisher_value_div:
        return None
    publisher = publisher_value_div.get_text(strip=True)

    name = soup.find('article', class_='dangdang_icon').get_text(strip=True)
    sell_price = soup.find('span', class_='main_price').get_text(strip=True)
    original_price = soup.find('div', class_='original_price').find('span').get_text(strip=True)

    li_arr = soup.find('ul', class_='top-slider').find_all('li')
    image_urls = []
    for li in li_arr:
        img = li.find('a').find('img')
        if img and 'src' in img.attrs:
            image_urls.append(img['src'])
        if img and 'imgsrc' in img.attrs:
            image_urls.append(img['imgsrc'])

    # ISBN, name, publisher, author, category, description, sell_price, original_price, imgs, site, biz_id
    return {
        'ISBN': ISBN,
        'name': name,
        'publisher': publisher,
        'author': author,
        'category': category,
        'description': description,
        'sell_price': sell_price,
        'original_price': original_price,
        'imgs': json.dumps(image_urls),
        'site': 1
    }


def main():
    conn = init_db()
    base_url = "http://product.m.dangdang.com/{}.html"

    for product_id in range(29503785, 31502099):
        url = base_url.format(product_id)
        print(f"Fetching {url}")

        book_info = parse_book_page(url)
        if book_info:
            insert_book(conn, book_info['ISBN'], book_info['name'], book_info['publisher'], book_info['author'],
                        book_info['category'], book_info['description'], book_info['sell_price'],
                        book_info['original_price'], book_info['imgs'], book_info['site'], product_id)

    print("All finish")


if __name__ == '__main__':
    main()
