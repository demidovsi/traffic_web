from flask import session
import datetime
import time
import base64

import config
import colors
import users_session

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


def find_user(user_id, req):
    return users_session.users.find_user(user_id, req)


def init_form(user_id, request, endpoint):
    """
    Initializes the form for a user session.

    This function loads the user session, finds the user based on the request,
    and checks if the user exists. If the user does not exist, it sets the
    return page in the session and saves the user session.

    Args:
        user_id (str): The ID of the user.
        request (Request): The request object containing user information.
        endpoint (str): The endpoint to return to if the user does not exist.

    Returns:
        str: The URL to redirect to if the user does not exist.
    """
    users_session.users.load()
    user_id = find_user(user_id, request)
    if not exist(user_id):
        session['page_for_return'] = endpoint
        users_session.users.save()
        return '/login/'


def default_form(user_id, array, answer, prefix):
    """
    Sets default values for a user form and updates the answer dictionary.

    This function iterates over an array of data, sets default values for each
    key in the user's session, and updates the answer dictionary with the
    retrieved values.

    Args:
        user_id (str): The ID of the user.
        array (list): A list of dictionaries containing 'key' and 'value' pairs.
        answer (dict): The dictionary to update with the retrieved values.
        prefix (str): The prefix to add to each key before storing in the session.

    """
    for data in array:
        default(user_id, prefix + data['key'], data['value'])
        answer[data['key']] = get(user_id, prefix + data['key'])


def save_form(user_id, array, answer, prefix):
    """
    Saves form data for a user session.

    This function iterates over an array of data, adds each key-value pair
    to the user's session with a specified prefix, and updates the answer
    dictionary with the provided values.

    Args:
        user_id (str): The ID of the user.
        array (list): A list of dictionaries containing 'key' and 'value' pairs.
        answer (dict): The dictionary containing the values to be saved.
        prefix (str): The prefix to add to each key before storing in the session.
    """
    for data in array:
        add(user_id, prefix + data['key'], answer[data['key']])

def calc_day(year, month, day, delta):
    """
    Calculates a new date by adding a delta to the given date.

    This function takes a year, month, and day, creates a date object,
    adds the specified number of days (delta) to it, and returns the
    new date's year, month, and day.

    Args:
        year (int): The year of the initial date.
        month (int): The month of the initial date.
        day (int): The day of the initial date.
        delta (int): The number of days to add to the initial date.

    Returns:
        tuple: A tuple containing the new date's year, month, and day.
    """
    date = datetime.date(int(year), int(month), int(day))
    new_date = date + datetime.timedelta(days=delta)
    return new_date.year, new_date.month, new_date.day


def get_st_date(year, month, day):
    """
    Formats a date as a string in the format 'YYYY-MM-DD'.

    This function takes a year, month, and day, and returns a string
    representing the date in the format 'YYYY-MM-DD', with the month
    and day padded with leading zeros if necessary.

    Args:
        year (int): The year of the date.
        month (int): The month of the date.
        day (int): The day of the date.

    Returns:
        str: The formatted date string.
    """
    return f"{year}-{str(month).zfill(2)}-{str(day).zfill(2)}"


def st_today():
    """
    Returns the current date in the format 'YYYY-MM-DD'.

    This function retrieves the current date in UTC, formats it as a string
    in the format 'YYYY-MM-DD', with the month and day padded with leading
    zeros if necessary.

    Returns:
        str: The formatted current date string.
    """
    today = time.gmtime()
    return f"{today.tm_year}-{str(today.tm_mon).zfill(2)}-{str(today.tm_mday).zfill(2)}"


def st_now_hour():
    """
    Returns the current date and hour in the format 'YYYY-MM-DDTHH:00'.

    This function retrieves the current local date and time, rounds the hour up
    if the current minute is greater than or equal to 30, and formats the result
    as a string in the format 'YYYY-MM-DDTHH:00', with the month, day, and hour
    padded with leading zeros if necessary.

    Returns:
        str: The formatted current date and hour string.
    """
    dt = datetime.datetime.now()
    hour = dt.hour + (1 if dt.minute >= 30 else 0)
    return f"{dt.year}-{str(dt.month).zfill(2)}-{str(dt.day).zfill(2)}T{str(hour).zfill(2)}:00"


