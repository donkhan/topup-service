MaxMoney Topup Service

Programming Language - Python
DB - MySQL

MySQL Installation in Debian/Ubuntu
apt-get install mysql-server
apt-get install mysql-client


PIP Installation
As a root
python get-pip.py

Plugin Installation
pip install mysql-connector==2.1.4



BACK UP RESTORE PROCEDURE
Backup - Take a dump. Store it somewhere safe. For Illustration i named the file as mmts.sql and store it in /tmp
mysqldump -uroot -pmaxmoney mmts  > /tmp/mmts.sql
Restore
mysql -uroot -pmaxmoney mmts < /tmp/mmts.sql
