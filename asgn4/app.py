# ---------------------------------------------------------------------------------
# Authors:   Rory Glenn, Seth Tonningsen, Timothy Chandler
# Email:     romglenn@ucsc.edu, stonning@ucsc.edu, tdchandl@ucsc.edu
# Team:      Laser Sharks
# Quarter:   Spring 2021
# Class:     CSE 138 (Distributed Systems)
# Project:   Assignment 4
# Professor: Lindsey Kuper
#
# app.py
#   Implementation file for sharded, fault-tolerant, key-value store
# ---------------------------------------------------------------------------------


import ast
import requests
import os
import flask
import json
import random

your_socket_address  = str()
my_shard             = str()  # "shard1", or "shard2" ect...
view_set             = set()
global_dictionary    = dict()
vector_clock_list    = list()
view_just_ips        = list()
all_nodes_ips        = list()
known_down_ips       = list()
shard_info           = dict() # {"shard1" : ["10.0.0.1", "10.0.0.2"],"shard2" : ["10.0.0.3", "10.0.0.4"],"shard3" : ["10.0.0.5", "10.0.0.6"]}

app = flask.Flask(__name__)

RESPONSE_PING               = {"message": "I'm alive!!"}
RESPONSE_DELETE_VIEW        = {"message": "Delete successful"}
RESPONSE_ADDED_VIEW         = {"message": "Add successful"}
RESPONSE_GET                = {"message": "Get Message Received"}
RESPONSE_BAD_REQUEST        = "Bad Request"
RESPONSE_METHOD_NOT_ALLOWED = "Method Not Allowed"
RESPONSE_B_V                = "Invalid Vector Clock"

STATUS_OK          = 200
STATUS_ADD_VALUE   = 201
STATUS_BAD_REQUEST = 400
STATUS_NOT_FOUND   = 404
STATUS_NOT_ALLOWED = 405
STATUS_BAD_VECTOR  = 406

GET    = "GET"
PUT    = "PUT"
DELETE = "DELETE"


def get_current_socket_index(socket_address) -> int:
    global view_just_ips
    index = -1
    for i in range(0, len(view_just_ips)):
        if view_just_ips[i] == socket_address:
            index = i
            break
    return index


def vector_clock_init() -> None:
    global vector_clock_list
    global view_just_ips
    # initialize the vector clock
    if len(vector_clock_list) == 0:
        for i in range(0, len(view_just_ips)):
            vector_clock_list.append(0)


def set_vector_clock() -> list:
    global view_just_ips
    clock = list()
    for i in range(0, len(view_just_ips)):
        clock.append(0)
    return clock


def reset_vector_clock() -> list:
    global view_just_ips
    clock = list()
    if len(clock) == 0:
        for i in range(0, len(view_just_ips)):
            clock.append(0)
    return clock


def list_to_string(the_list):
    """Converts each element in a list to a string with a comma in between elements"""
    result = ""
    for element in the_list:
        result += str(element) + ","
    result = result[:-1]
    return result


def check_valid_clock(foreign_clock, index_sender_address):
    global vector_clock_list
    
    while(len(foreign_clock) < len(vector_clock_list)):
        foreign_clock.append(0)
    while(len(foreign_clock) > len(vector_clock_list)):
        vector_clock_list.append(0)

    for i in range(0, len(foreign_clock)):
        if (i == index_sender_address) and (int(foreign_clock[i]) != int(vector_clock_list[i]) + 1):
            return False
        if (i != index_sender_address) and (int(foreign_clock[i]) > int(vector_clock_list[i])):
            return False
    return True


def get(key):
    global my_shard
    if key in global_dictionary.keys():
        return json.dumps(
            {"doesExist": True,
                "message": "Retrieved successfully",
                "value": global_dictionary[key],
                "causal-metadata": list_to_string(vector_clock_list)}), STATUS_OK
    else:
        return json.dumps({"doesExist": False,
                           "error": "Key does not exist",
                           "message": "Error in GET",
                           "causal-metadata": list_to_string(vector_clock_list)}), STATUS_NOT_FOUND


