#!/usr/bin/env python3

# User.py
# Authors: Kristen Friday, Carlo Preciado
# Date: November 1, 2021
#
# The User class defines a node in the chat system
# It serves as the abstraction template for basic functionality


class User:

    def __init__(self):
        '''Constructor for User objects'''

        self.username = ""
        self.location = (None, None)
        self.neighbors = {}
        self.friends = {}
        self.message_table = {}
        self.message_count = 0


    def connect(self):
        '''Allow user to enter chat ring'''
        pass


    def disconnect(self):
        '''Allow user to exit chat ring'''
        pass


    def send_message(self, message):
        '''Send a global message to all nodes in ring'''
        pass


    def direct_message(self, username, message):
        '''Send a direct message to a target user'''
        pass

