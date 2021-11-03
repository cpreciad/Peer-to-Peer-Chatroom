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


def main():
    '''Main runner function for service'''

    # TODO: Initialize SuperNode
    super_usr = SuperUser.SuperUser()
    super_usr.print_user()
    
    new_usr = User.User()
    new_usr.print_user()
    new_usr.connect()

    # TODO: Add User nodes to system


if __name__ == '__main__':
    main()
