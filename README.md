# Chess App
App to play or train chess with yourself, your friends or against AIs. It allows to play online, creating private rooms, with anyone you want (just run the 'server.py' code into your online server, more detailed info below)

All the rules of the chess are successfully implemented but with bad code style, the project needs a face lift (some years ago since I did this project but I am emotionally attached to it). Bear in mind that the moves and the basic AIs implemented hasn't been optimized to have fast computational performance. The default AI implemented prioritize moves in this order:
1. Moves that checks the enemy king
2. Moves that captures an enemy piece

I really encourage you to play and deploy your own server for online mode (read sections below for this step)

In game board image            |  Enemy king in check
:-------------------------:|:-------------------------:
![Board Image](/assets/board-available-moves.png) | ![Check Image](/assets/check.png) 

## How to execute

First install external dependencies with
```
pip install -r requirements.txt
```
Then, execute
- Windows
```
python chessApp.py
```
or
```
py chessApp.py
```
- Linux/Mac
```
python3 chessApp.py
```
## Program Modes Explanation
The program have 5 modes:
- Practice Mode (1 player): No turns
- Local (2 players): Normal game with the table turning 180 degrees when a move is completed
- Online (2 players): 2 players can play if they are connected to the same network (you need to update the ip variable the guest is connecting to with the hosts ip, and if you like also change the port where the connection will take place, default=9999) (read the 'How to configure Online Mode' below this section)
- Game vs AI: Prove your habilities against an AI that you may have coded yourself (or you can use my defualt dummy AIs)
- AI vs AI: Just for fun. You can test two different AIs or the same one against itself. Adjust the minimun time move variable to play a fast or slow game.

## How to configure Online Mode

```
git clone --branch server https://github.com/pgmesa/chess_app chess-server
```
...


