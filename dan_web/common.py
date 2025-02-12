import users_session
import config
from flask import session
from flask import flash
import json
import requests
from requests.exceptions import HTTPError
import base64
import os
import time
import datetime

app_lang = 'ru'
current_path = ''


def exist(user_id):
    return users_session.users.exist(user_id)


def add(user_id, key, value):
    users_session.users.add(user_id, key, value)


def get(user_id, key):
    return users_session.users.get(user_id, key)


def default(user_id, key, value):
    users_session.users.default(user_id, key, value)


def clear(user_id):
    return users_session.users.clear(user_id)


def to_string():
    return users_session.users.to_string()


def find_user(user_id, req):
    return users_session.users.find_user(user_id, req)


def decode(key, enc):
    dec = []
    enc = base64.urlsafe_b64decode(enc).decode()
    for i in range(len(enc)):
        key_c = key[i % len(key)]
        dec_c = chr((256 + ord(enc[i]) - ord(key_c)) % 256)
        dec.append(dec_c)
    return "".join(dec)


def encode(key, text):
    enc = []
    for i in range(len(text)):
        key_c = key[i % len(key)]
        enc_c = chr((ord(text[i]) + ord(key_c)) % 256)
        enc.append(enc_c)
    return base64.urlsafe_b64encode("".join(enc).encode()).decode()


def login_admin():
    result = False
    token_admin = ''
    lang_admin = ''
    txt_z = {"login": "superadmin", "password": decode('abcd', config.kirill), "rememberMe": True}
    try:
        headers = {"Accept": "application/json"}
        response = requests.request(
            'POST', config.URL + 'v1/login', headers=headers,
            json={"params": txt_z}
            )
    except HTTPError as err:
        txt = f'HTTP error occurred: {err}'
    except Exception as err:
        txt = f'Other error occurred: : {err}'
    else:
        try:
            txt = response.text
            result = response.ok
            if result:
                js = json.loads(txt)
                if "accessToken" in js:
                    token_admin = js["accessToken"]
                    token_admin = decode(decode('abcd', config.kirill), token_admin)
                    token_admin = json.loads(token_admin)
                if 'lang' in js:
                    lang_admin = js['lang']
            else:
                token = None
                return txt, result, token
        except Exception as err:
            txt = f'Error occurred: : {err}'
    return txt, result, token_admin, lang_admin


def send_rest(mes, directive="GET", params=None, lang='', token_user=None):
    js = {}
    if token_user is not None:
        # js['token'] = token_user
        js['token'] = encode(decode('abcd', config.kirill), json.dumps(token_user))
    if lang == '':
        lang = app_lang
    if directive == 'GET' and 'lang=' not in mes:
        if '?' in mes:
            mes = mes + '&lang=' + lang
        else:
            mes = mes + '?lang=' + lang
    else:
        js['lang'] = lang   # код языка пользователя
    if params:
        if type(params) is not str:
            params = json.dumps(params, ensure_ascii=False)
        js['params'] = params  # дополнительно заданные параметры
    try:
        headers = {"Accept": "application/json"}
        response = requests.request(directive, config.URL + mes.replace(' ', '+'), headers=headers, json=js)
    except HTTPError as err:
        txt = f'HTTP error occurred: {err}'
        return txt, False, None
    except Exception as err:
        txt = f'Other error occurred: {err}'
        return txt, False, None
    else:
        return response.text, response.ok, '<' + str(response.status_code) + '> - ' + response.reason


def write_log_db(level, src, msg, page=None, file_name='', law_id='', td=None):
    if page is None or page == '':
        page = 'NULL'
    if law_id is None:
        law_id = ''
    if file_name is None:
        file_name = ''
    td = 'NULL' if td is None else "%.1f" % td if type(td) == float else td
    st = "insert into {schema}.logs (level, source, comment, page, law_id, file_name, td) values " \
         "('{level}', '{source}', '{comment}', {page}, '{law_id}', '{file_name}', {td})".format(
            schema=config.SCHEMA, level=level, source=src,
            comment=msg.replace("'", '"'), page=page, law_id=law_id, file_name=file_name, td=td)
    txt, ok, token, lang = login_admin()
    if ok:
        answer, ok, status = send_rest('v1/NSI/script/execute', 'PUT', st, lang=lang, token_user=token)
        if not ok:
            flash(str(answer), 'warning')


