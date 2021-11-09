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
import threading
import hashlib

HOST = ''
PORT = 0
BYTES = 1024

def hash_data(data):
    return int(hashlib.md5(data.encode('ascii')).hexdigest(),16)

class SuperUser:

    def __init__(self):
        '''Constructor for User objects'''

        self.username = "super_user"
        self.neighbors = {}
        self.pending_table = {}
        self.message_queue = []
        self.display_queue = []

        ip = socket.gethostbyname(socket.gethostname())
        self.ip = ip

        serv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        serv_sock.bind((HOST,PORT))
        _, self.port = serv_sock.getsockname()
        self.serv_sock = serv_sock

        # socket to send or forward messages
        self.messaging_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


    def print_user(self):
        '''Method to print attributes of the SuperUser'''

        print(f'Username:  {self.username}')
        print(f'IP Addr:   {self.ip}')
        print(f'Port:      {self.port}')
        print(f'Neighbors: {self.neighbors}')
        print(f'Messages:  {self.pending_table}\n')


    def add_users(self, req):
        '''Method to listen for incoming clients and add to chat system'''

        print(f'SuperUser: Listening on port {self.port}...')
        while True:
            #data, rec_addr = self.serv_sock.recvfrom(BYTES)
            #req = json.loads(data.decode('utf-8'))
            print(f'{req["username"]}: {req}')
            location = (req["ip"], req["port"])
            new_next = (self.ip, self.port)
            new_next_next = None

            # if other users, inform the next user
            if "next_1" in self.neighbors:

                new_next = self.neighbors["next_1"]

                update = {
                    "purpose": "update_pointers",
                    "prev": location
                }

                count = 0
                while True:
                    if count >= 5:
                        print("SuperUser: Unable to add new user")
                        return

                    update = json.dumps(update).encode('utf-8')
                    self.serv_sock.sendto(update, self.neighbors["next_1"])
                    up_res, _ = self.serv_sock.recvfrom(BYTES)
                    json_up_res = json.loads(up_res.decode('utf-8'))
                    if (json_up_res["status"] == "success"):
                        new_next_next = json_up_res["curr_next"]
                        break
                    count += 1
                
                count = 0
                update = {
                    "purpose": "update_last_node",
                    "next_2": location
                }
                while True:
                    if count >= 5:
                        print("SuperUser: Unable to add new user")
                        return

                    update = json.dumps(update).encode('utf-8')
                    self.serv_sock.sendto(update, self.neighbors["prev"])
                    up_res, _ = self.serv_sock.recvfrom(BYTES)
                    json_up_res = json.loads(up_res.decode('utf-8'))
                    if (json_up_res["status"] == "success"):
                        break
                    count += 1

                self.neighbors["next_2"] = self.neighbors["next_1"]
            
            # update next pointers
            self.neighbors["next_1"] = location
            if "prev" not in self.neighbors:
                self.neighbors["prev"] = location

            json_res = {
                "status": "success",
                "next_1": new_next,
                "next_2": new_next_next
            }

            res = json.dumps(json_res).encode('utf-8')
            self.serv_sock.sendto(res, location)
            return 

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

        self.message_queue.append(encoded_req)

    def display_message(self, hashed_data):
        ''' add the request into the display message queue
            
            decode the message and put the string representation of the 
            request into the display_list
        '''
        self.display_queue(hashed_data)


    def direct_message(self, username, message):
        '''Send a direct message to a target user'''
        pass

    def send_internal(self):
        print('send internal beginning')
        ''' Internal method to send messages and wait for responses
            
            May have the additional responsibility of detecting if a 
            neighbor has crashed
        '''
        #  socket to send or forward messages
        messaging_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        while True:
            if self.message_queue != []:

                next_message = self.message_queue.pop(0)
                # TODO send the next message to this users next neighbor
                messaging_sock.sendto(next_message, tuple(self.neighbors['next_1']))

    def display_internal(self):
        print('display internal beginning')
        ''' Internal method to remove the messsage from the queue and 
            display the message
        '''

        while True:
            if self.display_queue != []:
                next_message = self.display_queue.pop(0)
                print(self.pending_data[next_messsage])
                # verify that the message id is in the 
                # pending_table

    def listen_internal(self):
        # socket for forwarding acknowledgements
        print('listen internal beginning')
        ack_sock =  socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # main listening loop
        while True:
            data = self.serv_sock.recv(BYTES)
            decoded_data = data.decode('utf-8')
            request = json.loads(decoded_data)
            print(request)

            # process the request accordingly
            if request['purpose'] == 'global':
                # simply add the request to the message queue and 
                # let the main program handle this, unless its from itself,
                # then start the acknowledgement test
                if request['username'] == self.username:
                    # forward the acknowledgement message
                    json_req = {
                        "username"    : self.username,
                        "purpose"     : "acknowledgement",
                        " message_id" : hash_data(decoded_data)
                    }
                    req = json.dumps(json_req)
                    encoded_req = req.encode('utf-8')
                    #TODO message to prev neighbor
                    ack_sock.sendto(data, tuple(self.neighbors['prev']))

                else:
                    self.pending_table[hash_data(decoded_data)] = request
                    self.message_queue.append(data)

            if request['purpose'] == 'acknowledgement':
                self.display_message(decoded_data)
                if request['username'] == self.username:
                    # stop forwarding the acknowledgement along
                    continue
                else:
                    #TODO move along the acknowledgement
                    ack_sock.sendto(data, tuple(self.neighbors['prev']))
            if request['purpose'] == 'connect':
                self.add_users(request)

            if request['purpose'] == 'direct':
                pass
            if request['purpose'] == 'dm_response':
                pass



if __name__ == '__main__':

    super_usr = SuperUser()
    super_usr.print_user()
    
    #connection_thread = threading.Thread(target = super_usr.add_users, daemon = True)
    #connection_thread.start()

    listen_thread = threading.Thread(target = super_usr.listen_internal, daemon = True)
    listen_thread.start()
        
    send_thread = threading.Thread(target = super_usr.send_internal, daemon = True)
    send_thread.start()

    display_thread = threading.Thread(target = super_usr.display_internal, daemon = True)
    display_thread.start()


    while True:
        message = input('> ')
        super_usr.send_message(message)
 
