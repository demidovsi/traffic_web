import os
import time
import json
import common
import config
import rss_mail_ru
import trafaret_rss
import trafaret_html
import rss_translate
import clear_logs

common.current_path = os.path.abspath(os.curdir)


common.write_log_db(
    'START', 'Сервис RSS DAN',
    'Старт сервиса контроля СМИ\n host RestAPI: ' + config.URL + ';\nschema: ' + config.schema_name,
    file_name=common.get_computer_name())

# rss_mail_ru.MailRuRSS('news.mail.ru').start()
# trafaret_rss.TrafaretRss('ru-crypto.com').start()
# trafaret_rss.TrafaretRss('forklog.com').start()
# trafaret_rss.TrafaretRss('Beincrypto').start()
# trafaret_rss.TrafaretRss('Twobitcoins').start()
# trafaret_rss.TrafaretRss('incrypted.com').start()
# trafaret_html.TrafaretHTML('bits_media').start()

clear_logs.ClearLogs('clear_logs').start()
rss_translate.TranslateRSS('rss_translate').start()

list_rss = list()
last_time = time.time()

def make_rss():
    ans, is_ok, status = common.send_rest("v2/select/{schema}/nsi_rss_list?column_order=id".format(
        schema=config.schema_name))
    if is_ok:
        ans = json.loads(ans)
        for unit in ans:
            if unit['id'] not in list_rss:
                if unit['is_rss'] == 1:
                    trafaret_rss.TrafaretRss(unit['sh_name']).start()
                elif unit['is_rss'] == 2:
                    rss_mail_ru.MailRuRSS(unit['sh_name']).start()
                else:
                    trafaret_html.TrafaretHTML(unit['sh_name']).start()
                list_rss.append(unit['id'])

while True:
    if time.time() >= last_time:
        make_rss()
        last_time = last_time + 60
    time.sleep(1)