def put(key, value):
    if len(key) > 50:
        return json.dumps(
            {"error": "Key is too long",
             "message": "Error in PUT", "causal-metadata": list_to_string(vector_clock_list),
             "shard-id": int(my_shard.replace('shard', ''))}), STATUS_BAD_REQUEST

    if key in global_dictionary.keys():
        global_dictionary[key] = value
        return json.dumps(
            {"message": "Updated successfully",
             "replaced": True, "causal-metadata": list_to_string(vector_clock_list),
             "shard-id": int(my_shard.replace('shard', ''))}), STATUS_OK
    else:
        global_dictionary[key] = value
        return json.dumps(
            {"message": "Added successfully",
                "replaced": False, "causal-metadata": list_to_string(vector_clock_list),
                "shard-id": int(my_shard.replace('shard', ''))}), STATUS_ADD_VALUE


def delete(key):
    global global_dictionary
    if key in global_dictionary.keys():
        global_dictionary.pop(key)
        return json.dumps({"doesExist": True, "message": "Deleted successfully", "causal-metadata": list_to_string(vector_clock_list), "shard-id": int(my_shard.replace('shard', ''))}), STATUS_OK
    else:
        return json.dumps({"doesExist": False, "error": "Key does not exist", "message": "Error in DELETE", "causal-metadata": list_to_string(vector_clock_list), "shard-id": int(my_shard.replace('shard', ''))}), STATUS_NOT_FOUND


@app.route('/ping', methods=[PUT, DELETE])
def ping():
    return json.dumps(RESPONSE_PING), STATUS_OK


@app.route('/remove-from-view/<ip>', methods=[DELETE])
def remove_from_view(ip):
    global vector_clock_list
    global view_just_ips

    if ip in view_just_ips:
        delete_index = get_current_socket_index(ip)
        view_just_ips.remove(ip)
        vector_clock_list.pop(delete_index)
    return json.dumps(RESPONSE_DELETE_VIEW), STATUS_OK


@app.route('/add-to-view/<ip>', methods=[PUT])
def add_to_view(ip):
    global vector_clock_list
    global view_just_ips

    if ip not in view_just_ips:
        view_just_ips.append(ip)
        vector_clock_list.append(0)
    return json.dumps(global_dictionary), STATUS_OK


@app.route('/get-all-data', methods=[GET])
def get_all_data_self():
    return json.dumps(global_dictionary), STATUS_OK


@app.route('/remove-from-shard-info/<ip>', methods=[DELETE])
def remove_ip_from_shard_info(ip):
    """Removes shard information from every ip we call"""
    global shard_info
    for shard_key in shard_info.keys():
        if ip in shard_info[shard_key]:
            shard_info[shard_key].remove(ip)
            break
    return RESPONSE_ADDED_VIEW, STATUS_OK


#  To do shard operations, a client or node sends GET (for retrieving information
# about shards) and PUT (for changing number of shards or changing the membership of nodes in the
# shards) requests to a node in the store.
@app.route('/key-value-store-shard/shard-ids', methods=[GET])
def get_all_shard_ids() -> json:
    """Get the ids of all shards in the store"""
    global shard_info
    # Get the IDs of all shards in the store
    ip_list = list()
    for shard in shard_info.keys():
        ip_list.append(int(shard.replace('shard', '')))
    return json.dumps({"message":"Shard IDs retrieved successfully","shard-ids":ip_list}), STATUS_OK


@app.route('/key-value-store-shard/node-shard-id', methods=[GET])
def get_shard_id_of_node():
    """Get the shard id of a replica"""
    global my_shard
    return json.dumps({"message":"Shard ID of the node retrieved successfully","shard-id": int(my_shard.replace('shard', ''))}), STATUS_OK


@app.route('/key-value-store-shard/shard-id-members/<shard_id>', methods=[GET])
def get_shard_members_data(shard_id):
    """Gets all of the replicas ip addresses from the shard id"""
    global shard_info
    shard_string = 'shard' + str(shard_id)
    if shard_string not in shard_info.keys():
        return json.dumps({"Message: The shard id given was not found, Error: Error in shard_id-members"}), RESPONSE_BAD_REQUEST
    return json.dumps({"message":"Members of shard ID retrieved successfully","shard-id-members": shard_info[shard_string]}), STATUS_OK


