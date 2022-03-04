
# Built-in
import os
import copy
import time
import json
import sys
import socket
import datetime as dt
import random, string
from pathlib import Path
from threading import Thread, Lock, Event

dir_ = Path(__file__).parent.resolve()
env_path = dir_/'.env.json'

stats_fname = './stats.json'
stats_path = dir_/stats_fname
log_dir = 'logs'
log_dir_path = dir_/log_dir
if not os.path.exists(log_dir_path):
    os.mkdir(log_dir_path)

def _generate_logfname(title:str) -> str:
    date = _get_date(path_friendly=True)
    return title + "_" + date

def _get_date(path_friendly:bool=False) -> str:
    datetime = dt.datetime.now()
    if path_friendly:
        date = str(datetime.date())
        time = str(datetime.time()).replace(':', "-").replace('.', '_')
        return date+"_"+time
    else:
        return str(datetime)

log_fname = _generate_logfname('log')

def log(msg:str, nl:bool=True, print_:bool=True):
    msg = str(msg)
    log_path = log_dir_path/log_fname
    mode = 'a'
    if not os.path.exists(log_path):
        mode = 'w'
    if nl: msg += "\n"
    with open(log_path, mode) as file:
        file.write(msg)
    if print_: 
        print(msg, end='')

def config(key) -> any:
    if not os.path.exists(env_path):
        raise Exception(f"Not '.env.json' file in '{dir_}'")
    with open(env_path, 'r') as file:
        env_dict = json.load(file)
    return env_dict[key]

# Environment variables
try:
    HOST_ADDRESS = config('HOST_ADDRESS')
    HOST_PORT = config('HOST_PORT')
    SERVER_PASSWORD = config('SERVER_PASSWORD')
    NAME = config('SERVER_NAME')
except Exception as err:
    log(err)
    exit(1)
    
ips_fname = 'ips.json'
ips_path = dir_/ips_fname

block_ip_time = 300 # Seconds
stats_squema = {
    "visits": 0,
    "active-threads": 0,
    "rooms": {"num": 0, "ids":[]},
    "active-chats": {"num": 0, "ids":[]}
}

exit_event = Event()

# Communication agreements
SUCCESS = "0"; FAIL = "1"
 
