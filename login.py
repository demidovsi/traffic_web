from flask import session
import os
import config
from common import get, add
import users_session
import colors
import language


def prepare_form(request):
    """
    Prepares the user form based on the POST request.

    This function handles the POST request to prepare the user form by generating a unique user ID,
    setting user session data, and saving the user preferences such as theme and language. It also
    handles redirection based on the session data.

    Args:
        request (flask.Request): The request object containing form data.

    Returns:
        tuple: A tuple containing the template name and the redirect URL.
    """
    if request.method == 'POST':
        user_id = os.urandom(20).hex()
        users_session.users.add_user(user_id)
        users_session.users.clear(user_id)
        users_session.users.add(user_id, "rights", '*')
        add(user_id, 'theme', request.form.get('select_theme'))
        add(user_id, 'select_language', request.form.get('select_language'))
        users_session.users.save()

        upr = {
            'user_name': get(user_id, 'user_name'),
            'user_id': user_id,
            'theme': request.form.get('select_theme'),
            'colors': colors.colors[get(user_id, 'theme')],
            'languages': config.languages
        }
        add(user_id, 'upr', upr)

        users_session.users.save()
        language.load_lang()

        if 'page_for_return' in session:
            st = session.pop('page_for_return')
            return '', f"{st}{user_id}/"
        return '', f"/road/{user_id}/"
    return 'login.html', ''