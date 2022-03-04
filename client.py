
import os
import socket
from threading import Thread
from pathlib import Path

from crypt_utilities.asymmetric import (
    generate_rsa_key_pairs, load_pem_private_key, load_pem_public_key, rsa_encrypt, rsa_decrypt,
    serialize_pem_public_key, serialization
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
    
# Communication agreements
SUCCESS = "0"; FAIL = "1"

class ChatClient(Thread):
    
    def init(self, name:str, adress:str, port:int, server_password:str):
        self.adress = adress
        self.port = port
        self.password = server_password
        self.name = name
    
    def run(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            print(f"Connecting to {self.adress}:{self.port}")
            self.client_socket.connect((self.adress, self.port))
            # Send User name
            self.client_socket.send(self.name.encode())
            flag = self.client_socket.recv(1024).decode()
            assert flag == SUCCESS
        except socket.error as err:
            print("[!]", str(err))
            return
        else:
            print("Connection established")
            
        # Send password
        try:
            self.client_socket.send(self.password.encode())
            login_outcome = self.client_socket.recv(1024).decode()
            if login_outcome == FAIL:
                print("[!] Seems that the password is incorrect, conexion refused")
                return
            elif login_outcome == SUCCESS:
                # Welcome Msg
                print("Credentials are correct")
                response = self.client_socket.recv(1024)
                print(response.decode())
        except socket.error:
            print("[!] Seems the server blocked this ip due to more than 3 failed attemps to connect with incorrect password")
            return
        try:
            print("+ 0 for creating a chat room")
            print("+ 1 for entering an existing chat room")
            while True:
                answer = str(input('-> Introduce your choice: '))
                if answer != "0" and answer != "1":
                    print(f"[!] Wrong Answer (must be 0 or 1 not '{answer}')")
                else:
                    break
            if answer == "0":
                self.client_socket.send(str.encode(answer))
                room_id = self.client_socket.recv(1024).decode()
                print(f"Your room-id is: '{room_id}'")
                print("Waiting for player conexion...")
                connection_outcome = self.client_socket.recv(1024).decode() 
                self.client_socket.send(SUCCESS.encode())
            if answer == "1":
                while True:
                    room_id = str(input("Introduce your room id: "))
                    if answer == "":
                        print(f"[!] Wrong Answer (can't be void)")
                    else:
                        break
                self.client_socket.send(str.encode(room_id))
                connection_outcome = self.client_socket.recv(1024).decode() 
            
            def valid_msg(msg:str) -> bool:
                if msg != "": return True
                return False
            
            if connection_outcome == SUCCESS:
                # Send the user name
                self.client_socket.sendall(self.name.encode())
                # Recieve other client name
                other_client = self.client_socket.recv(1024).decode()
                # Send the public key
                pk_dumped:bytes = serialize_pem_public_key(public_key)
                self.client_socket.sendall(pk_dumped)
                # Recieve other client public key
                pk_other_client_dumped = self.client_socket.recv(40960)
                pk_other_client = serialization.load_pem_public_key(pk_other_client_dumped)
                print(f"[%] Connection Succeed, connected with '{other_client}'")
                if answer == "1":
                    while True:
                        msg = str(input(f"=> Write your first msg here to '{other_client}': "))
                        if valid_msg(msg): break
                        print("[!] Can't send void msg")
                    encrp_msg = rsa_encrypt(msg.encode(), pk_other_client)
                    self.client_socket.send(encrp_msg)  
                while True:
                    print(f"Waiting for '{other_client}' to respond...")
                    recv_msg = self.client_socket.recv(1024)
                    if not recv_msg: break
                    decrp_msg = rsa_decrypt(recv_msg, private_key).decode()
                    print(f"+ '{other_client}' says:", decrp_msg)
                    while True:
                        msg = str(input(f"=> Write your msg here to '{other_client}': "))
                        if valid_msg(msg): break
                        print("[!] Can't send void msg")
                    encrp_msg = rsa_encrypt(msg.encode(), pk_other_client)
                    self.client_socket.send(encrp_msg)  
            elif connection_outcome == FAIL:
                print("[!] Connection Failed")
        except socket.error as err:
            print("[!]", str(err))

    def close(self):
        print("[%] Closing connection...")
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