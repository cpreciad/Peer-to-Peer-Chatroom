#!/usr/bin/env python3

# User.py
# Authors: Kristen Friday, Carlo Preciado
# Date: November 1, 2021
#
# The User class defines a node in the chat system
# It serves as the abstraction template for basic functionality
import threading
import socket
import json
import hashlib
import queue
import time


LOGIN_SERVER = ('', 9000)
BYTES = 1024
HOST = ''
PORT = 9020

def hash_data(data):
    return int(hashlib.md5(data.encode('ascii')).hexdigest(), 16) 


class User:

    def __init__(self):
        '''Constructor for User objects'''

        self.username = input("Enter your username: ")
        self.neighbors = {} # prev, next_1, next_2
        self.friends = {}
        self.pending_table = {} # pending
        self.message_queue = queue.Queue() 
        self.display_queue = queue.Queue() # history

        ip = socket.gethostbyname(socket.gethostname())
        self.ip = ip
       
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

        #  socket to send or forward messages
        self.messaging_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


    def print_user(self):
        '''Method to print attributes of the User'''                              

        print(f'Username:  {self.username}')
        print(f'IP Addr:   {self.ip}')
        print(f'Port:      {self.port}') 
        print(f'Neighbors: {self.neighbors}')
        print(f'Messages:  {self.pending_table}\n')


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
        data, rec_addr = self.sock.recvfrom(BYTES)
        data = json.loads(data.decode('utf-8'))
        self.neighbors["prev"] = leader
        self.neighbors["next_1"] = data["next_1"]
        self.neighbors["next_2"] = data["next_2"]

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


    def send_message(self, message):
        ''' Send a global message to all nodes in ring
            
            really just an abstraction for adding a message to a message queue
            encodes the message and add it to the message queue
        '''
        json_req = {
            "username": self.username,
            "purpose" : "global",
            "message" : message, 
            "ip"      : self.ip,
            "port"    : self.port
        }

        req = json.dumps(json_req)
        
        encoded_req = req.encode('utf-8')
        self.pending_table[hash_data(req)] = json_req
        self.message_queue.put(encoded_req)

    def direct_message(self, username, message):
        '''Send a direct message to a target user'''

        message = {
            "username": self.username,
            "purpose": "direct",
            "message": message,
            "ip": self.ip,
            "port": self.port,
            "target": username
        }

        
        req = json.dumps(message).encode('utf-8');
        # send direct message to next neighbor
        self.sock.sendto(req, self.neighbors["next_1"]);
        data = self.sock.recv(BYTES);


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
                "curr_next": self.neighbors["next_1"]
            }

            res = json.dumps(res).encode('utf-8')
            self.sock.sendto(res, leader)

        # update last node in ring to include new node
        else:
            self.neighbors["next_2"] = message["next_2"]
            res = {
                "status": "success",
            }
            res = json.dumps(res).encode('utf-8')
            self.sock.sendto(res, leader)
    

    def handle_direct(self, message):
        '''Handling the receival of a direct message'''

        # check if username matches
        if (self.username == message["username"]):
            source = tuple(message["ip"], message["port"])
            res = {
                "username": self.username,
                "status": "listening"
            }

            json_res = json.dumps(res).encode('utf-8')
            self.sock.sendto(json_res, source)

        # otherwise forward message to next
        else:
            # first send acknowledgement to sender
            res = {
                "username": self.username,
                "purpose": "acknowledgement"
            }
            ack = json.dumps(res).encode('utf-8')
            sender = tuple(message["ip"], message["port"])
            self.sock.sendto(ack, sender)

            # forward along message
            message = json.dumps(message).encode('utf-8')
            self.sock.sendto(message, self.neighbors["next_1"])

            # block until receiving acknowledgement
            while True:
                data = self.sock.recv(bytes)
                ack = json.loads(data.decode('utf-8'))
                if (ack["purpose"] and ack["purpose"] == "acknowledgement"):


    def send_internal(self):
        ''' Internal method to send messages and wait for responses
            
            May have the additional responsibility of detecting if a neighbor has crashed
        '''
        #  socket to send or forward messages
        messaging_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        while True:
            if self.message_queue != []:
                next_message = self.message_queue.get() 

                # TODO send the next message to this users next neighbor
                messaging_sock.sendto(next_message, tuple(self.neighbors['next_1']))

    def display_internal(self):
        '''Internal method to remove the messsage from the queue and display the message'''

        while True:
            if self.display_queue != []:
                next_message = self.display_queue.get()
                username = self.pending_table[next_message]['username']
                message = self.pending_table[next_message]['message']
                print(f'[{time.strftime("%H:%M",time.gmtime())}][{username}]: {message}', flush=True)
                print('')
                # verify that the message id is in the 
                # pending_table

    def listen_internal(self):
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
                # simply add the request to the message queue and 
                # let the main program handle this, unless its from itself,
                # then start the acknowledgement test
                if request['username'] == self.username:
                    # forward the acknowledgement message
                    json_req = {
                        "username"    : self.username,
                        "purpose"     : "acknowledgement",
                        "message_id" : hash_data(decoded_data) 
                    }
                    req = json.dumps(json_req)
                    encoded_req = req.encode('utf-8')
                    #TODO message to prev neighbor
                    ack_sock.sendto(encoded_req, tuple(self.neighbors['prev']))
 
                else:
                    self.pending_table[hash_data(decoded_data)] = request
                    self.message_queue.put(data)

            elif purpose == 'acknowledgement':
                # put the message hash into the queue
                self.display_queue.put(request['message_id'])
                if request['username'] == self.username:
                    # stop forwarding the acknowledgement along
                    continue
                else:
                    #TODO move along the acknowledgement
                    ack_sock.sendto(data, tuple(self.neighbors['prev']))
            
            elif purpose == 'direct':
                pass
            elif purpose == 'dm_response':
                pass

            # update pointers for a new node
            elif (purpose == "update_pointers" or purpose == "update_last_node"):
                self.update_pointers(purpose, request, addr)
            
            # direct message
            elif (purpose == "direct"):
                self.handle_direct(request)

