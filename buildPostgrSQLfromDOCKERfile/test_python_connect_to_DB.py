#!/usr/bin/env python3

import psycopg2
import psutil
from datetime import datetime
import time
import socket

db_params_1_user_remote = {
    'host':'192.168.50.60',
    'port':5423,
    'user':'test1',
    'password':'testPWD',
    'database':'TESTDB'
    }
db_params_1_user = {
    'host':'localhost',
    'port':5423,
    'user':'test1',
    'password':'testPWD',
    'database':'TESTDB'
    }
#db_params_1_owner = {
#    'host':'localhost',
#    'port':5423,
#    'user':'test2',
#    'password':'testPWD',
#    'database':'TESTDB'
#    }
#db_params_1_admin = {
#    'host':'localhost',
#    'port':5423,
#    'user':'root',
#    'password':'myROOTpasswd_',
#    'database':'TESTDB'
#    }
#db_params_0 = {
#    'host':'localhost',
#    'port':8080,
#    'user':'userdockerexec',
#    'password':'TESTuser',
#    'database':'databasedockerexec'
#    }


if __name__ == "__main__":

    # connect topostgreSQL
    db_param = db_params_1_user
    #db_param = db_params_1_user_remote
    conn = psycopg2.connect(**db_param)
    cursor = conn.cursor()
    print(f'connect to datbase {db_param["database"]}')

    i=10
    #while True:
    while i!=0:
        i-=1
        cpu_percent = psutil.cpu_percent()

        # inject data into CPU_usage table
        cursor.execute(
                f'INSERT INTO CPU_usage (usage) VALUES ({cpu_percent})'
                )
        conn.commit()
        time.sleep(1)
        print( f'CPU usage : {cpu_percent}' )
    conn.close()
