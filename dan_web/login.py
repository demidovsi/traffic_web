from flask import render_template, request, flash, redirect, session, send_file
import json
import common
import config
from common import exist, get, write_log_db, add
import users_session
import colors


def prepare_form(request):
    if request.method == 'POST':
        ok, user_id = common.make_login(request.form.get('user_name'), request.form.get('password'),
                                        common.st_address(request))
        if not ok:
            return 'login.html', ''
        if not exist(user_id) or 'visible' not in get(user_id, 'rights'):
            flash('Для пользователя {user_name} нет доступа к базе данных'.format(
                user_name=get(user_id, 'user_name')))
            return 'login.html', ''
        # записать в public login пользователя
        country, city = common.get_guest(user_id, common.st_address(request))
        st = country
        if country:
            st = ' ({country} {city})'.format(country=country, city=city)
        if common.ip_good(request):
            write_log_db('USER', 'LOGIN', 'Вход пользователя на WEB сайт' + common.st_system(request) +
                         ' [' + request.environ.get('HTTP_USER_AGENT') + ']', file_name=common.st_address(request) + st,
                         law_id=request.form.get('user_name'))
        else:
            country, city, ok_ip = common.define_guest(common.st_address(request), check_simple=False)
            if not ok_ip:
                country = city = ''
        time_zone = int(request.form.get('time_now').split('GMT')[1].split('(')[0][:3])
        users_session.users.load()
        add(user_id, 'user_address', get(user_id, 'user_name') + '; ' + common.st_address(request) + '; system=' +
            common.st_system(request) + ' ' + str(country) + ' ' + str(city))
        add(user_id, 'country', country)
        add(user_id, 'city', city)
        add(user_id, 'time_zone', time_zone)
        add(user_id, 'theme', request.form.get('select_theme'))

        upr = {}
        upr['user_name'] = get(user_id, 'user_name')
        upr['user_id'] = user_id
        upr['schema'] = get(user_id, 'schema')
        upr['admin'] = 'admin' in get(user_id, 'rights')
        upr['theme'] = request.form.get('select_theme')
        upr['colors'] = colors.colors[get(user_id, 'theme')]
        # upr['menus'] = common.get_menus(user_id)
        upr['time_zone'] = get(user_id, 'time_zone')
        add(user_id, 'upr', upr)

        users_session.users.save()

        # зафиксировать лог пользователя
        common.fix_login(user_id, common.st_address(request),
                         'Login ({user_name})'.format(user_name=get(user_id, 'user_name')))

        if 'page_for_return' in session:
            st = session['page_for_return']
            session.pop('page_for_return')
            return '', st + user_id + '/'
        else:
            return '', '/logs/{user_id}/'.format(user_id=user_id)
    return 'login.html', ''
