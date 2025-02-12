from flask import flash
import config
import common
from common import add, get, default, find_user, exist, to_string, clear
import datetime
import json

array_default = [
    {'key': 'scroll', 'value': 0},
    {'key': 'search', 'value': ''},
    {'key': 'row_count', 'value': 10},
    {'key': 'page', 'value': 1},
    {'key': 'count', 'value': 100},
    {'key': 'st_date', 'value': common.st_today()},
    {'key': 'switch', 'value': 'one_day'},
    {'key': 'list_rss', 'value': []},
    {'key': 'select_rss', 'value': 0},
    {'key': 'themes', 'value': []},
    {'key': 'select_theme', 'value': 0},
    {'key': 'select_lang', 'value': 'ru'},
    {'key': 'global_count', 'value': 0},
    {'key': 'format_dt', 'value': "HH:mm:ss D.M.Y"},
    {'key': 'languages', 'value': ['ru', 'en', 'he']},
]


def load_list_rss(answer):
    """
        чтение списка сайтов с RSS
    """
    answer['list_rss'] = []
    url = 'v2/entity/values?app_code={schema}&object_code=rss_list&column_order=id desc'.format(schema=config.SCHEMA)
    ans, is_ok, status = common.send_rest(url, params={"columns": "id, sh_name, lang"})
    if not is_ok:
        flash(str(ans), 'warning')
        return False
    else:
        answer['list_rss'] = json.loads(ans)
        answer['list_rss'].insert(0, {'id': 0, 'sh_name': '', 'lang': ''})
        return True


def load_themes(answer):
    """
        чтение списка сайтов с RSS
    """
    answer['themes'] = []
    url = 'v2/entity/values?app_code={schema}&object_code=rss_themes'.format(schema=config.SCHEMA)
    ans, is_ok, status = common.send_rest(url)
    if not is_ok:
        flash(str(ans), 'warning')
        return False
    else:
        answer['themes'] = json.loads(ans)
        # for data in answer['themes']:
            # data['value'] = common.translate_from_base(data['value']).strip()
            # data['value'] = data['value'].strip()
        answer['themes'].insert(0, {'id': 0, 'sh_name': '', 'value': ''})
        return True


def get_global_count(answer):
    answer['global_count'] = None
    url = 'v1/count/{schema}/nsi_rss_history'.format(schema=config.SCHEMA)
    ans, is_ok, status = common.send_rest(url)
    if not is_ok:
        flash(str(ans), 'warning')
        return False
    else:
        answer['global_count'] = ans
        return True


def get_where(user_id, answer):
    where = common.get_where(answer['search'],
                             ['name_theme', 'public_date::text', 'title_ru', 'description_ru',
                              'id::text', 'name_rss', 'title_en', 'description_en', 'author'])
    if answer['switch'] == 'one_day':
        year = answer['year']
        month = answer['month']
        day = answer['day']
        date_begin = common.get_date_sql([year, month, day], get(user_id, 'time_zone'))
        t = datetime.datetime(year, month, day) + datetime.timedelta(days=1)
        date_end = common.get_date_sql([t.year, t.month, t.day], get(user_id, 'time_zone'))
        where = where + ' and ' if where != '' else where
        where = where + "public_date>='{date_begin}' and public_date<'{date_end}'".format(
            date_begin=date_begin, date_end=date_end)
    if answer['select_theme']:
        where = where + ' and ' if where != '' else where
        where = where + "theme={theme}".format(theme=answer['select_theme'])
    if answer['select_rss']:
        where = where + ' and ' if where != '' else where
        where = where + "rss={rss}".format(rss=answer['select_rss'])
    return where


def get_count(user_id, answer):
    answer['count'] = 0
    try:
        url = 'v1/content/count/{schema}/v_nsi_rss_history?where={where}'.format(
            schema=config.SCHEMA, where=get_where(user_id, answer))
        ans, result, status_code = common.send_rest(url)
        if result:
            answer['count'] = int(ans)
        else:
            flash(str(ans), 'warning')
    except Exception as er:
        flash('Ошибка: ' + f"{er}", 'warning')


