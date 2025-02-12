import trafaret_thread
import common
import config
import json
import time
import datetime
import requests
import xml.etree.ElementTree as ET
import locale
from deep_translator import GoogleTranslator
from newspaper import Article


class TrafaretRss(trafaret_thread.TrafaretThread):
    rss_name = None
    rss_id = None
    rss_url = ''
    rss_lang = 'ru'
    items = ''
    themes = []
    rss_themes = []
    values = {}
    count_error = 0
    count_new = 0
    count = 0

    def __init__(self, name_rss):
        super(TrafaretRss, self).__init__(name_rss)
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
        try:
            r = requests.get(self.rss_url)
            if r.ok:
                rss_feed = r.content
                root = ET.fromstring(rss_feed)
                self.items = root.findall('.//item')
                if len(self.items) == 0:
                    self.items = root.findall('.//CONTENTITEM')
                return True
            else:
                self.count_error += 1
                common.write_log_db(
                    'error_requests', self.source, "Ошибка " + str(r.status_code) + ' ' + r.reason +
                                                   f"\nЗапрос ленты новостей с сайта\n\n{self.rss_url}",
                    file_name=common.get_computer_name(),
                    page=self.count, td=time.time() - t0)

        except Exception as er:
            self.count_error += 1
            self.items = []
            common.write_log_db(
                'error_requests', self.source, f"Ошибка {er}\nЗапрос ленты новостей с сайта\n\n{self.rss_url}",
                file_name=common.get_computer_name(),
                page=self.count, td=time.time() - t0)

    def special_values(self, item, j):
        # специализированная обработка (индивидуальная)
        pass

    def make_values(self, item, j):
        # разобрать item в self.values
        def trans(key, txt):
            if txt:
                if self.rss_lang == 'ru':
                    self.values[key + '_ru'] = txt
                    self.values[key + '_en'] = self.make_translate(txt, 'en')
                elif self.rss_lang == 'en':
                    self.values[key + '_en'] = txt
                    self.values[key + '_ru'] = self.make_translate(txt, 'ru')

        self.count += 1
        # заголовок новости
        if item.find('title') is not None:
            txt = common.extract_text(item.find('title'))
            trans('title', txt)
        elif item.find('HEADLINE') is not None:
            txt = common.extract_text(item.find('HEADLINE'))
            trans('title', txt)

        if item.find('SocialTitle'):
            trans('social_title', common.extract_text(item.find('SocialTitle')))
        # ссылка на источник
        if item.find('link') is not None:
            txt = common.extract_text(item.find('link'))
        elif item.find('URL') is not None:
            txt = common.extract_text(item.find('URL'))
        else:
            txt = None
        if txt:
            self.values['url'] = txt

        # текст новости
        if item.find('description') is not None:
            txt = common.extract_text(item.find('description'))
        elif item.find('ABSTRACT') is not None:
            txt = common.extract_text(item.find('ABSTRACT'))
        else:
            txt = ''
        if txt:
            description = common.make_description(txt)
            trans('description', description)

        # источник новости
        txt = common.extract_text(item.find('author'))
        if txt:
            self.values['author'] = txt

        # публичная дата новости
        locale.setlocale(locale.LC_ALL)
        txt = common.extract_text(item.find('pubDate'))
        if txt:
            txt = txt.replace(' GMT', '')
            try:
                dt = time.strptime(txt, '%a, %d %b %Y %H:%M:%S %z')
                # преобразуем к системному времени
                h = 0
                if '+' in txt:
                    h = int(txt.split('+')[1][:2])
                if '-' in txt:
                    h = int(txt.split('-')[1][:2])
                dt = datetime.datetime.fromtimestamp(time.mktime(dt)) - datetime.timedelta(hours=h)
                self.values['public_date'] = str(dt)
            except:
                dt = time.strptime(txt, '%a, %d %b %Y %H:%M:%S')
                self.values['public_date'] = time.strftime('%Y-%m-%d %H:%M:%S', dt)
        # дата и время записи новости в БД
        self.values['at_date_time'] = str(datetime.datetime.utcnow())

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
                    count += slave('social_title_ru', word)
                    count += slave('social_title_en', word)

                    count += slave('title_ru', word)
                    count += slave('title_en', word)

                    count += slave('description_ru', word)
                    count += slave('description_en', word)

            if count:
                self.values['themes'].append(data['id'])  # добавить идентификатор темы

    def is_exist_object(self, theme_id):
        if 'public_date' in self.values:
            where = "public_date='{dt}.000' and theme={theme} and rss={rss} and url=%s".format(
                dt=self.values['public_date'], theme=theme_id, rss=self.rss_id)
        else:
            where = "theme={theme} and rss={rss} and url=%s".format(theme=theme_id, rss=self.rss_id)
        ans, is_ok, status = common.send_rest(
            'v2/entity/values?app_code={app_code}&object_code=rss_history&where={where}'.format(
                app_code=config.schema_name, where=where), params={"datas": "{url}".format(url=self.values['url'])})
        if not is_ok:
            common.write_log_db(
                'error', self.source, f"Ошибка {ans}", file_name=common.get_computer_name())
            return
        ans = json.loads(ans)
        return len(ans) > 0

    def get_name_theme(self, theme_id):
        result = ''
        for data in self.rss_themes:
            if data['id'] == int(theme_id):
                return data['sh_name']
        return result

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
            # text = get_array_text(txt)
            # text_ru = ''
            # text_en = ''
            # self.values['error_translator'] = False
            # for unit in text:
            #     try:
            #         res = GoogleTranslator(target='ru').translate(unit)
            #         if res:
            #             text_ru += res
            #         else:
            #             text_ru += unit
            #     except:
            #         text_ru += unit
            #         self.values['error_translator'] = True
            #     try:
            #         res = GoogleTranslator(target='en').translate(unit)
            #         if res:
            #             text_en += res
            #         else:
            #             text_en += unit
            #     except:
            #         text_en += unit
            #         self.values['error_translator'] = True

            common.save_file_bucket('en_' + str(self.values['id']), text_en)
            common.save_file_bucket('ru_' + str(self.values['id']), text_ru)
            self.values['file'] = len(txt)
            return True
        else:
            return False

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
                  self.rss_name, 'theme=', theme_id, self.get_name_theme(theme_id),
                  'id={id}'.format(id=self.values['id']), 'file={file}'.format(file=self.values['file']))
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

    def work(self):
        super(TrafaretRss, self).work()
        if common.get_value_config_param('active', self.par) != 1:
            self.finish_text = 'Поток не АКТИВЕН (active)'
            return True
        # определить характеристики сайта для скачивания ленты новостей и список тем для сайта
        if self.make_login() and self.define_url() and self.define_themes():
            self.count_error = 0
            self.count_new = 0
            self.count = 0
            if self.get_inform_url():  # скачать текст с сайта ленты
                self.values = {"rss": self.rss_id, "lang": self.rss_lang}
                for j, item in enumerate(self.items):
                    try:
                        self.make_values(item, j)
                        self.special_values(item, j)
                        self.seek()
                        if self.values['themes']:  # есть вхождения из этого списка тем
                            for theme in self.values['themes']:
                                self.make_theme(theme, j)  # записать в БД и передать в ТГ
                    except Exception as er:
                        print(self.source, 'N=' + str(j), f"{er}")
                    if self.count_new:
                        self.page = self.count_new
                self.finish_text = 'Обработан {rss} сайт, получено новостей {global_count}, ' \
                                   'записано {global_new}, ошибок {global_error}\n'.\
                    format(rss=self.rss_name,
                           global_error=self.count_error,
                           global_count=self.count,
                           global_new=self.count_new)
                self.result_work = True
        else:
            self.result_work = False
            print(time.ctime())
