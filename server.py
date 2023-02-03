import socket
import ssl

HOST = "127.0.0.1"
PORT = 60000

if __name__ == '__main__':
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)

    # Устанавливаем сертификат сервера, подлинность которого будем проверять
    context.load_cert_chain(certfile="server.crt", keyfile="server.key", password="pass")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        sock.bind((HOST, PORT))
        sock.listen(0)

        print("Сервер запущен")
        with context.wrap_socket(sock, server_side=True) as ssock:
            while True:
                connection, client_address = ssock.accept()
                print('Got connection from', client_address)

                data = connection.recv(1024)
                if not data:
                    break
                print(f"Received: {data.decode('utf-8')}")

                with open('database.txt', 'r') as f:
                    values = f.read()

                if data.decode() in values:
                    connection.sendall(b"True")

                else:
                    connection.sendall(b"False")
                    
