# ---------------------------------------------------------------------------------
# Authors:   Rory Glenn, Seth Tonningsen, Timothy Chandler
# Email:     romglenn@ucsc.edu, stonning@ucsc.edu, tdchandl@ucsc.edu
# Team:      Laser Sharks
# Quarter:   Spring 2021
# Class:     CSE 138 (Distributed Systems)
# Project:   Assignment 3
# Professor: Lindsey Kuper
#
# app.py
#   Implementation file for httpserver
# ---------------------------------------------------------------------------------

import ast
import requests
import os
import flask
import json

your_socket_address  = str()
view_set             = set()
global_dictionary    = dict()
vector_clock_list    = list()
view_just_ips        = list()
global_request_queue = list()
known_down_ips       = list()

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
             "message": "Error in PUT", "causal-metadata": list_to_string(vector_clock_list)}), STATUS_BAD_REQUEST

    if key in global_dictionary.keys():
        global_dictionary[key] = value
        return json.dumps(
            {"message": "Updated successfully",
             "replaced": True, "causal-metadata": list_to_string(vector_clock_list)}), STATUS_OK
    else:
        global_dictionary[key] = value
        return json.dumps(
            {"message": "Added successfully",
                "replaced": False, "causal-metadata": list_to_string(vector_clock_list)}), STATUS_ADD_VALUE


def delete(key):
    global global_dictionary

    if key in global_dictionary.keys():
        global_dictionary.pop(key)
        return json.dumps({"doesExist": True, "message": "Deleted successfully", "causal-metadata": list_to_string(vector_clock_list)}), STATUS_OK
    else:
        return json.dumps({"doesExist": False, "error": "Key does not exist", "message": "Error in DELETE", "causal-metadata": list_to_string(vector_clock_list)}), STATUS_NOT_FOUND


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


@app.route('/get_causal_data', methods=[GET])
def get_c_d():
    global vector_clock_list
    return json.dumps({"vector-clock": list_to_string(vector_clock_list)}), STATUS_OK


# pings known dead servers to see if they came back online at any point
@app.route('/get_data', methods=[PUT, DELETE])
def get_all_data():
    init_server()
    return json.dumps({"message": "recieved all data"}), STATUS_OK


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
                # Bad Vector
                if response.status_code == STATUS_BAD_VECTOR:
                    # print("RECEIVED CODE OF BAD VECTOR", flush=True)
                    pass
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
    # Update Your vector clock
    else:
        for i in range(0, len(foreign_clock)):
            if int(foreign_clock[i]) > int(vector_clock_list[i]):
                vector_clock_list[i] = int(foreign_clock[i])

    # Update your dict values
    if value == "value":
        delete(key)
    else:
        put(key, value)

    return json.dumps(RESPONSE_PING), STATUS_OK



@app.route('/key-value-store-view', methods=[GET, PUT, DELETE])
def route_view():
    global view_just_ips
    temp_dict = {}

    if flask.request.method == GET:
        return json.dumps({"message": "View retrieved successfully", "view": list_to_string(view_just_ips)}), STATUS_OK

    try:
        temp_dict = flask.request.get_json()
    except:
        pass

    if temp_dict is None:
        temp_dict = flask.request.data.decode("utf-8")
        temp_dict = ast.literal_eval(temp_dict)

    if temp_dict == {} or temp_dict is None:
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


@app.route('/key-value-store/<key>', methods=[GET, PUT, DELETE])
def route_request(key):
    global vector_clock_list
    global view_just_ips
    global your_socket_address
    global view_set
    global global_request_queue

    response_check = 0
    temp_dict = dict()

    try:
        temp_dict = flask.request.get_json()
    except:
        pass

    if temp_dict == {} or temp_dict is None:
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



def init_server():
    global view_just_ips
    global your_socket_address
    global global_dictionary
    global vector_clock_list

    for k, v in os.environ.items():
        if k == "VIEW":
            view_just_ips = v.split(',')
        elif k == "SOCKET_ADDRESS":
            your_socket_address = v

    vector_clock_init()

    for ip in view_just_ips:
        if ip == your_socket_address:
            print("Ignoring self", flush=True)
            continue
        print("http://" + str(ip) + "/add-to-view/" + str(your_socket_address), flush=True)
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
