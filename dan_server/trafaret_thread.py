import threading
import time
import common as cd


class TrafaretThread(threading.Thread):
    source = ''
    code_period = ''
    code_function = ''
    description = ''
    token = ''
    lang = 'ru'
    time_begin = None
    from_time = None
    next_time = 0
    par = list()
    finish_text = ''
    law_id = ''
    page = None
    first_cycle = True
    t0 = None
    wait_for_error = 300
    result_work = False
    text_greetings = ''

    def __init__(self, code_function):
        threading.Thread.__init__(self)
        self.daemon = True
        self.source = code_function
        self.code_period = 'period'
        self.code_function = code_function
        self.description = f'Поток "Лента новостей {code_function}"'

    def make_next_time(self, value_minute, from_time):
        self.from_time = from_time
        self.next_time = from_time + value_minute * 60

    def define_next_time(self):
        if self.next_time is None or self.next_time == 0:
            self.next_time = time.time()
        else:
            self.make_next_time(cd.get_value_config_param(self.code_period, self.par), self.from_time)

    def analysis_changing_parameters(self, answer):
        if self.first_cycle:
            self.par = answer
        st_difference, st_param_work = cd.get_difference_config_params(self.par, answer)
        self.par = answer
        if self.first_cycle:
            cd.write_log_db('Параметры работы', self.source, cd.translate_from_base(st_param_work.strip()),
                            file_name=cd.get_computer_name())
        if st_difference != '' and not self.first_cycle:
            cd.write_log_db(
                'Изменение параметров', self.source, st_difference.strip(),
                file_name=cd.get_computer_name())
            last_time = self.next_time
            self.define_next_time()
            if last_time != self.next_time:
                cd.write_log_db(
                    'Следующая активность', self.source,
                    'Старая планируемая активность в ' + time.asctime(time.gmtime(last_time)) + '\n' +
                    'Новая планируемая активность в ' + time.asctime(time.gmtime(self.next_time)),
                    file_name=cd.get_computer_name())
        self.first_cycle = False

    def work(self):
        if cd.get_value_config_param('active', self.par) != 1:
            return False

    def get_duration(self):
        return cd.get_duration(time.time() - self.time_begin)

    def make_login(self):
        ans, is_ok, self.token, lang = cd.login_admin()
        return is_ok

    def run(self):
        cd.write_log_db('LOAD', self.source, self.text_greetings if self.text_greetings else self.description,
                        file_name=cd.get_computer_name())
        self.from_time = time.time()
        self.time_begin = time.time()
        self.next_time = time.time()
        while True:
            self.finish_text = ''
            self.law_id = ''
            self.page = None
            self.t0 = time.time()
            answer = cd.load_config_params(self.code_function)
            if answer is not None:
                self.analysis_changing_parameters(answer)  # анализ изменения параметров и реакция на это
                if time.time() >= self.next_time:  # подошло время работать
                    last_time = self.next_time
                    self.work()
                    if not self.result_work:
                        self.next_time = last_time + self.wait_for_error
                    else:
                        self.make_next_time(cd.get_value_config_param(self.code_period, self.par), self.next_time)
                        while self.next_time < time.time():
                            self.from_time = self.next_time
                            self.define_next_time()
                        st = 'Тайм-аут'+cd.get_duration(cd.get_value_config_param(self.code_period, self.par) * 60) + \
                             ' до ' + time.asctime(time.gmtime(self.next_time))
                        cd.write_log_db('Finish', self.source, st + '.\n' + self.finish_text, td=time.time()-self.t0,
                                        law_id=self.law_id, page=self.page, file_name=cd.get_computer_name())
            time_out = 60 - (time.time() - self.t0)
            if time_out <= 0:
                time_out = 60
            time.sleep(time_out)
