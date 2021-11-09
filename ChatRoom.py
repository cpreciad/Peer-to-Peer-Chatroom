#!/usr/bin/env python3

# ChatRoom.py
# Authors: Kristen Friday, Carlo Preciado
# Date: November 3, 2021
#
# ChatRoom.py serves as the main file to add User nodes


import User


def main():
    '''Main runner function to add nodes'''

    new_usr = User.User()
    new_usr.print_user()
    new_usr.connect()
    
    while True:
        message = input('> ')
        new_usr.send_message(message)

if __name__ == '__main__':
    main()
