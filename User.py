#!/usr/bin/env python3

# User.py
# Authors: Kristen Friday, Carlo Preciado
# Date: November 1, 2021
#
# The User class defines a node in the chat system
# It serves as the abstraction template for basic functionality

import Base_User

import threading
import socket
import json
import hashlib
import queue
import time


LOGIN_SERVER = ('', 9001)
BYTES = 1024
HOST = ''
PORT = 9907


class User(Base_User.Base_User):

    def __init__(self):
        self.username = input("Enter your username: ")
        super().__init__()

    def connect_to_login(self):
        '''Method to set up UDP connection with LoginServer'''

        json_req = {
            "username": self.username,
            "purpose": "connect"
        }

        req = json.dumps(json_req)
        encoded_req = req.encode('utf-8')

        self.sock.sendto(encoded_req, LOGIN_SERVER)
        data = self.sock.recv(BYTES)

        res = data.decode('utf-8')
        json_res = json.loads(res)
      
        if (json_res["status"] == "success"):
            return json_res["leader"]
        elif (json_res["status"] == "failure"):
            if (json_res["error"]) == "un-unique":
                raise Exception(f'The Username ({self.username}) is already in use')
 

    def connect(self):
        '''Allow user to enter chat ring'''

        leader = self.connect_to_login()

        json_req = {
            "username": self.username,
            "purpose": "connect",
            "ip": self.ip,
            "port": self.port
        }

        req = json.dumps(json_req)
        encoded_req = req.encode('utf-8')

        # send connection message to SuperUser
        self.sock.sendto(encoded_req, tuple(leader))
        data = self.sock.recv(BYTES)
        data = json.loads(data.decode('utf-8'))

        self.neighbors["prev"] = leader
        self.neighbors["next_1"] = data["next_1"]
        self.neighbors["next_2"] = data["next_2"]
        
        print(f'SuperUser: {data}')

        # set up threads for recieving messages, sending messages, and displaying messages
        listen_thread = threading.Thread(target = self.listen_internal, daemon = True)
        listen_thread.start()
        
        send_thread = threading.Thread(target = self.send_internal, daemon = True)
        send_thread.start()

        display_thread = threading.Thread(target = self.display_internal, daemon = True)
        display_thread.start()

    
    def disconnect(self):
        '''Allow user to exit chat ring'''
        pass


  
    def listen_internal(self):
        '''Listen for incoming messages and process accordingly'''

        # socket for forwarding acknowledgements
        ack_sock =  socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # main listening loop
        while True:
            data, addr = self.sock.recvfrom(BYTES)
            decoded_data = data.decode('utf-8')
            request = json.loads(decoded_data)
            purpose = request['purpose']

            # process the request accordingly
            if purpose == 'global':
                self.handle_global(request, ack_sock)

            elif purpose == 'global_response':
                # put the message hash into the queue
                self.display_queue.put(request['message_id'])
                if request['username'] == self.username:
                    # stop forwarding the acknowledgement along
                    continue
                else:
                    # move along the acknowledgement
                    ack_sock.sendto(data, tuple(self.neighbors['prev']))
            
            elif purpose == 'dm_response':
                # put private message into display queue
                self.display_queue.put(request['message_id'])

            # update pointers for a new node
            elif (purpose == "update_pointers" or purpose == "update_last_node"):
                self.update_pointers(purpose, request, addr)
            
            # direct message
            elif (purpose == "direct"):
                self.handle_direct(request, ack_sock)
            
            elif (purpose == "acknowledgement"):
                self.handle_ack(request, ack_sock)

            else:
                print(f"Unknown purpose: {purpose}")

