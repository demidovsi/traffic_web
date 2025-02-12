import trafaret_thread
import common
import config
import json
import time
from bs4 import BeautifulSoup
import requests
from requests.adapters import HTTPAdapter
import xml.etree.ElementTree as ET
from deep_translator import GoogleTranslator
from newspaper import Article

http_adapter = HTTPAdapter(max_retries=10)


class TrafaretHTML(trafaret_thread.TrafaretThread):
    rss_name = None
    rss_id = None
    rss_url = ''
    rss_lang = 'ru'
    text = ''
    themes = []
    rss_themes = []
    values = {}
    count_error = 0
    count_new = 0
    count = 0

    def __init__(self, name_rss):
        super(TrafaretHTML, self).__init__(name_rss)
        self.rss_name = name_rss

    def define_url(self):
        self.rss_url = ''
        self.rss_id = None
        ans, is_ok, status = common.send_rest("v2/select/{schema}/nsi_rss_list?where=sh_name='{name_rss}'".format(
            schema=config.schema_name, name_rss=self.rss_name))
        if is_ok:
            ans = json.loads(ans)
            if len(ans) > 0:
                ans = ans[0]
                self.rss_id = ans['id']
                self.rss_url = ans['url']
                self.rss_lang = ans['lang']
                return True
        else:
            common.write_log_db('error', self.source, 'Ошибка {er}'.format(er=ans),
                                file_name=common.get_computer_name())

    def define_themes(self):
        self.rss_themes = list()
        query = """
            select a.id, a.sh_name, a.value 
            from 
                {schema}.nsi_rss_themes a, 
                {schema}.rel_rss_list_rss_themes_themes b
            where 
                b.rss_themes_id=a.id
                and b.rss_list_id={rss_id};
            """.format(schema=config.schema_name, rss_id=self.rss_id)
        ans, is_ok, status = common.send_rest("v2/execute", 'PUT', params={"script": query}, token_user=self.token)
        if is_ok:
            self.rss_themes = json.loads(ans)
            return True
        else:
            common.write_log_db('error', self.source, 'Ошибка {er}'.format(er=ans),
                                file_name=common.get_computer_name())

    def get_inform_url(self):
        t0 = time.time()
        self.text = ''
        try:
            session = requests.Session()
            session.mount(self.rss_url, http_adapter)
            r = session.get(self.rss_url, timeout=(100, 100))
            if r.ok:  # 200
                self.text = r.text
                return True
        except Exception as er:
            self.count_error += 1
            common.write_log_db(
                'error_requests', self.source, f"Ошибка {er}\nЗапрос ленты новостей с сайта\n\n{self.rss_url}",
                file_name=common.get_computer_name(),
                page=self.count, td=time.time() - t0)

    def special_values(self, lw, j):
        # специализированная обработка (индивидуальная)
        pass

    def seek(self):
        def slave(key, word):
            if key in self.values:
                return common.make_search(word, self.values[key])
            else:
                return 0

        self.values['themes'] = []  # нет пока нет
        for data in self.rss_themes:
            words = data['value'].split(';')
            count = 0
            for word in words:
                if data['value'].strip() == '':
                    count += 1
                else:
                    count += slave('title_ru', word)
                    count += slave('title_en', word)
                    count += slave('description_ru', word)
                    count += slave('description_en', word)
            if count:
                self.values['themes'].append(data['id'])  # добавить идентификатор темы

    def is_exist_object(self, theme_id):
        if 'public_date' in self.values:
            where = "public_date='{dt} 00:00:00.000' and theme={theme} and rss={rss} and url=%s and title_ru=%s" .format(
                dt=self.values['public_date'], theme=theme_id, rss=self.rss_id)
        else:
            where = "theme={theme} and rss={rss} and url=%s and title_ru=%s".format(theme=theme_id, rss=self.rss_id)
        ans, is_ok, status = common.send_rest(
            'v2/entity/values?app_code={app_code}&object_code=rss_history&where={where}'.format(
                app_code=config.schema_name, where=where), params={"datas": "{url}~~~{title_ru}".format(
                url=self.values['url'], title_ru=self.values['title_ru'].strip())})
        if not is_ok:
            common.write_log_db(
                'error', self.source, f"Ошибка {ans}", file_name=common.get_computer_name())
            return
        ans = json.loads(ans)
        return len(ans) > 0

    def make_translate(self, txt, lang):
        text = common.get_array_text(txt)
        text_result = ''
        self.values['error_translator'] = False
        for unit in text:
            try:
                res = GoogleTranslator(target=lang).translate(unit)
                if res:
                    text_result += res
                else:
                    text_result += unit
            except:
                text_result += unit
                self.values['error_translator'] = True
        return text_result

    def load_article(self):
        if 'url' in self.values and self.values['url']:
            article = Article(self.values['url'])
            article.download()
            article.parse()
            self.values['meta_img'] = article.meta_img
            txt = article.text
            txt = common.make_description(txt)
            text_ru = self.make_translate(txt, 'ru')
            text_en = self.make_translate(txt, 'en')
            common.save_file_bucket('en_' + str(self.values['id']), text_en)
            common.save_file_bucket('ru_' + str(self.values['id']), text_ru)
            self.values['file'] = len(txt)
            return True
        else:
            return False

    def get_name_theme(self, theme_id):
        result = ''
        for data in self.rss_themes:
            if data['id'] == int(theme_id):
                return data['sh_name']
        return result

    def make_theme(self, theme_id, j):
        exist = self.is_exist_object(theme_id)
        if exist is not None and not exist:
            self.count_new += 1
            self.values['id'] = common.write_history(self.values, theme_id, self.token)
            if self.load_article():
                # добавленная запись параметров
                params = {"schema_name": config.schema_name, "object_code": "rss_history",
                          "values": {'id': self.values['id'], 'file': self.values['file'],
                                     'meta_img': self.values['meta_img'],
                                     'error_translator': self.values['error_translator']}}
                ans, is_ok, status = common.send_rest('v2/entity', 'PUT', params=params, token_user=self.token)
                if not is_ok:
                    common.write_log_db(
                        'error', 'write_history', f"Ошибка {ans}", file_name=common.get_computer_name())

            print(time.ctime(), '# '+str(j+1), 'count=', self.count, 'new=', self.count_new, 'rss=',
                  self.rss_name, 'theme=', theme_id, self.get_name_theme(theme_id))
            # передать в телеграм-канал
            # href = config.web + '/one_new/{id}'.format(id=self.values['id'])
            # st = "<u>{rss_name}</u> ({public_date})                        [{id}]" \
            #      "\n[<b>{theme_name}</b>] {lang}" \
            #      "\n\n<b>{title}</b>" \
            #      "\n{social_title}\n\n{description}\n\n<b>{href}</b>\n\n{url}".format(
            #     rss_name=self.rss_name,
            #     public_date=self.values['public_date'] if 'public_date' in self.values else 'нет даты новости',
            #     theme_name=self.get_name_theme(theme_id),
            #     title=common.translate_from_base(self.values['title_ru']), lang=self.rss_lang, id=self.values['id'],
            #     social_title=common.translate_from_base(
            #         self.values['social_title_ru']) if 'social_title_ru' in self.values else '',
            #     description=common.translate_from_base(self.values['description_ru']) if 'description_ru' in self.values else '',
            #     href=href, url=self.rss_url
            # )
            # if 'author' in self.values:
            #     st += '\nauthor [<b>{author}</b>]'.format(author=self.values['author'])
            # ans = common.send_tg(st)
            # if ans['ok']:
                # передача в чат прошла успешно
                # self.fixation_sent(ident, law_id, 'true')
                # common.write_log_db(
                #     'info', 'TG',
                #     'В ТЕЛЕГРАМ (Nasha_gazeta) передана новость с ID={id} от [{rss_name}]'.format(
                #         id=self.values['id'], rss_name=self.rss_name, file_name=common.get_computer_name(),
                #     law_id=self.get_name_theme(theme_id))
            # else:
                # ошибка передачи в чат - запишем в лог и попробуем позже
                # common.write_log_db(
                #     'ERROR', 'TG',
                #     'Ошибка: ' + str(ans) + '\n при передачи в ТЕЛЕГРАМ новости  с ID={id} от [{rss_name}]'.
                #     format(id=self.values['id'], rss_name=self.rss_name, file_name=common.get_computer_name(),
                #     law_id=self.get_name_theme(theme_id))
            self.values.pop('id')

    def make_values(self, lw, j):
        # разобрать item в self.values
        def trans(key, txt):
            if txt:
                if self.rss_lang == 'ru':
                    self.values[key + '_ru'] = txt
                    self.values[key + '_en'] = self.make_translate(txt, 'en')
                elif self.rss_lang == 'en':
                    self.values[key + '_en'] = txt
                    self.values[key + '_ru'] = self.make_translate(txt, 'ru')

        news_content = lw.find('div', class_='news-content')
        self.count += 1
        # заголовок новости
        txt = news_content.find('h2', class_='news-name').text
        trans('title', txt)
        # текст новости
        txt = news_content.find('a', class_='news-preview').text
        description = common.make_description(txt)
        trans('description', description)

        # публичная дата новости
        txt = news_content.find('span', class_='news-date').text
        dt = time.strptime(txt, '%d.%m.%Y')
        self.values['public_date'] = time.strftime('%Y-%m-%d', dt)

        # ссылка на источник
        txt = news_content.find('a', class_='news-link').attrs['href']
        if txt and txt[0] == '/':
            txt =  self.rss_url + txt[1:]
        self.values['url'] = txt

    def work(self):
        super(TrafaretHTML, self).work()
        if common.get_value_config_param('active', self.par) != 1:
            self.finish_text = 'Поток не АКТИВЕН (active)'
            return True
        # определить характеристики сайта для скачивания ленты новостей и список тем для сайта
        if self.make_login() and self.define_url() and self.define_themes():
            self.count_error = 0
            self.count_new = 0
            self.count = 0
            if self.get_inform_url():  # скачать текст с сайта ленты
                self.values = {"rss": self.rss_id, 'lang': self.rss_lang}
                news = BeautifulSoup(self.text, 'lxml').find_all('div', class_='news-item')
                for j, lw in enumerate(news):
                    try:
                        self.make_values(lw, j)
                        self.special_values(lw, j)
                        self.seek()
                        if self.values['themes']:  # есть вхождения из этого списка тем
                            for theme in self.values['themes']:
                                self.make_theme(theme, j)  # записать в БД и передать в ТГ
                    except Exception as er:
                        print(self.source, 'N=' + str(j), f"{er}")
                self.finish_text = 'Обработан {rss} сайт, получено новостей {global_count}, ' \
                                   'записано {global_new}, ошибок {global_error}\n'. \
                    format(rss=self.rss_name,
                           global_error=self.count_error,
                           global_count=self.count,
                           global_new=self.count_new)
                self.result_work = True
        else:
            self.result_work = False
            print(time.ctime())
