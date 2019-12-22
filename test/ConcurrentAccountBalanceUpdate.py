#!/usr/bin/python

import thread
import time
import urllib
import httplib
import sys

global acc_name

def send_data( threadName, delay,i):
   data = {'amount': i,'description' : 'AAA','entryMadeBy' : 'test'}
   params = urllib.urlencode(data)
   conn = httplib.HTTPConnection('localhost:5555')
   ep = '/accounts/account/'+acc_name+'/balance'
   conn.request("PUT", ep,params,{ "Content-Type" : "application/x-www-form-urlencoded" })
   response = conn.getresponse()
   print response.read()

def main():
    global acc_name
    arg_len = len(sys.argv)
    if arg_len < 3:
       print "Usage python ConcurrentAccountBalanceUpdate.py accountname #ofthreads"
       return
    acc_name = sys.argv[1]
    threads = int(sys.argv[2])
    for i in range(threads):
       try:
          thread.start_new_thread(send_data, ("Thread-" + str(i), i, i + 1))
       except:
          print "Error: unable to start thread"
    while 1:
      pass


if __name__ == "__main__":
    main()

