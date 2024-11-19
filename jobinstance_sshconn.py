import select
import time
import LoggingMgr
import paramiko
from pprint import pprint

DEBUG_MODE = False
def get_private_key(logFUNC,privateKEY):
    try:
        return paramiko.RSAKey.from_private_key_file(privateKEY)
    except paramiko.SSHException:
        logFUNC(f'[PrivateKeyNotFound] Path "{privateKEY}" is not a valid private key')

def IsActivate(sshCLIENT):
    if sshCLIENT == None: return False
    if sshCLIENT.get_transport() == None: return False
    if sshCLIENT.get_transport().is_active() == False: return False
    return True


def execute_command_with_timeout(ssh_client, logOUT, logERR, command, timeout):
    """
    Execute a command on the SSH server with a timeout for output.
    
    :param ssh_client: The Paramiko SSHClient object.
    :param command: The command to execute on the server.
    :param timeout: Timeout in seconds to wait for output.
                    If no any message found, the code keeps listening the next message.
                    timeout value used to prevent the code stucked on listening.
                    You can add additional function executing when waiting for the result.
                    Also, not to put time.sleep() when you are listening the next message.
    :return: nothing
    """

    try:
        logOUT.info(f'Send command "{ command }" to remote site')
        stdin, stdout, stderr = ssh_client.exec_command(command)


        # Monitor both stdout and stderr in real-time
        while True:
            if not IsActivate(ssh_client):
                logERR.warning('[Abort] SSH Connection was closed. Abort current job')

            # Use select to wait for either stream to have data
            ready_channels, _, _ = select.select([stdout.channel, stderr.channel], [], [], timeout)


            if not ready_channels:  # Timeout, no data yet
                continue

            for channel in ready_channels:
                if channel.recv_ready():  # Data in stdout
                    logOUT.info(channel.recv(1024).decode().strip())
                if channel.recv_stderr_ready():  # Data in stderr
                    logERR.info(channel.recv_stderr(1024).decode().strip())

            # Exit the loop if the command is finished and streams are empty
            if stdout.channel.exit_status_ready() and stdout.channel.recv_exit_status() == 0:
                logOUT.info(f'finished function execute_command_monitoring')
                return
    except Exception as e:
        logERR.info(f"An error occurred: {e}")
        if DEBUG_MODE: raise

def test_direct_run():
    stdout_err_mesg_filter = LoggingMgr.ErrorMessageFilter()
    stderr_err_mesg_filter = LoggingMgr.ErrorMessageFilter( [
            LoggingMgr.errortype('Type1Err', 0, '[running] 1'),
            LoggingMgr.errortype('Type3Err', 0, '[running] 3'),
        ])
    #global log_stdout, log_stderr
    log_stdout = LoggingMgr.configure_logger('out', 'log_stdout.txt', stdout_err_mesg_filter)
    log_stderr = LoggingMgr.configure_logger('err', 'log_stderr.txt', stderr_err_mesg_filter)



    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    
    pkey = get_private_key(log_stdout.info,'/Users/noises/.ssh/toNTU8')
    ssh_client.connect(hostname="ntugrid8.phys.ntu.edu.tw", username="ltsai", pkey = pkey)

    command = 'python3 -u main_job.py'
    #command = 'python3 -u main_job.py 1>&2'
    #command = 'sh main_job.sh 1>&2'
    execute_command_with_timeout(ssh_client, log_stdout, log_stderr, command, timeout=1)

    log_stdout.info('SSH client closed')
    ssh_client.close()
    log_stdout.info('end of test_direct_run()')

