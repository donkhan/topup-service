from AccountManagement import *
from LedgerManagement import *
from FinanceManagement import *
from TopUpModule import *
from SocketServer import ThreadingMixIn
from BaseHTTPServer import HTTPServer
import BaseHTTPServer
import ConfigParser
import sys
import urlparse
import re

sys.path.append('utils')
sys.path.append('dbutils')

helloPath = re.compile("^/hello$")
mobileProductPath = re.compile("^/product-detail$")
countries_path = re.compile("/countries$")
operatorsOfCountryPath = re.compile("^/[0-9]+/operators$")
operatorProductPath = re.compile("^/operator/product-detail$")
accountGetPath = re.compile("^/accounts/account/[a-zA-Z0-9@.]+")
accountsPath = re.compile("^/accounts$")
createAccountPath = re.compile("^/accounts/account$")
ledgerPath = re.compile("^/ledger$")
userLedgerPath = re.compile("^/ledger/[a-zA-Z0-9.@]+")
canTopupPath = re.compile("^/can\-topup$")
updateAccountBalancePath = re.compile("/accounts/account/[a-zA-Z0-9.@]+/balance")
updateAccountPath = re.compile("/accounts/account/[a-zA-Z0-9.@]+")
topupPath = re.compile("/topup")
financial_position_path = re.compile("/financial-position")
dump_path = re.compile("/dump/[0-9]{4}\-[0-9]{2}\-[0-9]{2}/[a-zA-Z0-9.@]+/\+[0-9]+")

class ThreadingServer(ThreadingMixIn, HTTPServer):
    pass


class RequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def send_data(self, code, content_type, data):
        self.send_response(code)
        self.send_header('Content-type', content_type)
        self.send_header("Content-Length", len(data))
        self.end_headers()
        self.wfile.write(data)

    def check_access(self):
        return self.client_address[0] == '127.0.0.1'

    def do_GET(self):
        logging.debug("Path %s", self.path)
        tokens = self.path.split('?')
        path = tokens[0]
        qs = ""
        if len(tokens) > 1:
            qs = tokens[1]
        if not self.check_access():
            self.send_data(httplib.UNAUTHORIZED, "text", "Access Denied from " + self.client_address[0])
            return
        if helloPath.match(path):
            self.send_data(httplib.OK, "text",
                           process(urllib.urlencode(prepare_payload(get_base_parameters(), {'action': 'ping'}))).read())
        elif operatorsOfCountryPath.match(path):
            self.send_data(httplib.OK, "text", operators(re.search('(/)([0-9]+)(/operators)', path).group(2)).read())
        elif accountGetPath.match(path):
            data = account(re.search('(/accounts/account/)([a-zA-Z0-9@.]+)', path).group(2))
            self.send_data(httplib.NOT_FOUND, "text", "Account Not Found") if data is None else self.send_data(200,
                                                                                                               "json",
                                                                                                               data)
        elif dump_path.match(path):
            content = get_content(path)
            if content is not None:
                self.send_data(httplib.OK,"text",content)
            else:
                self.send_data(httplib.NOT_FOUND,"text","File Not Found")
        elif accountsPath.match(path):
            self.send_data(httplib.OK, "json", accounts(qs))
        elif ledgerPath.match(path):
            self.send_data(httplib.OK, "json", ledger(qs))
        elif userLedgerPath.match(path):
            self.send_data(httplib.OK, "json", ledgerOfUser(re.search('(/ledger/)([a-zA-Z0-9.@]+)', path).group(2), qs))
        elif financial_position_path.match(path):
            self.send_data(httplib.OK, "json", get_financial_position())
        elif countries_path.match(path):
            self.send_data(httplib.OK, "json", json.dumps(get_topup_countries()))
        else:
            self.send_data(httplib.NOT_FOUND, "text", self.path + " not found ")

    def do_POST(self):
        logging.debug("Path %s", self.path)
        if not self.check_access():
            self.send_data(httplib.UNAUTHORIZED, "text", "Access Denied from " + self.client_address[0])
            return
        post_data = urlparse.parse_qs(self.rfile.read(int(self.headers['Content-Length'])).decode('utf-8'))
        logging.debug("Post Data %s", post_data)
        if canTopupPath.match(self.path):
            response_data = can_top_up(post_data)
            logging.debug("Response Data %s", response_data[0])
            if not response_data[0]:
                self.send_data(httplib.UNAUTHORIZED, "text", response_data[1])
            else:
                self.send_data(httplib.OK, "json", "")
        elif createAccountPath.match(self.path):
            new_account = create_account(post_data)
            if new_account is None:
                logging.debug("Unable to create needs to be sent back")
                self.send_data(httplib.NOT_ACCEPTABLE, "text", "Unable to create")
            else:
                self.send_data(httplib.OK, "json", new_account)
        elif topupPath.match(self.path):
            response_data = top_up(post_data)
            if response_data[0] != httplib.OK:
                self.send_data(httplib.UNAUTHORIZED, "text", response_data[1])
            else:
                self.send_data(httplib.OK, "text", response_data[1])
        elif mobileProductPath.match(self.path):
            self.send_data(httplib.OK, "json",
                           adjust_price_list(product_detail_of_no(post_data).read(), post_data['accountName'][0]))
        elif operatorProductPath.match(self.path):
            self.send_data(httplib.OK, "json",
                           adjust_price_list(product_detail_of_operator(post_data).read(), post_data['accountName'][0]))
        else:
            self.send_response(httplib.NOT_FOUND)

    def do_PUT(self):
        logging.debug("Path %s", self.path)
        if not self.check_access():
            self.send_data(httplib.UNAUTHORIZED, "text", "Access Denied from " + self.client_address[0])
            return
        put_data = urlparse.parse_qs(self.rfile.read(int(self.headers['Content-Length'])).decode('utf-8'))
        logging.debug("Put Data %s", put_data)
        if updateAccountBalancePath.match(self.path):
            updated_account = update_account_balance(re.search('(/accounts/account/)([a-zA-Z0-9.@]+)(/balance)',
                                                               self.path).group(2), put_data)
            self.send_data(httplib.NOT_FOUND, "text", "Account Not Found") if updated_account is None \
                else self.send_data(httplib.OK, "json", updated_account)
        elif updateAccountPath.match(self.path):
            updated_account = update_account(re.search('(/accounts/account/)([a-zA-Z0-9.@]+)', self.path).group(2),
                                            put_data)
            self.send_data(httplib.NOT_FOUND, "text", "Account Not Found") if updated_account is None \
                else self.send_data(httplib.OK, "json", updated_account)


config = ConfigParser.ConfigParser()
config.read("conf/transferto.ini")
logging.basicConfig(filename=config.get("log", "file"), level=config.get("log", "level"),
                    format='%(asctime)s %(levelname)s %(message)s')

dboperation.init_pool()
logging.debug("MMTS Server started")
ThreadingServer((config.get("networking", "web-server-host"), int(config.get("networking", 'web-server-port'))),
                RequestHandler).serve_forever()
