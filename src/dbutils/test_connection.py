import sys
import mysql.connector
from mysql.connector import errorcode


def main():
    print "Going to test Connection"
    if len(sys.argv) != 4:
        print "Usage python test_connection.py username password dbname"
        sys.exit(1)
    try:
        cnx = mysql.connector.connect(user=sys.argv[1],password=sys.argv[2],
                                      database=sys.argv[3])
        print cnx
        print "Connection Successful."
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)
    else:
        cnx.close()
    
    sys.exit(0)


if __name__ == '__main__':
    main()