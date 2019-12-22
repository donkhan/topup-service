#!/bin/bash

curl -X POST -H "Content-Type=plain/text" -d "accountName=a@a.com&status=A&balance=100&creditLimit=100&creditAllowed=1&createdBy=a@a.com&profitPercentage=23" http://localhost:5555/accounts/account