def st_system(request):
    try:
        return request.headers.environ['HTTP_SEC_CH_UA_PLATFORM']
    except Exception as err:
        return f"{err}"


def st_address(request):
    try:
        if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
            return request.remote_addr
        else:
            return request.environ['HTTP_X_FORWARDED_FOR']
    except Exception as err:
        return f"{err}"


def ip_good(request):
    ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    if ip != '127.0.0.1':
        return ip


def login(e_mail, password, ip_address):
    result = False
    txt_z = {"login": e_mail, "password": password, "rememberMe": True, "category": "sozd"}
    try:
        headers = {"Accept": "application/json"}
        response = requests.request(
            'POST', config.URL + 'v1/login', headers=headers,
            json={"params": txt_z}
            )
    except HTTPError as err:
        txt = f'HTTP error occurred: {err}'
    except Exception as err:
        txt = f'Other error occurred: : {err}'
    else:
        try:
            txt = response.text
            result = response.ok
            if result:
                js = json.loads(txt)
                token_db = ''
                if "accessToken" in js:
                    token_db = js["accessToken"]

                token = decode(decode('abcd', config.kirill), token_db)
                token = json.loads(token)
                rights = ''
                users_session.users.load()
                for key in token.keys():
                    if key == '***':
                        rights = 'visible, admin'
                    elif token[key] != 'GET' and token[key] != '' and 'visible' in token[key]:
                        rights = token[key]
                        break
                user_id = users_session.users.id_by_name(ip_address)
                if user_id is None:
                    user_id = os.urandom(20).hex()
                    users_session.users.add_user(user_id)
                users_session.users.clear(user_id)
                users_session.users.add(user_id, "user_name", e_mail)
                users_session.users.add(user_id, "token", token_db)
                users_session.users.add(user_id, "rights", rights)
                users_session.users.add(user_id, "select_group", "")

                if "expires" in js:
                    users_session.users.add(user_id, "expires", time.mktime(
                        time.strptime(js["expires"], '%Y-%m-%d %H:%M:%S')))
                if 'lang' in js:
                    users_session.users.add(user_id, "app_lang", js['lang'])
                if 'role' in js:
                    users_session.users.add(user_id, "user_role", js['role'])
                answer, ok, token_admin, lang_admin = login_admin()
                if ok:
                    add(user_id, 'token', token_admin)
                    add(user_id, 'lang', lang_admin)

                users_session.users.save()
                return txt, result, user_id
            else:
                return txt, result, ''
        except Exception as err:
            txt = f'Error occurred: : {err}'
    return txt, result, ''


def make_login(user_name, password, ip_address):
    try:
        txt, result, user_id = login(user_name, password, ip_address)
        if not result:
            try:
                txt = json.loads(txt)
                flash('Error login : ' + txt['detail'] + '; user_name=' + user_name, 'warning')
            except Exception as er:
                flash('Error login : ' + txt + '; user_name=' + user_name + ': ' + f"{er}", 'warning')
        return result, user_id
    except Exception as er:
        print('ERROR', 'make_login', f"{er}")
        return False, ''


