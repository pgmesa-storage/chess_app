
import os
import socket
from threading import Thread
from pathlib import Path
from random import choice

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
            msg = rsa_encrypt(msg.encode(), public_key)
        self.client_socket.sendall(msg)
    
    def recv(self, size:int=1024) -> bytes:
        response = self.client_socket.recv(size)
        try:
            response = rsa_decrypt(response, private_key)
        except: pass
        return response
        
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
                self.send(SUCCESS.encode())
            if self.action == 1:
                while self.room_id is None:
                    if self.kill: return
                self.send(str.encode(self.room_id))
                connection_outcome = int(self.recv().decode()) 
            
            def valid_msg(msg:str) -> bool:
                if msg != "": return True
                return False
            
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
                pk_other_client = serialization.load_pem_public_key(pk_other_client_dumped)
                # Radomly select the teams (the one who created the room)
                if self.action == 0:
                    self.team = choice(teams)
                    if teams.index(self.team) == 1:
                        self.enemy_team = teams[0]
                    else:
                        self.enemy_team = teams[1]
                    self.send(self.enemy_team.encode(), public_key=pk_other_client)
                if self.action == 1:
                    self.team = self.recv().decode()
                print(f"[%] Connection Succeed, connected with '{self.enemy_name}'")
                self.game_status = SUCCESS
                ...
                while True:
                    if self.kill: return
                # ------
                while True:
                    print(f"Waiting for '{self.enemy_name}' to respond...")
                    recv_msg = self.client_socket.recv(1024)
                    if not recv_msg: break
                    decrp_msg = rsa_decrypt(recv_msg, private_key).decode()
                    print(f"+ '{self.enemy_name}' says:", decrp_msg)
                    while True:
                        msg = str(input(f"=> Write your msg here to '{self.enemy_name}': "))
                        if valid_msg(msg): break
                        print("[!] Can't send void msg")
                    encrp_msg = rsa_encrypt(msg.encode(), pk_other_client)
                    self.client_socket.send(encrp_msg)  
            elif connection_outcome == FAIL:
                self.game_status = FAIL
                print("[!] Connection Failed")
        except socket.error as err:
            print("[!]", str(err))

    def close(self):
        print("[%] Closing connection...")
        self.kill = True
        self.client_socket.close()
       
# client = ChatClient()
# client.start()
# try:
#     while client.is_alive(): pass
# except KeyboardInterrupt: pass
# finally:
#     print("[%] Closing client...")
#     client.close()
#     #sys.stdout = open(os.devnull, 'w')
#     pid = os.getpid()
#     os.kill(pid,9)