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

HOST = ''
PORT = 0
BYTES = 1024

class SuperUser:

    def __init__(self):
        '''Constructor for User objects'''

        self.username = "super_user"
        self.neighbors = {}
        self.message_table = {}

        ip = socket.gethostbyname(socket.gethostname())
        self.ip = ip

        serv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        serv_sock.bind((HOST,PORT))
        _, self.port = serv_sock.getsockname()
        self.serv_sock = serv_sock


    def print_user(self):
        '''Method to print attributes of the SuperUser'''

        print(f'Username:  {self.username}')
        print(f'IP Addr:   {self.ip}')
        print(f'Port:      {self.port}')
        print(f'Neighbors: {self.neighbors}')
        print(f'Messages:  {self.message_table}\n')


    def add_users(self):
        '''Method to listen for incoming clients and add to chat system'''

        print(f'SuperUser: Listening on port {self.port}...')
        while True:
            data, rec_addr = self.serv_sock.recvfrom(BYTES)
            req = json.loads(data.decode('utf-8'))
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
            print(self.neighbors)


    def send_message(self, message):
        '''Send a global message to all nodes in ring'''
        pass


    def direct_message(self, username, message):
        '''Send a direct message to a target user'''
        pass


if __name__ == '__main__':

    super_usr = SuperUser()
    super_usr.print_user()
    super_usr.add_users()
