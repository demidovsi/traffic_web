from common import get, add
from flask import flash
import functions


def prepare_form(user_id, request):
    unit = get(user_id, 'delete_unit')
    if 'indexYes' in request.form:
        st = get(user_id, 'code')
        if st:
            if unit == 'delete_service':
                functions.make_delete_service(user_id, st)
            if unit == 'delete_parameter':
                functions.make_delete_parameter(user_id, st)
        else:
            flash('Отказ от подтверждения удаления (ни да, ни нет)', 'info')
    if 'indexNo' in request.form:
        if unit == 'delete_service':
            functions.refuse_delete_service(get(user_id, 'code'))
        if unit == 'delete_parameter':
            functions.refuse_delete_parameter(get(user_id, 'code'))
