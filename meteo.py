import common
import config
import json
import requests
from requests.exceptions import HTTPError
from flask import flash

api_id = 'e8Kew5PCm8Kiw49SbsKaYcKBw4rCpMOLwpzCpFFtb8KTwqzCmcKqwqDCo8OQwoLCn29of8Kd'
url_weather = 'https://api.openweathermap.org/data/3.0/onecall'


def send_url(url, api_id, x, y, directive="GET", qrepeat=2) -> (str, bool):
    """
    Sends a request to the specified URL with the given parameters and returns the response data.

    This function constructs a URL with the provided latitude, longitude, and API ID, and sends a request
    to the URL. It retries the request up to a specified number of times if it fails. The function returns
    the response data and a boolean indicating the success of the request.

    Args:
        url (str): The base URL to send the request to.
        api_id (str): The API ID for authentication.
        x (float): The latitude for the request.
        y (float): The longitude for the request.
        directive (str): The HTTP method to use for the request. Defaults to "GET".
        qrepeat (int): The number of times to retry the request if it fails. Defaults to 2.

    Returns:
        tuple: A tuple containing the response data as a string and a boolean indicating the success of the request.
    """
    result = False
    q = 0
    mes = data = ''
    headers = {"Accept": "application/json"}
    mes = f'?lat={x}&lon={y}&appid={api_id}&units=metric&exclude=daily,minutely,alerts'

    while not result and q < qrepeat:
        try:
            response = requests.request(directive, url + mes, headers=headers)
            data = response.text
            result = response.ok
        except HTTPError as err:
            data = f'HTTP error occurred: {err}'
        except Exception as err:
            data = f'Other error occurred: {err}'
        q += 1

    if not result:
        print('ERROR', 'send_url', data + '\n\t' + mes)
        flash(data + '\n\t' + mes, 'warning')

    return data, result


def get_forecast(lat, lon):
    """
    Retrieves the weather forecast for the given latitude and longitude.

    This function sends a request to the weather API using the provided latitude and longitude,
    and returns the parsed JSON response if the request is successful.

    Args:
        lat (float): The latitude for the weather forecast.
        lon (float): The longitude for the weather forecast.

    Returns:
        dict or None: The parsed JSON response from the weather API if the request is successful, otherwise None.
    """
    txt, result = send_url(url_weather, common.user_decode(api_id), lat, lon)
    return json.loads(txt) if result else None