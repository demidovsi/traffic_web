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
    {'key': 'dist', 'value': None},
    {'key': 'data', 'value': []},
    {'key': 'time', 'value': ''},
    {'key': 'begin_day', 'value': None},  # начало дня
    {'key': 'begin_night', 'value': None},  # начало ночи
    {'key': 'weight', 'value': None},  # начало ночи
    {'key': 'switch', 'value': 'accidents'},  # вид таблицы точек маршрута
    {'key': 'count_accidents', 'value': 0},  # кол-во аварий
    {'key': 'count', 'value': 0},  # кол-во точек маршрута
    {'key': 'coefficient', 'value': 0},  # вес, деленный на время движения в минутах
    {'key': 'empty_coefficient', 'value': 0},  # величина дополнения для спидометра
    {'key': 'speedometer', 'value': True},  # вывод спидометра
    {'key': 'value_green', 'value': 17},  # диапазон зеленого риска
    {'key': 'value_yellow', 'value': 6},  # диапазон желтого риска
    {'key': 'value_red', 'value': 7},  # диапазон красного риска
]
api_key = "5b3ce3597851110001cf62480ae97b5b07b24a2daeaa55007d357cec"
k_dig = 4


# Define a function to calculate the route using OpenRouteService
def calculate_route_ors(api_key, start_location, end_location):
    # Инициализировать клиент OpenRouteService
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
    try:
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


def calculate(answer):
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


def get_weather(answer, ind):
    txt = meteo.get_forecast(answer['data'][ind]['x'], answer['data'][ind]['y'])
    if txt:
        answer['begin_day'] = txt['current']['sunrise']
        answer['begin_night'] = txt['current']['sunset']
        answer['data'][ind]['weather_condition'] = None
        answer['data'][ind]['road_condition'] = None
        for hour in txt['hourly']:
            if hour['dt'] // 3600 == answer['data'][ind]['dt'] //3600:
                answer['data'][ind]['weather_condition'] = 'Clear' if 'rain' not in hour['weather'][0]['main'] else 'Rainy'
                answer['data'][ind]['road_condition'] = 'Dry' if answer['data'][ind]['weather_condition'] == 'Clear' else 'Wet (Water)'
                break


def load_weather(answer, ans_big):
    # чтение погоды для точек маршрута из статистики аварий
    index = list()
    for unit in ans_big:
        for i, data in enumerate(answer['data']):
            if data['x'] == round(unit['longitude'], k_dig) and data['y'] == round(unit['latitude'], k_dig):
                if i not in index:
                    index.append(i)
    for unit in index:
        get_weather(answer, unit)
        answer['data'][unit]['is_accident'] = True
    return len(index)


def make_data(answer, ans_big):
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
                data['count_accident'] += 1
                data['speed_limit'] = unit['speed_limit']
                data['district_name_eng'] = unit['district_name_eng']
                data['district_weight'] = unit['district_weight']
                if unit['severity'] > 1:
                    data['count_big_accident'] += 1
                data['severity'] = max(unit['severity'], data['severity'])

                if 'weather_condition' in data and data['weather_condition'] == unit['weather_condition']:
                    data['weather_condition_weight'] = unit['weather_condition_weight']

                if 'road_condition' in data and data['road_condition'] == unit['road_condition']:
                    data['road_condition_weight'] = unit['road_condition_weight']

                data['district_weight'] = unit['district_weight']

                dt = datetime.datetime.fromtimestamp(data['dt'])
                day_night = 'Day' if dt.hour >= begin_day and dt.hour < begin_night else 'Night'
                if day_night == unit['day_night']:
                    data['day_night_weight'] = unit['day_night_weight']
                    data['day_night'] = day_night

                day_week = dt.strftime("%A")
                if day_week == unit['day_of_week_name']:
                    data['day_of_week_weight'] = unit['day_of_week_weight']
                    data['day_of_week'] = day_week
                # data['lighting_weight'] = unit['lighting_weight']
                data['accident'] = unit
                count += 1
    return count


def calc_data(answer):
    answer['weight'] = 0
    max_weight = 0
    min_weight = 99999999999
    av_weight = 0
    for data in answer['data']:
        data['weight'] = 0
        if 'weather_condition_weight' in data and data['weather_condition_weight']:
            data['weight'] += data['weather_condition_weight']
        if 'road_condition_weight' in data and data['road_condition_weight']:
            data['weight'] += data['road_condition_weight']
        if 'day_night_weight' in data and data['day_night_weight']:
            data['weight'] += data['day_night_weight']
        if 'day_of_week_weight' in data and data['day_of_week_weight']:
            data['weight'] += data['day_of_week_weight']
        if 'district_weight' in data and data['district_weight']:
            data['weight'] += data['district_weight']
        if 'severity' in data and data['severity']:
            data['weight'] += data['severity']
        answer['weight'] += data['weight']
        max_weight = max(max_weight, data['weight'])
        min_weight = min(min_weight, data['weight'])
        av_weight += data['weight']
    answer['max_weight'] = max_weight
    answer['min_weight'] = min_weight
    answer['av_weight'] = int(av_weight / len(answer['data']))


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
        if 'weather_condition' in data and data['weather_condition']:
            weather_condition = data['weather_condition']
            weather_condition_weight = 79 if weather_condition == 'Clear' else 3
        else:
            data['weather_condition'] = weather_condition
            data['weather_condition_weight'] = weather_condition_weight

        if 'road_condition' in data and data['road_condition']:
            road_condition = data['road_condition']
            road_condition_weight = 81 if road_condition == 'Dry' else 4
        else:
            data['road_condition'] = road_condition
            data['road_condition_weight'] = road_condition_weight
        define_day_week(answer, i)


