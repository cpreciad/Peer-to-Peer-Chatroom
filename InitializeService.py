#!/usr/bin/env python3

# ChatService.py
# Authors: Kristen Friday, Carlo Preciado
# Date: November 1, 2021
#
# ChatService.py serves as the main runner file to initiate
# the chat service

import socket
import SuperUser
import User
from  LoginServer import run_server


def main():
    '''Main runner function for service'''

    # Initialize SuperNode
    super_usr = SuperUser.SuperUser()
    super_usr.print_user()
    super_usr.add_user()


if __name__ == '__main__':
    main()
