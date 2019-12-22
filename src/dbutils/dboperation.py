import logging
import ConfigParser
import datetime
import mysql.connector.pooling
import threading
account_balance_lock = threading.Lock()

cnx_pool = None


def get_config():
    logging.debug("Config is read from conf/transferto.ini")
    config = ConfigParser.ConfigParser()
    config.read("conf/transferto.ini")

    db_config = {
        "database": config.get("database", "db-name"),
        "user": config.get("database", 'username'),
        "password": config.get("database", 'password'),
        "host": config.get("database", "mysql-host")
    }
    return db_config,config.get("database", "pool-size")


def init_pool():
    global cnx_pool
    if cnx_pool is None:
        logging.debug("Cnx Pool is empty. Going to create...")
        import time
        pool_name = "mmts_pool_" + str(time.time())
        logging.debug("Pool Name %s",pool_name)
        config = get_config()
        db_config = config[0]
        try:
            cnx_pool = mysql.connector.pooling.MySQLConnectionPool(pool_name=pool_name,
                                                           pool_size=int(config[1]), **db_config)
            logging.debug("Pool Created")
        except mysql.connector.PoolError as p_error:
            logging.error("Pool Error Happened %s",p_error)
        except mysql.connector.Error as error:
            logging.error("Error Happened %s",error)


def make_account_creation_ledger_entry(description, amount, account_name, tran_id, mobile_no, operator, country, customer, product,
                   transaction_type, entry_by,
                   unique_key, balance, retail_price, whole_sale_price, service_fee, destination_currency,agent_price
                   ):
    cnx = get_connection()
    cursor = cnx.cursor()
    logging.info("Making ledger entry for Create Account")
    insert_into_ledger(description, amount, account_name, tran_id, mobile_no, operator, country, customer, product,
                   transaction_type, entry_by,
                   unique_key, balance, retail_price, whole_sale_price, service_fee, destination_currency,agent_price,
                    'Account Created','SUCCESS',cursor)
    cnx.commit()
    cnx.close()
    logging.info("Ledger entry is made for create account")


def insert_into_ledger(description, amount, account_name, tran_id, mobile_no, operator, country, customer, product,
                   transaction_type, entry_by,
                   unique_key, balance, retail_price, whole_sale_price, service_fee, destination_currency,agent_price,
                   reason,status,cursor):
    data = { 'description' : description, 'time' : datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'accountName' : account_name, 'refId': tran_id , 'amount' : amount , 'balance' : balance,
             'mobileNo' : mobile_no, 'operator' :operator, 'country' : country, 'product' : product, 'sender' : customer,
             'entryMadeBy' : entry_by, 'type' : transaction_type , 'uniqueKey' : unique_key,
             'retailPrice' : retail_price, 'wholeSalePrice' : whole_sale_price, 'serviceFee' : service_fee,
             'destinationCurrency' : destination_currency, 'agentPrice' : agent_price, 'reason' : reason, 'status': status
             }
    sql = "INSERT INTO ledger (description,time,accountName,refId,amount,balance,mobileNo,operator,country," \
          "product,sender,entryMadeBy,type,uniqueKey,retailPrice,wholeSalePrice,serviceFee,destinationCurrency,agentPrice,reason,status) " \
          "VALUES (%(description)s,"
    sql = sql + "%(time)s, %(accountName)s, %(refId)s, %(amount)s, %(balance)s, %(mobileNo)s, %(operator)s," \
                " %(country)s,%(product)s, %(sender)s, %(entryMadeBy)s, %(type)s, %(uniqueKey)s,"
    sql = sql + "%(retailPrice)s, %(wholeSalePrice)s, %(serviceFee)s, %(destinationCurrency)s, %(agentPrice)s, %(reason)s, %(status)s)"
    cursor.execute(sql,data);


def create_account_by_name(name, amount, credit_allowed, status, credit_limit,profit_percentage):
    cnx = get_connection()
    create_account(cnx, name, amount, credit_allowed, status, credit_limit,profit_percentage)
    cnx.close()


def create_account(cnx, name, amount, credit_allowed, status, credit_limit,profit_percentage):
    logging.info("Create Account")
    a_cursor = cnx.cursor()
    a_cursor.execute("INSERT INTO account (name,balance,creditAllowed,status,creditLimit,profitPercentage)"
                     " VALUES (%(name)s, %(balance)s,"
                     " %(creditAllowed)s, %(status)s, %(creditLimit)s, %(profitPercentage)s )", {
        'name': name, 'balance': amount, 'creditAllowed': credit_allowed,
        'status': status, 'creditLimit': credit_limit, 'profitPercentage' : profit_percentage
    })
    a_cursor.close()
    cnx.commit()


def update_account_balance_by_name(account_name, amount,ledger_entry):
    cnx = get_connection()
    balance = update_account_balance(cnx,account_name, amount,ledger_entry)
    cnx.close()
    return balance


def update_account(account):
    cnx = get_connection()
    update_account_internal(cnx, account)
    cnx.close()


