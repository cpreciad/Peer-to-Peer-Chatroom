#!/usr/bin/env python3

# SuperUser.py
# Authors: Kristen Friday, Carlo Preciado
# Date: November 1, 2021
#
# The SuperUser class defines a centralized leader in the 
# chat system to allow for new User entry


import socket
import json
import time

HOST = ''
PORT = 0
BYTES = 1024

class SuperUser:

    def __init__(self):
        '''Constructor for User objects'''

        self.username = "super_user"
        self.neighbors = {}
        self.message_table = {}

        ip = socket.gethostbyname(socket.gethostname())
        self.ip = ip

        client_sock = socket.socket()
        client_sock.bind((HOST, PORT))
        _, self.port = client_sock.getsockname()


    def print_user(self):
        '''Method to print attributes of the SuperUser'''

        print(f'Username:  {self.username}')
        print(f'IP Addr:   {self.ip}')
        print(f'Port:      {self.port}')
        print(f'Neighbors: {self.neighbors}')
        print(f'Messages:  {self.message_table}\n')


    def add_users(self):
        '''Method to listen for incoming clients and add to chat system'''

        super_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        super_sock.bind((self.ip, self.port))

        while True:
            data, rec_addr = super_sock.recvfrom(BYTES)
            req = json.loads(data.decode('utf-8'))
            print(req)
            location = (req["ip"], req["port"])
            json_res = {
                "status": "success",
                "message": "Connected to chat room"
            }
            res = json.dumps(json_res).encode('utf-8')
            print(res)
            print(location)
            print("sending message")
            super_sock.sendto(res, location)
            print("sent")


    def send_message(self, message):
        '''Send a global message to all nodes in ring'''
        pass


    def direct_message(self, username, message):
        '''Send a direct message to a target user'''
        pass


if __name__ == '__main__':

    super_usr = SuperUser()
    super_usr.print_user()
    super_usr.add_users()
