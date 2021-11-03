#!/usr/bin/env python3

# User.py
# Authors: Kristen Friday, Carlo Preciado
# Date: November 1, 2021
#
# The User class defines a node in the chat system
# It serves as the abstraction template for basic functionality

import socket
import json


LOGIN_SERVER = ('student00.cse.nd.edu', 9000)
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
        
        client_sock = socket.socket()
        client_sock.bind((HOST, PORT))
        _, self.port = client_sock.getsockname()


    def print_user(self):
        '''Method to print attributes of the User'''                              

        print(f'Username:  {self.username}')
        print(f'IP Addr:   {self.ip}')
        print(f'Port:      {self.port}') 
        print(f'Neighbors: {self.neighbors}')
        print(f'Messages:  {self.message_table}')


    def connect_to_host(self, addr):
        '''Method to set up UDP connection with a given host and port'''

        host, port = addr

        sock = None
        sockaddr = None

        for res in socket.getaddrinfo(host, port, socket.AF_UNSPEC, 
            socket.SOCK_DGRAM, 0, socket.AI_PASSIVE):
            
            family, s_type, proto, _, sockaddr = res

            # return the socket and socket address
            sock = socket.socket(family, s_type, proto)

            return sock, sockaddr

        if not sock or not sockaddr:
            print(f'{self.username}: Could not connect to ({host},{port})')     
            return None


    def connect_to_login(self):
        '''Method to set up UDP connection with LoginServer'''
        
        connection = self.connect_to_host(LOGIN_SERVER)
        if not connection:
            return

        login_sock, sockaddr = connection

        json_req = {
            "username": self.username,
            "purpose": "connect"
        }

        req = json.dumps(json_req)
        encoded_req = req.encode('utf-8')

        # TODO: add try/except
        login_sock.sendto(encoded_req, sockaddr)
        data, rec_addr = login_sock.recvfrom(BYTES)

        res = data.decode('utf-8')
        json_res = json.loads(res)
        
        if (json_res["status"] == "success"):
            return json_res["leader"]
        else:
            print(json_res["error"])
            return None
    

    def connect(self):
        '''Allow user to enter chat ring'''
   
        leader = self.connect_to_login()
        print(f'Leader: {leader}')
        lead_connection = self.connect_to_host(leader) 
        if not lead_connection:
            return

        lead_sock, _ = lead_connection

        json_req = {
            "username": self.username,
            "purpose": "connect",
            "ip": self.ip,
            "port": self.port
        }

        req = json.dumps(json_req)
        print(req)
        encoded_req = req.encode('utf-8')

        # send connection message to SuperUser
        lead_sock.sendto(encoded_req, tuple(leader))

        while True:
            data, rec_addr = lead_sock.recvfrom(BYTES)
            print(data)



    def disconnect(self):
        '''Allow user to exit chat ring'''
        pass


    def send_message(self, message):
        '''Send a global message to all nodes in ring'''
        pass


    def direct_message(self, username, message):
        '''Send a direct message to a target user'''
        pass

