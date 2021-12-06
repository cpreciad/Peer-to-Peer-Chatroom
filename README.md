# Peer-to-Peer-Chatroom
Distributed Systems Project


## Initialize Service:
  - start SuperNode 
     - run ./SuperNode.py
  - start LoginServer
     - run on student10.cse.nd.edu assuming that the Login Server poses as a well-known service
     - note that if attempting to run the Login Server on a different machine, one must change the value of LOGIN_SERVER in User.py, Base_User.py, and SuperUser.py
     - run ./LoginServer.py [SUPERHOST_IP] [SUPERPORT] (where the 2 arguments are the credentials of the SuperNode; host must be entered as the specific IP address)
  - add Users
     - run ./ChatRoom.py and enter username
     - if the User receives a message that the username or location is not unique, simply retry logging in (either the user recently crashed and the system is still remediating or the username is truly not unique)
     - if the User recevies a message saying that the system is currently remediating/recovering, simply retry logging in
 
 
## Note About Performance Testing:
- Comment out line 425 in Base_User.py to remove all print statements
   - this step will yield the most accurate performance results
- TestPerformance.py does not behave as a typical User
   - it merely evaluates the speed of sending and receiving messages
   - as a result, the test user does not have the capability to listen and recover from crashed nodes
   - crashing another user in the system will not allow for system recovery because TestPerformance.py does not auto-remediate 
- TestBasics.py likewise does not behave as a typical User
   - functionality testing was mostly manual due to the nature of the service
   - TestBasics.py tests the service functionality at the most basic level of sending and receiving, but likewise does not handle failures normally 

