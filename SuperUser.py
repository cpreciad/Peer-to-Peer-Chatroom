#!/usr/bin/env python3

# SuperUser.py
# Authors: Kristen Friday, Carlo Preciado
# Date: November 1, 2021
#
# The SuperUser class defines a centralized leader in the 
# chat system to allow for new User entry


class SuperUser:

    def __init__(self):
        '''Constructor for User objects'''

        self.username = ""
        self.location = (None, None)
        self.neighbors = {}
        self.message_table = {}


    def send_message(self, message):
        '''Send a global message to all nodes in ring'''
        pass


    def direct_message(self, username, message):
        '''Send a direct message to a target user'''
        pass

