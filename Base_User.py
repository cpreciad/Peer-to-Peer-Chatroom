#!/usr/bin/env python3

# Base_User.py
# Authors: Kristen Friday, Carlo Preciado
# Date: November 10, 2021
#
# The Base User class defines a basic implementation of a node in the chat system
# It serves as the abstraction template for basic functionality

import socket
import json
import hashlib
import queue
import time
import select
import sys


LOGIN_SERVER = ('', 9001)
BYTES = 1024
HOST = ''
PORT = 9907


class Base_User:

    def __init__(self):
        '''Constructor for User objects'''

        self.username = None
        self.neighbors = {}
        self.pending_table = {} # pending

        self.ip = socket.gethostbyname(socket.gethostname())
       
        # "server" socket to listen for other peer's messages
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		# find a port to bind to, which is in the range from 9000-9999
        for port_num in range(9000, 10000):
            try:
                sock.bind((HOST,port_num))
                break
            except OSError:
                continue

        _, self.port = sock.getsockname()
        self.sock = sock


    def hash_data(self, data):
        return int(hashlib.md5(data.encode('ascii')).hexdigest(), 16)


    def print_user(self):
        '''Method to print attributes of the User'''                      

        print(f'Username:  {self.username}')
        print(f'IP Addr:   {self.ip}')
        print(f'Port:      {self.port}\n')


    def send_message(self, message):
        ''' Send a global message to all nodes in ring
            
            really just an abstraction for adding a message to a message queue
            encodes the message and add it to the message queue
        '''

        print(message)
        if message == "direct":
            user = input('@')
            content = input(f'(@{user})> ') 
            self.direct_message(user, content)
            return

        json_req = {
            "username": self.username,
            "purpose" : "global",
            "message" : message,
            "ip"      : self.ip,
            "port"    : self.port
        }

        req = json.dumps(json_req)
        encoded_req = req.encode('utf-8')

        # add transaction to pending
        self.pending_table[self.hash_data(req)] = json_req

        # forward message to neighbor
        self.sock.sendto(encoded_req, tuple(self.neighbors['next_1']))


    def direct_message(self, username, message):
        '''Send a direct message to a target user'''

        message = {
            "username"   : self.username,
            "purpose"    : "direct",
            "message"    : message,
            "ip"         : self.ip,
            "port"       : self.port,
            "target"     : username,
        }
        
        req = json.dumps(message)
        encoded = req.encode('utf-8');

        # add transaction to pending
        self.pending_table[self.hash_data(req)] = message

        # forward message to neighbor
        self.sock.sendto(encoded, tuple(self.neighbors['next_1']))


    def update_pointers(self, purpose, message, leader):
        '''Update pointers to accomodate new nodes'''

        if (purpose == "update_pointers"):
            self.neighbors["prev"] = message["prev"]
            if self.neighbors["next_2"] == None:
                # next next pointer is the new node
                self.neighbors["next_2"] = message["prev"]
                # next pointer is the leader
                self.neighbors["next_1"] = leader
    
            res = {
                "status": "success",
                "curr_next": self.neighbors["next_1"],
                "purpose": "update_pointers"
            }

        # purpose = "update_last_node"
        else:
            self.neighbors["next_2"] = message["next_2"]
            res = {
                "status": "success",
                "purpose": "update_pointers"
            }
        
        res = json.dumps(res).encode('utf-8')
        self.sock.sendto(res, leader)
    

    def handle_ack(self, message):
        '''Handle sending an acknowledgment back to send'''

        res = {
            "username": self.username,
            "ip"      : self.ip,
            "port"    : self.port,
            "purpose" : "acknowledgement"
        }

        ack = json.dumps(res).encode('utf-8')
        sender = (message["ip"], message["port"])
        self.sock.sendto(ack, sender)


    def handle_direct(self, message):
        '''Handling the receival of a direct message'''

        decoded_data = json.dumps(message)

        # check if message made it to sender without finding target
        if (self.username == message["username"]):
            print(f'{message["target"]} does not exist')
            return

        # check if username matches target
        elif (self.username == message["target"]):
            source = (message["ip"], message["port"])
            json_res = {
                "username"  : self.username,
                "ip"        : self.ip,
                "port"      : self.port,
                "status"    : "listening",
                "purpose"   : "dm_response",
                "message_id": self.hash_data(decoded_data)
            }

            res = json.dumps(json_res)
            encoded = res.encode('utf-8')
            # display message
            self.pending_table[self.hash_data(decoded_data)] = message
            self.display(self.hash_data(decoded_data))
            self.sock.sendto(encoded, source)

        # otherwise forward message to next
        else:
            # first send acknowledgement to sender
            # self.handle_ack(message)

            # forward along message
            message = json.dumps(message).encode('utf-8')
            self.sock.sendto(message, tuple(self.neighbors["next_1"]))


    def handle_global(self, request):
        '''
            simply add the request to the message queue and 
            let the main program handle this, unless its from itself,
            then start acknowledgement test
        '''

        decoded_data = json.dumps(request)
        data = decoded_data.encode('utf-8')

        if request['username'] == self.username:
            # reach end of ring; send back response
            json_req = {
                "username"    : self.username,
                "purpose"     : "global_response",
                "message_id"  : self.hash_data(decoded_data) 
            }
            req = json.dumps(json_req)
            encoded_req = req.encode('utf-8')
            # message to prev neighbor
            self.sock.sendto(encoded_req, tuple(self.neighbors['prev']))

        else:
            self.pending_table[self.hash_data(decoded_data)] = request

            # forward message to neighbor
            self.sock.sendto(data, tuple(self.neighbors['next_1']))


    def handle_disconnect(self, request):
        '''
            recieves a disconnect request, updates either the prev or 
            next neighbor
        '''
        
        if request['prev'] != 'same':
            self.neighbors['prev'] = request['prev']

        if request['next_1'] != 'same':
            self.neighbors['next_1'] = request['next_1']
            json_req = {
                "purpose": "disconnect",
                "next_1" : "same",
                "next_2" : self.neighbors['next_1'],
                "prev"   : "same" 
            }
            req = json.dumps(json_req)
            encoded_req = req.encode('utf-8')
            self.sock.sendto(encoded_req, tuple(self.neighbors['prev'])) 
 
        if request['next_2'] != 'same':
            self.neighbors['next_2']  = request['next_2']
 
        if self.neighbors['next_1'] == self.neighbors['prev']:
            self.neighbors['next_2'] = None
        
        # server case, when it is the only one left in the system
        if self.neighbors['next_1'] == (self.ip, self.port):
            self.neighbors = {}

    
    def display(self, message_id):
        '''Internal method to display the message with a given id'''
        
        username = self.pending_table[message_id]['username']
        message = self.pending_table[message_id]['message']

        begin = f'[{time.strftime("%H:%M",time.gmtime())}][{username}]'
        if (self.pending_table[message_id]["purpose"] == "direct"):
            begin += f' (direct)'
        
        print(f'{begin}: {message}')

        # remove from pending table
        self.pending_table.pop(message_id)



