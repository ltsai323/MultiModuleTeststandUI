import paramiko

def ssh_command(hostname, port, username, password, command):
    # Create an SSH client
    client = paramiko.SSHClient()

    try:
        # Automatically add the server's host key (this is insecure, see comments below)
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Connect to the SSH server with AES encryption
        client.connect(hostname, port, username, password,)

        # Execute the command
        stdin, stdout, stderr = client.exec_command(command)

        # Print the command output
        print("Command Output:")
        print(stdout.read().decode())

    except Exception as e:
        print(f"Error: {e}")

    finally:
        # Close the SSH connection
        client.close()


from dataclasses import dataclass
@dataclass
class ConnectionConfig:
    host:str
    port:int
    user:str
    pwd:str

class Connector:
    def __init__(self, connectCONFIG:ConnectionConfig):
        self.config = connectCONFIG
        self.connection1 = paramiko.SSHClient()
        self.connection2 = paramiko.SSHClient()

    def send_command(self, sshCONNECTOR, theCMD):
        print('hi')
        try:
            # Automatically add the server's host key (this is insecure, see comments below)
            sshCONNECTOR.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Connect to the SSH server with AES encryption
            sshCONNECTOR.connect(self.config.host, self.config.port, self.config.user, self.config.pwd)

            # Execute the command
            stdin, stdout, stderr = sshCONNECTOR.exec_command(theCMD)

            # Print the command output
            print("Command Output:")
            print(stdout.read().decode())

        except Exception as e:
            print(f"Error: {e}")

    def ActivateDAQClient(self):
        #self.send_command(self.connection1,"daq_client")
        self.send_command(self.connection1,"cd V3HD_hexactrl && ls")
    def SendCMD(self,theCMD):
        self.send_command(self.connection2,theCMD)
        self.connection2.close()

    def StopDAQClient(self):
        self.send_command(self.connection1,"echo 'hiii'")
        self.connection1.close()



if __name__ == "__main__":
    # SSH server details
    # SSH server details
    host = "192.168.50.140"
    port = 22  # Default SSH port
    user = "ntucms"
    password = "9ol.1qaz5tgb"
    connConfig = ConnectionConfig(
            host = host,
            port = port,
            user = user,
            pwd = password
            )
    conn = Connector(connConfig)
    conn.ActivateDAQClient()
    conn.SendCMD('cd V3HD_hexactrl && ls && ./run.sh TWH015_fixed')
    conn.StopDAQClient()
