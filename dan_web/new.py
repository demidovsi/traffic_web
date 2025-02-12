from flask import flash
import py7zr
from google.cloud import storage
from google.oauth2 import service_account
import config
import common
from common import add, get, default, find_user, exist, to_string, clear
import datetime
import json
import shutil
import os

array_default = [
    {'key': 'scroll', 'value': 0},
    {'key': 'page_for_return', 'value': 0},
    {'key': 'unit', 'value': {}},
    {'key': 'select_lang', 'value': 'ru'},
    {'key': 'languages', 'value': ['ru', 'en', 'he']},
]

t = 'w7LCk8Ouwr3DmcKdccKQwpdWwqbCqcOcw5nCuMKyw5zDjsK1wqbDkcOSw4DDiMOrwpJ5XcKZw6HDrMKzw5PCncKyw4rDlsKdwpdmwqTCg3HCv8Ojw5DDjcKqw6DDksOAw4jDm8KdwoBwwqnCqMKrdMKLZG94w6fCpsKcwrrDi8OXwrTCrsOiw5TDjcKiw5fDh23ClMKXwpJ_wp_CqsKiwrJ6w4rCmsKwwovDm2rCmMKqwqLClsKxwoLCqcOSwot3wqHClMKDwo3Dm8KpwrDCn8Oaw5bDnHvCnmnCsMKKw5zClVVwworChcK_w4HDoMOlwrXCt8OTw4LCtsK_w7DCksKHXcKZwp7Cp3HClmXCkcKbwr59woFkwrrCtcKYwqXCuMODwpljwrnCqMKkwofCpMKdemrDk8Ofw4fCjcKyfcOFwr3DgHZ0wojCq8KxwpHCtsOiw6DCvMKuw5fCqsKEw5HCp8Kywo7CjsK8wrfCu8KFwrx7wpHCocOewqvCmsKrwr3DjsKQwrbCvMKwwpXCssK3wqXCjMKrwrvDhMK4wqTCqsK_w6vClMKawqfCkMKhwqJ1wo_CssKcw5HCusKxwrzDncKfwrDCuMOWwq7DicOqw4PCpcK0w6vCpcOCwqjDoMKqwp7CusK9woDCnHXDkMONwqHCpcOCw4bCnsKIwqDCuMOCwovDj8K-w4fCosOnwrnDhMKKwqvCosOAwq7CqMKGwovCrcOhw4jChcKHw6PDqMKFdcOKw5HCr8Kgw4TDmsK_wovCrMObw7PCu8KewozCucKhw7BjwqjCscKtw5nCg8KAw6HDp8OGwq3CtMKVwprCm8Ovw5LCmcKnw67DnMKzwo_Cm8KqwqfCosOadcKUwqzCmcKxw4TCgMKuw4bCrHbCssOGwq_DksOcw6fCpsKtw4fCtMOWwrLCnMKcwrrCt8OkwqDCgHPDkcOGw4PCpsONw4XCqcK9w6PCl3vDg8KtwrnCmcKgwq3DqMOKd8KaY8Kaw4HCrcKGXsKMwqvCvcK4wqTCpsOpwpbCscK1wrnCtcKrw6vDg8K9wrXDmsK9w6HCvcK0wp_DiMOBw4TCh3XCqcOGw5HCnMK7w6jCtsKpbsOcwrXCnsKNwrrCo8KhwrXCucKnw6Vvwr99wpvCrcOcwprChMKYwr7CvMK6wpLDqcK5wq10wrXClsKZwq_Cv8K7w4PCo8OJwr3Dg8Kpw6JresOPw6fCgmR2w4HCjsKywpLCrsKhwqXCr8Ofw4jCp8OIw6TCtsOCwqHDqsOhw4jClsK2Y8K1wpzCucKeesKawrvCtsKBwrnDh8K5wrjClMObw4vCksKFw4DDgsKVwojDhcK5w4rCp8K5wpDCvMKXw5nCgsKodsKvw4XCkMKyw6_DpMK3wqXCvMOYwo3CtMORwqjCssKGw4XDisKqwpjDhcKmw4nCrMOZwoZ1wrHDj8KcwpDCtsOEwrHClcKEwrPCpsKyw4HCvMKxwpfCgsK9wrjDocKZwrrCn8OBwqDDkcKKwpnCksOTw53CqMKhw6jCnsOGe8KiwpvCosK8w4HCtsK9wojDg8Odw6t7w5V_wprDkMOfwovCiMKPwpXDisKrwr3DisOow4HCtsOowpvDhMKhwqrDg8OEwqHDgMOrwql9wpzCrcOCw4fCqMKff8K2wrLDhcKUwprCsMOgwprCm8OIw5PCksKyw53CpsK4wonDmsOCw4DCscOCwqjCp8K5w4TCosKsc8K6w4fCo8Khw4XCucKpwqXDnMKae8Klw5PDnsKRwo7Dh8Kjw7LCncK7wrHCpMKbw5zCrcKcwrHCmsOPwpnDhsKpw5fCo8KuwqLDicK4w4nCuMK0fMKJw4XDl8OzfMORwo7CtsKcw4h_wqzClMObwpXCtcKQw4nDmMK4wqfDo8KlwqLCjsOYwrrCtsKowq7DqcOowrXCsnHCq8OEw6rCln17w5zCsMKjwr7DpMOfwpnCiMOQwqbClcK9w6bDpcKYwoHDscOkw4_CrcK3wq7CtcKNw45jdMKww4DClsOGwpzCsMOIwrfCrsOkw5J-wq7DrcOSfcKJwqvDhcOIwqvCqsKDw4TCqsOFd2jCucOQw5rDgcKzw5PDncKMwonDiMKswpHCv8K_wrjChcKlw5HDmMONwqXCsGzCtsKnw6_CjsKswqvDocKkwp3Ck8OswqbCicKow5vCt37Cr8Otw6rDhcKwwr7CusKvfMOTwpzCusKbw6Z_ecKTwr7Dm8K3woHDqsOnw4HCmcOaw4rCksOJw4TDlcKpwqvDpcOiwrHCjsOBwpLCksKbwr1twozCtsK-w5DCoMKbw4HCvMKbwpXCpcKbe8Kww6XDk8Klf8OjwrnDoMKswptjwoHDjcOxe8KmeMODwrTCmsKRw57DgMKYdMOUwpfCj8Kiw4vDoMOEwozDn8Olw4PClMK0asK0wqrDk8KiwofCrsKbwrvDicKnw5HCsMK6wqXCvMOXwr3DkcOqw5vCkcKNwrvDi8OLwpzDjm_CncKjw6LCq3XCt8K_wqjCp8KUwrzDmMK-wofCscOHwp_Cs8OrwrrCt8Kzwr7Dq8K8wrfCtsKlwoDCi8Obwqlqc8OEw4nDhMKEwr_Cp8KwwrHCvcKxwo7CkcOJwrfCg8Kjw6LDpsODwobCtMKpwpvCmMObwoF9wpzDgsOHwpzCqMOHw5DDhcKpwqTDhMOFw43DscOHwpfChMK9wrPDtMKpwrbChcKCwrjCq8KMYsKUwq_CtMKdwrTDq8K0wqDCisKgw5PCo8KuwqrDlsK6wrXDk8Ofw5t0wpt5wp3CncKpanTCi8OPwrfCmcKGw4bDosK8wozCn8OFwpnCrsOmwqF9wo7DgsKzw6HClcKtwpvCvcONwrtrwqjCmMOfwqbClMKfw5vCtsKFdsK4wrrCtcKjwqfDocKzb8OLwrfCqsKvwqx-wqTCocODwp3Cj8Kyw5HDlMOAwr7CrsOZw43CjsOlwrzCm8Kvw6DDiMKbwpXDhsKcw47CrcK5wqPCpcKOw6PChcKbwq7CucK7wpvDicKowrTCo8Kaw4HDlMKSwqPDgMOhwrTCj8Oow4HDgsKHwp_CkMKSwqXCvsKDY8KawrDCscKWwqfDpsOCw4fCkcOKw5HCo8Kuw5_DmsKTwpTDocKnw4HCiMK5cMKawq_Dq2rCh8Ksw5bCtcK6wrfDncKhwpbClsKnw4jDgMKyw6_CpsKiwoLCqMOfw6J4wpjChHrCvMOrwp3CpsKZw4zDncOCw4XCr8OYwod1wrDCmcKOw5HDgsOfwrfCssKrw6PDlsKywrzCjMKGwpnCvcKHaMKXwrbCtMKawpHDnsOAwpfCmcKxw5x2wo3Cp8OAwqXCk8OowpzDssKuwp3CjcK-w4HDpHpewpLDm8OYwp7CssK6wqbCp8Kpw4jDlMKUw5HCrMK-wr3CqMOKwpzDnMKVwqLCisKHwrzCqMKIwqvClMOGw5HCt8Kmw4PDhsKVwrPCpMK1wpTCvMKuw6HCt8Kew6bDicOtwrPDjcKJwqTCsMOrwofClsK3wr7ClMKYwrXCsMOZwqjCmsOhwrDCjcOHw4fDg8KCwpTCqsOgw6h2w4HCp8Kpwq3DmHzCmcKHwrbDksK8wprDnMKlwp7CrcOVw4zCp8OIwr_CssKFwofDr8K9w4vCvcKqworCssKLwqvCrHrCrMK5wrTCsXrDrcKxw4Fuw5PCq8KAwovCpsOcwpXCk8Oaw4HDsMKFwr_CoMKgwonCqHxrwpLCvsKlwpTCiMODwqfDjMKWwrLClcKWw4TDrsOBwph_w57DgsK9wq3DhcKmwp_CmcOZwpZswpbDgsKqwrjDgcONw5LCm8Knw5fCtcOBw4rCosOTwq_Cn8Otw6TDg8KQw4DCosK6wojCqXnChcKqwrvCmsKxwoTCqcKzw4R8w4DCrsOAwrTDscOXw4PCgsK-w4HCu8KewpzCjsK3wprCrGvCqsKTw4TCpMKrwr3DjsOIw4PCt8Kdw4bCuMKww4TCosKFwoTDhcOKw516wpjCqsKTw4zDh8KMwoDCvcK5w5HCl8KFwr_CmsKawrPCocK7wozCjMOnwrvCv8Kmw6fDnsOJwrbCmMKcw4nCjsOPwqHCqsKSwqDCs8KXwpfDscKiwonCj8K1wrPCt8OKw5PDnsKxwofCqsK5wr_ClcKYaMKfw4PDqcKLZ3bDkcKZwrrDh8OiwqjCp8K0w5bCqsKvw43Dr8K5wr7ClcOowrrDs8KIwqDCpsKdwoHCq8Kof8KVwrXCpcK2wpPDgMOZwpXCicK8w5vClsKsw6jCv8KmwpTDmMKcw4fCrsK-wpLCq8OEw7DCi8KVd8Ohw47CksKWwrnCp8Knwq3Dj8K6wpPCvMKuw5vCg8Kiw6fDo8Klwq3CmcKowobDjcOiwohodsOYwrfDh8KjwqnDqMOEdsKiwqbCvsK8w4PCtsKkwp_DgMK8w593wqp5w4XCmsOjwoZ_fcK2w5HCgsKbw5PDncOHesOWw5vCnsKcw5zDgsOAwqfDgcOKwqrCu8Kbf8KFwq_DpMKoacK5w5vCr8KFw4jCvsKmwojChMOkwpLCmMK7w6DCtsK5wpDDpcKjw4jCnsK4wrHCnMKnwqnCmmfCi8Kaw51_wpTDjcOiwprCicK_wpLCvsKQw4vDh8KpwqvDmcOGw4LCtsKuZ8KQwprDkcKfwqTCtcKzwq7CvcKXw5vDgMKqbsK-wo7DhcKNw5PDnnpqwqTCnsKnwonCt3xvwqbDiX3CicKFwr7CqG_CmsK8w4jCgXDCm8KQeMK2w6XCknldwpnDlMOmwq3DjsKmw4PCtcOcwqHClMKtw5bChcKJb8KZw5rCvcK1w5fDj8K3wofDm8OVwrrCpsObw6DDsHHDnMKZwo_DhsOjwpXCrMKrw5zDksOEwr3Dm8Kcwod2wqDCmnzCisKlw5nCrsKqwqXDmMOtwqnDm8KuwrjCucOcwpXClsKnw5nDmMK9w4PCpcOSw4PCsMKQwo9rfMOaw5zCtsKiw6XDpcOZwq3DjVrCiXbCmWVkd8KdwprChcKEwqvCn8KKe8Klwpt_wpPCqMKgwoFxwqnCpsKccMKJWsKww4vDq8KcwpLCucOcw4xxwonCl8KRwrzCt8Oiw5PCvsKUwqbCn8KuwqDDmsOgw6_CssOdwqt9wr3DpsKjwprCsMOPwpHCssK-w6TCnsODcsOdw4TDgMOOw5_ConzCnsOsw6XDombClVhxw4rDpsKfwpjCssOJw5jDgcK4wpnCqXRlw5bDl8K_w4rDqsKqfGzDpsOSw6_CuMORan3CvcOmwqPCmsKww4_DhMK_wrjDqsKdwrfCssObwpLCv8OJw6LDlcK7X8KjwpHCnMKlw57CrMK3wrXDp8KmwqLCusOTw4fCtMOBw5bDp8KJc8Knw4LCrsK_w6nDpMKswrLDqcOdwpx-wolawrfDisOrwqTCpn7CmcKSw4bDhsOuwp3Cu8Kyw53DisK3wr_DmMOgwrbCsMKlw5TDqcKxwpjCp8Kww4vDq8KcZXPDoMKUfsKyw5zDocOIwrbCkMKPa3zDmsOcwrbCosOlw6XDmcK8wp5owojCtcOawpnCpcK4w4nDmMOBwrvCmcKpdGXDlsOXwr_DisOqwqp8bMOuw6jDsXLDkMKnwr7CvcOjwpnClMK0w5PDln3CssOmw5zCg8K1w53DhcK6w47CpsOmfmzDpMOWw67CpcONwpnDg8K3wqbCrGh0wqPCksK6wrjDqcOYw4DCr8Kbw4fCsMOHw6DDlMK8wrPCpMOkw5tpwp1owr_DgsOYwq3CmsK2w5nDmMK9wrPCpMKiwod1wqXClHvCiMOgw5HCumvDnsOkw5_CtsOfwqHCssK7w5jCl8KWwrPDn8ORw4N9w5rDnsOBZcKawoNtw4_DpcOZw4PCosOpw6TDn8Kjw43Cp8K8wrfDoMKiVX7CisKFwrbCvsOmw5bDgMKow4_Dk8K0w43CpcOTwrzCqsKZw64='
bucket_name = 'dan_alex'


