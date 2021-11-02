#!/usr/bin/env python3

# User.py
# Authors: Kristen Friday, Carlo Preciado
# Date: November 2, 2021
# 
# This program runs the login server for the peer to peer chat room
# This server listens for new Users wishing to connect, and forwards 
# inforation about the SuperUser

# Global Variables:
HOST = ''
PORT = 0
BUFSIZ = 1024

def socket_listen():
    '''
        Creates and returns a listening UDP socket
        
        Return Values:
        Success: socket object
        Failure: None type
    '''
    pass

def recieve_request(server_socket):
    '''
        Waits for new requests to come in from clients, and returns
        the decoded request to the main loop for processing
        
        Return Values:
        Success: decoded request from client
        Failure: json string containing thrown error
    '''
    pass

def process_request(request):
    '''
        Converts the decoded request into a json object
        and create an encoded json response

        Return Values:
        (client IP, client port, response)

        response will vary based on the success or failure of parsing the request
        Successful response: b'{host: ~~~, port: ~~~}'

    '''
    pass

def send_response(server_socket, response_package):
    #TODO may want to implement retries, but probably not since this is a server 
    '''
        Simply sends the response back to the client 
    '''
    client_ip, client_port, response = response_package
    pass

def main():
    
    # create a new listening socket 
    server_socket = socket_listen()

    # main while loop to listen for client requests
    while True:
        request  = recieve_request(server_socket) 
        response_package = process_request(request)
        send_response(server_socket, response_package)
        
if __name__ == "__main__":
    main()

