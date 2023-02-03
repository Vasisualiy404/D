from time import sleep

import sys
import crcmod
import socket
import ssl


SERVER_HOST = "127.0.0.1"
SERVER_PORT = 60000

HOST = "127.0.0.1"
PORT = 60002


crc_params = [
#    ["CRC-16/AUG-CCITT", 0x11021, 0x1d0f, False, 0x00, 0xe5cc],
    ["Username01", 0x1000000000000001B, 0x00, True, 0x00, 0x46a5a9388a5beffe],
]


def crc_format(self, format_spec):
    spad = " " * int(16 - self.w)
    rev = "REVERSED " if self.reverse else ""
    perm = "PERMUTATION" if self.permutation else ""
    fmt = "%s{:0{zpad}x} poly: %s{:0{zpad}x} init: %s{:0{zpad}x} xor: %s{:0{zpad}x} {}{}" % (
        spad, spad, spad, spad)
    return fmt.format(self.crcValue, self.poly, self.initCrc, self.xorOut, rev, perm, zpad=self.w)


def init_crcs(crc_params):
    crcs = []
    for item in crc_params:
        crc = crcmod.Crc(item[1], initCrc=item[2], rev=item[3], xorOut=item[4])
        test = crc.copy()
        crc.name = item[0]
        crc.permutation = False
        crc.w = int(width(crc.poly) / 4)
        test.update(b"123456789")
        if test.crcValue != item[5]:
            print("Test for %s failed: expected: %x got: %x" %
                  (item[0], item[5], test.crcValue))
            sys.exit()
        crcs.append(crc)

    return crcs


def init_crcs_permutation(crc_params):
    crcs = []
    for seed in crc_params:
        crc = crcmod.Crc(seed[1], initCrc=0x00, rev=True, xorOut=0x00)
        crc.name = seed[0]
        crc.permutation = True
        crc.w = int(width(crc.poly) / 4)
        crcs.append(crc)

        crc = crcmod.Crc(seed[1], initCrc=0x00, rev=False, xorOut=0x00)
        crc.name = seed[0]
        crc.permutation = True
        crc.w = int(width(crc.poly) / 4)
        crcs.append(crc)

        crc = crcmod.Crc(seed[1], initCrc=0x00, rev=True, xorOut=0xffffffff)
        crc.name = seed[0]
        crc.permutation = True
        crc.w = int(width(crc.poly) / 4)
        crcs.append(crc)

        crc = crcmod.Crc(seed[1], initCrc=0x00, rev=False, xorOut=0xffffffff)
        crc.name = seed[0]
        crc.permutation = True
        crc.w = int(width(crc.poly) / 4)
        crcs.append(crc)

    return crcs


def width(poly):
    count = 0
    while poly:
        poly = poly >> 1
        count += 1
    return count


def max_length_name(crcs):
    length = 0
    for crc in crcs:
        length = max(len(crc.name), length)
    return length


def calculate_file(filename):
    with open(filename, "rb") as f:
        while True:
            data = f.read(1024)
            if not data:
                break
            for crc in crcs:
                crc.update(data)

    max_string_len = max_length_name(crcs)

    for index, crc in enumerate(crcs):
        fmt = "{:2} {:{spad}} {}"

        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)

        # Устанавливаем сертификат удостоверяющего центра, с помощью которого
        # был сгенерирован сертификат сервера, с которым планируем установить связь
        context.load_verify_locations("ca.crt")

        print("Контекст определён")

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            sock.bind((HOST, PORT))
            sock.connect((SERVER_HOST, SERVER_PORT))

            with context.wrap_socket(sock, server_hostname=HOST) as client:
                print("Отправка сообщения...")
                try:
                    client.send((fmt.format(index, crc.name, crc, spad=max_string_len)[0:30]).encode("utf-8"))
                    # receive data from the server
                    callback = client.recv(1024).decode("utf-8")
                    if callback == "True":
                        pass
                    elif callback == "False":
                        with open("main.exe", "r+b") as file:
                            content: bytes = file.read()
                            file.write(content.replace(b"\x02", b"\x01"))
                            print("Program is not validated")
                            sys.exit()                
                         
                    # close the connection
                    client.close()
                except:
                    print("Need connect to Internet to work the program")
                    sys.exit()

crcmod.Crc.__format__ = crc_format
crcs = init_crcs(crc_params)
