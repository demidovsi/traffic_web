import time

from bs4 import BeautifulSoup
import requests
from requests.adapters import HTTPAdapter
import trafaret_html
import trafaret_rss


# url = 'https://bits.media/'
# http_adapter = HTTPAdapter(max_retries=10)
#
# session = requests.Session()
# session.mount(url, http_adapter)
# r = session.get(url, timeout=(100, 100))
# if r.ok:  # 200
#     news = BeautifulSoup(r.text, 'lxml').find_all('div', class_='news-item')
#     for lw in news:
#         news_content = lw.find('div', class_='news-content')
#         title = news_content.find('h2', class_='news-name').text
#         description = news_content.find('a', class_='news-preview').text
#         date = news_content.find('span', class_='news-date').text
#         url = news_content.find('a', class_='news-link').attrs['href']
#         print(date, title, description, url)

trafaret_html.TrafaretHTML('Bits-Media').start()
# trafaret_rss.TrafaretRss('Incrypted', 'incrypted', 'period', 'Поток "Лента новостей Incrypted" загружен', 'incrypted.com').start()
while True:
    time.sleep((5))
