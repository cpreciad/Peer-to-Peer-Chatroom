#!/usr/bin/env python3

# User.py
# Authors: Kristen Friday, Carlo Preciado
# Date: November 2, 2021
# 
# This program runs the login server for the peer to peer chat room
# This server listens for new Users wishing to connect, and forwards 
# inforation about the SuperUser

# Imports
import socket
import json 
import sys
# Global Variables:
HOST = ''
PORT = 3000
BUFSIZ = 4096

SUPERUSER_PORT = 0 
SUPERUSER_HOST = ''

def socket_bind():
    '''
        Creates and returns a listening UDP socket
        
        Return Values:
        Success: socket object
        Failure: None type
    '''

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    s.bind((HOST,PORT))

    return s

def receive_request(server_socket):
    '''
        Waits for new requests to come in from clients, and returns
        the decoded request to the main loop for processing
        
        Return Values:
        Success: dictionary with decoded request from client,
                 client ip, and client port
        Failure: json string containing thrown error
    '''
    
    data, address = server_socket.recvfrom(BUFSIZ)
    
    return {'request': data.decode('utf-8'), 'ip': address[0], 'port': int(address[1])}

def process_request(server_socket, data, leader_info, name_list):
    '''
        Converts the decoded request into a json object
        and create an encoded json response

        Return Values:
        (response, client IP, client port)

        response will vary based on the success or failure of parsing the request
        Successful response: b'{host: ~~~, port: ~~~}'

    '''
    
    #TODO come up with different ways to process request 
   
    # reassign the name_list
    request = json.loads(data['request'])
    if request['username'] == 'super_user':
        pass

    if request['purpose'] == 'connect':
        if request['username'] in name_list:
            # send a request for a names list to the user
            # if username in new name_list, respond with failure
            message = {"status": "failure", "error": "username not unique" }
            message = json.dumps(message)
            message = message.encode('utf-8')
            return (message, data['ip'], data['port'])

        else:
            # add the username to the list continue on
            name_list.append(request['username'])

    leader_ip, leader_port = leader_info 
    
    message = {"status": "success", "leader": (leader_ip, leader_port)}
    message = json.dumps(message)
    message = message.encode('utf-8')

    return ((message, data['ip'], data['port']), name_list)
     

def send_response(server_socket, response_package):
    #TODO may want to implement retries, but probably not since this is a server 
    '''
        Simply sends the response back to the client 
    '''
    message, ip, port = response_package
    server_socket.sendto(message, (ip, port))

def run_server(leader_info):
    
    # create a new listening socket 
    server_socket = socket_bind()

    # create a list of names
    name_list = []

    # main while loop to listen for client requests
    _, port = server_socket.getsockname()
    print(f'LoginServer listening on port {port}...')
    while True:
        data  = receive_request(server_socket) 
        response_package, name_list = process_request(server_socket, data, leader_info, name_list)
        print('Users in Chat Room: ', end='')
        print(name_list)
        send_response(server_socket, response_package)

def usage():
    print('Usage: [SUPERHOST] [SUPERPORT]')
    sys.exit(0)


def main():
    
    if len(sys.argv) != 3:
        usage()

    run_server((sys.argv[1], int(sys.argv[2])))


if __name__ == "__main__":
    main()

