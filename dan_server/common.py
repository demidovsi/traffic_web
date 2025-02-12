api_key_nasdaq = 'qHziAyeMciFhcGHmpSiz'
import socket
import time
import config
import requests
import json
import base64
import os
import re
from requests.exceptions import HTTPError
import py7zr
from google.cloud import storage
from google.oauth2 import service_account

t = 'w7LCk8Ouwr3DmcKdccKQwpdWwqbCqcOcw5nCuMKyw5zDjsK1wqbDkcOSw4DDiMOrwpJ5XcKZw6HDrMKzw5PCncKyw4rDlsKdwpdmwqTCg3HCv8Ojw5DDjcKqw6DDksOAw4jDm8KdwoBwwqnCqMKrdMKLZG94w6fCpsKcwrrDi8OXwrTCrsOiw5TDjcKiw5fDh23ClMKXwpJ_wp_CqsKiwrJ6w4rCmsKwwovDm2rCmMKqwqLClsKxwoLCqcOSwot3wqHClMKDwo3Dm8KpwrDCn8Oaw5bDnHvCnmnCsMKKw5zClVVwworChcK_w4HDoMOlwrXCt8OTw4LCtsK_w7DCksKHXcKZwp7Cp3HClmXCkcKbwr59woFkwrrCtcKYwqXCuMODwpljwrnCqMKkwofCpMKdemrDk8Ofw4fCjcKyfcOFwr3DgHZ0wojCq8KxwpHCtsOiw6DCvMKuw5fCqsKEw5HCp8Kywo7CjsK8wrfCu8KFwrx7wpHCocOewqvCmsKrwr3DjsKQwrbCvMKwwpXCssK3wqXCjMKrwrvDhMK4wqTCqsK_w6vClMKawqfCkMKhwqJ1wo_CssKcw5HCusKxwrzDncKfwrDCuMOWwq7DicOqw4PCpcK0w6vCpcOCwqjDoMKqwp7CusK9woDCnHXDkMONwqHCpcOCw4bCnsKIwqDCuMOCwovDj8K-w4fCosOnwrnDhMKKwqvCosOAwq7CqMKGwovCrcOhw4jChcKHw6PDqMKFdcOKw5HCr8Kgw4TDmsK_wovCrMObw7PCu8KewozCucKhw7BjwqjCscKtw5nCg8KAw6HDp8OGwq3CtMKVwprCm8Ovw5LCmcKnw67DnMKzwo_Cm8KqwqfCosOadcKUwqzCmcKxw4TCgMKuw4bCrHbCssOGwq_DksOcw6fCpsKtw4fCtMOWwrLCnMKcwrrCt8OkwqDCgHPDkcOGw4PCpsONw4XCqcK9w6PCl3vDg8KtwrnCmcKgwq3DqMOKd8KaY8Kaw4HCrcKGXsKMwqvCvcK4wqTCpsOpwpbCscK1wrnCtcKrw6vDg8K9wrXDmsK9w6HCvcK0wp_DiMOBw4TCh3XCqcOGw5HCnMK7w6jCtsKpbsOcwrXCnsKNwrrCo8KhwrXCucKnw6Vvwr99wpvCrcOcwprChMKYwr7CvMK6wpLDqcK5wq10wrXClsKZwq_Cv8K7w4PCo8OJwr3Dg8Kpw6JresOPw6fCgmR2w4HCjsKywpLCrsKhwqXCr8Ofw4jCp8OIw6TCtsOCwqHDqsOhw4jClsK2Y8K1wpzCucKeesKawrvCtsKBwrnDh8K5wrjClMObw4vCksKFw4DDgsKVwojDhcK5w4rCp8K5wpDCvMKXw5nCgsKodsKvw4XCkMKyw6_DpMK3wqXCvMOYwo3CtMORwqjCssKGw4XDisKqwpjDhcKmw4nCrMOZwoZ1wrHDj8KcwpDCtsOEwrHClcKEwrPCpsKyw4HCvMKxwpfCgsK9wrjDocKZwrrCn8OBwqDDkcKKwpnCksOTw53CqMKhw6jCnsOGe8KiwpvCosK8w4HCtsK9wojDg8Odw6t7w5V_wprDkMOfwovCiMKPwpXDisKrwr3DisOow4HCtsOowpvDhMKhwqrDg8OEwqHDgMOrwql9wpzCrcOCw4fCqMKff8K2wrLDhcKUwprCsMOgwprCm8OIw5PCksKyw53CpsK4wonDmsOCw4DCscOCwqjCp8K5w4TCosKsc8K6w4fCo8Khw4XCucKpwqXDnMKae8Klw5PDnsKRwo7Dh8Kjw7LCncK7wrHCpMKbw5zCrcKcwrHCmsOPwpnDhsKpw5fCo8KuwqLDicK4w4nCuMK0fMKJw4XDl8OzfMORwo7CtsKcw4h_wqzClMObwpXCtcKQw4nDmMK4wqfDo8KlwqLCjsOYwrrCtsKowq7DqcOowrXCsnHCq8OEw6rCln17w5zCsMKjwr7DpMOfwpnCiMOQwqbClcK9w6bDpcKYwoHDscOkw4_CrcK3wq7CtcKNw45jdMKww4DClsOGwpzCsMOIwrfCrsOkw5J-wq7DrcOSfcKJwqvDhcOIwqvCqsKDw4TCqsOFd2jCucOQw5rDgcKzw5PDncKMwonDiMKswpHCv8K_wrjChcKlw5HDmMONwqXCsGzCtsKnw6_CjsKswqvDocKkwp3Ck8OswqbCicKow5vCt37Cr8Otw6rDhcKwwr7CusKvfMOTwpzCusKbw6Z_ecKTwr7Dm8K3woHDqsOnw4HCmcOaw4rCksOJw4TDlcKpwqvDpcOiwrHCjsOBwpLCksKbwr1twozCtsK-w5DCoMKbw4HCvMKbwpXCpcKbe8Kww6XDk8Klf8OjwrnDoMKswptjwoHDjcOxe8KmeMODwrTCmsKRw57DgMKYdMOUwpfCj8Kiw4vDoMOEwozDn8Olw4PClMK0asK0wqrDk8KiwofCrsKbwrvDicKnw5HCsMK6wqXCvMOXwr3DkcOqw5vCkcKNwrvDi8OLwpzDjm_CncKjw6LCq3XCt8K_wqjCp8KUwrzDmMK-wofCscOHwp_Cs8OrwrrCt8Kzwr7Dq8K8wrfCtsKlwoDCi8Obwqlqc8OEw4nDhMKEwr_Cp8KwwrHCvcKxwo7CkcOJwrfCg8Kjw6LDpsODwobCtMKpwpvCmMObwoF9wpzDgsOHwpzCqMOHw5DDhcKpwqTDhMOFw43DscOHwpfChMK9wrPDtMKpwrbChcKCwrjCq8KMYsKUwq_CtMKdwrTDq8K0wqDCisKgw5PCo8KuwqrDlsK6wrXDk8Ofw5t0wpt5wp3CncKpanTCi8OPwrfCmcKGw4bDosK8wozCn8OFwpnCrsOmwqF9wo7DgsKzw6HClcKtwpvCvcONwrtrwqjCmMOfwqbClMKfw5vCtsKFdsK4wrrCtcKjwqfDocKzb8OLwrfCqsKvwqx-wqTCocODwp3Cj8Kyw5HDlMOAwr7CrsOZw43CjsOlwrzCm8Kvw6DDiMKbwpXDhsKcw47CrcK5wqPCpcKOw6PChcKbwq7CucK7wpvDicKowrTCo8Kaw4HDlMKSwqPDgMOhwrTCj8Oow4HDgsKHwp_CkMKSwqXCvsKDY8KawrDCscKWwqfDpsOCw4fCkcOKw5HCo8Kuw5_DmsKTwpTDocKnw4HCiMK5cMKawq_Dq2rCh8Ksw5bCtcK6wrfDncKhwpbClsKnw4jDgMKyw6_CpsKiwoLCqMOfw6J4wpjChHrCvMOrwp3CpsKZw4zDncOCw4XCr8OYwod1wrDCmcKOw5HDgsOfwrfCssKrw6PDlsKywrzCjMKGwpnCvcKHaMKXwrbCtMKawpHDnsOAwpfCmcKxw5x2wo3Cp8OAwqXCk8OowpzDssKuwp3CjcK-w4HDpHpewpLDm8OYwp7CssK6wqbCp8Kpw4jDlMKUw5HCrMK-wr3CqMOKwpzDnMKVwqLCisKHwrzCqMKIwqvClMOGw5HCt8Kmw4PDhsKVwrPCpMK1wpTCvMKuw6HCt8Kew6bDicOtwrPDjcKJwqTCsMOrwofClsK3wr7ClMKYwrXCsMOZwqjCmsOhwrDCjcOHw4fDg8KCwpTCqsOgw6h2w4HCp8Kpwq3DmHzCmcKHwrbDksK8wprDnMKlwp7CrcOVw4zCp8OIwr_CssKFwofDr8K9w4vCvcKqworCssKLwqvCrHrCrMK5wrTCsXrDrcKxw4Fuw5PCq8KAwovCpsOcwpXCk8Oaw4HDsMKFwr_CoMKgwonCqHxrwpLCvsKlwpTCiMODwqfDjMKWwrLClcKWw4TDrsOBwph_w57DgsK9wq3DhcKmwp_CmcOZwpZswpbDgsKqwrjDgcONw5LCm8Knw5fCtcOBw4rCosOTwq_Cn8Otw6TDg8KQw4DCosK6wojCqXnChcKqwrvCmsKxwoTCqcKzw4R8w4DCrsOAwrTDscOXw4PCgsK-w4HCu8KewpzCjsK3wprCrGvCqsKTw4TCpMKrwr3DjsOIw4PCt8Kdw4bCuMKww4TCosKFwoTDhcOKw516wpjCqsKTw4zDh8KMwoDCvcK5w5HCl8KFwr_CmsKawrPCocK7wozCjMOnwrvCv8Kmw6fDnsOJwrbCmMKcw4nCjsOPwqHCqsKSwqDCs8KXwpfDscKiwonCj8K1wrPCt8OKw5PDnsKxwofCqsK5wr_ClcKYaMKfw4PDqcKLZ3bDkcKZwrrDh8OiwqjCp8K0w5bCqsKvw43Dr8K5wr7ClcOowrrDs8KIwqDCpsKdwoHCq8Kof8KVwrXCpcK2wpPDgMOZwpXCicK8w5vClsKsw6jCv8KmwpTDmMKcw4fCrsK-wpLCq8OEw7DCi8KVd8Ohw47CksKWwrnCp8Knwq3Dj8K6wpPCvMKuw5vCg8Kiw6fDo8Klwq3CmcKowobDjcOiwohodsOYwrfDh8KjwqnDqMOEdsKiwqbCvsK8w4PCtsKkwp_DgMK8w593wqp5w4XCmsOjwoZ_fcK2w5HCgsKbw5PDncOHesOWw5vCnsKcw5zDgsOAwqfDgcOKwqrCu8Kbf8KFwq_DpMKoacK5w5vCr8KFw4jCvsKmwojChMOkwpLCmMK7w6DCtsK5wpDDpcKjw4jCnsK4wrHCnMKnwqnCmmfCi8Kaw51_wpTDjcOiwprCicK_wpLCvsKQw4vDh8KpwqvDmcOGw4LCtsKuZ8KQwprDkcKfwqTCtcKzwq7CvcKXw5vDgMKqbsK-wo7DhcKNw5PDnnpqwqTCnsKnwonCt3xvwqbDiX3CicKFwr7CqG_CmsK8w4jCgXDCm8KQeMK2w6XCknldwpnDlMOmwq3DjsKmw4PCtcOcwqHClMKtw5bChcKJb8KZw5rCvcK1w5fDj8K3wofDm8OVwrrCpsObw6DDsHHDnMKZwo_DhsOjwpXCrMKrw5zDksOEwr3Dm8Kcwod2wqDCmnzCisKlw5nCrsKqwqXDmMOtwqnDm8KuwrjCucOcwpXClsKnw5nDmMK9w4PCpcOSw4PCsMKQwo9rfMOaw5zCtsKiw6XDpcOZwq3DjVrCiXbCmWVkd8KdwprChcKEwqvCn8KKe8Klwpt_wpPCqMKgwoFxwqnCpsKccMKJWsKww4vDq8KcwpLCucOcw4xxwonCl8KRwrzCt8Oiw5PCvsKUwqbCn8KuwqDDmsOgw6_CssOdwqt9wr3DpsKjwprCsMOPwpHCssK-w6TCnsODcsOdw4TDgMOOw5_ConzCnsOsw6XDombClVhxw4rDpsKfwpjCssOJw5jDgcK4wpnCqXRlw5bDl8K_w4rDqsKqfGzDpsOSw6_CuMORan3CvcOmwqPCmsKww4_DhMK_wrjDqsKdwrfCssObwpLCv8OJw6LDlcK7X8KjwpHCnMKlw57CrMK3wrXDp8KmwqLCusOTw4fCtMOBw5bDp8KJc8Knw4LCrsK_w6nDpMKswrLDqcOdwpx-wolawrfDisOrwqTCpn7CmcKSw4bDhsOuwp3Cu8Kyw53DisK3wr_DmMOgwrbCsMKlw5TDqcKxwpjCp8Kww4vDq8KcZXPDoMKUfsKyw5zDocOIwrbCkMKPa3zDmsOcwrbCosOlw6XDmcK8wp5owojCtcOawpnCpcK4w4nDmMOBwrvCmcKpdGXDlsOXwr_DisOqwqp8bMOuw6jDsXLDkMKnwr7CvcOjwpnClMK0w5PDln3CssOmw5zCg8K1w53DhcK6w47CpsOmfmzDpMOWw67CpcONwpnDg8K3wqbCrGh0wqPCksK6wrjDqcOYw4DCr8Kbw4fCsMOHw6DDlMK8wrPCpMOkw5tpwp1owr_DgsOYwq3CmsK2w5nDmMK9wrPCpMKiwod1wqXClHvCiMOgw5HCumvDnsOkw5_CtsOfwqHCssK7w5jCl8KWwrPDn8ORw4N9w5rDnsOBZcKawoNtw4_DpcOZw4PCosOpw6TDn8Kjw43Cp8K8wrfDoMKiVX7CisKFwrbCvsOmw5bDgMKow4_Dk8K0w43CpcOTwrzCqsKZw64='
bucket_name = 'dan_alex'
current_path = ''


