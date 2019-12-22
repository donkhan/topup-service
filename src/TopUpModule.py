import httplib
import logging
import sys
import time
from utils.md5utils import md5
import ConfigParser
import urllib
from dbutils import dboperation
from utils import propertyparser
from utils import price_utils
import os
import datetime
import re


sys.path.append("dbutils")


current_milli_time = lambda: int(round(time.time() * 1000))


def get_base_parameters():
    key = current_milli_time()
    return {'login': login, 'key': key, 'md5' : md5(login + token + str(key))}


def prepare_payload(base_params, request_params):
    base_params.update(request_params)
    return base_params


def process(params):
    conn = httplib.HTTPSConnection(address)
    conn.request("POST", endpoint,params,{ "Content-Type" : "application/x-www-form-urlencoded" })
    response = conn.getresponse()
    return response


def topup_account_balance():
    return propertyparser.parse_property(process(urllib.urlencode(prepare_payload(get_base_parameters(),
            {'action' : 'check_wallet'}))).read())


def product_detail_of_no(post_data):
    mobile_no = post_data['mobileNo'][0]
    return process(urllib.urlencode(prepare_payload(get_base_parameters(),
            {'action' : 'msisdn_info','destination_msisdn' :mobile_no, 'return_service_fee': 1})))


def operators(country_id):
    return process(urllib.urlencode(prepare_payload(get_base_parameters(),
            {'action' : 'pricelist', 'info_type': 'country', 'content' :country_id})))


def product_detail_of_operator(post_data):
    operator_id = post_data['operatorId'][0]
    logging.debug("Operator Id %s",operator_id)
    return process(urllib.urlencode(prepare_payload(get_base_parameters(),
            {'action' : 'pricelist','info_type':'operator','content' :operator_id, 'return_service_fee': 1})))


def get_topup_countries():
    dict = propertyparser.parse_property(process(urllib.urlencode(prepare_payload(get_base_parameters(),
                {'action': 'pricelist', 'info_type': 'countries'}))).read())
    return map(make_json,zip(dict.get('country').split(","), dict.get('countryId').split(",")))


def can_top_up(post_data):
    result = get_access_control(post_data['accountName'][0], post_data['retailPrice'][0])
    return result


def cost_data_of_product(data):
    product_data = propertyparser.parse_property(product_detail_of_operator(data).read())
    try:
        index = product_data['productList'].index(data['product'][0])
    except ValueError:
        return None
    return product_data['retailPriceList'][index],product_data['wholeSalePriceList'][index],product_data['serviceFeeList'][index]


def top_up(data):
    account_name = data['accountName'][0]
    mobile_no = data['mobileNo'][0]
    logging.debug("Top Up Requested for %s by %s mode %s ", mobile_no, account_name,mode)
    product = cost_data_of_product(data)
    logging.info("Product Price " + str(product))
    if product is None:
        return httplib.BAD_REQUEST,"Product is not available with the given Operator"
    sender_mobile = data['senderMobileNo'][0]
    can_topup = get_access_control(account_name, product)
    if can_topup[0] == False:
         return httplib.UNAUTHORIZED,can_topup[1] + ".Please contact Finance Manager"
    params = prepare_payload(get_base_parameters(), {'action' : mode, 'destination_msisdn': mobile_no, 'msisdn':sender_mobile,
                                                 'product':data['product'][0],'return_service_fee': 1})
    logging.debug("Params %s " , str(params))
    dump_file = open(get_file(account_name,mobile_no),"w")
    dump_request(dump_file,params)
    if data.has_key('smscontent'):
        params.update({'smsContent':data['smscontent'][0]})
    response = process(urllib.urlencode(params))
    if response.status == httplib.OK:
        logging.debug("Topup Http Status is Success for %s ",mobile_no)
        topup_response = response.read()
        dump_response(dump_file,topup_response)
        error_tuple = parse_and_insert(topup_response, account_name, product, params['key'],data['product'][0])
    else:
        dump_response(dump_file,"Did not get proper response. status " + response.status + " content " + response.read())
    if error_tuple[0] != 0:
        logging.debug("Topup Failure for %s. Error Code %d Error Text %s",mobile_no,error_tuple[0],error_tuple[1])
        return httplib.UNAUTHORIZED,error_tuple[1]
    return httplib.OK,topup_response


