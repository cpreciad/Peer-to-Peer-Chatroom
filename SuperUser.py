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
import queue

HOST = ''
PORT = 9060
BYTES = 1024


class SuperUser():

    def __init__(self):
        '''Constructor for SuperUser objects'''

        self.username = "super_user"
        self.neighbors = {} # prev, next_1, next_2
        self.pending_table = {} # pending
        self.message_queue = queue.Queue()
        self.display_queue = queue.Queue() # history

        ip = socket.gethostbyname(socket.gethostname())
        self.ip = ip

        serv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        serv_sock.bind((HOST,PORT))
        _, self.port = serv_sock.getsockname()
        self.sock = serv_sock

        # socket to send or forward messages
        self.messaging_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    
    def print_user(self):
        '''Method to print attributes of the User'''

        print(f'Username:  {self.username}')
        print(f'IP Addr:   {self.ip}')
        print(f'Port:      {self.port}\n')


    def hash_data(self, data):
        return int(hashlib.md5(data.encode('ascii')).hexdigest(), 16)


    def send_message(self, message):
        ''' Send a global message to all nodes in ring

            really just an abstraction for adding a message to a message queue
            encodes the message and add it to the message queue
        '''

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
        # put message in the queue for consistent ordering
        self.message_queue.put(encoded_req)


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
        # put message in the queue for consistent ordering
        self.message_queue.put(encoded)
 

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


    def handle_ack(self, message, ack_sock):
        '''Handle sending an acknowledgment back to send'''

        res = {
            "username": self.username,
            "ip"      : self.ip,
            "port"    : self.port,
            "purpose" : "acknowledgement"
        }

        ack = json.dumps(res).encode('utf-8')
        sender = (message["ip"], message["port"])
        ack_sock.sendto(ack, sender)


    def handle_direct(self, message, ack_sock):
        '''Handling the receival of a direct message'''

        decoded_data = json.dumps(message)

        # check if message made it to sender without finding target
        if (self.username == message["username"]):
            print(f'{message["target"]} does not exist')
            return

        # check if username matches the target
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
            self.display_queue.put(self.hash_data(decoded_data))
            ack_sock.sendto(encoded, source)

        # otherwise forward message to next
        else:
            # first send acknowledgement to sender
            self.handle_ack(message, ack_sock)

            # forward along message
            message = json.dumps(message).encode('utf-8')
            ack_sock.sendto(message, tuple(self.neighbors["next_1"]))

            # TODO: determine if forwarded message is received


    def handle_global(self, request, ack_sock):
        '''
            simply add the request to the message queue and
            let the main program handle this, unless its from itself,
            then start the acknowledgement test
        '''

        decoded_data = json.dumps(request)
        data = decoded_data.encode('utf-8')
        # check if message made it back to sender
        if request['username'] == self.username:
            # forward the acknowledgement message
            json_req = {
                "username"    : self.username,
                "purpose"     : "global_response",
                "message_id"  : self.hash_data(decoded_data)
            }
            req = json.dumps(json_req)
            encoded_req = req.encode('utf-8')
            #TODO message to prev neighbor
            ack_sock.sendto(encoded_req, tuple(self.neighbors['prev']))

        else:
            self.pending_table[self.hash_data(decoded_data)] = request
            self.message_queue.put(data)


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
                print(self.pending_table[next_message])
                # verify that the message id is in the
                # pending_table


    def add_users(self, req):
        '''Method to listen for incoming clients and add to chat system'''

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
                    print("SuperUser: Unable to retrieve next neighbor")
                    return

                update = json.dumps(update).encode('utf-8')

                # request current next's next neighbor
                self.sock.sendto(update, self.neighbors["next_1"])
                up_res, _ = self.sock.recvfrom(BYTES)
                json_up_res = json.loads(up_res.decode('utf-8'))

                if (json_up_res["status"] == "success"):
                    new_next_next = json_up_res["curr_next"]
                    break

                count += 1
            
            count = 0
            # inform last node in ring that it must update next_2
            update = {
                "purpose": "update_last_node",
                "next_2": location
            }
            while True:
                if count >= 5:
                    print("SuperUser: Unable to update next_2")
                    return

                update = json.dumps(update).encode('utf-8')
                self.sock.sendto(update, self.neighbors["prev"])
                up_res, _ = self.sock.recvfrom(BYTES)
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
        print(f'Added User {req["username"]}')
        self.sock.sendto(res, location)

    
    def listen_internal(self):
        # socket for forwarding acknowledgements
        ack_sock =  socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        print(f'SuperUser: Listening on port {self.port}...')
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
                    #TODO move along the acknowledgement
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

            elif (purpose == "connect"):
                self.add_users(request)

            else:
                print(f"Unknown purpose: {purpose}")
            


if __name__ == '__main__':

    super_usr = SuperUser()
    super_usr.print_user()

    listen_thread = threading.Thread(target = super_usr.listen_internal, daemon = True)
    listen_thread.start()
        
    send_thread = threading.Thread(target = super_usr.send_internal, daemon = True)
    send_thread.start()

    display_thread = threading.Thread(target = super_usr.display_internal, daemon = True)
    display_thread.start()


    while True:
        message = input('> ')
        super_usr.send_message(message)
 