def encode(key, clear):
    """
    Encodes a clear text string using a key with a simple character shift and base64 encoding.

    This function takes a clear text string and a key, shifts each character in the clear text
    by the corresponding character in the key (repeating the key if necessary), and then encodes
    the result using base64.

    Args:
        key (str): The key used for encoding.
        clear (str): The clear text string to be encoded.

    Returns:
        str: The base64 encoded string.
    """
    enc = [
        chr((ord(clear[i]) + ord(key[i % len(key)])) % 256)
        for i in range(len(clear))
    ]
    return base64.urlsafe_b64encode("".join(enc).encode()).decode()


def decode(key, enc):
    """
    Decodes an encoded string using a key with a simple character shift and base64 decoding.

    This function takes an encoded string and a key, decodes the string from base64,
    shifts each character back by the corresponding character in the key (repeating the key if necessary),
    and returns the decoded clear text string.

    Args:
        key (str): The key used for decoding.
        enc (str): The base64 encoded string to be decoded.

    Returns:
        str: The decoded clear text string.
    """
    enc = base64.urlsafe_b64decode(enc).decode()
    return "".join(
        chr((256 + ord(enc[i]) - ord(key[i % len(key)])) % 256)
        for i in range(len(enc))
    )


def get_duration(td):
    """
    Converts a time duration in seconds to a human-readable string format.

    This function takes a time duration in seconds and returns a string
    representing the duration in a more readable format, including days,
    hours, minutes, and seconds.

    Args:
        td (float or int): The time duration in seconds.

    Returns:
        str: The formatted duration string.
    """
    if td is None:
        return ''
    if '<' in str(td):
        return str(td) + ' sec'
    tdr = int(td + 0.5)
    if tdr == 0:
        return '< 0.5 sec'
    result = ''
    if tdr >= 86400:
        days = tdr // 86400
        result += f"{days} day{'s' if days != 1 else ''}"
        tdr %= 86400
    if tdr // 3600 == 0:
        result += f" {tdr % 3600 // 60:02}:{tdr % 3600 % 60:02}"
    else:
        result += f" {tdr // 3600:02}:{tdr % 3600 // 60:02}:{tdr % 3600 % 60:02}"
    return result

def str1000(number, sep=' '):
    """
    Formats an integer with thousand separators.

    Args:
        number (int or str): The number to format.
        sep (str): The separator to use between thousands.

    Returns:
        str: The formatted number as a string.
    """
    if number is None:
        return ''
    if isinstance(number, (int, str)):
        n = str(number)[::-1]
        return sep.join(n[i:i + 3] for i in range(0, len(n), 3))[::-1]
    return str(number)


def float1000(number, k_round=2):
    """
    Formats a floating-point number with thousand separators and rounds it to a specified number of decimal places.

    This function takes a floating-point number, rounds it to the specified number of decimal places,
    and formats it with thousand separators. If the number is in scientific notation, it converts it
    to a regular floating-point format before formatting.

    Args:
        number (float or str): The number to format.
        k_round (int): The number of decimal places to round to. Defaults to 2.

    Returns:
        str: The formatted number as a string.
    """
    if number is None:
        return ''
    if 'e-' in str(number):
        value = str(number).split('e-')
        number = f"{number:.{int(value[1])}f}"
    else:
        if not isinstance(number, str):
            number = round(number, k_round) if k_round != 0 else round(number)
        number = str(number)
    st_number = number.split('.')
    st_number[0] = str1000(int(st_number[0]))
    return f"{st_number[0]}.{st_number[1][:2]}" if len(st_number) > 1 else st_number[0]


def user_decode(txt):
    """
    Decodes a given text using a double decode process with a predefined key and encoded configuration value.

    This function first encodes a predefined configuration value using a key, then decodes the result twice
    with the same key and the given text.

    Args:
        txt (str): The text to be decoded.

    Returns:
        str: The decoded text.
    """
    # перевод в нормальный вид
    return decode(decode('abcd', encode('abcd', config.kirill)), txt)


def choose_language(user_id, request):
    if 'select_language' in request.form:
        upr = get(user_id, 'upr')
        upr['select_language'] = request.form.get('select_language')
        add(user_id, 'upr', upr)
    if 'select_theme' in request.form:
        add(user_id, 'theme', request.form.get('select_theme'))
        upr = get(user_id, 'upr')
        upr['select_theme'] = request.form.get('select_theme')
        upr['colors'] = colors.colors[get(user_id, 'theme')]
        add(user_id, 'upr', upr)
