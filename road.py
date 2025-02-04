import time
import common
import datetime
from flask import flash
import openrouteservice
import folium
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import big_query
import meteo

types = [
    'Table', 'Riskmeter', 'Chart coeff', 'Chart weight'
]

array_default = [
    {'key': 'dt_start', 'value': common.st_now_hour()},
    {'key': 'start_point', 'value': 'Bat Yam'},
    {'key': 'start_x', 'value': None},
    {'key': 'start_y', 'value': None},
    {'key': 'start_xy', 'value': ''},
    {'key': 'end_xy', 'value': ''},
    {'key': 'end_x', 'value': None},
    {'key': 'end_y', 'value': None},
    {'key': 'end_point', 'value': 'Tel-Aviv'},
    {'key': 'locations', 'value': []},
    {'key': 'weathers', 'value': []},
    {'key': 'dist', 'value': None},
    {'key': 'data', 'value': []},
    {'key': 'time', 'value': ''},
    {'key': 'sec_route', 'value': 0},
    {'key': 'begin_day', 'value': None},  # начало дня
    {'key': 'begin_night', 'value': None},  # начало ночи
    {'key': 'weight', 'value': None},  # начало ночи
    {'key': 'switch', 'value': 'accidents'},  # вид таблицы точек маршрута
    {'key': 'count_accidents', 'value': 0},  # кол-во аварий
    {'key': 'count', 'value': 0},  # кол-во точек маршрута
    {'key': 'coefficient', 'value': 0},  # вес, деленный на время движения в минутах
    {'key': 'empty_coefficient', 'value': 0},  # величина дополнения для спидометра
    {'key': 'value_green', 'value': 17},  # диапазон зеленого риска
    {'key': 'value_yellow', 'value': 6},  # диапазон желтого риска
    {'key': 'value_red', 'value': 7},  # диапазон красного риска
    {'key': 'types', 'value': types},  # тип левой части
    {'key': 'select_type', 'value': 'Riskmeter'},  # тип левой части
    {'key': 'with_accidents', 'value': True},  # учитывать аварии на маршруте
    {'key': 'scroll', 'value': 0},  # смещение в таблице
]
api_key = "5b3ce3597851110001cf62480ae97b5b07b24a2daeaa55007d357cec"
k_dig = 4

# Define a function to calculate the route using OpenRouteService
def calculate_route_ors(api_key, start_location, end_location):
    # Инициализировать клиент OpenRouteService
    try:
        client = openrouteservice.Client(key=api_key)

    # Используйте Geopy для получения координат начального и конечного местоположения.
        geolocator = Nominatim(user_agent="demidovsi@gmail.com")
        start = geolocator.geocode(start_location)
        end = geolocator.geocode(end_location)

        if not start or not end:
            flash("Не найдено местоположений для начальной и конечной точек.", 'warning')
            return None, None, None, None
        # raise ValueError("Не найдено местоположений для начальной и конечной точек.")

        start_coords = (start.latitude, start.longitude)
        end_coords = (end.latitude, end.longitude)

    # Рассчитать маршрут
        route = client.directions(
            coordinates=[(start_coords[1], start_coords[0]), (end_coords[1], end_coords[0])],
            profile='driving-car',
            format='geojson'
        )
    except Exception as er:
        flash(f"{er}", 'warning')
        return None, None, None, None

    route_coords = [(point[1], point[0]) for point in route['features'][0]['geometry']['coordinates']]
    return start_coords, end_coords, route_coords, route


# Определить функцию для отображения маршрута на карте
def display_route(route_coords):
    return folium.PolyLine(route_coords, color="blue", weight=5, opacity=0.8)


def calculate_route(answer):
    t0 = time.time()
    answer['route'] = None
    start_coords, end_coords, route_coords, route = \
        calculate_route_ors(api_key, answer['start_point'], answer['end_point'])
    if start_coords:
        answer['start_x'] = start_coords[0]
        answer['start_y'] = start_coords[1]
        answer['start_xy'] = '(' + str(start_coords[0]) + ' - ' + str(start_coords[1]) + ')'
        answer['end_x'] = end_coords[0]
        answer['end_y'] = end_coords[1]
        answer['end_xy'] =  '(' + str(end_coords[0]) + ' - ' + str(end_coords[1]) + ')'
        answer['locations'] = []
        locations = display_route(route_coords).locations
        for point in locations:
            answer['locations'].append(point)
        answer['route'] = route
    answer['data'] = []
    print('расчет маршрута', 'точек маршрута=', len(answer['locations']), 'время=', time.time() - t0)


