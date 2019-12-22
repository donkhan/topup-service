#!/bin/bash

curl -X POST -H "Content-Type: text" --data-urlencode "accountName=sa@maxmoney.com" --data-urlencode "mobileNo=+628123456780"  --data-urlencode "operatorId=1310" --data-urlencode "senderMobileNo=+919845104104" --data-urlencode "product=50000" http://localhost:5555/topup