"""
Для новостей, у которых отсутствует перевод текста статьи, производится попытка перевода текста статьи и записи
файлов на трех языках в облако
"""
import trafaret_thread
import common
import config
import json
from deep_translator import GoogleTranslator
from google.cloud import storage
import py7zr
import time
import os
import shutil


def load_file_bucket(filename):
    try:
        filename = str(filename)
        client = storage.Client.from_service_account_json(json_credentials_path=common.path_to_private_key)
        bucket = storage.Bucket(client, common.bucket_name)  # указать текущий начальный bucket
        temp_dir = common.current_path + '/news'
        if not os.path.exists(temp_dir + '/' + filename):
            file_name = os.path.splitext(filename)[0] + '.7z'
            blob = bucket.blob(file_name)
            os.makedirs(temp_dir, exist_ok=True)
            blob.download_to_filename(temp_dir + '/' + file_name)  # это загрузка файла
            with py7zr.SevenZipFile(temp_dir + '/' + file_name, 'r') as arch:
                arch.extractall(path=temp_dir)
            os.remove(temp_dir + '/' + file_name)
            filepath = temp_dir + '/' + filename + '.txt'
            f = open(filepath, 'r', encoding='utf-8')
            with f:
                txt = f.read()
            os.remove(filepath)
            shutil.rmtree(common.current_path + '/news/', ignore_errors=True)
            return txt, True
    except Exception as er:
        filename = filename if filename is not None else 'None' + '" в облаке недоступен или отсутствует'
        txt = f'ERROR: {er} ' + filename
        return txt, False


class TranslateRSS(trafaret_thread.TrafaretThread):
    list_complete = list()
    global_count = 0
    global_new = 0
    global_error = 0
    last_length = 0
    limit = 0

    def __init__(self, source):
        super(TranslateRSS, self).__init__(source)
        self.text_greetings = "Поток 'Повторная трансляция файлов для новостей с error_translate'"

    def load_list_translate(self):
        where ='error_translator'
        ans, is_ok, status = common.send_rest(
            'v2/entity/values?app_code={app_code}&object_code=rss_history&where={where}&column_order=id'.format(
                app_code=config.schema_name, where=where), params={"columns": "id, lang"})
        if not is_ok:
            common.write_log_db(
                'error', 'load_list_translator', f"Ошибка {ans}", file_name=common.get_computer_name())
            return False
        self.list_complete = json.loads(ans)
        return len(ans) > 0

    def make_translate(self, values):
        txt, is_ok = load_file_bucket(values['lang'] + '_' + str(values['id']))
        if not is_ok:
            return False, txt
        self.last_length = len(txt)
        text = common.get_array_text(txt)
        text_ru = ''
        text_en = ''
        for unit in text:
            if values['lang'] != 'ru':
                try:
                    res = GoogleTranslator(target='ru').translate(unit)
                    if res:
                        text_ru += res
                    else:
                        text_ru += unit
                except Exception as er:
                    return False, er
            if values['lang'] != 'en':
                try:
                    res = GoogleTranslator(target='en').translate(unit)
                    if res:
                        text_en += res
                    else:
                        text_en += unit
                except Exception as er:
                    return False, er
        if values['lang'] != 'ru':
            common.save_file_bucket('ru_' + str(values['id']), text_ru)
        if values['lang'] != 'en':
            common.save_file_bucket('en_' + str(values['id']), text_en)
        params = {"schema_name": config.schema_name, "object_code": "rss_history",
                  "values": {'id': values['id'], 'error_translator': 'false'}}
        ans, is_ok, status = common.send_rest('v2/entity', 'PUT', params=params, token_user=self.token)
        if not is_ok:
            common.write_log_db(
                'error', self.source, f"Ошибка {ans}", file_name=common.get_computer_name())
        return True, ''

    def work(self):
        super(TranslateRSS, self).work()
        if self.load_list_translate() and self.make_login():
            self.limit = common.get_value_config_param('limit', self.par)
            self.limit = 1000
            self.global_count = len(self.list_complete)
            self.global_error = 0
            self.global_new = 0
            for j, data in enumerate(self.list_complete):
                t0 = time.time()
                try:
                    is_ok, er = self.make_translate(data)
                    if not is_ok:
                        self.global_error += 1
                        common.write_log_db(
                            'error', self.source, f"Ошибка {er}", file_name=common.get_computer_name(),
                            law_id=data['id'], page=j+1, td=time.time() - t0)
                    else:
                        common.write_log_db(
                            'translate', self.source, "Трансляция статьи завершена",
                            file_name=common.get_computer_name(),
                            law_id=data['id'], page=j+1, td=time.time() - t0)
                except Exception as er:
                    self.global_error += 1
                    common.write_log_db(
                        'error', self.source, f"Ошибка {er}", file_name=common.get_computer_name(),
                        law_id=data['id'], page=j+1, td=time.time() - t0)
            self.finish_text += 'Трансляция статей новостей:\nВсего пропусков={global_count}\n' \
                                'Добавлено={global_new}\nОшибок={global_error}'.format(
                global_count=self.global_count, global_error=self.global_error, global_new=self.global_new)
            self.result_work = True


# common.current_path = os.path.abspath(os.curdir)
# TranslateRSS('rss_translate').start()
#
# while True:
#     time.sleep(5)
