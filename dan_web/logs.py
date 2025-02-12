from flask import flash
import config
import common
from common import add, get, default, find_user, exist, to_string, clear
import datetime
import json

array_default = [
    {'key': 'scroll', 'value': 0},
    {'key': 'search', 'value': ''},
    {'key': 'row_count', 'value': 100},
    {'key': 'page', 'value': 1},
    {'key': 'st_date', 'value': common.st_today()},
    {'key': 'do_update', 'value': True},
    {'key': 'switch', 'value': 'one_day'}
]

def get_where(user_id, answer):
    where = common.get_where(answer['search'], ['level', 'source', 'comment', 'law_id', 'file_name'])
    if answer['switch'] == 'one_day':
        year = answer['year']
        month = answer['month']
        day = answer['day']
        date_begin = common.get_date_sql([year, month, day], get(user_id, 'time_zone'))
        t = datetime.datetime(year, month, day) + datetime.timedelta(days=1)
        date_end = common.get_date_sql([t.year, t.month, t.day], get(user_id, 'time_zone'))
        where = where + ' and ' if where != '' else where
        where = where + "at_date_time>='{date_begin}' and at_date_time<'{date_end}'".format(
            date_begin=date_begin, date_end=date_end)
    return where


def get_count_log(user_id, answer):
    try:
        url = 'v1/content/count/{schema}/v_logs?where={where}'.format(
            schema=config.SCHEMA, where=get_where(user_id, answer))
        ans, result, status_code = common.send_rest(url)
        if result:
            return int(ans)
        else:
            flash(str(ans), 'warning')
            return 0
    except Exception as er:
        flash('Ошибка: ' + f"{er}", 'warning')
        return 0


def load_inform(user_id, answer):
    row_count = int(answer['row_count'])
    page_from = int(answer['page'])
    try:
        url = 'v2/select/{schema}/v_logs'.format(schema=config.SCHEMA)
        st = get_where(user_id, answer)
        if st != '':
            url = url + '?where=' + st + ' order by id desc'
        else:
            url = url + '?order=order by id desc'
        url = url + '&row_count=' + str(row_count) + '&row_from=' + str(row_count * (max(1, page_from) - 1))
        ans, result, status_code = common.send_rest(url)
        if result:
            ans = json.loads(ans)
            for unit in ans:
                unit['td'] = common.get_duration(unit['td'])
                unit['at_date_time'] = datetime.datetime.strptime(unit['at_date_time'], "%Y-%m-%dT%H:%M:%S.%f")
                # unit['comment'] = common.translate_from_base(unit['comment'])
                # unit['file_name'] = common.translate_from_base(unit['file_name'])
                unit['comment'] = unit['comment']
                unit['file_name'] = unit['file_name']
            return ans
        else:
            flash(str(ans), 'warning')
            return []
    except Exception as er:
        flash('Ошибка: ' + f"{er}", 'warning')
        return []


def define_pages_data(user_id, answer):
    count = get_count_log(user_id, answer)
    answer['count'] = 0 if count is None else count
    common.define_pages(answer)
    answer['data'] = load_inform(user_id, answer)


def prepare_form(user_id, request):
    answer = dict()
    st = common.init_form(user_id, request, '/logs/')
    if st:
        answer['redirect'] = st
        return answer
    common.default_form(user_id, array_default, answer, 'log_')
    year, month, day = answer['st_date'].split('-')
    if request.method == 'POST':
        common.define_param_for_page(request, answer)
        answer['do_update'] = 'do_update' in request.form
        if 'dt_start' in request.form and request.form.get('dt_start') != answer['st_date']:
            try:
                year, month, day = request.form.get('dt_start').split('-')
                answer['st_date'] = common.get_st_date(year, month, day)
                answer['do_update'] = True
                answer['scroll'] = 0
            except:
                pass
        if 'one_day' in request.form and answer['switch'] != 'one_day':
            answer['switch'] = 'one_day'
            answer['do_update'] = answer['st_date'] == common.st_today()
            answer['scroll'] = 0
        if 'all_days' in request.form:
            answer['switch'] = 'all_days'
        if 'current_day' in request.form:
            year =datetime.date.today().year
            month = datetime.date.today().month
            day = datetime.date.today().day
            answer['st_date'] = common.get_st_date(year, month, day)
            answer['do_update'] = True
            answer['scroll'] = 0
        elif 'left' in request.form:
            year, month, day = common.calc_day(year, month, day, -1)
            answer['st_date'] = common.get_st_date(year, month, day)
            answer['do_update'] = answer['st_date'] == common.st_today()
            answer['scroll'] = 0
        elif 'right' in request.form:
            year, month, day = common.calc_day(year, month, day, 1)
            answer['st_date'] = common.get_st_date(year, month, day)
            answer['do_update'] = answer['st_date'] == common.st_today()
            answer['scroll'] = 0
    else:
        common.write_quest(user_id, request, 'Log')

    answer['is_today'] = answer['st_date'] == common.st_today()
    answer['st_date'] = common.get_st_date(year, month, day)
    answer['year'] = int(year)
    answer['month'] = int(month)
    answer['day'] = int(day)
    define_pages_data(user_id, answer)
    if answer['switch'] == 'all_days':
        format_dt = "HH:mm:ss D.M.Y"
    else:
        format_dt = 'HH:mm:ss'
    answer['format_dt'] = format_dt
    answer['title_search'] = 'Поиск (фильтрация) производится по колонкам OPERATION, SOURCE, LAW_ID, COMMENT, MESSAGE'
    answer['title'] = 'Содержимое лог файла'
    # для возврата в форму из других форм
    common.save_form(user_id, array_default, answer, 'log_')
    return answer
