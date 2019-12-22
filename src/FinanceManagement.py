import sys
import json
from TopUpModule import *

sys.path.append("simulation")
sys.path.append("dbutils")
#from simulation import dboperation
from dbutils import dboperation


def get_financial_position():
    data = {}
    account_credit = dboperation.get_account_balance()
    if account_credit is None:
        account_credit = 0
    account_credit_balance = dboperation.get_account_credit_balance()
    if account_credit_balance is None:
        account_credit_balance = 0
    data['account-credit'] = account_credit
    data['accounts-credit-balance'] = account_credit_balance
    data['account-debit'] = float(topup_account_balance()['balance'])
    return json.dumps(data)