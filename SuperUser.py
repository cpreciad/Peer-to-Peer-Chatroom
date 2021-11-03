#!/usr/bin/env python3

# SuperUser.py
# Authors: Kristen Friday, Carlo Preciado
# Date: November 1, 2021
#
# The SuperUser class defines a centralized leader in the 
# chat system to allow for new User entry


import socket

HOST = ''
PORT = 0

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


    def add_user(self):
        '''Method to listen for incoming clients and add to chat system'''

        super_sock = socket.socket()
        super_sock.bind((HOST, PORT))
        super_sock.listen()
        client_sock, addr = super_sock.accept()


    def send_message(self, message):
        '''Send a global message to all nodes in ring'''
        pass


    def direct_message(self, username, message):
        '''Send a direct message to a target user'''
        pass