def get_value_config_param(key, par, default=None):
    for unit in par:
        if unit['code'] == key:
            if 'is_number' not in unit or unit['is_number']:
                return int(unit['value'])
            return unit['value']
    return default


def get_difference(caption, value_old, value):
    if value != value_old:
        return caption + ': ' + str(value_old) + ' -> ' + str(value) + '; \n'
    else:
        return ''


def get_param_work(caption, value):
    return caption + ': ' + str(value) + '; \n'


def get_param_telegram():
    par = load_config_params('TG')
    token_bot = decode('abcd', get_value_config_param('token_bot', par))
    chat_id = get_value_config_param('chat_id', par)
    return token_bot, chat_id


def get_difference_config_params(par, answer):
    st_difference = ''
    st_param_work = ''
    for data in par:
        for unit in answer:
            if unit['code'] == data['code']:
                data['is_number'] = unit['is_number']
                if data['value'] != unit['value']:
                    st_difference += get_difference(unit['sh_name'], data['value'], unit['value'])
                data['value'] = unit['value']
                st_param_work += get_param_work(unit['sh_name'], unit['value'])
                break
    return st_difference, st_param_work


def get_computer_name():
    st = socket.gethostbyname(socket.gethostname())
    st = '' if st == '127.0.0.1' else st
    return socket.gethostname() + '; ' + st


