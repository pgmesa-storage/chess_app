# Chess Server

App to play or train chess with yourself, your friends or against AIs. It allows to play online, creating private rooms, with anyone you want (just run the 'server.py' code into your online server (AWS, Azure, Google Cloud, raspberrypi ...)

The server code also provides some basic features of logging and statistical analysis of your server state, active connections and ips info in real time and provides a blocking ip function to block connections from ips which tried to connect 3 times with incorrect credentials.

The server code could be deployed for example on an Amazon Web Server, and X people could connect to play online simultaneously in different private rooms of 2 people size. In concrete, with AWS the host_address in the server should be the private DNS address and the client ip to connect should be the public DNS address.

Link to complete github project -> https://github.com/pgmesa/chess_app

## Run the server
- Windows
```
python server.py
```
or 
```
py server.py
```
- Linux and MAC
```
python3 server.py
```

## Reset server files
Deletes './ips.json', './stats.json' and all the logs in './log'
```
python3 server.py reset
```