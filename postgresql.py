import psycopg2

import config
import common


def execute_script(sqltext, params=None, need_answer=True):
    try:
        password = common.decode(config.kirill, config.PASSWORD_DB)[0:-1]  # почему-то так
        connection = psycopg2.connect(
            user=config.USER_DB, password=password, port=config.PORT_DB, host=config.HOST_DB, database=config.DATA_BASE)
        connection.autocommit = True
        cursor = connection.cursor()
        cursor.execute(sqltext, (params,))
        if need_answer:
            result = list()
            if cursor.rowcount > 0:
                for row in cursor:
                    unit = {}
                    for i in range(len(row)):
                        unit[cursor.description[i].name] = row[i]
                    result.append(unit)
            return True, result
        else:
            return None, None
    except Exception as e:
        text_error = f"{e}"
        return False, text_error