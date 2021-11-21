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
import time
import select
import sys
import collections


LOGIN_SERVER = ('', 9001)
BYTES = 1024
HOST = ''
PORT = 9907


class Base_User:

    def __init__(self):
        '''Constructor for User objects'''

        self.username = None
        self.neighbors = {}
        self.pending_table = collections.OrderedDict() # pending
        self.history_table = set()
        self.message_count = time.time()

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
        
        self.message_count = time.time()

        if message.strip() == "direct":
            user = input('@')
            content = input(f'(@{user})> ') 
            self.direct_message(user, content)
            return
        
        json_req = {
            "username"      : self.username,
            "purpose"       : "global",
            "message"       : message,
            "ip"            : self.ip,
            "port"          : self.port,
            "message_count" : self.message_count
        }

        req = json.dumps(json_req)
        encoded_req = req.encode('utf-8')

        # add transaction to pending; mark as dirty (not yet displayed)
        self.pending_table[self.hash_data(req)] = ['dirty', json_req, self.username, time.time(), False]

        # forward message to neighbor
        self.sock.sendto(encoded_req, tuple(self.neighbors['next_1']))


    def direct_message(self, username, message):
        '''Send a direct message to a target user'''

        message = {
            "username"     : self.username,
            "purpose"      : "direct",
            "message"      : message,
            "ip"           : self.ip,
            "port"         : self.port,
            "target"       : username,
            "message_count": self.message_count
        }
        
        req = json.dumps(message)
        encoded = req.encode('utf-8');

        # add transaction to pending
        self.pending_table[self.hash_data(req)] = ['dirty', message, self.username, time.time(), False]

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
            self.pending_table[self.hash_data(decoded_data)] = ["clean", message, message['username'], time.time(), False]  
            self.display(self.hash_data(decoded_data))
            self.sock.sendto(encoded, source)

        # otherwise forward message to next
        else:
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

        # global acknowledgement response, for when message has either
        # circulated through entire ring, or message has reached a User 
        # who has already seen the message

        json_req = {
            "username"    : self.username,
            "purpose"     : "global_response",
            "message_id"  : self.hash_data(decoded_data) 
        }
        req = json.dumps(json_req)
        encoded_req = req.encode('utf-8')

        # check if incoming data is already in the hisory table
        if self.hash_data(decoded_data) in self.history_table:
            # send back the acknowledgement messages
            self.sock.sendto(encoded_req, tuple(self.neighbors['prev']))
            return 


        # reach end of ring; send back response
        if request['username'] == self.username:

            # update entry in pending table to having been received
            self.pending_table[self.hash_data(decoded_data)][0] = 'clean'

            # check if message is at top of queue to ensure consistent ordering
            if self.hash_data(decoded_data) == list(self.pending_table.keys())[0]:
                # message to prev neighbor
                self.sock.sendto(encoded_req, tuple(self.neighbors['prev']))

        else:
            self.pending_table[self.hash_data(decoded_data)] = ['dirty', request, request['username'], time.time(), False]

            # forward message to neighbor
            self.sock.sendto(data, tuple(self.neighbors['next_1']))


    def handle_disconnect(self, request):
        '''
            recieves a disconnect request, updates either the prev or 
            next neighbor
        '''
        
        if request['prev'] != 'same':
            self.neighbors['prev'] = request['prev']
            if request['cause'] == 'crash':
                json_req = {
                    "purpose": "disconnect",
                    "next_1" : "same",
                    "next_2" : self.neighbors['next_1'],
                    "prev"   : "same",
                    "cause"  : "crash"
                }
                req = json.dumps(json_req)
                encoded_req = req.encode('utf-8')
                self.sock.sendto(encoded_req, tuple(self.neighbors['prev'])) 
                # now that the ordering is all fixed, forward the last message in the pening queue
                

        elif request['next_1'] != 'same' and request['next_2'] != 'same':

            self.neighbors['next_1'] = request['next_1']
            self.neighbors['next_2'] = request['next_2']
            if request['cause'] == 'disconnect':
                json_req = { "purpose": "disconnect",
                    "next_1" : "same",
                    "next_2" : self.neighbors['next_1'],
                    "prev"   : "same",
                    "cause"  : "disconnect"
                }
                req = json.dumps(json_req)
                encoded_req = req.encode('utf-8')
                self.sock.sendto(encoded_req, tuple(self.neighbors['prev'])) 
 
        elif request['next_2'] != 'same':
            if self.neighbors == {}:
                return
            self.neighbors['next_2']  = request['next_2']
            #TODO confirm that this is the correct message to send back
            if request['cause'] == 'crash':
                resumed_request = list(self.pending_table.values())[0][1]
                req = json.dumps(resumed_request).encode('utf-8')
                self.sock.sendto(req, tuple(self.neighbors['next_1']))
                
		
		# case where system is super user and a single user
        if self.neighbors['next_1'] == self.neighbors['prev']:
            self.neighbors['next_2'] = None
        
        # when super user is the only one left in the system
        if tuple(self.neighbors['next_1']) == (self.ip, self.port):
            self.neighbors = {}

	
    def handle_crash(self, request):
        if tuple(self.neighbors['next_1']) != tuple(request['info']):
            # forward to the next node
            self.sock.sendto(json.dumps(request).encode('utf-8'), tuple(self.neighbors['next_1']))
            return 
        # next node is the crashed one, start reassigning neighbors
        self.neighbors['next_1'] = self.neighbors['next_2']
        # notify the prev node
        
        json_req = {
            "purpose": "disconnect",
            "next_1" : (self.ip, self.port),
            "next_2" : self.neighbors['next_1'],
            "prev"   : "same",
            "cause"  : "crash"
        }
        req = json.dumps(json_req)
        encoded_req = req.encode('utf-8')
        self.sock.sendto(encoded_req, tuple(self.neighbors['prev'])) 
        # notify the new next node this node will need to message back with the new next_2

        json_req = {
            "purpose": "disconnect",
            "next_1" : "same",
            "next_2" : "same",
            "prev"   : (self.ip, self.port),
            "cause"  : "crash"
        }

        req = json.dumps(json_req)
        encoded_req = req.encode('utf-8')
        self.sock.sendto(encoded_req, tuple(self.neighbors['next_1'])) 
        
    
    def display(self, message_id):
        '''Internal method to display the message with a given id'''
        if message_id in self.history_table:
            return
        req = self.pending_table[message_id][1]
        username = req['username']
        message = req['message']

        begin = f'[{time.strftime("%H:%M",time.gmtime())}][{username}]'
        if (req["purpose"] == "direct"):
            begin += f'(direct)'
        
        print(f'{begin}: {message}')

        # remove from pending table
        self.pending_table.pop(message_id)
        # add the message_id to the history table
        self.history_table.add(message_id)

