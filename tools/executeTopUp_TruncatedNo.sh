#!/bin/bash

curl -X POST -H "Content-Type: text" --data-urlencode "accountName=sa@maxmoney.com" --data-urlencode "mobileNo=+601078608"  --data-urlencode "operatorId=1735" --data-urlencode "senderMobileNo=+919845104104" --data-urlencode "product=10" http://localhost:5555/topup