# Chess App

App to play or train chess with yourself, your friends or against IAs

All the rules of the chess are successfully implemented but with bad code style, the project needs a face lift (some years ago since I did this project but I am emotionally attached to it). Bear in mind that the moves and the basic IAs implemented hasn't been optimized to have fast computational performance, but I think this project is fun to use and may be useful for someone. The default IA implemented prioritize moves in this order:
1. Moves that checks the enemy king
2. Moves that captures an enemy piece

I really encourage you to play and if you like, code your own IAs!

:-------------------------:|:-------------------------:
![Board Image](/assets/board.png) | ![Check Image](/assets/check.png) 

## How to execute

#### Option 1
Run the .exe if you are in windows
#### Option 2
First install external dependencies with
```
pip install -r requirements.txt
```
Then, execute
- Windows
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
- Online (2 players): 2 players can play if they are connected to the same network (you need to update the ip variable the guest is connecting to with the hosts ip, and if you like also change the port where the connection will take place, default=9999)
- Game vs IA: Prove your habilities against an IA that you may have coded yourself (or you can use my defualt dummy IAs)
- IA vs IA: Just for fun. You can test two different IAs or the same one against itself. Adjust the minimun time move variable to play a fast or slow game.



