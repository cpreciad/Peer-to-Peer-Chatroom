#!/usr/bin/env python3

# User.py
# Authors: Kristen Friday, Carlo Preciado
# Date: November 1, 2021
#
# The User class defines a node in the chat system
# It serves as the abstraction template for basic functionality

import Base_User

import socket
import json
import hashlib
import queue
import time
import sys
import select


LOGIN_SERVER = ('', 9001)
BYTES = 1024
HOST = ''
PORT = 9907


class User(Base_User.Base_User):

    def __init__(self, username=None):
        super().__init__()
        if username is None:
            self.username = input("Enter your username: ")
        else:
            self.username = username


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

    
    def disconnect(self):
        '''Allow user to exit chat ring'''
        
        # make the first disconnection request to the next neighbor
        json_req = {
            "purpose": "disconnect",
            "next_1"   : "same",
            "next_2"   : "same",
            "prev"   : self.neighbors['prev']
        }

        req = json.dumps(json_req)
        encoded_req = req.encode('utf-8')
        self.sock.sendto(encoded_req, tuple(self.neighbors['next_1']))

        # make the second disconnection request to the prev neighbors
        json_req = {
            "purpose": "disconnect",
            "next_1"   : self.neighbors['next_1'],
            "next_2"   : "same",
            "prev"   : "same"
        }

        req = json.dumps(json_req)
        encoded_req = req.encode('utf-8')
        self.sock.sendto(encoded_req, tuple(self.neighbors['prev']))


    def receive_message(self):
        '''Listen for incoming messages and process accordingly'''

        # main listening loop
        data, addr = self.sock.recvfrom(BYTES)
        decoded_data = data.decode('utf-8')
        request = json.loads(decoded_data)
        purpose = request['purpose']

        # process the request accordingly
        if purpose == 'global':
            self.handle_global(request)

        elif purpose == 'global_response':
            # display the message
            self.display(request["message_id"])

            if request['username'] == self.username:
                # check for additional acknowledged messages in pending
                if self.pending_table:
                    first_val = list(self.pending_table.values())[0]
                    if first_val[0] == "clean":
                        self.handle_global(first_val[1])

                # stop forwarding the acknowledgement along
                return
            else:
                # move along the acknowledgement
                self.sock.sendto(data, tuple(self.neighbors['prev']))
        
        elif purpose == 'dm_response':
            # put private message into display queue
            self.display(request['message_id'])

        # update pointers for a new node
        elif (purpose == "update_pointers" or purpose == "update_last_node"):
            self.update_pointers(purpose, request, addr)
        
        # direct message
        elif (purpose == "direct"):
            self.handle_direct(request)
        
        elif (purpose == "disconnect"):
            self.handle_disconnect(request)
        else:
            print(f"Unknown purpose: {purpose}")


    def listen(self):
        '''Function to listen for incoming messages'''
        
        while True:

            rlist, _, _ = select.select([sys.stdin, self.sock], [], [])

            # user entered input
            for read_s in rlist:
                # read input
                if read_s == sys.stdin:
                    usr_input = sys.stdin.readline()
                    if usr_input.strip() == "disconnect":
                        self.disconnect()
                        sys.exit(0)
                    self.send_message(usr_input)

                # read incoming messages
                else:
                    self.receive_message()