@app.route('/key-value-store-shard/shard-id-key-count/<shard_id>', methods=[GET])
def get_shard_key_count(shard_id):
    """Gets number of keys in the shard from shard id"""
    global shard_info
    global my_shard
    global global_dictionary
    shard_string = 'shard' + str(shard_id)
    length       = 0

    if my_shard == shard_string:
        length = len(global_dictionary)
    else:
         for shard_id in shard_info.keys():
            if shard_id == shard_string:
                for replica in shard_info[shard_id]:
                    try:
                        response = requests.get("http://" + replica + "/shard-keys")
                        length = int(response.text)
                        break
                    except:
                        pass
    return json.dumps({"message":"Key count of shard ID retrieved successfully","shard-id-key-count":length}), STATUS_OK


@app.route('/shard-keys', methods=[GET])
def shard_keys():
    global global_dictionary
    return str(len(global_dictionary)) # this also works with len(global_dictionary.keys())


@app.route('/key-value-store-shard/add-member/<shard_id>', methods=[PUT])
def add_member(shard_id):
    """How the client adds a new node"""
    global shard_info
    global your_socket_address
    shard_string = 'shard' + str(shard_id)
    temp_dict = {}
    try:
        temp_dict = flask.request.get_json()
    except:
        pass

    if temp_dict == {} or temp_dict is None:
        return json.dumps({"error": "Value is missing", "message": "Error in add-member"}), STATUS_BAD_REQUEST
    
    new_socket_address = temp_dict['socket-address']
    if shard_string in shard_info.keys() and new_socket_address not in shard_info[shard_string]:
        for shard_id in shard_info.keys():
            for replica in shard_info[shard_id]:
                if replica == your_socket_address:
                    continue
                requests.put("http://" + replica + "/add-shard-replica/" + str(shard_string) + '/' + str(new_socket_address)) # tells every shard that a new node replica exists
        shard_info[shard_string].append(new_socket_address)
        # TELL NEW SOCKET ADDRESS to get special init()
        requests.put("http://" + str(new_socket_address) + "/new_node_init/" + str(shard_string), json=shard_info)
    return json.dumps({}), STATUS_OK


@app.route('/add-shard-replica/<shard_id>/<ip>', methods=[PUT])
def add_ip_to_shard_info(shard_id, ip):
    """Adds shard information for every ip we call"""
    global shard_info
    if shard_id in shard_info.keys() and ip not in shard_info[shard_id]:
        shard_info[shard_id].append(ip)
    return str(STATUS_OK)


