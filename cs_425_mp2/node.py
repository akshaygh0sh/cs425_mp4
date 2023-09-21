import threading
import socket
import datetime
import json
import time
import random

class Node:
    MACHINE_LIST = [
        "fa23-cs425-5601.cs.illinois.edu",
        "fa23-cs425-5602.cs.illinois.edu",
        "fa23-cs425-5603.cs.illinois.edu",
        "fa23-cs425-5604.cs.illinois.edu",  
        "fa23-cs425-5605.cs.illinois.edu",
        "fa23-cs425-5606.cs.illinois.edu",
        "fa23-cs425-5607.cs.illinois.edu",
        "fa23-cs425-5608.cs.illinois.edu",
        "fa23-cs425-5609.cs.illinois.edu",
        "fa23-cs425-5610.cs.illinois.edu"
    ]

    # Set heartbeat interval to 2 seconds
    HEARBEAT_INTERVAL = 2

    def __init__(self):
        self.version_number = -1
        self.ip, self.current_machine_ix,  = self.get_info()
        self.id = self.update_id()
        self.member_list = dict()
        # Used to stop gossiping (if incoming gossip has a stale timestamp don't retransmit - figure this out later)
        self.last_gossip_timestamp = ""
        
    # Gets device info (ip and machine number)
    def get_info(self):
        try:
            hostname = socket.gethostname()
            current_machine_ix = hostname[13 : 15]
            local_ip = socket.gethostbyname(hostname)
            return local_ip, int(current_machine_ix)
        except Exception as e:
            print("Error:", e)
    
    # Update the ID of the node (used for when attempting to join membership list)
    def update_id(self):
        self.version_number += 1
        return f"{self.ip}@{self.current_machine_ix}:{self.version_number}"

    def listen(self):
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        local_ip = "0.0.0.0"
        local_udp_port = 49153

        # Bind socket to local port
        udp_socket.bind((local_ip, local_udp_port))

        while True:
            try:
                # Receive the command from the client
                data, client_address = udp_socket.recvfrom(8096)
                data = data.decode()
                data = json.loads(data)
                local_time = int(time.time())
                
                # Send heartbeat periodically, via gossip
                if (local_time % self.HEARBEAT_INTERVAL == 0):
                    pass
                # Join request from a machine, gossip new membership list
                if ("join" in data):
                    pass
                print("Received data:", data)

            except Exception as e:
                print("Error:", e)
    
    # Triggers a gossip round (sends to N/2 random machines)
    def gossip(self, message):
        target_machines = self.member_list.keys
        target_machines.remove(self.current_machine_ix)
        num_gossip = (len(target_machines) // 2) + 1
        target_machines = random.sample(target_machines, num_gossip)
        for machine in target_machines:
            self.send(machine, message)
    
    # Attempts to join the membership group (via introducer on machine 1)
    def join_group(self):
        self.update_id()
        join_dict = {
            "join" : self.id
        }
        self.send(1,join_dict)

    # Leave group, gossip that you have left
    def leave_group(self):
        # Remove current node from membership list and 
        # gossip to other machines (so they update)
        # Reset membership list
        self.version_number += 1
        self.member_list = {}

    # Sends a message via UDP to machine #<machine_ix>
    def send(self, machine_ix, message):
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        machine = self.MACHINE_LIST[machine_ix - 1]
        remote_port = 49153
    
        try:
            udp_socket.sendto(str(message).encode(), (machine, remote_port))
        except socket.error as e:
            print("Could not connect to: ", machine, ": ", e)
        finally:
            udp_socket.close()
    
    def get_membership_list(self):
        return self.member_list

def process_input(node, command):
    if (command == "list_mem"):
        return node.get_membership_list()
    elif (command == "list_self"):
        return node.id
    # Just to test, remove later
    elif (command.startswith("send")):
        split_ix = command.find("send ")
        node.send(2, command[split_ix + 5:])
        return ""
    else:
        return "Command not recognized."
    
def prompt_user(node):
    while True:
        user_input = input("Enter command: (or 'exit' to terminate): ")
        if user_input.lower() == 'exit':
            break
        else:
            print(process_input(node, user_input))


if __name__ == "__main__":
    test = Node()
    # Create a thread for user input
    listen_thread = threading.Thread(target=test.listen, args=())
    listen_thread.daemon = True  # Set the thread as a daemon so it doesn't block program exit
    listen_thread.start()

    prompt_user(test)

