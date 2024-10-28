#!/usr/bin/env python3
import paramiko
import threading

def close_connection(conn):
    import time
    if conn == None: return
    print('terminating counter started')

    time.sleep(20)
    conn.close()
    print('terminating counter activated')


if __name__ == "__main__":
    try:
        conn = paramiko.SSHClient()
        conn.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        conn.connect( '192.168.50.140', 22, 'ntucms', '9ol.1qaz5tgb')

        the_shell = conn.invoke_shell()

        bkg_thread = threading.Thread(target=close_connection, args=(conn,))
        bkg_thread.start()
        bashCOMMAND = 'for a in `seq 1 1000`; do echo $a; sleep 10 ; done'
        stdin, stdout, stderr = conn.exec_command(bashCOMMAND)

        print('start bash script')
        for line in stdout:
            print(line.strip())
        print('ENDED OF CODE')
        if conn != None:
            conn.close()

    except Exception as e:
        print('ExceptionRaised', f'Got Error {type(e)} : {e}')