def load_inform(answer):
    answer['unit'] = dict()
    ans, is_ok, status = common.send_rest(
        'v2/entity/values?app_code={schema}&object_code=rss_history&object_id={id}'.format(
            schema=config.SCHEMA, id=answer['new_id']))
    if not is_ok:
        flash(str(ans), 'warning')
        return False
    else:
        unit = json.loads(ans)[0]
        if unit['public_date']:
            unit['public_date'] = unit['public_date'].replace('T', ' ')

        unit['title_ru_init'] = unit['title_ru']
        unit['title_en_init'] = unit['title_en']
        unit['description_ru_init'] = unit['description_ru']
        unit['description_en_init'] = unit['description_en']

        answer['unit'] = unit
        return True


def load_file(user_id, filename):
    try:
        credentials = service_account.Credentials.from_service_account_info(json.loads(common.decode(config.kirill, t)))
        client = storage.Client(credentials=credentials, project=credentials.project_id)
        bucket = storage.Bucket(client, bucket_name)  # указать текущий начальный bucket
        temp_dir = common.current_path + '/news/' + user_id
        if not os.path.exists(temp_dir + '/' + filename):
            file_name = os.path.splitext(filename)[0] + '.7z'
            blob = bucket.blob(file_name)
            os.makedirs(temp_dir, exist_ok=True)
            blob.download_to_filename(temp_dir + '/' + file_name)  # это загрузка файла
            with py7zr.SevenZipFile(temp_dir + '/' + file_name, 'r') as arch:
                arch.extractall(path=temp_dir)
            os.remove(temp_dir + '/' + file_name)
            filepath = temp_dir + '/' + filename + '.txt'
            f = open(filepath, 'r', encoding='utf-8')
            with f:
                txt = f.read()
            os.remove(filepath)
            shutil.rmtree(common.current_path + '/news/', ignore_errors=True)
            return txt
    except Exception as er:
        filename = filename if filename is not None else 'None' + '" в облаке недоступен или отсутствует'
        txt = f'ERROR: {er} ' + filename
        flash(txt, 'warning')


