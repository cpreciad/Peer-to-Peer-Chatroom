#!/usr/bin/env python3

# LoginServer.py
# Authors: Kristen Friday, Carlo Preciado
# Date: November 2, 2021
# 
# This program runs the login server for the peer to peer chat room.
# This server listens for new Users wishing to connect, and forwards 
# information about the SuperUser

# Imports
import socket
import json 
import sys
import time
import select

# Global Variables:
HOST = ''
PORT = 9000
BUFSIZ = 4096

SUPERUSER_PORT = 0 
SUPERUSER_HOST = ''
TIMEOUT = 1


def socket_bind():
    '''
        Creates and returns a listening UDP socket
        
        Return Values:
        Success: socket object
        Failure: None type
    '''

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    for port in range(9000,10000):
        try:
            s.bind((HOST,port))
        except OSError:
            continue
            

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
    
    if request['purpose'] == 'checkup':
        name_list = check_on_users(server_socket, name_list, leader_info)
        return (None, name_list)

    if request['purpose'] == 'disconnect':
        name_list.pop(request['username'])
        return (None, name_list)

    if request['purpose'] == 'connect':
        if request['username'] in name_list:
            # send a request for a names list to the user
            # if username in new name_list, respond with failure
            message = {"status": "failure", "error": "un-unique" }
            message = json.dumps(message).encode('utf-8')
            return ((message, data['ip'], data['port']), name_list)

        else:
            # add the username to the list continue on
            name_list[request['username']] = (request['ip'], request['port'])

    leader_ip, leader_port = leader_info 
    
    message = {"status": "success", "leader": (leader_ip, leader_port)}
    message = json.dumps(message).encode('utf-8')

    return ((message, data['ip'], data['port']), name_list)
     

def send_response(server_socket, response_package):
    #TODO may want to implement retries, but probably not since this is a server 
    '''
        Simply sends the response back to the client 
    '''
    message, ip, port = response_package
    server_socket.sendto(message, (ip, port))

def send_alert(username, user_info, server_socket, leader_info):
    '''Send a crash alert to the super user, figure out which node in the system crashed'''

    json_req = {"purpose" : "crash",
                "username": username,
                "info"    : user_info}
    req = json.dumps(json_req)
    encoded_req = req.encode('utf-8')
    server_socket.sendto(encoded_req, leader_info) 


    print(f"{username} has crashed")

def check_on_users(server_socket, name_list, leader_info):
    # temporarily set a timeout to recieve
    server_socket.settimeout(TIMEOUT)
    names_to_remove = []
    for key in name_list:
        server_socket.sendto(json.dumps({"purpose": "checkup"}).encode('utf-8'), name_list[key])
        try:
            data = server_socket.recv(BUFSIZ)
        except socket.timeout:
            # if a response hasnt been recieved before 5 seconds, send a disconnection alert and remove the username
            send_alert(key, name_list[key], server_socket, leader_info)
            names_to_remove.append(key)
    
    # set the time back
    
    for key in names_to_remove:
        name_list.pop(key)

    server_socket.settimeout(None)
    return name_list

def run_server(leader_info):
    '''
        Listen for incoming Users
    '''
    
    # create a new listening socket 
    server_socket = socket_bind()

    # create a list of names
    name_list = {}

    # main while loop to listen for client requests
    _, port = server_socket.getsockname()
    print(f'LoginServer listening on port {port}...')
    while True:
        rlist, _, _ = select.select([server_socket], [], [])
        if rlist != []:
            data  = receive_request(server_socket) 
            response_package, name_list = process_request(server_socket, data, leader_info, name_list)
            print('Users in Chat Room: ', end='')
            print(name_list)
            if response_package == None:
                continue
            send_response(server_socket, response_package)
        else:
            check_on_users(server_socket, name_list)

        

def usage():

    print('Usage: [SUPERHOST] [SUPERPORT]')
    sys.exit(0)


def main():
    
    if len(sys.argv) != 3:
        usage()

    run_server((sys.argv[1], int(sys.argv[2])))


if __name__ == "__main__":
    main()