def decode(key, enc):
    # раскодировать
    dec = []
    enc = base64.urlsafe_b64decode(enc).decode()
    for i in range(len(enc)):
        key_c = key[i % len(key)]
        dec_c = chr((256 + ord(enc[i]) - ord(key_c)) % 256)
        dec.append(dec_c)
    return "".join(dec)


def encode(key, text):
    enc = []
    for i in range(len(text)):
        key_c = key[i % len(key)]
        enc_c = chr((ord(text[i]) + ord(key_c)) % 256)
        enc.append(enc_c)
    return base64.urlsafe_b64encode("".join(enc).encode()).decode()


def login_admin():
    result = False
    token_admin = ''
    lang_admin = ''
    txt_z = {"login": "superadmin", "password": decode('abcd', config.kirill), "rememberMe": True}
    try:
        headers = {"Accept": "application/json"}
        response = requests.request(
            'POST', config.URL + 'v1/login', headers=headers,
            json={"params": txt_z}
            )
    except HTTPError as err:
        txt = f'HTTP error occurred: {err}'
    except Exception as err:
        txt = f'Other error occurred: : {err}'
    else:
        try:
            txt = response.text
            result = response.ok
            if result:
                js = json.loads(txt)
                if "accessToken" in js:
                    token_admin = js["accessToken"]
                if 'lang' in js:
                    lang_admin = js['lang']
            else:
                token = None
                return txt, result, token
        except Exception as err:
            txt = f'Error occurred: : {err}'
    return txt, result, token_admin, lang_admin


