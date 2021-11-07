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

        serv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        serv_sock.bind((HOST,PORT))
        _, self.port = serv_sock.getsockname()
        self.serv_sock = serv_sock


    def print_user(self):
        '''Method to print attributes of the SuperUser'''

        print(f'Username:  {self.username}')
        print(f'IP Addr:   {self.ip}')
        print(f'Port:      {self.port}')
        print(f'Neighbors: {self.neighbors}')
        print(f'Messages:  {self.message_table}\n')


    def add_users(self):
        '''Method to listen for incoming clients and add to chat system'''

        print(f'SuperUser: Listening on port {self.port}...')
        while True:
            data, rec_addr = self.serv_sock.recvfrom(BYTES)
            req = json.loads(data.decode('utf-8'))
            print(f'{req["username"]}: {req}')
            location = (req["ip"], req["port"])
            json_res = {
                "status": "success",
                "message": "Connected to chat room"
            }
            res = json.dumps(json_res).encode('utf-8')
            self.serv_sock.sendto(res, location)


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
