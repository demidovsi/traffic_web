import common as cd
import config
import json
from flask import flash
from common import get, add, default, write_log, write_quest
import time

array_default = [
    {'key': 'scroll', 'value': 0},
    {'key': 'name_function', 'value': ''},
    {'key': 'description_function', 'value': ''},
    {'key': 'id_function', 'value': 0},
    {'key': 'id_parameter', 'value': 0},
    {'key': 'code_parameter', 'value': ''},
    {'key': 'comment_parameter', 'value': ''},
    {'key': 'function_parameter', 'value': 0},
    {'key': 'is_number_parameter', 'value': True},
]


def load_data(answer):
    url = 'v2/select/{schema}/nsi_parser_functions?column_order=sh_name'.format(schema=config.SCHEMA)
    ans, is_ok, status_code = cd.send_rest(url)
    if is_ok:
        answer['functions'] = json.loads(ans)
    else:
        flash(str(ans), 'warning')
        return
    url = "v2/select/{schema}/v_nsi_functions_params?type_view=view&column_order=name_function, code".format(
        schema=config.SCHEMA)
    ans, is_ok, status_code = cd.send_rest(url)
    if is_ok:
        ans = json.loads(ans)
        for i, unit in enumerate(ans):
            unit['init_value'] = unit['value']
            name_function = unit['name_function']
            if name_function != '':
                for j in range(i+1, len(ans)):
                    if ans[j]['name_function'] == name_function:
                        ans[j]['name_function'] = ''
        for unit in answer['functions']:
            for data in ans:
                if unit['id'] == data['function']:
                    data['description'] = unit['description']
                    break
        answer['data'] = ans
    else:
        flash(str(ans), 'warning')
        answer['data'] = []


def save(user_id, answer):
    values = []
    for unit in answer['data']:
        if unit['value'] != unit['init_value']:
            values.append({"id": unit["id"], "value": unit["value"]})
    if len(values) > 0:
        params = {"schema_name": config.SCHEMA, "object_code": "functions_params", "values": values}
        # url = 'v1/objects'
        url = 'v2/entity'
        ans, ok, status = cd.send_rest(url, 'PUT', params=params, token_user=get(user_id, 'token'))
        if not ok:
            flash(str(ans), 'warning')
        else:
            name_function = ''
            for unit in answer['data']:
                if unit['name_function'] != '':
                    name_function = unit['name_function']
                if unit['value'] != unit['init_value']:
                    st_change = unit['sh_name'] + ": " + str(unit['init_value']) + ' -> ' + str(unit['value'])
                    cd.write_log_db('Коррекция параметров (request)', 'functions', st_change, law_id=name_function,
                                    file_name=get(user_id, 'user_address'))


def get_from_form(request, answer):
    # взять данные с формы и положить в структуру
    load_data(answer)
    for unit in answer['data']:
        unit['value'] = request.form.get(str(unit['id']))
    answer['name_function'] = request.form.get('name_function')
    answer['description_function'] = request.form.get('description_function')
    answer['code_parameter'] = request.form.get('code_parameter')
    answer['comment_parameter'] = request.form.get('comment_parameter')
    answer['function_parameter'] = int(request.form.get('select_function'))
    answer['is_number_parameter'] = 'is_number_parameter' in request.form


def check_corr_function(request, answer):
    for key in request.form.keys():
        if 'corr_function~' in key:
            st2, st2 = key.split('corr_function~')
            for data in answer['functions']:
                if data['sh_name'] == st2:
                    answer['id_function'] = data['id']
                    answer['name_function'] = st2
                    answer['description_function'] = data['description']
                    return


def get_name_function_by_id(answer, function_id):
    for data in answer['functions']:
        if str(data['id']) == str(function_id):
            return data['sh_name']


def check_corr_parameter(request, answer):
    for key in request.form.keys():
        if 'corr_parameter~' in key:
            st2, st2 = key.split('corr_parameter~')
            for data in answer['data']:
                if str(data['id']) == st2:
                    answer['id_parameter'] = data['id']
                    answer['code_parameter'] = data['code']
                    answer['comment_parameter'] = data['sh_name']
                    answer['function_parameter'] = data['function']
                    answer['is_number_parameter'] = data['is_number']
                    return