def get_guest(user_id, ip_text):
    country = city = ''
    if ip_text != '127.0.0.1':
        answer, ok, status_result = send_rest("v1/content/{schema}/guests?where=sh_name='{ip}'".format(
            schema=config.SCHEMA, ip=ip_text))
        if ok:
            answer = json.loads(answer)
            if len(answer) == 0:  # записать нового пользователя
                country, city, ok_ip = define_guest(ip_text)
                if not ok_ip:
                    country = city = ''
                txt = "null, '" + ip_text + "', '" + country + "', '" + city + "'"
                answer, ok, status_result = send_rest('v1/object/{schema}/guests?param_list={param_list}'.format(
                    schema=config.SCHEMA, param_list=txt), 'PUT', token_user=get(user_id, 'token'))
                if not ok:
                    print('get_quest', str(answer))
            else:
                country = answer[0]['country']
                city = answer[0]['city']
    add(user_id, 'country', country)
    add(user_id, 'city', city)
    return country, city


def define_guest(ip_text, check_simple=True):
    if check_simple and ip_text == '127.0.0.1':
        return '', '', True
    headers = {"Accept": "application/json"}
    try:
        response = requests.request('GET', 'http://ip-api.com/json/{ip}?lang=ru'.format(ip=ip_text), headers=headers)
    except HTTPError as err:
        txt = f'HTTP error occurred: {err}'
        print('ERROR', 'Ошибка запроса', txt)
        return txt, '', False
    try:
        if response.ok:
            answer = json.loads(response.text)
            return answer['country'], answer['city'], True
        else:
            print('ERROR', response.text)
            return response.text.replace('\\n', '\n'), '', False
    except Exception as err:
        return f"{err}", '', False


def fix_login(user_id, ip, value):
    if ip.strip() == '127.0.0.1':
        return
    # фиксация логина (текст в value) пользователя
    answer, ok, status_result = send_rest("v1/content/{schema}/guests?where=sh_name='{ip}'".format(
        schema=config.SCHEMA, ip=ip))
    if ok:
        answer = json.loads(answer)
        if len(answer) != 0:  # есть пользователь
            guest_id = answer[0]['id']
            url = "v1/MDM/his/{schema}/guests/{param}/{obj_id}?value='{value}'".format(
                schema=config.SCHEMA, param='page', obj_id=guest_id, value=value)
            answer, ok, token_admin, lang_admin = login_admin()
            answer, ok, status_result = send_rest(url, 'POST', token_user=token_admin)
            if not ok:
                print('write_quest', str(answer))


def init_form(user_id, request, endpoint):
    users_session.users.load()
    user_id = find_user(user_id, request)
    if not exist(user_id):
        session['page_for_return'] = endpoint
        users_session.users.save()
        return '/login/'


def write_quest(user_id, request, name_page):
    txt = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    if txt == '127.0.0.1':
        return '', ''
    guest_id = None
    country = ''
    city = ''
    answer, ok, status_result = send_rest("v1/content/{schema}/guests?where=sh_name='{ip}'".format(
        schema=config.SCHEMA, ip=txt))
    if ok:
        answer = json.loads(answer)
        if len(answer) == 0:  # записать нового пользователя
            country, city, ok_ip = define_guest(txt)
            if not ok_ip:
                country = city = ''
            txt = "null, '" + txt + "', '" + country + "', '" + city + "'"
            answer, ok, status_result = send_rest('v1/object/{schema}/guests?param_list={param_list}'.format(
                schema=config.SCHEMA, param_list=txt), 'PUT', token_user=get(user_id, 'token'))
            if not ok:
                print('write_quest', str(answer))
            else:
                guest_id = int(answer.replace('"', ''))
        else:
            guest_id = answer[0]['id']
            country = answer[0]['country']
            city = answer[0]['city']
            if country is None or country == '' or city is None or city == '':
                country, city, ok_ip = define_guest(txt)
                txt = str(guest_id) + ", '" + txt + "', '" + country + "', '" + city + "'"
                send_rest('v1/object/{schema}/guests?param_list={param_list}'.format(
                    schema=config.SCHEMA, param_list=txt), 'PUT', token_user=get(user_id, 'token'))
        if guest_id is not None:
            url = "v1/MDM/his/{schema}/guests/{param}/{obj_id}?value='{value}'".format(
                schema=config.SCHEMA, param='page', obj_id=guest_id, value=name_page)
            answer, ok, status_result = send_rest(url, 'POST', token_user=get(user_id, 'token'))
            if not ok:
                print('write_quest', str(answer))
    else:
        print('write_quest', str(answer))
    return country, city


