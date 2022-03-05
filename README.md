# Chess App
App to play or train chess with yourself, your friends or against AIs. It allows to play online, creating private rooms, with anyone you want (just run the 'server.py' code into your online server (AWS, Azure, Google Cloud, raspberrypi ..., more detailed info below)

All the rules of the chess are successfully implemented but with bad code style, the project needs a face lift (some years ago since I did this project but I am emotionally attached to it) (online mode is a new feature). Bear in mind that the moves and the basic AIs implemented hasn't been optimized to have fast computational performance. The default AI implemented prioritize moves in this order:
1. Moves that checks the enemy king
2. Moves that captures an enemy piece

This project also has implmented the RSA public_key exchange between the clients through the sever in case you want to add user profile features with personal information that you want to be encrypted, but it is not used in the project because there is no personal information to hide. 

I really encourage you to play and deploy your own server for creating a basic online chess app on the internet (read sections below for this step)

In game board image      |  Enemy king in check
:-------------------------:|:-------------------------:
![Board Image](/assets/board-available-moves.png) | ![Check Image](/assets/check.png) 

I have prepared other 2 branches 'server' and 'client' with the necessary code and a short README of how to run each one. The idea is to download the code with:
```
git clone --branch server https://github.com/pgmesa/chess_app chess-server
```
or 
```
git clone --branch client https://github.com/pgmesa/chess_app chess-client
```
and then create your '.env.json' file following the '.env_example.json'. When done, you could send your friends the client configured (e.g. in a .zip file) with the server password and where to connect to establish connection with them. 
## How to execute
First install external dependencies with
```
pip install -r requirements.txt
```
Then, execute
- Windows
```
python chess_app.py
```
or
```
py chess_app.py
```
- Linux/Mac
```
python3 chess_app.py
```
## Program Modes Explanation
The program have 5 modes:
- Practice Mode (1 player): No turns, do whatever you want (you can kill the king)
- Local (2 players): Normal game with the table turning 180 degrees when a move is completed
- Online (2 players): 2 players can play over the internet with a server running the 'server.py' code to act like a bridge between them
- Game vs AI: Prove your abilities against an AI that you may have coded yourself (or you can use my default dummy AIs)
- AI vs AI: Just for fun. You can test two different AIs or the same one against itself. Adjust the minimun time move variable to play a fast or slow game.

## How to configure Online Mode
Make an easy test in localhost:
1. Create a '.env.json' file with the variables specified in the '.env_example.json' (copy and paste), change them if you want.
```
{
    "HOST_ADDRESS": "localhost",
    "HOST_PORT": 8888,
    "SERVER_PASSWORD": "test12345",
    "SERVER_NAME": "PyChat",
    "USER_NAME": "Unknown" 
}
```
2. Open 3 terminals in the projects directory. Run the server.py in one of them, and the 'client.py' in the other
3. Create a room with one client and connect with that room_id with the other client
4. Play a game against yourself

To deploy the code in a server with the intention to play with someone over the internet:
1. Move the 'server.py' file to your online server (AWS, Azure, Google Cloud...)
2. Create the '.env.json' file in the same directory as the file and change the variables to fit your server (remember to open the server port you specify in the '.env.json' file before you run the program)
3. Run the 'server.py' file
4. Create the '.env.json' file for the 'client.py' (the password must be the same as the one in the server '.env.json' file)
5. Tell your friend to do the same as you
5. Both run the 'client.py' file. One should create a room and the other must connect to that room.
6. Play a game and enjoy