class JobUnit:
    def __init__(self, hostNAME:str, userNAME:str, privateKEYfile:str, timeOUT:float,
                 stdOUT, stdERR,
                 cmdTEMPLATEs:dict, argCONFIGs:dict):

        self.ssh_client = paramiko.SSHClient()
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.pkey = get_private_key(stdOUT.info, privateKEYfile)
        self.user = userNAME
        self.host = hostNAME
        self.timeout = timeOUT

        self.log = stdOUT
        self.err = stdERR
        self.config = argCONFIGs
        self.cmd_template = cmdTEMPLATEs
    def Initialize(self):
        try:
            self.ssh_client.connect(hostname=self.host, username=self.user, pkey=self.pkey)
            execute_command_with_timeout(self.ssh_client,
                                         self.log, self.err,
                                         self.cmd_template['init'], timeout = 0.4)
            execute_command_with_timeout(self.ssh_client,
                                         self.log, self.err,
                                         'echo FINISHED', timeout = 0.4)
            
        except Exception as e:
            self.err.error(f'Unexpected Error')
            self.err.error(e)
            if DEBUG_MODE: raise
        finally:
            self.ssh_client.close()
    def Configure(self, updatedCONF:dict):
        '''
        Update old argument config only if all configs in old argument config being confirmed.
        If there are some redundant key - value pair in updatedCONF, these configs are ignored.

        updatedCONF: dict. It should have the same format with original arg config
        '''
        valid_keys = [ 1  if oldkey in updatedCONF else 0 for oldkey in self.config.keys() ]
        if sum(valid_keys) == len(self.config):
            for key, newval in updatedCONF.items():
                self.config[key] = newval
        else:
            self.err.warning('ConfigureFailed')
            self.err.warning(f'[InvalidNewConfig] {updatedCONF}')
            self.err.warning(f'[OrigConfig] {self.config}')
    def Run(self):
        try:
            self.ssh_client.connect(hostname=self.host, username=self.user, pkey=self.pkey)

            run_cmd = self.cmd_template['run'].format(**self.config)
            if IsActivate(self.ssh_client):
                execute_command_with_timeout(self.ssh_client,
                                            self.log, self.err,
                                            run_cmd, timeout = 0.4)
            if IsActivate(self.ssh_client):
                execute_command_with_timeout(self.ssh_client,
                                            self.log, self.err,
                                            'echo FINISHED', timeout = 0.4)
            else:
                self.err.warning('[ExternalTerminated] Run() is terminated from external signal')
            
        except Exception as e:
            self.err.error(f'Unexpected Error')
            self.err.error(e)
            if DEBUG_MODE: raise
        finally:
            self.ssh_client.close()
    def Stop(self):
        while IsActivate(self.ssh_client):
            self.ssh_client.close()
            time.sleep(0.2)
    def Destroy(self):
        while IsActivate(self.ssh_client):
            self.ssh_client.close()
            time.sleep(0.2)

def test_jobunit():
    host = 'ntugrid8.phys.ntu.edu.tw'
    user = 'ltsai'
    pkey = '/Users/noises/.ssh/toNTU8'
    
    #### configure the status output
    stdout_filter = LoggingMgr.ErrorMessageFilter([
            LoggingMgr.errortype_exact('Type0Err', 0, '[running] 0'),
            LoggingMgr.errortype_contain('Type3Err', 0, '[running] 3'),

            LoggingMgr.errortype_exact('idle', 0, 'FINISHED'),
            ])
    stderr_filter = LoggingMgr.ErrorMessageFilter( [
            LoggingMgr.errortype_exact('Type1Err', 0, '[running] 1'),
            LoggingMgr.errortype_contain('Type3Err', 0, '[running] 3'),
            LoggingMgr.errortype_contain('RaiseErr', 0, 'Error'),

        ])
    log_stdout = LoggingMgr.configure_logger('out', 'log_stdout.txt', stdout_filter)
    log_stderr = LoggingMgr.configure_logger('err', 'log_stderr.txt', stderr_filter)

    cmd_template = {
        'init': 'echo "connection established"',
        'run': 'python3 -u main_job.py; echo "config: {prefix}"',
        'stop': 'exit'
    }
    arg_config = {
        'prefix': 'default',
    }
    timeout = 0.4

    job_unit = JobUnit(
            host, user, pkey, timeout,
            log_stdout, log_stderr,
            cmd_template, arg_config)

    job_unit.Initialize()
    job_unit.Configure( {'prefix': 'confiugred'} )
    job_unit.Run()

    exit()
if __name__ == "__main__":
    #test_direct_run()
    test_jobunit()
