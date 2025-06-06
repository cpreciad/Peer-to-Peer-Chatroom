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


LOGIN_SERVER = ('student10.cse.nd.edu', 9999)
BYTES = 1024
TIMEOUT = .5


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
            "purpose" : "connect",
            "ip"      : self.ip,
            "port"    : self.port
        }

        req = json.dumps(json_req)
        encoded_req = req.encode('utf-8')

        self.sock.sendto(encoded_req, LOGIN_SERVER)

        # throw exception if LoginServer doesn't respond in 3 seconds
        self.sock.settimeout(3)
        try:
            data = self.sock.recv(BYTES)
            self.sock.settimeout(None)
        except socket.timeout:
            print(f"User {self.username} could not connect to LoginServer")
            sys.exit(-1)
          
        res = data.decode('utf-8')
        json_res = json.loads(res)
        try:
            status = json_res["status"]
        except KeyError:
            print(f"User {self.username} could not connect to LoginServer")
            sys.exit(-1)

        if (status == "success"):
            return json_res["leader"]
        else:
            if (json_res["error"]) == "un-unique":
                raise Exception(f'The Username or (IP,PORT) is already in use')
            if (json_res["error"]) == "server_down":
                raise Exception(f'The System currently under repair due to a crashed user. Please reconnect in a moment')
 

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
        '''Allow user to cleanly exit chat ring'''
        
        # make the first disconnection request to the next neighbor
        json_req = {
            "purpose"  : "disconnect",
            "next_1"   : "same",
            "next_2"   : "same",
            "prev"     : self.neighbors['prev'],
            "cause"    : "disconnect"
        }

        req = json.dumps(json_req)
        encoded_req = req.encode('utf-8')
        self.sock.sendto(encoded_req, tuple(self.neighbors['next_1']))

        # make the second disconnection request to the prev neighbors
        json_req = {
            "purpose"  : "disconnect",
            "next_1"   : self.neighbors['next_1'],
            "next_2"   : self.neighbors['next_2'],
            "prev"     : "same",
            "cause"    : "disconnect"
        }

        req = json.dumps(json_req)
        encoded_req = req.encode('utf-8')
        self.sock.sendto(encoded_req, tuple(self.neighbors['prev']))

        # final request to login server to notify name removal from system
        json_req = {
		    "purpose": "disconnect",
            "username": self.username
        }
        req = json.dumps(json_req)
        encoded_req = req.encode('utf-8')
        self.sock.sendto(encoded_req, LOGIN_SERVER)
        sys.exit(0)


    def receive_message(self):
        '''Listen for incoming messages and process accordingly'''

        # main listening loop
        data, addr = self.sock.recvfrom(BYTES)
        decoded_data = data.decode('utf-8')
        request = json.loads(decoded_data)
        purpose = request['purpose']

        # process the request accordingly
        if purpose == 'global':
            self.handle_global(request, addr)

        elif purpose == 'global_response':
            # display the message
            self.display(request["message_id"])

            if request['username'] == self.username:
                # check for additional acknowledged messages in pending
                if self.pending_table:
                    first_val = list(self.pending_table.values())[0]
                    if first_val[0] == "clean":
                        self.handle_global(first_val[1], [self.ip, self.port])

                # stop forwarding the acknowledgement along
                return
            else:
                # move along the acknowledgement
                self.sock.sendto(data, tuple(self.neighbors['prev']))
        
        elif purpose == 'dm_response':
            # display private message
            self.display(request['message_id'])

        # update pointers for a new node
        elif (purpose == "update_pointers" or purpose == "update_last_node"):
            self.update_pointers(purpose, request, addr)
        
        # direct message
        elif (purpose == "direct"):
            self.handle_direct(request, addr)
        
        elif (purpose == "disconnect"):
            self.handle_disconnect(request)

        elif (purpose == "checkup"):
            self.sock.sendto(json.dumps({
                "status":"ok",
                "purpose": "checkup_res"
            }).encode('utf-8'), LOGIN_SERVER)
        
        elif (purpose == "crash"):
            self.handle_crash(request)

        elif (purpose == "kicked_out"):
            print("Disconnected from chat room. Please retry logging in.")
            sys.exit(-1)

        elif (purpose == "total_failure"):
            print("Multiple users crashed. Please retry logging in.")
            sys.exit(-1)
        
        else:
            print(f"Unknown purpose: {purpose}")


    def check_pending(self):
        '''Determine if direct messages are still pending'''
        for key in self.pending_table:
            if self.username == self.pending_table[key][2]:
                return True
        return False


    def listen(self):
        '''Function to listen for incoming messages (send or receive)'''
        
        while True:

            rlist, _, _ = select.select([sys.stdin, self.sock], [], [], TIMEOUT)

            for read_s in rlist:

                # read input
                if read_s == sys.stdin:
                    usr_input = sys.stdin.readline()
                    if usr_input.strip() == "disconnect":
                        if not self.check_pending():
                            self.disconnect()
                            sys.exit(0)
                        else:
                            print('processing messages, please try disconnecting later')
                    else:        
                        self.send_message(usr_input)

                # read incoming messages
                else:
                    self.receive_message()
                    
            # check if there have been timeouts for a message at top of pending queue
            if not self.pending_table:
                continue

            for idx, value in enumerate(list(self.pending_table.values())):
                req  = value[1]
                name = value[2]
                user_time = value[3]
                sent = value[4]
                
                if time.time() - user_time > TIMEOUT and name == self.username:
                    if sent == False:
                        # it's this users responsibility to prompt the checkins
                        # tell the login server to check for timeouts
                        self.sock.sendto(json.dumps(
                            {"purpose":"checkup"}).encode('utf-8'), LOGIN_SERVER)
                        self.pending_table[
                                list(self.pending_table.keys())[idx]][4] = True
                    else:
                        self.sock.sendto(json.dumps(
                            req).encode('utf-8'), tuple(self.neighbors['next_1']))
            

