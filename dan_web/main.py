import os
import config
import common
from common import get, add
import datetime
from flask import Flask, render_template, request, flash, redirect, session, send_file
import login as c_login
import logs as c_logs
import news as c_news
import functions as c_functions
import delete_unit as c_delete_unit
import new as c_new
import users_session
from flask_moment import Moment

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
        return render_template(st_html)
    else:
        return redirect(st_redirect)


@app.route('/delete_unit/<user_id>/', methods=('GET', 'POST'))
def delete_unit(user_id):
    try:
        if request.method == 'POST':
            users_session.users.load()
            c_delete_unit.prepare_form(user_id, request)
            if get(user_id, 'page_for_return') is not None:
                st = get(user_id, 'page_for_return')
                add(user_id, 'page_for_return', None)
                users_session.users.save()
                return redirect(st)
            else:
                return redirect('/login/')
        return render_template(
            'delete_unit.html', user_id=user_id,
            theme=get(user_id, 'theme'), colors=get(user_id, 'upr')['colors'],
            confirmation_text=get(user_id, 'confirmation_text'),
            question_text=get(user_id, 'question_text')
        )
    except:
        return redirect('/login/')


@app.route('/logs/<user_id>/', methods=('GET', 'POST'))
def logs(user_id):
    par = c_logs.prepare_form(user_id, request)
    users_session.users.save()
    if 'redirect' in par:
        return redirect(par['redirect'])
    return render_template(
        'logs.html', colors=get(user_id, 'upr')['colors'], upr=get(user_id, 'upr'), par=par,
        own='logs')


@app.route('/news/<user_id>/', methods=('GET', 'POST'))
def news(user_id):
    par = c_news.prepare_form(user_id, request)
    users_session.users.save()
    if 'redirect' in par:
        return redirect(par['redirect'])
    return render_template(
        'news.html', colors=get(user_id, 'upr')['colors'], upr=get(user_id, 'upr'), par=par,
        own='news')


@app.route('/new/<user_id>/<new_id>/', methods=('GET', 'POST'))
def new(user_id, new_id):
    par = c_new.prepare_form(user_id, request, new_id)
    users_session.users.save()
    if 'redirect' in par:
        return redirect(par['redirect'])
    return render_template(
        'new.html', colors=get(user_id, 'upr')['colors'], upr=get(user_id, 'upr'), par=par,
        own='new')


@app.route('/functions/<user_id>/', methods=('GET', 'POST'))
def functions(user_id):
    par = c_functions.prepare_form(user_id, request)
    users_session.users.save()
    if 'redirect' in par:
        return redirect(par['redirect'])
    return render_template(
        "functions.html", colors=get(user_id, 'upr')['colors'], upr=get(user_id, 'upr'), par=par,
        own='functions')


common.current_path = os.path.abspath(os.curdir)
users_session.users = users_session.Session()
moment = Moment(app)

if __name__ == '__main__':
    if os.path.exists('static/session.json'):
        os.remove('static/session.json')
    app.run(port=config.OWN_PORT, host=config.OWN_HOST)
