#!/usr/bin/env python3

# SuperUser.py
# Authors: Kristen Friday, Carlo Preciado
# Date: November 1, 2021
#
# The SuperUser class defines a centralized leader in the 
# chat system to allow for new User entry

import Base_User

import socket
import json
import time
import hashlib
import queue
import select
import sys

HOST = ''
PORT = 9060
BYTES = 1024


class SuperUser(Base_User.Base_User):
   
    def __init__(self):
        self.username = 'super_user'
        super().__init__()

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
                self.sock.sendto(update, tuple(self.neighbors["next_1"]))
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
                self.sock.sendto(update, tuple(self.neighbors["prev"]))
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
        print(self.neighbors)
        self.sock.sendto(res, location)

    
    def receive_message(self):
        
        # main listening loop
        while True:
            data, addr = self.sock.recvfrom(BYTES)
            decoded_data = data.decode('utf-8')
            request = json.loads(decoded_data)
            purpose = request['purpose']
            
            # process the request accordingly
            if purpose == 'global':
                self.handle_global(request)
                
            elif purpose == 'global_response':
                # put the message hash into the queue
                self.display(request['message_id'])
                if request['username'] == self.username:
                    # stop forwarding the acknowledgement along
                    continue
                else:
                    #TODO move along the acknowledgement
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

            elif (purpose == "acknowledgement"):
                self.handle_ack(request)

            elif (purpose == "connect"):
                self.add_users(request)

            elif (purpose == "disconnect"):
                self.handle_disconnect(request)
            else:
                print(f"Unknown purpose: {purpose}")
            
    
    def listen(self):
        '''Function to listen for incoming messages'''

        print(f'SuperUser: Listening on port {self.port}...')
        while True:

            rlist, _, _ = select.select([sys.stdin, self.sock], [], [])

            # user entered input
            for read_s in rlist:
                # read input
                if read_s == sys.stdin:
                    self.send_message(sys.stdin.readline())

                # read incoming messages
                else:
                    self.receive_message()


if __name__ == '__main__':

    super_usr = SuperUser()
    super_usr.print_user()
    super_usr.listen()
 