def make_info(user_id, answer):
    lang = answer['select_lang']
    answer['unit']['title'] = answer['unit']['title_' + lang]
    answer['unit']['title_init'] = answer['unit']['title_' + lang + '_init']

    answer['unit']['description'] = answer['unit']['description_'+lang]
    answer['unit']['description_init'] = answer['unit']['description_'+lang + '_init']

    if 'full_' + lang not in answer['unit']:
        answer['unit']['full_' + lang] = load_file(user_id, lang + '_' + str(answer['unit']['id']))
        answer['unit']['full_' + lang + '_init'] = answer['unit']['full_' + lang]
    answer['unit']['full'] = answer['unit']['full_'+lang]
    answer['unit']['full_init'] = answer['unit']['full_' + lang + '_init']


def refresh(answer):
    def slave(key):
        if key + '_init' in answer['unit']:
            answer['unit'][key] = answer['unit'][key + '_init']

    slave('title_ru')
    slave('title_en')
    slave('title')
    slave('description_ru')
    slave('description_en')
    slave('description')
    slave('full_ru')
    slave('full_en')
    slave('full')


def define_from_form(request, answer):
    lang = answer['select_lang']
    answer['unit']['title_' + lang] = request.form.get('title')
    answer['unit']['title'] = request.form.get('title')

    answer['unit']['description_' + lang] = request.form.get('description')
    answer['unit']['description'] = request.form.get('description')

    answer['unit']['full_' + lang] = request.form.get('full')
    answer['unit']['full'] = request.form.get('full')


