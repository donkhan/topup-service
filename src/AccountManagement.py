import sys
import json
import logging
from dbutils import dboperation
from utils import urlutils
from utils import propertyparser
from utils import price_utils

sys.path.append("dbutils")


def account(name):
    acc = dboperation.get_account_by_name(name)
    if not account:
        return None
    return json.dumps(acc)


def create_account(post_data):
    acc_name = post_data['accountName'][0]
    logging.debug("Going to create account with name " + acc_name)
    acc = dboperation.get_account_by_name(acc_name)
    if acc:
        logging.error("Account exist. Returning None")
        return None
    dboperation.create_account_by_name(acc_name,
                                       post_data['balance'][0], json.loads(post_data['creditAllowed'][0]),
                                       post_data['status'][0], post_data['creditLimit'][0],
                                       post_data['profitPercentage'][0])
    acc = dboperation.get_account_by_name(acc_name)
    dboperation.make_account_creation_ledger_entry('Create Account', post_data['balance'][0], acc_name, '', '', '',
                    'Malaysia', '', '','GENERAL',
                    post_data['createdBy'][0], '', acc['balance'], '', '', '', 'MYR',0)
    logging.debug("Account Created...")
    return json.dumps(acc)


def update_account_balance(account_name, data):
    amount = float(data['amount'][0])
    balance = dboperation.update_account_balance_by_name(account_name, amount,
            [data['description'][0], amount, account_name, '', '', '', '', 'Malaysia', '', 'GENERAL',
                                data['entryMadeBy'][0],'', 0,'','','','MYR',0,'','SUCCESS'])
    return json.dumps({"balance":balance,"account_name":account_name})


def update_account(account_name, data):
    acc = dboperation.get_account_by_name(account_name)
    if not acc:
        return None
    if data.has_key('creditAllowed'):
        acc['creditAllowed'] = json.loads(data['creditAllowed'][0])
    if data.has_key('status'):
        acc['status'] = data['status'][0]
    if data.has_key('creditLimit'):
        acc['creditLimit'] = json.loads(data['creditLimit'][0])
    if data.has_key('profitPercentage'):
        acc['profitPercentage'] = json.loads(data['profitPercentage'][0])
    dboperation.update_account(acc)
    acc = dboperation.get_account_by_name(account_name)
    return json.dumps(acc)


def accounts(qs):
    parsed_q_s = urlutils.get_qs_parsed(qs)
    total = dboperation.get_total_accounts()
    data = {}
    data["total"] = total
    data["accounts"] = dboperation.get_accounts(urlutils.get_parameter(parsed_q_s, 'pageNo', 1) - 1,
                                                urlutils.get_parameter(parsed_q_s, 'pageSize', 50))
    return json.dumps(data)


def adjust_price_list(product_content,account_name):
    account = dboperation.get_account_by_name(account_name)
    if account is not None:
        profit_percentage = account['profitPercentage']
    else:
        profit_percentage = 0
    logging.debug("Profit Percentage of %s = %s",account_name,profit_percentage)
    dicti = propertyparser.parse_property(product_content)
    new_wholesale_list = map(price_utils.adjusted_price_from_tuple,zip(
                        dicti['retailPriceList'],dicti['wholeSalePriceList'],
                        [profit_percentage] * len(dicti['wholeSalePriceList'])))
    logging.info(new_wholesale_list)
    dicti['wholeSalePriceList']=new_wholesale_list
    dicti = remove_from_dicti(dicti,['error_txt','error_code','connection_status','authentication_key'])
    return json.dumps(dicti)


def remove_from_dicti(dict,list):
    for key in list:
        if dict.has_key(key):
            dict.pop(key)
    return dict