def send_rest(mes, directive="GET", params=None, lang='', token_user=None):
    js = {}
    if token_user is not None:
        js['token'] = token_user
    if lang == '':
        lang = config.app_lang
    if directive == 'GET' and 'lang=' not in mes:
        if '?' in mes:
            mes = mes + '&lang=' + lang
        else:
            mes = mes + '?lang=' + lang
    else:
        js['lang'] = lang   # код языка пользователя
    if params:
        if type(params) is not str:
            params = json.dumps(params, ensure_ascii=False)
        js['params'] = params  # дополнительно заданные параметры
    try:
        headers = {"Accept": "application/json"}
        response = requests.request(directive, config.URL + mes.replace(' ', '+'), headers=headers, json=js)
    except HTTPError as err:
        txt = f'HTTP error occurred: {err}'
        return txt, False, None
    except Exception as err:
        txt = f'Other error occurred: {err}'
        return txt, False, None
    else:
        return response.text, response.ok, '<' + str(response.status_code) + '> - ' + response.reason


def write_log_db(level, src, msg, page=None, file_name='', law_id='', td=None, write_to_db=True,
                 write_to_console=True, token=None):
    st_td = '' if td is None else "td=%.1f sec;" % td
    st_file_name = '' if file_name is None or file_name == '' else 'file=' + file_name + ';'
    st_law_id = '' if law_id is None or law_id == '' else 'law_id=' + str(law_id) + ';'
    st_page = '' if page is None or page == '' else 'page=' + str(page) + ';'
    if write_to_console:
        print(time.asctime(time.gmtime(time.time())) + ':', level + ';', src + ';', st_td, st_page, st_law_id,
              st_file_name.replace('\n', ' '), msg.replace('\n', ' '), flush=True)
    if not write_to_db:
        return
    if token is None:
        answer, is_ok, token, lang = login_admin()
    else:
        is_ok = True
        answer = ''
    if is_ok:
        page = 'NULL' if page is None or page == '' else page
        law_id = '' if law_id is None else law_id
        file_name = '' if file_name is None else file_name
        td = 'NULL' if td is None else float("%.1f" % td)
        st = "select {schema}.pw_logs('{level}', '{source}', %s, {page}, '{law_id}', %s, {td})".format(
                schema=config.schema_name, level=level, source=src, page=page, law_id=law_id, td=td
              )
        answer, is_ok, status = send_rest(
            'v2/execute', 'PUT', params={"script": st, "datas": "{comment}~~~{file_name}".format(
                comment=msg, file_name=file_name)},
            lang=config.app_lang, token_user=token)
        if not is_ok:
            print(time.ctime(), 'ERROR', 'write_log_db', str(answer), st, flush=True)
    else:
        print(time.ctime(), 'ERROR', 'write_log_db', str(answer), flush=True)