def prepare_form(user_id, request):
    answer = dict()
    st = common.init_form(user_id, request, '/road/')
    if st:
        answer['redirect'] = st
        return answer
    common.default_form(user_id, array_default, answer, 'road_')
    if request.method == 'POST':
        if 'dt_start' in request.form:
            if answer['dt_start'] != request.form.get('dt_start'):
                answer['locations'] = []
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
            t0 = time.time()
            calculate(answer)
            answer['data'] = []
            print('calculate', time.time() - t0)
        if 'table' in request.form:
            answer['speedometer'] = False
        if 'speedometer' in request.form:
            answer['speedometer'] = True

    answer['title'] = 'Define route'
    sec_route = 0
    if len(answer['data']) == 0:
        answer['dist'] = 0
        answer['data'] = []
        query = ''
        t0=time.time()
        dt = time.mktime(time.strptime(answer['dt_start'], '%Y-%m-%dT%H:%M'))
        try:
            steps = answer['route']['features'][0]['properties']['segments'][0]['steps'] if 'route' in answer else None
        except:
            steps = None
        for i, point in enumerate(answer['locations']):
            if i == len(answer['locations']) -1 :
                break
            s = geodesic(answer['locations'][i], answer['locations'][i+1]).km  # расстояние отрезка
            # определить среднюю скорость
            average_speed = 60
            if steps:
                for step in steps:
                    if i >= step['way_points'][0] and i < step['way_points'][1]:
                        average_speed = step['distance'] / step['duration'] * 3600 / 1000
                        break
            t = s / average_speed * 3600
            sec_route += t
            answer['dist'] += s
            answer['data'].append({
                'number': i+1, 'length': round(s, 3), 'time': round(t), 'dt': dt + int(sec_route),
                'speed': round(average_speed, 1), 'severity': 0, 'count_accident': 0,
                'count_big_accident': 0,
                'dt_show': datetime.datetime.fromtimestamp(dt + int(sec_route)).strftime('%H:%M:%S'),
                'x': round(point[0], k_dig), 'y': round(point[1], k_dig), 'way': round(answer['dist'], 3)})
            x = round(point[0], k_dig)
            y = round(point[1], k_dig)
            query = query + ' or ' if query else query
            query += 'ROUND(longitude,'+ str(k_dig) + ')=' +  str(x) + ' and ROUND(latitude,' + str(k_dig) + ')=' + str(y)
        print('data', time.time() - t0)
        answer['dist'] = str(round(answer['dist'],1)) if answer['dist'] else ''  # общее расстояние
        answer['time'] = common.get_duration(sec_route) if sec_route else ''  # время движения
        answer['count'] = len(answer['data'])
        if query:
            t0 = time.time()
            query = 'select * from {schema}.traffic.accident_analysis where '.format(schema=big_query.catalog) + query
            is_ok, ans_big = big_query.execute_script(query)
            print('big-query', len(ans_big), time.time() - t0)
            if is_ok:
                t0 = time.time()
                count = load_weather(answer, ans_big)
                answer['count_accidents'] = count
                print('weather', 'count=', count, 'time=', time.time() - t0)
                t0 = time.time()
                count = make_data(answer, ans_big)
                print('make_data', 'count=', count, 'time=', time.time() - t0)
            else:
                flash(ans_big, 'warning')
        # временно не пользуемся чтобы не тратить бесплатные обращения
        if len(answer['locations']) > 0:
            get_weather(answer, 0)  # погода в начале пути
            data = answer['data'][0]
            data['weather_condition_weight'] = 79 if 'weather_condition' in data and data['weather_condition'] == 'Clear' else 3
            data['road_condition_weight'] = 81 if 'road_condition' in data and data['road_condition'] == 'Dry' else 4
            define_day_week(answer, 0)
    for data in answer['data']:
        data['show'] = True if answer['switch'] == 'all_route' or 'is_accident' in data and data['is_accident'] else False
    # дополним точки без аварий
    if len(answer['locations']) > 0:
        dop_points(answer)
        calc_data(answer)  # рассчитать сумму весов и общий вес

    if answer['weight'] and sec_route:
        answer['coefficient'] = int(answer['weight'] / (sec_route / 60) / 100)
        answer['empty_coefficient'] = max(0, answer['value_green'] + answer['value_yellow'] + answer['value_red'] -
                                      answer['coefficient'])
    answer['weight'] = common.str1000(answer['weight'])
    common.save_form(user_id, array_default, answer, 'road_')
    return answer