def write_log(source, user_id, request, law_id='', mes='Вход пользователя на страницу'):
    ip = ip_good(request)
    if ip:
        write_quest(user_id, request, source)
        write_log_db('USER', source, mes, law_id=law_id, file_name=get(user_id, 'user_address'))


def default_form(user_id, array, answer, prefix):
    for data in array:
        default(user_id, prefix + data['key'], data['value'])
        answer[data['key']] = get(user_id, prefix + data['key'])


def save_form(user_id, array, answer, prefix):
    for data in array:
        add(user_id, prefix + data['key'], answer[data['key']])


def define_param_for_page(request, answer):
    last_row_count = answer['row_count']
    answer['change_page'] = False
    answer['change_sort'] = False
    if 'scroll' in request.form and request.form.get('scroll'):
        answer['scroll'] = int(request.form.get('scroll'))
    if 'page' in request.form:
        answer['change_page'] = answer['page'] != int(request.form.get('page'))
        answer['page'] = int(request.form.get('page'))
    if 'row_count' in request.form:
        answer['row_count'] = int(request.form.get('row_count'))

    if last_row_count != answer['row_count']:  # сменилось количество строк в таблице
        # answer['page'] = last_page * last_row_count // answer['row_count'] + 1
        # if not answer['change_page']:
        answer['page'] = 1
        answer['scroll'] = 0
        answer['change_page'] = True

    if 'next' in request.form:
        answer['page'] = answer['page'] + 1
        answer['scroll'] = 0
    if 'prev' in request.form:
        answer['page'] = answer['page'] - 1
        answer['scroll'] = 0
    if 'search' in request.form:
        answer['search'] = request.form.get('search')
    for key in request.form.keys():
        if 'page(' in key:
            st2, st2 = key.split('page(')
            if st2 != '...)':
                answer['page'] = int(st2.split(')')[0])
                answer['scroll'] = 0
            break
    if 'sort' in request.form:
        if answer['selected_sort'] != request.form.get('sort'):
            answer['change_sort'] = True
        answer['selected_sort'] = request.form.get('sort')
        # answer['page'] = 1
    if 'sort_trend0' in request.form:
        if answer['sort_trend'] != 0:
            answer['change_sort'] = True
        answer['sort_trend'] = 0
        # answer['page'] = 1
    if 'sort_trend1' in request.form:
        if answer['sort_trend'] != 1:
            answer['change_sort'] = True
        answer['sort_trend'] = 1


