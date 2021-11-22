#!/usr/bin/env python3

# TestPerformance.py
# Authors: Kristen Friday, Carlo Preciado
# Date: November 15, 2021
#
# TestPerformance.py evaluates the latency and throughput of message delivery


import User
import time


def test_direct():
    '''Measure latency and throughput of direct messaging'''
    
    usr = User.User("test_user1")
    usr.print_user()
    usr.username = f"test_user{time.time()}"
    usr.connect()

    start = time.time_ns()
    elapsed = 0
    count = 0

    while elapsed <= 3000000000:
        usr.direct_message("super_user", "test message")
        usr.receive_message()
        count += 1

        elapsed = time.time_ns() - start

    print("\nPerformance of Direct Messaging:")
    print(f"Elapsed Time:          {(elapsed / (10 ** 9))} seconds")
    print(f"Total Operations:      {count} operations")
    print(f"Bandwith (ops/sec):    {count / (elapsed / (10 ** 9)):.0f} ops/second")
    print(f"Latency (avg time/op): {(elapsed / count):.0f} nanoseconds/op\n")
    
    usr.disconnect()


def test_global():
    '''Measure latency and throughput of global messaging'''
    
    usr = User.User("test_user1")
    usr.print_user()
    usr.username = f"test_user{time.time()}"
    usr.connect()

    start = time.time_ns()
    elapsed = 0
    count = 0

    while elapsed <= 3000000000:
        usr.send_message(f"test message {count}")
        # receive original
        usr.receive_message()
        # receive response
        usr.receive_message()
        count += 1
        elapsed = time.time_ns() - start

    print("\nPerformance of Global Messaging:")
    print(f"Elapsed Time:          {(elapsed / (10 ** 9))} seconds")
    print(f"Total Operations:      {count} operations")
    print(f"Bandwith (ops/sec):    {count / (elapsed / (10 ** 9)):.0f} ops/second")
    print(f"Latency (avg time/op): {(elapsed / count):.0f} nanoseconds/op\n")

    usr.disconnect()


def main():
    '''Runner function for performance testing'''

    #test_direct();
    test_global();


if __name__ == '__main__':
    main()