class SocketListener(Thread):
    def run(self):
        self.num_connections = 0; self.threads = []
        self.rooms = {}; self.active_rooms = []
        self.lock = Lock(); self.blocked_ips = {}; self.ips_that_fail = {}
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.server_socket.bind((HOST_ADDRESS, HOST_PORT)) 
        except socket.error as err:
            log("[!]" + str(err))
        else:
            log(f"Server '{NAME}' is up and running")
            log("[%] Waiting for conexions...")
            self.server_socket.listen(1)
            while True:
                client, address = self.server_socket.accept()
                client_name = client.recv(2048).decode()
                client.send(SUCCESS.encode())
                ip = address[0]
                # Comprobamos si es una ip bloqueada
                if ip in self.blocked_ips:
                    t0 = self.blocked_ips[ip]
                    tf = time.time()
                    remaining_t = block_ip_time - (tf - t0)
                    if remaining_t < block_ip_time:
                        log(f"Connection Refused '{ip}' is in blocked ips -> '{round(remaining_t, 2)}'s remaining")
                        client.close()
                        self.update_ips(ip, client_name, blocked=True)
                        continue
                    else:
                        self.blocked_ips.pop(ip)
                # Esperamos la contraseña
                password = client.recv(2048).decode()
                if password != SERVER_PASSWORD:
                    log(f"Connection Refused -> '{ip}', wrong password '{password}'")
                    if ip not in self.ips_that_fail:
                        self.ips_that_fail[ip] = 0
                    self.ips_that_fail[ip] += 1
                    if self.ips_that_fail[ip] >= 3:
                        log("Blocking ip due to 3 failed attempts")
                        self.blocked_ips[ip] = time.time()
                        self.ips_that_fail.pop(ip)
                        self.update_ips(ip, client_name, wrong_key=True, blocked=True)
                    else:
                        self.update_ips(ip, client_name, wrong_key=True)
                    client.send(FAIL.encode())
                    client.close()
                    continue
                self.update_ips(ip, client_name)
                client.send(SUCCESS.encode())
                log(f"[%] Connection stablished with client '{client_name}' -> " + ip + ':' + str(address[1]))
                thread = Thread(target=self.threaded_client, args=(client,))
                self.threads.append(thread)
                self.num_connections += 1
                thread.start()
                self.update_stats()
                
    def update_ips(self, ip:str, client_name:str, wrong_key:bool=False, blocked:bool=False):
        self.lock.acquire()
        ips = {}
        base_dict = {"num-connections": 1, "num-wrong-credentials": 0, "blocked-times": 0}
        if not os.path.exists(ips_path):
            ips[ip] = {client_name: base_dict}
        else:
            with open(ips_path, 'r') as file:
                ips = json.load(file)
            if not ip in ips:
                ips[ip] = {client_name: base_dict}
            if not client_name in ips[ip]:
                ips[ip][client_name] = base_dict
            else:
                ips [ip][client_name]["num-connections"] += 1
        if wrong_key:
            ips[ip][client_name]["num-wrong-credentials"] += 1
        if blocked:
            ips[ip][client_name]["blocked-times"] += 1
        with open(ips_path, 'w') as file:
            json.dump(ips, file, indent=4)
        self.lock.release()
        
    def update_stats(self, reset:bool=False, _shutting_thread=False):
        stats = self.load_stats()
        active_threads = self.check_threads(kill_all=reset)
        if _shutting_thread: active_threads -= 1
        if reset:
            visits = stats['visits']
            stats = copy.copy(stats_squema)
            stats['visits'] = visits
        else:
            stats['visits'] = self.num_connections
            stats['active-threads'] = active_threads
            stats['rooms'] = {"num": len(self.rooms), "ids": list(self.rooms.keys())}
            stats['active-chats'] = {"num": len(self.active_rooms), "ids": self.active_rooms}
        self.lock.acquire()
        try:
            with open(stats_path, 'w') as file:
                json.dump(stats, file, indent=4)
        finally:
            self.lock.release()
    
    def load_stats(self) -> dict:
        if not os.path.exists(stats_path):
            stats = copy.copy(stats_squema)
        else:
            self.lock.acquire()
            try:
                with open(stats_path, 'r') as file:
                    stats = json.load(file)
            finally:
                self.lock.release()
        return stats
        
    def check_threads(self, kill_all:bool=False) -> int:
        self.lock.acquire()
        active_threads = 0
        delete_buffer = []
        if kill_all:
            for sock in self.rooms.values():
                try: sock.close()
                except: pass
        time.sleep(0.5)
        for t in self.threads:
            if t.is_alive():
                active_threads += 1
            else:
                delete_buffer.append(t)
        for t in delete_buffer:
            self.threads.remove(t)
        self.lock.release()
        return active_threads
    
    def threaded_client(self, socket_connection):        
        socket_connection.send(str.encode(f"Welcome to the Server '{NAME}'"))
        data = socket_connection.recv(2048)
        if not data:
            log("Wrong client response, finishing conexion")
            socket_connection.close()
        else:
            data = data.decode()
            if data == "0":
                room_id = self._generate_id()
                log(f"Creating room with id '{room_id}'")
                self.create_chat(room_id, socket_connection)
            else:
                room_id = data
                log(f"Joining room '{room_id}'")
                self.establish_clients_connection(room_id, socket_connection)
        self.update_stats(_shutting_thread=True)
        sys.exit()
    
    def _generate_id(self, size:int=12) -> str:
        # Size: number of characters in the string.  
        # call random.choices() string module to find the string in Uppercase + numeric data.  
        ran = ''.join(random.choices(string.ascii_uppercase + string.digits, k = size))    
        return str(ran)  
    
    def create_chat(self, room_id:str, socket_connection):
        self.lock.acquire()
        try:
            self.rooms[room_id] = socket_connection
            socket_connection.sendall(room_id.encode())
        finally:
            self.lock.release() 
        self.update_stats()
        try:
            flag = socket_connection.recv(1024).decode()
            if flag == FAIL or flag == "":
                raise socket.error()
        except socket.error:
            self.rooms.pop(room_id)
            log(f"Room '{room_id}' canceled")
    
    def establish_clients_connection(self, room_id, second_connection):
        first_connection = None; reply = FAIL
        try:
            self.lock.acquire()
            if room_id in self.rooms:
                first_connection = self.rooms[room_id]
                reply = SUCCESS
        except Exception as err:
            log(err)
        finally:
            self.lock.release()
        second_connection.sendall(reply.encode())
        if first_connection is not None:
            first_connection.sendall(reply.encode())
            self.start_chat(room_id, first_connection, second_connection)
           
    def start_chat(self, room_id, socket1, socket2):
        self.lock.acquire()
        self.rooms.pop(room_id)
        self.lock.release()
        self.active_rooms.append(room_id)
        self.update_stats()
        try:
            # Enviamos a cada uno el nombre del otro
            name1 = socket1.recv(2048); name2 = socket2.recv(2048)
            socket1.send(name2); socket2.send(name1)
            # Send public key to each client
            pk1 = socket1.recv(40960); pk2 = socket2.recv(40960)
            socket1.send(pk2); socket2.send(pk1)
            # Primero habla el que se une a la sala
            while True:
                # set to True event
                if exit_event.is_set():
                    break
                recv_msg_from2 = socket2.recv(2048)
                if not recv_msg_from2: break
                socket1.sendall(recv_msg_from2)
                recv_msg_from1 = socket1.recv(2048)
                if not recv_msg_from1: break
                socket2.sendall(recv_msg_from1)
        except socket.error: pass
        finally:
            log(f"[!] Closing connection in room '{room_id}'")
            self.active_rooms.remove(room_id)
            log(f"Active Chat Rooms: {len(self.active_rooms)}")
            socket1.close(); socket2.close()
    
    def close(self):
        log("Stats before closing:")
        stats = json.dumps(self.load_stats(), indent=4)
        log(stats)
        log("[%] Closing connection...")
        # Reseteamos las estadisticas tambien (menos numero de visitas)
        exit_event.set()
        self.update_stats(reset=True)
        self.server_socket.close()

if "reset" in sys.argv:
    if os.path.exists(ips_path):
        os.remove(ips_path)
    if os.path.exists(stats_path):
        os.remove(stats_path)
    if os.path.exists(log_dir_path):
        files = os.listdir(log_dir_path)
        for f in files: os.remove(log_dir_path/f)
        os.rmdir(log_dir_path)
    exit()
        
try:
    sl = SocketListener()
    sl.start()
    log('-> Socket is listening, press any ctrl-c to abort...')
    while sl.is_alive(): pass
except Exception as err:
    log(f"[!] {err}")
except KeyboardInterrupt: pass
finally:
    log("[%] Closing Server")
    sl.close()
    pid = os.getpid()
    os.kill(pid,9)