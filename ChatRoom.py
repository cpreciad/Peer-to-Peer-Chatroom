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

    print("Messaging Options")
    print("------------------")
    print("<message>   - Global Message")
    print("direct      - Direct Message")
    print("disconnect  - Exit System\n")

    new_usr.connect()
    new_usr.listen()


if __name__ == '__main__':
    main()