def update_account_internal(cnx, account):
    u_cursor = cnx.cursor()
    u_cursor.execute("UPDATE account set creditAllowed = %(creditAllowed)s,status = %(status)s,"
                     "creditLimit = %(creditLimit)s, profitPercentage = %(profitPercentage)s where name = %(name)s",
                    {'status': account['status'], 'creditAllowed': account['creditAllowed'] ,'name': account['name'],
                     'creditLimit': account['creditLimit'],'profitPercentage': account['profitPercentage']})
    u_cursor.close()
    cnx.commit()


def update_account_balance(cnx, name, amount,le):
    cnx.start_transaction()
    ucursor = cnx.cursor()
    ucursor.execute("select * from account where name = %(name)s for update",{'name' : name})
    status = le[19]
    balance = ucursor.fetchone()[1]
    if status == 'FAILURE':
        amount = 0
        le[1] = 0
    balance = balance + amount

    insert_into_ledger(le[0],le[1],le[2],le[3],le[4],le[5],le[6],le[7],le[8],le[9],le[10],le[11],
                       balance,le[13],le[14],le[15],le[16],le[17],le[18],le[19],ucursor)
    ucursor.execute("UPDATE account set balance = %(balance)s where name = %(name)s",
                    {'balance': balance, 'name': name})
    ucursor.close()
    cnx.commit()
    return balance


def get_account(cnx, name):
    q_cursor = cnx.cursor()
    q_cursor.execute("SELECT name,balance,creditAllowed,status,creditLimit,profitPercentage "
                     "FROM account where name = %(name)s",{'name': name})
    row = q_cursor.fetchone()
    if not row:
        return None
    account = {'name': row[0], 'balance': row[1], 'creditAllowed': row[2],
               'status': row[3], 'creditLimit': row[4], 'profitPercentage': row[5]}
    q_cursor.close()
    return account


def get_account_by_name(name):
    cnx = get_connection()
    account = get_account(cnx, name)
    cnx.close()
    return account


def get_total_accounts():
    return get_total("account")[0]


def get_accounts(page_no, page_size):
    query = ("SELECT name,balance,creditAllowed,status,creditLimit,profitPercentage FROM account limit "
             + str(page_no * page_size) + "," + str(page_size))
    rows = fetch_all(query)
    accounts = []
    for row in rows:
        account = {'name': row[0], 'balance': row[1], 'creditAllowed': row[2],
                   'status': row[3], 'creditLimit': row[4],'profitPercentage' : row[5]}
        accounts.append(account)
    return accounts


def fetch_all(query):
    cnx = get_connection()
    q_cursor = cnx.cursor()
    q_cursor.execute(query)
    rows = q_cursor.fetchall()
    q_cursor.close()
    cnx.close()
    return rows


def fetch_all_with_params(query, params):
    cnx = get_connection()
    qcursor = cnx.cursor()
    qcursor.execute(query,params)
    rows = qcursor.fetchall()
    qcursor.close()
    cnx.close()
    return rows


ledger_body = "accountName,description,time,balance,amount,refId,mobileNo,sender,product,operator,country,id,type," \
              "entryMadeBy,retailPrice,wholeSalePrice,agentPrice,reason,status"


def ledger(page_no, page_size,from_date,to_date):
    query = ("SELECT " + ledger_body + " FROM ledger where time >= %(from)s and time <= %(to)s order by time desc limit "
             + str(page_no * page_size) + "," + str(page_size))
    return fetch_all_with_params(query,{'from' : from_date,'to' : to_date})


def ledger_of_user(account_name, page_no, page_size,from_date,to_date):
    query = ("SELECT " + ledger_body + " FROM ledger where  time >= %(from)s and time <= %(to)s and "
                                       " accountName = %(accountName)s order by time desc limit "
             + str(page_no * page_size) + "," + str(page_size))
    return fetch_all_with_params(query, {'accountName' : account_name,'from': from_date,'to': to_date})


def get_total_ledger_entries(from_date,to_date):
     return fetch_one_with_params("select count(*) from ledger where time >= %s and time <= %s ",
                                  (from_date,to_date))[0]


def get_total(table_name):
    return fetch_one("select count(*) from " + table_name)


def get_total_ledger_entries_of(account_name,from_date,to_date):
    return fetch_one_with_params(
        "select count(*) from ledger where accountName = %s and  time >= %s and time <= %s ",(account_name,from_date,to_date))[0]


def get_account_balance():
    return fetch_one("SELECT sum(balance) from account where balance > 0")[0]


def get_account_credit_balance():
    return fetch_one("SELECT sum(balance) from account where balance < 0")[0]


def fetch_one_with_params(query,tuple):
    cnx = get_connection()
    t_cursor = cnx.cursor()
    t_cursor.execute(query,tuple)
    row = t_cursor.fetchone()
    t_cursor.close()
    cnx.close()
    return row


def fetch_one(query):
    cnx = get_connection()
    t_cursor = cnx.cursor()
    t_cursor.execute(query)
    row = t_cursor.fetchone()
    t_cursor.close()
    cnx.close()
    return row


def get_connection():
    global cnx_pool
    try:
        init_pool()
        cnx = cnx_pool.get_connection()
        if not cnx.is_connected():
            logging.debug("Connection is gone. So reconnecting")
            cnx.connect()
        return cnx
    except mysql.connector.PoolError as error:
        logging.error("Pool Error Happened....")
        logging.error(error)
        cnx_pool = None
        return get_connection()