def define_pages(answer):
    count = answer['count'] if 'count' in answer else None
    answer['count'] = 0 if count is None else count
    answer['page_count'] = (answer['count'] + int(answer['row_count']) - 1) // int(answer['row_count'])
    answer['page'] = max(1, answer['page'])
    answer['page'] = min(answer['page'], max(1, answer['page_count']))
    answer['page'] = min(answer['page'], (answer['count'] + answer['row_count'] - 1) // answer['row_count'])
    answer['array_pages'] = define_button(answer['page_count'], answer['page'])
    answer['first'] = str((answer['page'] - 1) * int(answer['row_count']) + 1) if answer['count'] != 0 else '0'
    last = answer['page'] * int(answer['row_count']) if answer['count'] != 0 else 0
    answer['last'] = str(min(last, answer['count']))


def define_button(last_page, page_from):
    array_pages = list()
    length = 5
    for i in range(length):
        array_pages.append({})
    try:
        q = last_page - 2
        if q < 5:
            for i in range(length):
                if i < q:
                    array_pages[i]['visible'] = True
                    array_pages[i]['page'] = i + 2
                    array_pages[i]['text'] = 'page(' + str(i+2) + ')'
                else:
                    array_pages[i]['visible'] = False
        else:
            array_pages[0]['text'] = '...'
            array_pages[-1]['text'] = '...'
            if page_from <= 4:
                pages = ['2', '3', '4', '5', '...']
            else:
                if page_from > last_page - 4:
                    pages = ['...', str(last_page - 4), str(last_page - 3), str(last_page - 2), str(last_page - 1)]
                else:
                    pages = ['...', str(page_from - 1), str(page_from), str(page_from + 1), '...']
            for i in range(length):
                array_pages[i]['visible'] = True
                array_pages[i]['text'] = 'page(' + pages[i] + ')'
                if pages[i] == '...':
                    array_pages[i]['page'] = pages[i]
                else:
                    array_pages[i]['page'] = int(pages[i])
        if last_page > 1:
            array_pages.append({'visible': True, "page": last_page, "text": "page(" + str(last_page) + ")"})
    except Exception as er:
        print('table', 'define_button', f"{er}")
    return array_pages


def get_where(search, columns):
    where = ''
    if search:
        array_search = search.split('&')
        for unit in array_search:
            list_search = unit.split(';')
            where_or = ''
            for search in list_search:
                where_or = where_or + ' or ' if where_or != '' else where_or
                st_column = ''
                for column in columns:
                    st_column = st_column + ' or ' if st_column != '' else st_column
                    st_column += (column + " ilike N'%{search}%'")
                where_or = where_or + "(" + st_column.format(search=search.strip()) + ")"
            if where_or != '':
                where = where + ' and ' if where != '' else where
            where += '(' + where_or + ')'
    return where


def get_date_sql(st, time_zone):
    if type(st) == list:
        year = st[0]
        month = st[1]
        day = st[2]
    else:
        year, month, day = st.split('-')
    date = datetime.datetime(int(year), int(month), int(day))
    dt = date - datetime.timedelta(hours=time_zone if time_zone else 0)
    return '{year}-{month}-{day} {hour}:{minute}:{second}'.format(
        year=dt.year, month=dt.month, day=dt.day, hour=dt.hour, minute=dt.minute, second=dt.second)


def st_today():
    return str(time.gmtime().tm_year) + '-' + str(time.gmtime().tm_mon).rjust(2, '0') + '-' + \
           str(time.gmtime().tm_mday).rjust(2, '0')


def translate_from_base(st):
    if st is None:
        return ''
    st = st.replace('~A~', '(').replace('~B~', ')').replace('~a1~', '@').replace('~LF~', '\n')
    st = st.replace('~a2~', ',').replace('~a3~', '=').replace('~a4~', '"').replace('~a5~', "'")
    st = st.replace('~a6~', ':').replace('~b1~', '/').replace('~b2~', '&').replace('~R~', '\r')
    return st


def get_duration(td):
    result = ''
    if td is None:
        return result
    if '<' in str(td):
        return str(td) + ' sec'
    tdr = int(td + 0.5)
    if tdr == 0:
        return '< 0.5 sec'
    if tdr >= 86400:
        result = str(tdr // 86400) + ' day'
        if tdr // 86400 != 1:
            result = result + 's'
        tdr = tdr % 86400
    if tdr // 3600 == 0:
        result = result + " {minute:02}:{second:02}".format(
            minute=tdr % 3600 // 60, second=tdr % 3600 % 60)
    else:
        result = result + " {hour:02}:{minute:02}:{second:02}".format(
            hour=tdr // 3600, minute=tdr % 3600 // 60, second=tdr % 3600 % 60)
    return result


def get_st_date(year, month, day):
    return str(year) + '-' + str(month).rjust(2, '0') + '-' + str(day).rjust(2, '0')


def calc_day(year, month, day, delta):
    dt = datetime.date(int(year), int(month), int(day)) + datetime.timedelta(days=delta)
    return dt.year, dt.month, dt.day