def get_access_control(account_name, product):
    account = dboperation.get_account_by_name(account_name)
    amount = price_utils.adjusted_price(product[0],product[1],account['profitPercentage'])
    if not account:
        logging.error("Account does not exist")
        return False,'Account not exist'
    if account['status'] == 'I':
        logging.error("Account is in inactive state")
        return False,'Account is in not active'
    logging.debug("Account " + account_name  + " Account Balance " + str(account['balance'])
                  + " Credit Allowed:" + str(account['creditAllowed']) + " Credit Limit " + str(account['creditLimit']))
    logging.debug("Topup Amount " +  str(amount))
    if account['creditAllowed'] == 0:
        logging.debug("Credit is not allowed for this account ")
        if account['balance'] <= float(amount):
            logging.debug("Balance is less than Retail Price. so Not allowing")
            return False,"Credit Not allowed for this account and Balance is less than " + str(amount)
        else:
            return True,
    if account['creditAllowed'] == 1:
        logging.debug("Account Balance %s Retail Price %s", account['balance'], amount)
        post_balance = account['balance'] + account['creditLimit'] - float(amount)
        logging.debug("Likely Account Balance with credit Limit after this transaction %s", str(post_balance))
        if post_balance >= 0:
            return True, ''
        else:
            logging.error("Credit Limit is reached")
            return False, "Credit Limit is reached"


def parse_and_insert(data, account_name, product, unique_key,product_name):
    account = dboperation.get_account_by_name(account_name)
    dict = propertyparser.parse_property(data)
    logging.info(dict)
    error_code = int(get_from_dict(dict,'error_code'))
    error_text = get_from_dict(dict,'error_txt')
    reason = get_from_dict(dict,'reason')
    if error_code == 0:
        status = 'SUCCESS'
    else:
        status = 'FAILURE'
        reason = error_text
    agent_price = price_utils.adjusted_price(float(product[0]),float(product[1]),float(account['profitPercentage']))
    service_fee = get_from_dict(dict,'service_fee','0')
    total_cost = agent_price + float(service_fee)
    dboperation.update_account_balance_by_name(account_name, -1 * total_cost,["Top Up Transaction", -1 * total_cost,
                    account_name, get_from_dict(dict,'transactionid'), get_from_dict(dict,'mobileNo'),
                    get_from_dict(dict,'operator'), get_from_dict(dict,'country'), get_from_dict(dict,'msisdn'),
                    product_name, 'TOPUP', account_name, unique_key, 0,
                    float(product[0]),float(product[1]), float(product[2]), get_from_dict(dict,'destinationCurrency'),
                    agent_price,reason,status])
    return error_code,error_text


def get_from_dict(dict,key,default_value=''):
    if dict.has_key(key):
        return dict.get(key)
    return default_value

def make_json(t):
    return {'country': t[0], 'countryid': t[1]}


def current_time():
    now = datetime.datetime.now()
    return str(now)


def dump_request(dump_file,params):
    dump_file.write("Request to Transfer-To @  " + current_time() + ".....\n")
    dump_file.write(str(params))
    dump_file.write("\n----------------------------------------------------------------------------------\n")
    dump_file.flush()


def dump_response(dump_file,topup_response):
    dump_file.write("Response from Transfer-To @  " + current_time() + ".....\n")
    dump_file.write(topup_response)
    dump_file.write("\n------------------------------------------------------------------------------------\n")
    dump_file.flush()


def get_file(account_name,mobile_no):
    file_name = dump_folder + "/" + str(datetime.date.today()) + "-" + account_name + "-" + mobile_no + ".rr"
    file_name = file_name.replace("@","-")
    logging.debug("Dumping in File %s",file_name)
    return file_name


def get_content(path):
    r = re.search("(/dump/)([0-9]{4}\-[0-9]{2}\-[0-9]{2})(/)([a-zA-Z0-9.@]+)(/)(\+[0-9]+)",
                path)
    file_name = dump_folder + "/" + r.group(2) + "-" + r.group(4) + "-" + r.group(6) + ".rr"
    file_name = file_name.replace("@","-")
    logging.debug("File Dump expected is " + file_name)
    if os.path.exists(file_name):
        fd = open(file_name)
        content = fd.read()
        fd.close()
        return content
    logging.error("File does not exist in " + dump_folder)
    return None

config = ConfigParser.ConfigParser()
config.read("conf/transferto.ini")
login = config.get("credentials",'login')
token = config.get("credentials",'token')
address = config.get("transferto",'api-host')
endpoint = config.get("transferto",'end-point')
mode = config.get("transferto",'mode')
dump_folder=config.get("log","dump_folder")