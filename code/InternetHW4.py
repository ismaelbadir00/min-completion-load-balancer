import socket
import threading
from enum import Enum

# given addresses for servers
SERVERS_ADDRS = [
    "192.168.0.101",  # VIDEO-1
    "192.168.0.102",  # VIDEO-2
    "192.168.0.103",  # MUSIC-1
]

# factors for each type
MULTIPLIERFACTOR = [
    [1, 1, 2],
    [1, 1, 2],
    [2, 3, 1],
]

class Server:
    def __init__(self, addr):
        self.addr = addr
        self.port = 80
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.sock.connect((self.addr, self.port)) #connecting server to lb
        self.lock = threading.Lock()  # ensure one request at a time on this socket


# function for the thread of the server to handle the request
def handle_client(client_sock, running_server, req):
    if req:
        with running_server.lock:              # we want only 1 thread touches backend.sock
            running_server.sock.sendall(req)
            resp = running_server.sock.recv(2) # receiving the sock
        client_sock.sendall(resp)  # send back sock
    client_sock.close()


# ----------------------------------------------------------------------
def main():
    # create the three given servers (persistent connections)
    servers = [
        Server(SERVERS_ADDRS[0]),
        Server(SERVERS_ADDRS[1]),
        Server(SERVERS_ADDRS[2]),
    ]

    # array to keep track of finish times for each server
    # is updated after a server handles a request
    finish_times = [0, 0, 0]

    # Creating a socket to accept requests from Hosts
    # we used the ip for the LB that's connected to the host subnet , and the given port
    LB_IP, LB_PORT = "10.0.0.1", 80
    listen_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listen_sock.bind((LB_IP, LB_PORT))
    listen_sock.listen(10)

    while True:
        # accepting if we got a request .
        client_sock, client_addr = listen_sock.accept()
        req = client_sock.recv(2)

        req_type = chr(req[0])
        run_time = req[1]
        req_char = 0 # if type is picture

        if req_type == "V":
            req_char = 1
        elif req_type == "M":
            req_char = 2

        # calculate the finish time for this request
        candidates = []
        for i in range(3):
            mult = MULTIPLIERFACTOR[i][req_char]
            candidate_finish = finish_times[i] + (run_time * mult)
            candidates.append(candidate_finish)

        # find the index of the minimum finish time
        best_idx = candidates.index(min(candidates))

        # update that server’s finish time
        finish_times[best_idx] = candidates[best_idx]

        # handle the request
        running_server = servers[best_idx]
        threading.Thread(target=handle_client,
                         args=(client_sock, running_server, req),
                         daemon=True).start()


if __name__ == "__main__":
    main()