def load_inform(user_id, answer):
    answer['data'] = []
    row_count = int(answer['row_count'])
    page_from = int(answer['page'])
    lang = '_' + answer['select_lang']
    try:
        url = 'v2/select/{schema}/v_nsi_rss_history'.format(schema=config.SCHEMA)
        st = get_where(user_id, answer)
        if st != '':
            url = url + '?where=' + st + ' order by public_date desc, id desc'
        else:
            url = url + '?order=order by public_date desc'
        url = url + '&row_count=' + str(row_count) + '&row_from=' + str(row_count * (max(1, page_from) - 1))
        ans, result, status_code = common.send_rest(url)
        if result:
            ans = json.loads(ans)
            for unit in ans:
                data = {'id': unit['id'], 'name_theme': unit['name_theme'], 'error_translator': unit['error_translator'],
                        'url': unit['url'], 'author': unit['author'], 'name_rss': unit['name_rss'],
                        'file': unit['file'], 'lang': unit['lang']}
                data['public_date'] = unit['public_date'].split('.')[0]
                if data['public_date']:
                    data['at_date_time'] = datetime.datetime.strptime(unit['public_date'], "%Y-%m-%dT%H:%M:%S")
                else:
                    data['at_date_time'] = ''
                data['public_date'] = data['public_date'].replace('T', ' ')
                # data['title'] = common.translate_from_base(unit['title'+lang])
                # data['social_title'] = common.translate_from_base(unit['social_title'+lang])
                # data['description'] = common.translate_from_base(unit['description'+lang])
                data['title'] = unit['title'+lang]
                data['social_title'] = unit['social_title'+lang]
                data['description'] = unit['description'+lang]
                answer['data'].append(data)
        else:
            flash(str(ans), 'warning')
    except Exception as er:
        flash('Ошибка: ' + f"{er}", 'warning')


def check_show(user_id, request, answer):
    for key in request.form.keys():
        if 'id_' in key:
            new_id, new_id = key.split('id_')
            add(user_id, 'page_for_return', '/news/{user_id}'.format(user_id=user_id))
            add(user_id, 'text_for_return', 'Назад в список новостей')
            answer['redirect'] = '/new/{user_id}/{new_id}/'.format(user_id=user_id, new_id=new_id)
            return True


def prepare_form(user_id, request):
    answer = dict()
    st = common.init_form(user_id, request, '/news/')
    if st:
        answer['redirect'] = st
        return answer
    common.default_form(user_id, array_default, answer, 'news_')
    year, month, day = answer['st_date'].split('-')
    if request.method == 'POST':
        common.define_param_for_page(request, answer)
        if 'dt_start' in request.form:
            try:
                year, month, day = request.form.get('dt_start').split('-')
            except:
                pass
        if 'one_day' in request.form:
            answer['switch'] = 'one_day'
        if 'all_days' in request.form:
            answer['switch'] = 'all_days'
        if 'current_day' in request.form:
            year =datetime.date.today().year
            month = datetime.date.today().month
            day = datetime.date.today().day
        elif 'left' in request.form:
            year, month, day = common.calc_day(year, month, day, -1)
        elif 'right' in request.form:
            year, month, day = common.calc_day(year, month, day, 1)
        if 'select_rss' in request.form:
            answer['select_rss'] = int(request.form.get('select_rss'))
        if 'select_theme' in request.form:
            answer['select_theme'] = int(request.form.get('select_theme'))
        if 'select_lang' in request.form:
            answer['select_lang'] = request.form.get('select_lang')
        if check_show(user_id, request, answer):  # проверить необходимость вывода новости
            common.save_form(user_id, array_default, answer, 'news_')
            return answer
    else:
        common.write_quest(user_id, request, 'News')

    answer['st_date'] = common.get_st_date(year, month, day)
    answer['year'] = int(year)
    answer['month'] = int(month)
    answer['day'] = int(day)

    if len(answer['list_rss']) == 0:
        load_list_rss(answer)
    if len(answer['themes']) == 0:
        load_themes(answer)
    get_global_count(answer)
    get_count(user_id, answer)
    common.define_pages(answer)
    load_inform(user_id, answer)
    answer['title'] = 'Лента новостей из списка сайтов'
    # для возврата в форму из других форм
    common.save_form(user_id, array_default, answer, 'news_')
    return answer