def save_function(user_id, answer):
    if answer['name_function']:
        operation = 'Создание'
        values = {"sh_name": answer['name_function'], "description": answer['description_function']}
        for data in answer['functions']:
            if data['id'] == answer['id_function']:
                values['id'] = data['id']
                operation = 'Коррекция '
                break
        params = {"schema_name": config.SCHEMA, "object_code": "parser_functions", "values": values}
        # url = 'v1/objects'
        url = 'v2/entity'
        ans, ok, status = cd.send_rest(url, 'PUT', params=params, token_user=get(user_id, 'token'))
        if not ok:
            flash(str(ans), 'warning')
        else:
            cd.write_log_db(operation + ' сервиса (request)', 'functions', str(values), law_id=answer['name_function'],
                            file_name=get(user_id, 'user_address'))
            load_data(answer)
    else:
        flash('Необходимо задание имени сервиса', 'warning')


def save_parameter(user_id, answer):
    # answer['code_parameter']
    # answer['comment_parameter']
    # answer['function_parameter']
    # answer['is_number_parameter']
    st = ''
    if not answer['function_parameter']:
        st = 'Необходимо выбрать сервис для параметра; '
    if not answer['code_parameter']:
        st += 'Необходимо задать код параметра;'
    if st:
        flash(st, 'warning')
    else:
        values = {"sh_name": answer['comment_parameter'], "code": answer['code_parameter'],
                  "is_number": answer['is_number_parameter'], "function": answer['function_parameter']}
        operation = 'Создание'
        for data in answer['data']:
            if data['function'] == answer['function_parameter'] and data['code'] == answer['code_parameter']:
                values['id'] = data['id']
                operation = 'Коррекция'
        params = {"schema_name": config.SCHEMA, "object_code": "functions_params", "values": values}
        # url = 'v1/objects'
        url = 'v2/entity'
        ans, ok, status = cd.send_rest(url, 'PUT', params=params, token_user=get(user_id, 'token'))
        if not ok:
            flash(str(ans), 'warning')
        else:
            cd.write_log_db(operation + ' параметра сервиса (request)', 'functions', str(values),
                            law_id=get_name_function_by_id(answer, answer['function_parameter']) + '.' +
                                   answer['code_parameter'],
                            file_name=get(user_id, 'user_address'))
            load_data(answer)


def make_delete_parameter(user_id, object_id):
    t0 = time.time()
    st = 'Сервис [{code_service}], Параметр [{code_parameter}]'.format(
        code_service=get(user_id, 'code_service'), code_parameter=get(user_id, 'code_parameter'))
    url = 'v2/entity/{app_code}/functions_params/{object_id}'.format(object_id=object_id, app_code=config.SCHEMA)
    answer, ok, status_answer = cd.send_rest(url, 'DELETE', token_user=get(user_id, 'token'))
    if ok:
        cd.write_log_db('Удаление параметра сервиса', 'functions', st + '\n (' + get(user_id, 'user_address') + ')',
                        td=time.time() - t0)
        add(user_id, 'function_id_parameter', None)
        add(user_id, 'function_code_parameter', None)
        add(user_id, 'function_comment_parameter', None)
        add(user_id, 'function_function_parameter', None)
        add(user_id, 'function_is_number_parameter', None)
    else:
        cd.write_log_db('error', 'functions', ' Ошибка при удалении параметра сервиса: ' + str(answer) + ';\n' +
                            st + '\n (' + get(user_id, 'user_address') + ')', td=time.time() - t0)


