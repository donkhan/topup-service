import sys
import json
from time import strftime,gmtime
import time
sys.path.append("simulation")
sys.path.append("dbutils")
sys.path.append("utils")
from dbutils import dboperation
from utils import urlutils


def get_from_dates(parsedQS):
    from_date = urlutils.get_string_parameter(parsedQS, 'from', '1970-01-01')
    from_date = from_date + " 00:00:00"
    return from_date


def get_to_date(parsedQS):
    to_date = urlutils.get_string_parameter(parsedQS, 'to', time.strftime("%Y-%m-%d", gmtime()))
    to_date = to_date + " 23:59:59"
    return to_date


def ledger(qs):
    parsedQS = urlutils.get_qs_parsed(qs)
    from_date = get_from_dates(parsedQS)
    to_date = get_to_date(parsedQS)
    return parseLedgerEntriesAndSendAsJson(dboperation.ledger(urlutils.get_parameter(parsedQS, 'pageNo', 1) - 1,
                                                              urlutils.get_parameter(parsedQS, 'pageSize', 50),
                                                              from_date,to_date),
                                           dboperation.get_total_ledger_entries(from_date,to_date),
                                           urlutils.get_string_parameter(parsedQS, 'role', 'maxcddofficer'))


def ledgerOfUser(username, qs):
    parsedQS = urlutils.get_qs_parsed(qs)
    from_date = get_from_dates(parsedQS)
    to_date = get_to_date(parsedQS)
    return parseLedgerEntriesAndSendAsJson(dboperation.ledger_of_user(username,
                                                                      urlutils.get_parameter(parsedQS, 'pageNo', 1) - 1,
                                                                      urlutils.get_parameter(parsedQS, 'pageSize', 50),
                                                                      from_date,to_date),
                                           dboperation.get_total_ledger_entries_of(username,from_date,to_date),
                                           urlutils.get_string_parameter(parsedQS, 'role', 'maxcddofficer'))


def find_and_append_rates(entry,row,role):
    if entry['type'] == 'TOPUP':
        entry['retailPrice'] = float(row[14])
        entry['agentPrice'] = float(row[16])
        role_name = str(role)
        if role_name.lower() == 'financemanager' or role_name == "admin":
            entry['wholeSalePrice'] = float(row[15])
            entry['companyProfit'] = entry['agentPrice'] - entry['wholeSalePrice']
        entry['agentProfit'] = entry['retailPrice'] - entry['agentPrice']
        if entry['status'] == 'FAILURE':
            entry['agentProfit'] = 0
            entry['companyProfit'] = 0


def parseLedgerEntriesAndSendAsJson(rows, total,role):
    entries = []
    tuples = [(0, "accountName"), (1, "description"), (3, "balance"), (5, "transferToId"), (6, "mobileNo"),
              (7, "sender"), (8, "product"),(9, "operator"), (10, 'country'), (11, 'id'), (12, 'type'),
              (13, 'entryMade'),(17,'reason'),(18,'status')]
    for row in rows:
        entry = {}
        for tuple in tuples:
            entry[tuple[1]] = row[tuple[0]]
        entry['time'] = row[2].strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        amount = float(row[4])
        if amount < 0.0:
            entry['debit'] = -1 * amount
            entry['credit'] = ''
        if amount > 0.0:
            entry['credit'] = amount
            entry['debit'] = ''
        if amount == 0.0:
            entry['credit'] = ''
            entry['debit'] = ''

        find_and_append_rates(entry,row,role)

        entries.append(entry)
    data = {}
    data['total'] = total
    data['entries'] = entries
    return json.dumps(data)
