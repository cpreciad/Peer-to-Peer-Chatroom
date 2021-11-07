#!/usr/bin/env python3

# User.py
# Authors: Kristen Friday, Carlo Preciado
# Date: November 1, 2021
#
# The User class defines a node in the chat system
# It serves as the abstraction template for basic functionality

import socket
import json


LOGIN_SERVER = ('student00.cse.nd.edu', 3000)
BYTES = 1024
HOST = ''
PORT = 0

class User:

    def __init__(self):
        '''Constructor for User objects'''

        self.username = input("Enter your username: ")
        self.neighbors = {}
        self.friends = {}
        self.message_table = {}
        self.message_count = 0

        ip = socket.gethostbyname(socket.gethostname())
        self.ip = ip
       
        # "server" socket to listen for other peer's messages
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((HOST,PORT))
        _, self.port = sock.getsockname()
        self.sock = sock


    def print_user(self):
        '''Method to print attributes of the User'''                              

        print(f'Username:  {self.username}')
        print(f'IP Addr:   {self.ip}')
        print(f'Port:      {self.port}') 
        print(f'Neighbors: {self.neighbors}')
        print(f'Messages:  {self.message_table}\n')


    def connect_to_login(self):
        '''Method to set up UDP connection with LoginServer'''

        json_req = {
            "username": self.username,
            "purpose": "connect"
        }

        req = json.dumps(json_req)
        encoded_req = req.encode('utf-8')

        self.sock.sendto(encoded_req, LOGIN_SERVER)
        data, _ = self.sock.recvfrom(BYTES)

        res = data.decode('utf-8')
        json_res = json.loads(res)
        print(f'LoginServer: {json_res}')
        
        if (json_res["status"] == "success"):
            return json_res["leader"]
        else:
            print(json_res["error"])
            return None
    

    def connect(self):
        '''Allow user to enter chat ring'''
   
        leader = self.connect_to_login()
        if not leader:
            print(f'{self.username}: Connection to LoginServer failed')
            return

        json_req = {
            "username": self.username,
            "purpose": "connect",
            "ip": self.ip,
            "port": self.port
        }

        req = json.dumps(json_req)
        print(f'{self.username}: {req}')
        encoded_req = req.encode('utf-8')

        # send connection message to SuperUser
        self.sock.sendto(encoded_req, tuple(leader))
        data, rec_addr = self.sock.recvfrom(BYTES)
        data = data.decode('utf-8')
        print(f'{self.username}: {data}')


    def disconnect(self):
        '''Allow user to exit chat ring'''
        pass


    def send_message(self, message):
        '''Send a global message to all nodes in ring'''
        pass


    def direct_message(self, username, message):
        '''Send a direct message to a target user'''
        pass

