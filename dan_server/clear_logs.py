import json
import trafaret_thread
import time
import common
import datetime
import config as cfg


class ClearLogs(trafaret_thread.TrafaretThread):
    def __init__(self, source):
        super(ClearLogs, self).__init__(source)
        self.text_greetings = "Поток 'Чистка log-а'"

    def work(self):
        super(ClearLogs, self).work()
        self.result_work = False
        if self.make_login():  # есть связь с RestAPI и токен
            count_days = common.get_value_config_param("count_days", self.par)
            if count_days <= 0:
                common.write_log_db('ERROR', self.source,
                                    "Ошибка в задании кол-ва дней хранения {count_days};\nПовторим через 5 минут".format(
                                        count_days=count_days), td=time.time() - self.t0)
                return
            first_date = datetime.date.today() - datetime.timedelta(days=count_days)
            last_date = str(first_date.year) + '-' + str(first_date.month).zfill(2) + '-' + str(first_date.day).zfill(2)
            answer, is_ok, status = common.send_rest(
                "v1/function/{schema}/delete_logs?text='{text}'&view=0".format(
                    schema=cfg.schema_name, text=last_date), 'POST', token_user=self.token)
            if is_ok:
                answer = json.loads(answer)
                if 'count_before' in answer:
                    start_count = answer['count_before']
                    finish_count = answer['count_after']
                    self.finish_text = 'Было строк = ' + str(start_count) + '.\nСтало строк = ' + str(finish_count) + \
                        ".\nКол-во дней хранения = {count_days}".format(count_days=count_days)
                    self.result_work = True
                    return
            else:
                common.write_log_db('ERROR', self.source, str(answer) + ";\nПовторим через 5 минут",
                                    td=time.time() - self.t0)


# ClearLogs('clear_logs').start()
# while True:
#     time.sleep(5)