@app.route('/key-value-store-shard/reshard', methods=[PUT])
def reshard():
    global all_nodes_ips
    global shard_info
    global view_just_ips
    global global_dictionary
    global my_shard

    shard_count   = 0
    response_dict = dict()
    
    try:
        response_dict = flask.request.get_json()
    except:
        pass

    if len(response_dict.keys()) == 0:
        return json.dumps({"error": "Shard Count is missing", "message": "Error in Reshard"}), STATUS_BAD_REQUEST
    shard_count = int(response_dict['shard-count'])
    
    #Check to see if valid
    total_num_nodes  = len(all_nodes_ips)

    if (total_num_nodes//shard_count) < 2:
        return json.dumps({"message":"Not enough nodes to provide fault-tolerance with the given shard count!"}), STATUS_BAD_REQUEST
    
    # Get all key-value-strs
    complete_sys_dict = retrieve_all_system_data_kv()

    # Divide the shards into the new place
    shard_info = divide_shards(list_to_string(all_nodes_ips), int(shard_count))

    # Reset your own data
    my_shard      = get_myshard_info(your_socket_address)
    view_just_ips = shard_info[my_shard] # "shard1", or "shard2" ect...
    vector_clock_list.clear()
    vector_clock_init()
    global_dictionary.clear()

    # Reset everyone elses data
    set_shard_info_broadcaster(shard_info)

    #Hash all the values out
    for key in complete_sys_dict.keys():
        route_to_shard(key, "PUT", message_json={"value":complete_sys_dict[key], "causal-metadata": ""})
    return json.dumps({"message":"Resharding done successfully"}), STATUS_OK

    
def set_shard_info_broadcaster(shard_info):
    for ip in all_nodes_ips:
        if ip == your_socket_address:
            continue
        try:
            requests.put("http://" + str(ip) + "/set-shard-info", json={"shard_info": shard_info}).json()
        except:
            pass


@app.route('/set-shard-info', methods=[PUT])
def set_shard_info_receiver():
    global shard_info
    global view_just_ips
    global global_dictionary
    global my_shard
    
    shard_info = flask.request.get_json()["shard_info"]
    my_shard = get_myshard_info(your_socket_address)
    view_just_ips = shard_info[my_shard]
    vector_clock_list.clear()
    vector_clock_init()
    global_dictionary.clear()
    return json.dumps({"message": "success"}), STATUS_OK



def get_myshard_info(ip_to_find):
    """find where you are in the shard right now and assign it to my_shard"""
    global shard_info
    result = None
    for shard_name, ip_list in shard_info.items():
        for ip in ip_list:
            if ip == ip_to_find: # if the ip matches the one we are searching for, return the shard name (shard_name)
                return shard_name
    return result


@app.route('/get_causal_data', methods=[GET])
def get_c_d():
    global vector_clock_list
    return json.dumps({"vector-clock": list_to_string(vector_clock_list)}), STATUS_OK


# pings known dead servers to see if they came back online at any point
@app.route('/get_data', methods=[PUT, DELETE])
def get_all_data():
    init_server()
    return json.dumps({"message": "received all data"}), STATUS_OK


def send_broadcast():
    global view_set
    global view_just_ips
    global known_down_ips

    response                = None
    ips_to_remove_from_view = list()
    vs_copy                 = view_set.copy()

    for dead_ip in known_down_ips:
        try:
            response = requests.put("http://" + str(dead_ip) + "/get_data").json()
            known_down_ips.remove(dead_ip)
        except:
            pass

    for url in vs_copy:
        response_check = None
        response_ping  = None

        try:
            response_ping  = requests.get(url[0])
            response_check = STATUS_OK
        except Exception as e:
            response_check = 420

        # Check if the server is down
        if response_check == 420:

            # DELETE SOCKET ADDRESS FROM VIEW
            if url in vs_copy:
                if url in view_set:
                    view_set.remove(url)
                if url[2] in view_just_ips:
                    ips_to_remove_from_view.append(url[2])
                    known_down_ips.append(url[2])
                    delete_index = get_current_socket_index(url[2])
                    view_just_ips.remove(url[2])
                    vector_clock_list.pop(delete_index)

        # Server is not down, now broadcast to server
        else:
            if flask.request.method == PUT or flask.request.method == DELETE:
                response = requests.get(url[1])
            else:
                # should never happen
                return STATUS_NOT_ALLOWED

    if len(ips_to_remove_from_view) > 0:
        for ip in view_just_ips:
            for ip_to_remove in ips_to_remove_from_view:
                requests.delete("http://" + str(ip) + "/remove-from-view/" + str(ip_to_remove))
    
    view_set = set()
    return response


@app.route('/broadcast/<key>/<value>/<vector_string>/<sender_address>', methods=[GET])
def broadcast(key, value, vector_string, sender_address):
    global vector_clock_list

    foreign_clock = vector_string.split(',')
    check         = check_valid_clock(foreign_clock, get_current_socket_index(sender_address))

    if not check:
        init_server()
    else:
        # Update Your vector clock
        for i in range(0, len(foreign_clock)):
            if int(foreign_clock[i]) > int(vector_clock_list[i]):
                vector_clock_list[i] = int(foreign_clock[i])
    # Update your dict values
    if value == "delete":
        delete(key)
    else:
        put(key, value)
    return json.dumps(RESPONSE_PING), STATUS_OK



@app.route('/key-value-store-view', methods=[GET, PUT, DELETE])
def route_view():
    global view_just_ips
    global all_nodes_ips

    temp_dict = {}
    all_nodes_ips.sort()

    if flask.request.method == GET:
        return json.dumps({"message": "View retrieved successfully", "view": list_to_string(all_nodes_ips)}), STATUS_OK
    try:
        temp_dict = flask.request.get_json()
    except:
        pass

    if temp_dict is None:
        temp_dict = flask.request.data.decode("utf-8")
        temp_dict = ast.literal_eval(temp_dict)

    # if temp_dict == {} or temp_dict is None:
    if len(temp_dict.keys()) == 0:
        return json.dumps({"error": "Value is missing", "message": "Error in PUT"}), STATUS_BAD_REQUEST

    socket_address       = temp_dict['socket-address']
    check_socket_address = socket_address in view_just_ips

    if flask.request.method == DELETE:
        if check_socket_address:
            delete_index = get_current_socket_index(socket_address)
            view_just_ips.remove(socket_address)
            vector_clock_list.pop(delete_index)
            return json.dumps({"message": "Replica deleted successfully from the view"}), STATUS_OK
        else:
            return json.dumps({"error": "Socket address does not exist in the view", "message": "Error in DELETE"}), STATUS_NOT_FOUND
    if flask.request.method == PUT:
        if check_socket_address:
            return json.dumps({"error": "Socket address already exists in the view", "message": "Error in PUT"}), STATUS_NOT_FOUND
        else:
            view_just_ips.append(socket_address)
            return json.dumps({"message": "Replica added successfully to the view"}), STATUS_ADD_VALUE
    return STATUS_NOT_ALLOWED


def make_broadcast_urls(key, temp_dict):
    global view_just_ips
    global your_socket_address
    global view_set

    for element in view_just_ips:
        if element == your_socket_address:
            continue
        url = ""
        if flask.request.method == PUT:
            url = ("http://" + element + "/broadcast/" + str(key) + '/' + str(temp_dict["value"]) + '/' + list_to_string(vector_clock_list) + '/' + str(your_socket_address))
        else:
            url = ("http://" + element + "/broadcast/" + str(key) + '/delete/' + list_to_string(vector_clock_list) + '/' + str(your_socket_address))
        t = ("http://" + element + "/ping", url, element)
        view_set.add(t)


def route_hashing(key):
    global shard_info
    my_hash = int(' '.join(format(ord(x), 'b') for x in key).replace(" ", ""), 2) # basic predictable hash
    return "shard" + str(my_hash % len(shard_info.keys()) + 1)
    

# Returns true if key belongs in this node.
def in_correct_shard(key):
    global my_shard
    return bool(my_shard == route_hashing(key))


def route_to_shard(key, message_method, message_json):
    shard = route_hashing(key) # select which shard to route to
    # random_index = random.randint(0,len(shard_info[shard])-1)
    random_index = 0
    
    # TODO: add try, in case replica is down.
    ip = shard_info[shard][random_index] #randomly choose ip from list (reduce load)

    if message_method == GET:
        return requests.get("http://" + str(ip) + "/key-value-store/" + key, json=message_json).json()
    elif message_method == PUT:
        return requests.put("http://" + str(ip) + "/key-value-store/" + key, json=message_json).json()
    elif message_method == DELETE:
        return requests.delete("http://" + str(ip) + "/key-value-store/" + key, json=message_json).json()


# Get entire system data as a heirarchy
@app.route('/retrieve-system', methods=[GET])
def retrieve_all_system_data():
    return_info = dict()
    for shard in shard_info.keys():
        return_info[shard] = dict()
        for ip in shard_info[shard]:
            ip_data = requests.get("http://" + str(ip) + "/get-all-data").json()
            return_info[shard][ip] = ip_data
    return return_info, STATUS_OK


def retrieve_all_system_data_kv():
    return_info = dict()
    for shard in shard_info.keys():
        shard_kv = requests.get("http://" + str(shard_info[shard][0]) + "/get-all-data").json()
        return_info.update(shard_kv)
    return return_info


@app.route('/key-value-store/<key>', methods=[GET, PUT, DELETE])
def route_request(key):
    global vector_clock_list
    global view_just_ips
    global your_socket_address
    global view_set

    response_check = 0
    temp_dict = dict()

    # if not in correct shard, go route to some ip in the correct shard
    if not in_correct_shard(key):
        return route_to_shard(key, flask.request.method, flask.request.get_json())

    try:
        temp_dict = flask.request.get_json()
    except:
        pass

    if len(temp_dict.keys()) == 0:
        return json.dumps({"error": "Values are missing", "message": "Error from Client"}), STATUS_BAD_REQUEST

    # Init the client's causal-metadata
    client_clock = temp_dict['causal-metadata']
    
    if client_clock == "":
        client_clock = set_vector_clock()
    else:
        client_clock = client_clock.split(',')

    # Check to see if client sent valid vector clock
    valid_clock = check_valid_clock(client_clock, -1)
    if not valid_clock:
        init_server()
    
    # If get request then return local value
    if flask.request.method == GET:
        return get(key)

    index = get_current_socket_index(your_socket_address)
    vector_clock_list[index] += 1 # this need to be a string not an int!
    make_broadcast_urls(key, temp_dict)

    # BROADCAST HERE
    send_broadcast()
    if flask.request.method == PUT:
        return put(key, temp_dict["value"])
    elif flask.request.method == DELETE:
        return delete(key)




def divide_shards(vview, shard_num):
    """Splits the view list and adds the nodes to the shard_dict"""
    view = vview.split(',')
    shard_dict = dict()
    for i in range(shard_num):
        shard_dict["shard" + str(i + 1)] = list()
    for i in range(0, len(view)):
        shard_dict["shard" + str((i % shard_num) + 1)].append(view[i])
    return shard_dict


@app.route('/add_node_to_global_view/<ip>', methods=[PUT])
def add_global_view(ip):
    all_nodes_ips.append(ip)
    return str(STATUS_OK)


@app.route('/new_node_init/<shard_id>', methods=[PUT])
def new_node_init(shard_id):
    global view_just_ips
    global your_socket_address
    global global_dictionary
    global vector_clock_list
    global shard_info
    global my_shard
    global all_nodes_ips

    my_shard = shard_id

    try:
        shard_info = flask.request.get_json()
    except:
        pass

    view_just_ips = shard_info[my_shard]

    for ip in view_just_ips:
        if ip == your_socket_address:
            continue
        try:
            my_json = json.loads(json.dumps(requests.put("http://" + str(ip) + "/add-to-view/" + str(your_socket_address)).json()))
            global_dictionary = my_json
        except:
            pass

    for ip in view_just_ips:
        if ip == your_socket_address:
            continue
        try:
            new_causal_metadata = json.loads(json.dumps(requests.get("http://" + str(ip) + "/get_causal_data").json()))
            vector_clock_list = new_causal_metadata['vector-clock'].split(',')
            for i in range(0,len(vector_clock_list)):
                vector_clock_list[i] = int(vector_clock_list[i])
            break
        except:
            pass
    return str(STATUS_OK)


def init_server():
    global view_just_ips
    global your_socket_address
    global global_dictionary
    global vector_clock_list
    global shard_info
    global my_shard
    global all_nodes_ips

    shard_count = 0
    
    for k, v in os.environ.items():
        if k == "SHARD_COUNT":
            shard_count = v
        elif k == "SOCKET_ADDRESS": # ip address
            your_socket_address = v
        elif k == "VIEW":
            all_nodes_ips = v.split(",")

    #If added node,
    if shard_count == 0:
        for ip in all_nodes_ips:
            if ip == your_socket_address:
                continue
            try:
                requests.put("http://" + str(ip) + "/add_node_to_global_view/" + str(your_socket_address))
            except:
                pass
        return
        
    for k, v in os.environ.items():
        if k == "VIEW":
            shard_info = divide_shards(v, int(shard_count))

    # determine what shard youre in.
    for key in shard_info.keys():
        if your_socket_address in shard_info[key]:
            view_just_ips = shard_info[key]
            my_shard = key
            break

    vector_clock_init()

    for ip in view_just_ips:
        if ip == your_socket_address:
            continue

        try:
            my_json = json.loads(json.dumps(requests.put("http://" + str(ip) + "/add-to-view/" + str(your_socket_address)).json()))
            global_dictionary = my_json
        except:
            pass

    for ip in view_just_ips:
        if ip == your_socket_address:
            continue
        try:
            new_causal_metadata = json.loads(json.dumps(requests.get("http://" + str(ip) + "/get_causal_data").json()))
            vector_clock_list = new_causal_metadata['vector-clock'].split(',')
            
            for i in range(0,len(vector_clock_list)):
                vector_clock_list[i] = int(vector_clock_list[i])
            
            break
        except:
            pass
 


# ==============================
#  MAIN FUNCTION
# ==============================
if __name__ == "__main__":
    init_server()
    app.run(host='0.0.0.0', port=8085)