def save(user_id, answer):
    id = int(answer['new_id'])
    values = dict()
    values['id'] = id
    lang = answer['select_lang']
    if answer['unit']['title'] != answer['unit']['title_init']:  # записать в БД
        params = {"schema_name": config.SCHEMA, "object_code": "rss_history", "values": values}
        if answer['unit']['title'] != answer['unit']['title_init']:
            values["title" + '_' + lang] = answer['unit']['title']
            ans, is_ok, status = common.send_rest('v2/entity', 'PUT', params=params, token_user=get(user_id, 'token'))
            if not is_ok:
                flash(str(ans), 'warning')
            else:
                answer['unit']['title_' + lang + '_init'] = answer['unit']['title_' + lang]
    if answer['unit']['description'] != answer['unit']['description_init']:  # записать в БД
        params = {"schema_name": config.SCHEMA, "object_code": "rss_history", "values": values}
        if answer['unit']['description'] != answer['unit']['description_init']:
            values["description" + '_' + lang] = answer['unit']['description']
            ans, is_ok, status = common.send_rest('v2/entity', 'PUT', params=params, token_user=get(user_id, 'token'))
            if not is_ok:
                flash(str(ans), 'warning')
            else:
                answer['unit']['description_' + lang + '_init'] = answer['unit']['description_' + lang]


def prepare_form(user_id, request, new_id):
    answer = dict()
    st = common.init_form(user_id, request, '/news/')
    if st:
        answer['redirect'] = st
        return answer
    common.default_form(user_id, array_default, answer, 'one_new_')
    answer['new_id'] = new_id
    if request.method == 'POST':
        if 'back' in request.form:
            answer['redirect'] = answer['page_for_return']
            add(user_id, 'page_for_return', '')
            add(user_id, 'text_for_return', '')
            return answer
        define_from_form(request, answer)
        if 'select_lang' in request.form:
            answer['select_lang'] = request.form.get('select_lang')
        if 'refresh' in request.form:
            refresh(answer)
        if 'save' in request.form:
            save(user_id, answer)
    else:
        common.write_quest(user_id, request, 'one_new')
        load_inform(answer)

    make_info(user_id, answer)
    answer['title'] = 'Полная информация по новости'
    answer['page_for_return'] = get(user_id, 'page_for_return')
    answer['text_for_return'] = get(user_id, 'text_for_return')
    # для возврата в форму из других форм
    common.save_form(user_id, array_default, answer, 'one_new_')
    return answer