def get_duration(td):
    result = ''
    if td is None:
        return result
    if '<' in str(td):
        return str(td) + ' sec'
    tdr = int(td + 0.5)
    if tdr == 0:
        return '< 0.5 sec'
    if tdr >= 86400:
        result = str(tdr // 86400) + ' day'
        if tdr // 86400 != 1:
            result = result + 's'
        tdr = tdr % 86400
    if tdr // 3600:
        result = result + " {hour:02}:{minute:02}:{second:02}".format(
            hour=tdr // 3600, minute=tdr % 3600 // 60, second=tdr % 3600 % 60)
    else:
        result = result + " {minute:02}:{second:02}".format(minute=tdr % 3600 // 60, second=tdr % 3600 % 60)
    return result


def load_config_params(name_function):
    url = "v1/select/{schema}/v_nsi_functions_params?where=name_function='{name_function}'".format(
        schema=config.schema_name, name_function=name_function)
    answer, is_ok, status_code = send_rest(url)
    if is_ok:
        answer = json.loads(answer)
        return answer


def translate_to_base(st):
    if st is None:
        return st
    st = st.replace('\n', '~LF~').replace('(', '~A~').replace(')', '~B~').replace('@', '~a1~')
    st = st.replace(',', '~a2~').replace('=', '~a3~').replace('"', '~a4~').replace("'", '~a5~')
    st = st.replace(':', '~a6~').replace('/', '~b1~').replace('&', '~b2~').replace('\r', '~R~')
    return st


def translate_from_base(st):
    if st is not None:
        st = st.replace('~A~', '(').replace('~B~', ')').replace('~a1~', '@').replace('~LF~', '\n')
        st = st.replace('~a2~', ',').replace('~a3~', '=').replace('~a4~', '"').replace('~a5~', "'")
        st = st.replace('~a6~', ':').replace('~b1~', '/').replace('~b2~', '&').replace('~R~', '\r')
    return st


def send_tg(st):
    token_bot, chat_id = get_param_telegram()
    url = f'https://api.telegram.org/bot{token_bot}/sendMessage?' + f'chat_id={chat_id}&text={st}&parse_mode=html'
    answer = requests.get(url).json()
    return answer

#----------------------------------------------------------------
def save_file_bucket(file_name, text, with_zip=True):
    """
    Записать файл в облако
    :param file_name - имя файла
    :param text: - текст файла
    :return:
    """
    global bucket
    # file_name = str(id) + '.txt'
    file_name = os.path.splitext(str(file_name))[0] + '.txt'
    f = open(file_name, 'w', encoding='utf-8')
    with f:
        f.write(text)
    if with_zip:
        arch_path_file = os.path.splitext(file_name)[0] + '.7z'
        with py7zr.SevenZipFile(arch_path_file, 'w') as arch:
            arch.writeall(file_name)
    else:
        arch_path_file = file_name
    blob_name = os.path.basename(arch_path_file)  # The name of file on GCS once uploaded
    blob = bucket.blob(blob_name)
    blob.upload_from_filename(arch_path_file, timeout=3600)  # The content that will be uploaded
    try:
        os.remove(file_name)  # удалить файл с документом
        if with_zip:
            os.remove(arch_path_file)  # удалить и архивный файл
    except:
        pass


def get_array_text(text, limit=1000):
    if len(text) < limit:
        return [text]
    result = []
    while len(text) > 0:
        st = text[:limit]
        if len(st) < limit:
            result.append(st)
            text = ''
        else:
            i = len(st) - 1
            while i>0 and st[i] != '.':
                i -=1
            result.append(st[:i+1])
            text = text[i+1:]
    return result


def write_history(values, theme_id, token):
    values['theme'] = theme_id
    params = {"schema_name": config.schema_name, "object_code": "rss_history", "values": values}
    ans, is_ok, status = send_rest('v2/entity', 'PUT', params=params, token_user=token)
    if not is_ok:
        write_log_db(
            'error', 'write_history', f"Ошибка {ans}", file_name=get_computer_name())
    else:
        return int(json.loads(ans)[0]['id'])


def make_search(word, txt):
    result = 0
    if word:
        word = word.strip()
        if word:
            if word[0] == '^':
                word_s = r"\b{word}\b".format(word=word[1:-1].strip())
                matches = re.findall(word_s, txt)
            else:
                word_s = r"\b{word}\b".format(word=word)
                matches = re.findall(word_s, txt, re.IGNORECASE)
            return len(matches)  # количество вхождений в текст
    return result


def extract_text(element, default=''):
    if element is not None:
        result = element.text
        if result:
            return result.strip()
        else:
            return default
    return default

def make_description(init_description):
    array = [
        '<![CDATA[', ']]>', '<p>', '</p>', '<!-- wp:paragraph -->', '<!-- /wp:paragraph -->', '<!-- wp:image -->',
        '<!-- wp:heading -->', '<blockquote class="wp-block-quote">', '</blockquote>', '<ol>', '</ol>',
        '<li>', '</li', '<ul>', '</ul>', '<em>', '</em>'
    ]
    array_begin = [
        '<!-- wp:html -->', '<!-- wp:image -->',
    ]
    array_end = [
        '<!-- /wp:html -->', '<!-- /wp:image -->'
    ]
    if init_description:
        for data in array:
            init_description = init_description.replace(data, '')
        description = ''
        init_description = init_description.split('\n')
        skip = False
        i = 0
        while i < len(init_description):
            row = init_description[i].strip()
            if row in array_begin:
                skip = True
            if not skip:
                description += row + '\n'
            i += 1
            if row in array_end:
                skip = False

        # description = description.replace('<a href="', ' ')
        while '<a' in description:
            ind_begin = description.index('<a')
            ind_end = description.index('</a>')
            st = description[ind_begin:ind_end]
            ind1 = st.index('href="')
            st = st[ind1+6:]
            ind2 = st.index('"')
            st = ' ' + st[:ind2] + ' '
            description = description[:ind_begin] + st + description[ind_end + 3:]

        while '<!--' in description:
            ind_begin = description.index('<!--')
            ind_end = description.index('-->')
            if ind_end > ind_begin:
                description = description[:ind_begin] + description[ind_end + 3:]
            else:
                description = description[:ind_end] + description[ind_end + 3:]

        while '<h2' in description:
            ind_begin = description.index('<h2')
            ind_end = description.index('</h2>')
            if ind_end > ind_begin:
                description = description[:ind_begin] + description[ind_end + 5:]
            else:
                description = description[:ind_end] + description[ind_end + 5:]

        while '<span' in description:
            ind_begin = description.index('<span')
            ind_end = description.index('</span>')
            if ind_end > ind_begin:
                description = description[:ind_begin] + description[ind_end + 6:]
            else:
                description = description[:ind_end] + description[ind_end + 6:]

        while '<figure' in description:
            ind_begin = description.index('<figure')
            ind_end = description.index('</figure>')
            if ind_end > ind_begin:
                description = description[:ind_begin] + description[ind_end + 9:]
            else:
                description = description[:ind_end] + description[ind_end + 9:]

        while '<strong' in description:
            ind_begin = description.index('<strong')
            ind_end = description.index('</strong>')
            if ind_end > ind_begin:
                description = description[:ind_begin] + description[ind_end + 9:]
            else:
                description = description[:ind_end] + description[ind_end + 9:]

        if description[0:4] == '<img':
            i = description.index('/>')
            description = description[i + 2:]

        description = description.split('<br/>')
        if len(description) > 1:
            description = description[1]
        else:
            description = description[0]

        description = description.split('<br />')
        if len(description) > 1:
            description = description[1]
        else:
            description = description[0]

        description = description.split('/div>')
        if len(description) > 1:
            description = description[1]
        else:
            description = description[0]
        while '\n\n\n' in description:
            description = description.replace('\n\n\n', '\n\n')
        description = description.replace('&nbsp', ' ')
        description = description.replace('">', ' ')
        description = description.replace('>', ' ')
    else:
        return ''
    return description.strip()

credentials = service_account.Credentials.from_service_account_info(json.loads(decode(config.kirill, t)))
client = storage.Client(credentials=credentials, project=credentials.project_id)
bucket = storage.Bucket(client, bucket_name)  # указать текущий начальный bucket