def make_delete_service(user_id, object_id):
    t0 = time.time()
    st = 'Сервис [{code_service}]'.format(
        code_service=get(user_id, 'function_name_function'))
    url = 'v2/entity/{app_code}/parser_functions/{object_id}'.format(object_id=object_id, app_code=config.SCHEMA)
    answer, ok, status_answer = cd.send_rest(url, 'DELETE', token_user=get(user_id, 'token'))
    if ok:
        cd.write_log_db('Удаление сервиса', 'functions', st + '\n (' + get(user_id, 'user_address') + ')',
                        td=time.time() - t0)
        add(user_id, 'function_id_function', None)
        add(user_id, 'function_name_function', None)
        add(user_id, 'function_description_function', None)
    else:
        cd.write_log_db('error', 'functions', ' Ошибка при удалении сервиса: ' + str(answer) + ';\n' +
                            st + '\n (' + get(user_id, 'user_address') + ')', td=time.time() - t0)


def refuse_delete_parameter(parameter_id):
    flash('Отказ от удаления параметра сервиса с ID={id}'.format(id=parameter_id), 'success')


def refuse_delete_service(parameter_id):
    flash('Отказ от удаления сервиса с ID={id}'.format(id=parameter_id), 'success')


def prepare_form(user_id, request):
    answer = dict()
    st = cd.init_form(user_id, request, '/functions/')  # проверить наличие user_id
    if st:  # необходимо делать login
        answer['redirect'] = st
        return answer
    cd.default_form(user_id, array_default, answer, 'function_')
    if request.method == 'POST':
        if 'scroll' in request.form and request.form.get('scroll'):
            answer['scroll'] = int(request.form.get('scroll'))
        get_from_form(request, answer)  # прочитать данные из БД и изменить их данными с формы
        if 'refresh' in request.form:
            load_data(answer)
            answer['id_parameter'] = None
            answer['code_parameter'] = None
            answer['comment_parameter'] = None
            answer['function_parameter'] = None
            answer['is_number_parameter'] = None
            answer['id_function'] = None
            answer['name_function'] = None
            answer['description_function'] = None
        if 'save_function' in request.form:
            save_function(user_id, answer)
        if 'save_parameter' in request.form:
            save_parameter(user_id, answer)
        if 'save' in request.form:
            save(user_id, answer)
        if 'delete_parameter' in request.form:
            add(user_id, 'page_for_return', f'/functions/{user_id}/'.format(user_id=user_id))
            add(user_id, 'delete_unit', 'delete_parameter')
            add(user_id, 'code', answer['id_parameter'])
            add(user_id, 'confirmation_text', 'Подтверждение удаления параметра сервиса')
            add(user_id, 'question_text',
                'Действительно удалить параметр [{code_parameter}] из сервиса [{name_service}]?'.format(
                    name_service=get_name_function_by_id(answer, answer['function_parameter']),
                    code_parameter=answer['code_parameter']))

            add(user_id, 'code_parameter', answer['code_parameter'])
            add(user_id, 'code_service', get_name_function_by_id(answer, answer['function_parameter']))
            answer['redirect'] = '/delete_unit/{user_id}/'.format(user_id=user_id)
            cd.save_form(user_id, array_default, answer, 'function_')
            return answer
        if 'delete_service' in request.form:
            add(user_id, 'page_for_return', f'/functions/{user_id}/'.format(user_id=user_id))
            add(user_id, 'delete_unit', 'delete_service')
            add(user_id, 'code', answer['id_function'])
            add(user_id, 'confirmation_text', 'Подтверждение удаления сервиса')
            add(user_id, 'question_text',
                'Действительно удалить сервис [{name_service}]?'.format(name_service=answer['name_function']))
            answer['redirect'] = '/delete_unit/{user_id}/'.format(user_id=user_id)
            cd.save_form(user_id, array_default, answer, 'function_')
            return answer
    else:  # первый вывод формы
        write_log('Параметры сервисов', user_id, request)
        load_data(answer)
    # answer['data'] = get_data(user_id)
    check_corr_function(request, answer)
    check_corr_parameter(request, answer)
    cd.save_form(user_id, array_default, answer, 'function_')
    answer['functions'].insert(0, {'id': 0, 'sh_name': ''})
    return answer