def remember_point(answer, ind, txt):
    """
    This function records weather and road conditions for a specific point in the route.

    Parameters:
    answer (dict): A dictionary containing route information and weather data.
    ind (int): The index of the current point in the route.
    txt (dict): A dictionary containing weather forecast data.

    Returns:
    dict: A dictionary containing the recorded weather and road conditions for the specified point.

    The function performs the following steps:
    1. Initializes a dictionary `unit` with the date, sunrise, sunset, and coordinates of the point.
    2. Iterates through the hourly weather data and records the weather and road conditions.
    3. Appends the `unit` dictionary to the `weathers` list in the `answer` dictionary.
    """
    dt = time.strptime(answer['dt_start'], '%Y-%m-%dT%H:%M')
    dt = f"{dt.tm_year}-{str(dt.tm_mon).zfill(2)}-{str(dt.tm_mday).zfill(2)}"
    unit = {
        'dt': dt,
        'begin_day': txt['current']['sunrise'],
        'begin_night': txt['current']['sunset'],
        'x': answer['data'][ind]['x'],
        'y': answer['data'][ind]['y']
    }
    for hour in txt['hourly']:
        weather_condition = 'Clear' if 'rain' not in hour['weather'][0]['main'] else 'Rainy'
        unit[str(hour['dt'] // 3600)] = {
            'weather_condition': weather_condition,
            'road_condition': 'Dry' if weather_condition == 'Clear' else 'Wet (Water)'
        }
    answer['weathers'].append(unit)
    return unit


def get_point(answer, ind):
    point = (answer['data'][ind]['x'], answer['data'][ind]['y'])
    dt = time.strptime(answer['dt_start'], '%Y-%m-%dT%H:%M')
    dt = f"{dt.tm_year}-{str(dt.tm_mon).zfill(2)}-{str(dt.tm_mday).zfill(2)}"
    for unit in answer['weathers']:
        if unit['x'] == point[0] and unit['y'] == point[1] and unit['dt'] == dt:
            return unit
    for unit in answer['weathers']:
        point_1 = (unit['x'], unit['y'])
        if geodesic(point, point_1).km < 10 and unit['dt'] == dt:
            return unit

def get_weather(answer, ind):
    unit = get_point(answer, ind)
    if unit is None:
        txt = meteo.get_forecast(answer['data'][ind]['x'], answer['data'][ind]['y'])
        answer['count_weather'] += 1
        unit = remember_point(answer, ind, txt)
    answer['begin_day'] = unit['begin_day']
    answer['begin_night'] = unit['begin_night']
    answer['data'][ind]['weather_condition'] = None
    answer['data'][ind]['road_condition'] = None
    dt = str(int(answer['data'][ind]['dt'] //3600))
    if dt in unit:
        answer['data'][ind]['weather_condition'] = unit[dt]['weather_condition']
        answer['data'][ind]['road_condition'] = unit[dt]['road_condition']


def make_count_accident(answer):
    # Пометить точки маршрута, в которых произошли аварии
    answer['count_accidents'] = 0
    for unit in answer['data']:
        if 'accident' in unit:
            answer['count_accidents'] += 1


def load_weather(answer):
    for i in range(len(answer['data'])):
        get_weather(answer, i)


def make_data_accident(answer, ans_big):
    def slave(key):
        data[key] = data[key] + unit[key] if key in data else unit[key]

    count = 0
    if 'begin_day' in answer and answer['begin_day']:
        begin_day = datetime.datetime.fromtimestamp(answer['begin_day']).hour
        begin_night = datetime.datetime.fromtimestamp(answer['begin_night']).hour
    else:
        begin_day = 6
        begin_night = 18
    for unit in ans_big:
        for i, data in enumerate(answer['data']):
            if data['x'] == round(unit['longitude'], k_dig) and data['y'] == round(unit['latitude'], k_dig):
                data['is_accident'] = True
                data['count_accident'] += 1
                data['speed_limit'] = unit['speed_limit']
                data['district_name_eng'] = unit['district_name_eng']
                dt = datetime.datetime.fromtimestamp(data['dt'])
                day_night = 'Day' if  begin_day <= dt.hour < begin_night else 'Night'
                day_week = dt.strftime("%A")
                data['day_night'] = day_night
                data['day_of_week'] = day_week
                if unit['severity'] > 1:
                    data['big_accident_in_point'] = True

                is_need = 'weather_condition' in data and data['weather_condition'] == unit['weather_condition'] and \
                    'road_condition' in data and data['road_condition'] == unit['road_condition'] and \
                    day_night == unit['day_night'] and day_week == unit['day_of_week_name']
                if is_need:  # подходящая авария
                    if unit['severity'] > 1:
                        data['count_big_accident'] += 1
                    data['count_own_accident'] += 1
                    slave('speed_limit_weight')
                    slave('district_weight')
                    slave('severity')
                    slave('weather_condition_weight')
                    slave('road_condition_weight')
                    slave('district_weight')
                    slave('day_night_weight')
                    slave('day_of_week_weight')
                    data['accident'] = unit
                count += 1
    for data in answer['data']:
        if 'speed_limit_weight' in data:
            data['speed_limit_weight'] = round(data['speed_limit_weight'], 1)
    return count


def calc_weight(answer):
    answer['weight'] = 0
    max_weight = 0
    min_weight = 99999999999
    av_weight = 0
    for data in answer['data']:
        weight = 0
        if 'weather_condition_weight' in data and data['weather_condition_weight']:
            weight += data['weather_condition_weight']
        if 'road_condition_weight' in data and data['road_condition_weight']:
            weight += data['road_condition_weight']
        if 'day_night_weight' in data and data['day_night_weight']:
            weight += data['day_night_weight']
        if 'day_of_week_weight' in data and data['day_of_week_weight']:
            weight += data['day_of_week_weight']
        if 'district_weight' in data and data['district_weight']:
            weight += data['district_weight']
        if 'speed_limit_weight' in data and data['speed_limit_weight']:
            weight += data['speed_limit_weight']
        if 'severity' in data and data['severity']:
            weight += data['severity']
        data['weight_0'] = weight
        weight = round(weight * data['time'], 3)
        data['weight'] = weight
        answer['weight'] += data['weight']
        max_weight = max(max_weight, weight)
        min_weight = min(min_weight, weight)
        av_weight += weight
    answer['weight'] = round(answer['weight'] / answer['sec_route'], 3)
    answer['max_weight'] = str(round(max_weight / answer['sec_route'], 3))
    answer['min_weight'] = str(round(min_weight / answer['sec_route'], 3))
    answer['av_weight'] = str(round(av_weight / answer['sec_route'] / len(answer['data']), 3))


def define_day_week(answer, ind):
    if 'begin_day' in answer and answer['begin_day']:
        begin_day = datetime.datetime.fromtimestamp(answer['begin_day']).hour
        begin_night = datetime.datetime.fromtimestamp(answer['begin_night']).hour
    else:
        begin_day = 6
        begin_night = 18
    data = answer['data'][ind]
    dt = datetime.datetime.fromtimestamp(data['dt'])
    day_night = 'Day' if begin_day <= dt.hour < begin_night else 'Night'
    data['day_night_weight'] = 66 if day_night == 'Day' else 33
    data['day_night'] = day_night

    day_week = dt.strftime("%A")
    data['day_of_week'] = day_week
    if day_week == 'Sunday':
        data['day_of_week_weight'] = 17
    elif day_week == 'Tuesday':
        data['day_of_week_weight'] = 16
    elif day_week == 'Monday':
        data['day_of_week_weight'] = 15
    elif day_week == 'Wednesday':
        data['day_of_week_weight'] = 15
    elif day_week == 'Thursday':
        data['day_of_week_weight'] = 16
    elif day_week == 'Friday':
        data['day_of_week_weight'] = 14
    else:
        data['day_of_week_weight'] = 9


def dop_points(answer):
    weather_condition = None
    weather_condition_weight = None
    road_condition = None
    road_condition_weight = None
    for i, data in enumerate(answer['data']):
        define_day_week(answer, i)
        if 'accident' not in data:  # это не аварийная точка
            if 'weather_condition' in data:
                weather_condition = data['weather_condition']
                weather_condition_weight = 79 if weather_condition == 'Clear' else 3
            data['weather_condition'] = weather_condition
            data['weather_condition_weight'] = weather_condition_weight
            if 'road_condition' in data:
                road_condition = data['road_condition']
                road_condition_weight = 81 if road_condition == 'Dry' else 4
            data['road_condition'] = road_condition
            data['road_condition_weight'] = road_condition_weight
        good = ('accident' in data and data['day_night'] == data['accident']['day_night'] and
                data['day_of_week'] == data['accident']['day_of_week_name'])
        if good:  # авария и она подходит по времени суток и дню недели
            data['weather_condition'] = data['accident']['weather_condition']
            data['weather_condition_weight'] = data['accident']['weather_condition_weight']
            data['road_condition'] = data['accident']['road_condition']
            data['road_condition_weight'] = data['accident']['road_condition_weight']
    road_condition_weight = None
    weather_condition_weight = None
    for i, data in enumerate(answer['data']):
        if 'road_condition_weight' in data and data['road_condition_weight'] is not None:
            road_condition_weight = data['road_condition_weight']
        if 'weather_condition_weight' in data and data['weather_condition_weight'] is not None:
            weather_condition_weight = data['weather_condition_weight']
        if 'road_condition_weight' not in data or data['road_condition_weight'] is None:
            data['road_condition_weight'] = road_condition_weight
        if 'weather_condition_weight' not in data or data['weather_condition_weight'] is None:
            data['weather_condition_weight'] = weather_condition_weight


def analyses_request(answer, request):
    if answer['with_accidents'] != ('with_accidents' in request.form):
        answer['data'] = []
    answer['with_accidents'] = 'with_accidents' in request.form
    if 'dt_start' in request.form:
        if answer['dt_start'] != request.form.get('dt_start'):
            answer['data'] = []
        answer['dt_start'] = request.form.get('dt_start')
    if 'accidents' in request.form:
        answer['switch'] = 'accidents'
    if 'all_route' in request.form:
        answer['switch'] = 'all_route'
    if 'select_lang' in request.form:
        answer['select_lang'] = request.form.get('select_lang')
    if answer['start_point'] != request.form.get('start_point'):
        answer['start_point'] = request.form.get('start_point')
        answer['locations'] = []
        answer['data'] = []
    if answer['end_point'] != request.form.get('end_point'):
        answer['end_point'] = request.form.get('end_point')
        answer['locations'] = []
        answer['data'] = []
    if 'calculate' in request.form and len(answer['locations']) == 0:
        calculate_route(answer)
    if 'select_vid' in request.form:
        answer['select_type'] = request.form.get('select_vid')
    if answer['select_type'] == 'Table':
        if 'scroll' in request.form and request.form.get('scroll'):
            answer['scroll'] = int(request.form.get('scroll'))


def create_data(answer):
    answer['dist'] = 0
    answer['data'] = []
    answer['sec_route'] = 0
    t0 = time.time()
    dt = time.mktime(time.strptime(answer['dt_start'], '%Y-%m-%dT%H:%M'))
    try:
        steps = answer['route']['features'][0]['properties']['segments'][0]['steps'] if 'route' in answer else None
    except:
        steps = None
    for i, point in enumerate(answer['locations']):
        if i == len(answer['locations']) - 1:
            break
        s = geodesic(answer['locations'][i], answer['locations'][i + 1]).km  # расстояние отрезка
        # определить среднюю скорость
        average_speed = 60
        if steps:
            for step in steps:
                if step['way_points'][0] <= i < step['way_points'][1]:
                    average_speed = step['distance'] / step['duration'] * 3600 / 1000
                    break
        t = s / average_speed * 3600
        answer['sec_route'] += t
        answer['dist'] += s
        answer['data'].append({
            'number': i + 1, 'length': round(s, 3), 'time': t, 'dt': dt + int(answer['sec_route']),
            'speed': round(average_speed, 1), 'severity': 0, 'count_accident': 0,
            'count_big_accident': 0, 'count_own_accident': 0, 'is_accident': False,
            'dt_show': datetime.datetime.fromtimestamp(dt + int(answer['sec_route'])).strftime('%H:%M:%S'),
            'x': round(point[0], k_dig), 'y': round(point[1], k_dig), 'way': round(answer['dist'], 3)})
    answer['dist'] = str(round(answer['dist'], 1)) if answer['dist'] else ''  # общее расстояние
    answer['time'] = common.get_duration(answer['sec_route']) if answer['sec_route'] else ''  # время движения
    answer['count'] = len(answer['data'])
    print('изготовление таблицы data', 'время=', time.time() - t0)


def load_accidents(answer):
    answer['count_accidents'] = 0
    if not answer['with_accidents']:
        return
    query = ''
    for data in answer['data']:
        x = data['x']
        y = data['y']
        query = query + ',\n' if query else query
        query += "('{x}', '{y}')".format(x=x, y=y)
    if query:
        query = ('select * from {schema}.traffic.accident_analysis where '
                 '(longitude_str, latitude_str) IN UNNEST([{query}]) order by year_accident;').format(
            schema=big_query.catalog, query=query)
        t0 = time.time()
        is_ok, ans_big = big_query.execute_script(query)
        print('чтение из big-query', 'получено строк=', len(ans_big), 'время=', time.time() - t0)
        if is_ok:
            t0 = time.time()
            count = make_data_accident(answer, ans_big)
            make_count_accident(answer)  # подсчитать количество аварий на маршруте
            print('make_data_accident', 'count=', count, 'время=', time.time() - t0)
        else:
            flash(ans_big, 'warning')


def make_chart(answer, key='coeff'):
    answer['value_x'] = []
    answer['value_y'] = []
    time_way = 0
    for i in range(len(answer['data'])):
        if key == 'coeff':
            time_way = 0
            weight = 0
            for j in range(i + 1):
                weight += answer['data'][j]['weight']
                time_way += answer['data'][j]['time']
            weight = round(weight / time_way / 60, 3)
            answer['value_x'].append(common.get_duration(time_way).strip())
            answer['value_y'].append(weight)
        else:
            time_way += answer['data'][i]['time']
            answer['value_x'].append(common.get_duration(time_way).strip())
            answer['value_y'].append(answer['data'][i]['weight_0'])


def make_tooltip_accident(answer):
    for data in answer['data']:
        if data['is_accident']:
            if data['count_own_accident']:
                data['tooltip_accident'] =  ("{number} ({x} - {y}) {way} km\n"
                                             "acc={count} big={big_accident}").format(
                    number=data['number'], x=data['x'], y=data['y'], way=data['way'], count=data['count_accident'],
                    big_accident=data['count_big_accident'])
                if data['count_own_accident']:
                    data['tooltip_accident'] += " calc={accident_calc}".format(
                        accident_calc= data['count_own_accident'])
            else:
                data['tooltip_accident'] = "{number} {x} - {y} {way} km acc={count}".format(
                    number=data['number'], x=data['x'], y=data['y'], way=data['way'], count=data['count_accident'])


def prepare_form(user_id, request):
    answer = dict()
    st = common.init_form(user_id, request, '/road/')
    if st:
        answer['redirect'] = st
        return answer
    common.default_form(user_id, array_default, answer, 'road_')
    if request.method == 'POST':
        analyses_request(answer, request)

    answer['count_weather'] = 0  # кол-во запросов погоды
    if len(answer['data']) == 0:
        create_data(answer)  # создать таблицу data
        load_weather(answer)  # загрузить погоду
        load_accidents(answer)  # загрузить аварии
    if len(answer['locations']) > 0:
        dop_points(answer)  # дополнительные точки по погоде и дню недели
        calc_weight(answer)  # рассчитать сумму весов и общий вес

    if answer['weight']:  # and answer['sec_route']:
        # answer['coefficient'] = int(answer['weight'] / (sec_route / 60) / 100)
        answer['coefficient'] = round(float(answer['weight']) / 60, 3)
        answer['empty_coefficient'] = max(0, answer['value_green'] + answer['value_yellow'] + answer['value_red'] -
                                      answer['coefficient'])
        answer['weight'] = common.float1000(round(answer['weight'], 1))
        if answer['coefficient'] <= answer['value_green']:
            answer['result_risk'] = 10
        elif answer['coefficient'] <= answer['value_yellow'] + answer['value_yellow']:
            answer['result_risk'] = 11
        else:
            answer['result_risk'] = 12
        make_tooltip_accident(answer)
    for data in answer['data']:
        data['show'] = True if answer['switch'] == 'all_route' or 'is_accident' in data and data['is_accident'] else False
    if answer['select_type'] == 'Chart coeff':
        make_chart(answer)
    if answer['select_type'] == 'Chart weight':
        make_chart(answer, 'weight')
    common.save_form(user_id, array_default, answer, 'road_')
    print('weathers', 'count=', len(answer['weathers']), 'запросов погоды=', answer['count_weather'])
    return answer
