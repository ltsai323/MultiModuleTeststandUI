import socket
import threading
import time

def cmd_receive_feedback(server_socket):
    while True:
        try:
            cmd = server_socket.recv(1024).decode('utf-8')
            print(f'Received command from client : {cmd}')
            if cmd == 'close':
                server_socket.close()
                return
        except OSError as e:
            print('section closed')
            return


def send_status_commands(server_socket):
    idx = 0
    try:
        while True:
            # Get user input for the status
            status = f'status = {idx}\n'
            idx += 1

            # Send the status to the server
            server_socket.send(status.encode('utf-8'))
            time.sleep(1)
    except OSError as e:
        print('section closed')
        return
    except (socket.error, BrokenPipeError):
        return # Ignore the process

def main():
    # Configure the client to connect to the server
    server_ip = '0.0.0.0'  # Replace with the actual server IP
    first_port = 3000

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', first_port))
    server_socket.listen(5)

    orig_address = None

    while True:
        client_socket, address = server_socket.accept()
        if orig_address == None:
            orig_address = address
        elif orig_address != address:
            print('new connection from {address} refused')
            continue
        # Accept a client connection
        print(f"Accepted connection from {address}")

        # Start threads for sending and receiving
        send_status_thread = threading.Thread(target=send_status_commands, args=(client_socket,))
        cmd_receive_thread = threading.Thread(target=cmd_receive_feedback, args=(client_socket,))

        send_status_thread.start()
        cmd_receive_thread.start()

        # Wait for both threads to finish
        send_status_thread.join()
        cmd_receive_thread.join()


    server_socket.close()

if __name__ == "__main__":
    main()

