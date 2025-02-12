import time
import trafaret_rss

class MailRuRSS(trafaret_rss.TrafaretRss):

    def __init__(self, name_rss):
        super(MailRuRSS, self).__init__(name_rss)

    def special_values(self, item, j):
        if 'url' in self.values:
            st = self.values['url'].replace('https://news.mail.ru/', '')
            st = st.split('/')
            self.values['unknown_category'] = st[0]

# MailRuRSS('MailRuRSS', 'MailRuRSS', 'period', 'Поток "Лента новостей mail.ru" загружен', 'news.mail.ru').start()
# while True:
#     time.sleep(5)