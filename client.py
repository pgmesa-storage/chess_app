
import os
import pickle
import socket
from threading import Thread
from pathlib import Path

from classes.chessPiece_class import ChessPiece
from crypt_utilities.asymmetric import (
    generate_rsa_key_pairs, load_pem_private_key, load_pem_public_key, rsa_encrypt, rsa_decrypt,
    serialize_pem_public_key, serialization, RSAPublicKey
)

dir_ = Path(__file__).parent.resolve()

# RSA vars
credentials_dir_path = dir_/'.rsa_key_pair'
public_key_path = credentials_dir_path/'public_key'
private_key_path = credentials_dir_path/'private_key'
if not os.path.exists(credentials_dir_path):
    os.mkdir(credentials_dir_path)
    generate_rsa_key_pairs(file_path=credentials_dir_path)
try:
    public_key = load_pem_public_key(public_key_path)
    private_key = load_pem_private_key(private_key_path)
except Exception as err:
    print(f"[!] {err}"); exit(1)
    
teams = ["black", "white"]
    
# Communication agreements
SUCCESS = 0; FAIL = 1; END = -1

class ChessClient(Thread):
    
    def init(self, name:str, adress:str, port:int, server_password:str):
        self.adress = adress
        self.port = port
        self.password = server_password
        self.name = name; self.enemy_name = None
        self.action = None
        self.connection = False
        self.room_id = None
        self.game_status = None
        self.team = None; self.enemy_team = None
        self.enemy_move = None
        self.turn = "white"; self.move_sent = False
        self.kill = False
        
    def is_enemy_move_recvd(self) -> bool:
        if self.enemy_move is None:
            return False
        return True
        
    def get_enemy_move(self) -> list:
        move = self.enemy_move
        self.enemy_move = None
        return move
        
    def is_connected(self,) -> bool:
        return self.connection
        
    def set_action(self, num:int):
        """ 0 for creating a chat room, 1 for entering an existing chat room"""
        if num != 0 and num != 1:
            print(f"[!] Wrong Answer (must be 0 or 1 not '{num}')")
            return
        self.action = num
        
    def set_room_id(self, id_:str):
        self.room_id = id_
        
    def send(self, msg:bytes, public_key:RSAPublicKey=None) -> None:
        if public_key is not None:
            msg = rsa_encrypt(msg, public_key)
        self.client_socket.sendall(msg)
    
    def recv(self, size:int=1024) -> bytes:
        response = self.client_socket.recv(size)
        try:
            response = rsa_decrypt(response, private_key)
        except: pass
        return response
    
#     # -----------------------------------------------------------------------------------    
    def send_move(self, move):
        """self.move variable should be loaded first"""
        dumped_move = pickle.dumps(move)
        self.send(dumped_move)
        self.move = None
        self.move_sent = True
    
    def recv_move(self):
        move = self.recv(size=40960)
        if not move:
            self.connection = False
            return
        self.enemy_move = pickle.loads(move)
        
    def read_enemy_move(self) -> tuple[ChessPiece, tuple[int,int]]:
        enemy_move = self.enemy_move
        self.enemy_move = None
        return enemy_move
        
    def run(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            print(f"Connecting to {self.adress}:{self.port}")
            self.client_socket.connect((self.adress, self.port))
            # Send User name
            self.send(self.name.encode())
            flag = int(self.recv().decode())
            assert flag == SUCCESS
        except socket.error as err:
            print("[!]", str(err))
            return
        else:
            print("Connection established")
        # Send password
        try:
            self.send(self.password.encode())
            login_outcome = int(self.recv().decode())
            if login_outcome == FAIL:
                print("[!] Seems that the password is incorrect, conexion refused")
                return
            elif login_outcome == SUCCESS:
                # Welcome Msg
                print("Credentials are correct")
                response = self.recv()
                print(response.decode())
        except socket.error:
            print("[!] Seems the server blocked this ip due to more than 3 failed attemps to connect with incorrect password")
            return
        else:
            self.connection = True
        
        # Wait until we now what action to do
        while self.action is None:
            if self.kill: return
        try:
            if self.action == 0:
                self.send(str(self.action).encode())
                self.room_id = self.recv().decode()
                print(f"Your room-id is: '{self.room_id}'")
                print("Waiting for player connection...")
                connection_outcome = int(self.recv().decode()) 
                self.send(str(SUCCESS).encode())
            if self.action == 1:
                while self.room_id is None:
                    if self.kill: return
                self.send(str.encode(self.room_id))
                connection_outcome = int(self.recv().decode()) 
            
            if connection_outcome == SUCCESS:
                # Send the user name
                self.send(self.name.encode())
                # recv other client name
                self.enemy_name = self.recv().decode()
                # Send the public key
                pk_dumped:bytes = serialize_pem_public_key(public_key)
                self.send(pk_dumped)
                # recv other client public key
                pk_other_client_dumped = self.recv(40960)
                public_key_client2 = serialization.load_pem_public_key(pk_other_client_dumped)
                # Get the random selected team
                print("Getting assignated team...")
                self.team = self.recv().decode()
                if self.team == 'black':
                    self.enemy_team = 'white'
                else:
                    self.enemy_team = 'black'
                print(f"[%] Connection succeed, connected with '{self.enemy_name}' (team={self.team})")
                self.game_status = SUCCESS
                while True:
                    if self.kill: return
                    if self.turn == self.team:
                        while self.room_id is None:
                            if not self.move_sent: return
                        self.turn = self.enemy_team
                        self.move_sent = False
                    else:
                        self.recv_move()
                        self.turn = self.team  
            elif connection_outcome == FAIL:
                self.game_status = FAIL
                print("[!] Connection Failed")
        except socket.error as err:
            print("[!]", str(err))

    def close(self):
        print("[%] Closing connection...")
        self.kill = True
        self.client_socket.close()