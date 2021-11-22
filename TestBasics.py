#!/usr/bin/env python3

# TestBasics.py
# Authors: Kristen Friday, Carlo Preciado
# Date: November 15, 2021
#
# TestBasics.py evaluates basic functionality of chat system

import sys
import time
import select
import User


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

    usr1 = User.User("test_user1")
    usr1.username = f"test_user{time.time()}"
    usr1.print_user()
    usr1.connect()
    
    socks = [sys.stdin, usr1.sock]
    while True:

        rlist, _, _ = select.select(socks, [], [], 1)

        # user entered input
        for read_s in rlist:
            # read input
            if read_s == sys.stdin:
                usr_input = sys.stdin.readline().strip()
                if not usr_input:
                    socks.pop(0)
                    break

                else:
                    usr1.send_message(usr_input)

            # read incoming messages
            else:
                usr1.receive_message()


if __name__ == '__main__':
    main()
