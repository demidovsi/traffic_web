import os
import datetime
from flask import Flask, render_template, request, redirect
import users_session
import config
import common
from common import get, add
import login as c_login
import road as c_road
import big_query
import language
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(20).hex()
app.config['CSRF_ENABLED'] = True
app.permanent = True
app.permanent_session_lifetime = datetime.timedelta(hours=24)


@app.route('/')
def index():
    return redirect('/login/')


@app.route('/login/', methods=('GET', 'POST'))
def login():
    st_html, st_redirect = c_login.prepare_form(request)
    if st_html:
        return render_template(st_html, languages=config.languages, select_language='en')
    else:
        return redirect(st_redirect)


@app.route('/road/<user_id>/', methods=('GET', 'POST'))
def road(user_id):
    par = c_road.prepare_form(user_id, request)
    users_session.users.save()
    if 'redirect' in par:
        return redirect(par['redirect'])
    return render_template(
        'route_map.html', colors=get(user_id, 'upr')['colors'], upr=get(user_id, 'upr'), par=par,
        own='road',
        txt=language.get_lang(user_id, 'road', language.road),
        menu_txt=language.get_lang(user_id, 'menu', language.menu),
        lang=get(user_id, 'select_language'), languages=config.languages)


common.current_path = os.path.abspath(os.curdir)
config.kirill = common.decode('abcd', config.kirill)
users_session.users = users_session.Session()

# print(t0)
# t1 = common.encode(common.encode('abcd',config.kirill), t0)
# print(t1)
# print(decode(config.kirill, t1))
# print(common.decode(common.encode('abcd', config.kirill), t1))

if __name__ == '__main__':
    if os.path.exists('static/session.json'):
        os.remove('static/session.json')
    big_query.init_work()
    app.run(port=config.OWN_PORT, host=config.OWN_HOST)
