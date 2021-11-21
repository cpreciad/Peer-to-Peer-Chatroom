#!/usr/bin/env python3

# TestBasics.py
# Authors: Kristen Friday, Carlo Preciado
# Date: November 15, 2021
#
# TestBasics.py evaluates basic functionality of chat system


import User
import time


def test_direct(usr):
    '''Test functionality of direct messaging'''
    
    usr.direct_message("super_user", "test direct message")
    # receive response
    usr.receive_message()


def test_global(usr):
    '''Test functionality of global messaging'''
    
    usr.send_message("test global message")
    # receive original message
    usr.receive_message()
    # receive global response
    usr.receive_message()


def main():
    '''Runner function for performance testing'''

    usr = User.User("test_user1")
    usr.username = f"test_user{usr.port}"
    usr.connect()

    test_direct(usr);
    test_global(usr);


if __name__ == '__main__':
    main()
