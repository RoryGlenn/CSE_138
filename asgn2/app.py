# ---------------------------------------------------------------------------------
# Authors:   Rory Glenn, Seth Tonningsen, Timothy Chandler
# Email:     romglenn@ucsc.edu, stonning@ucsc.edu, tdchandl@ucsc.edu
# Team:      Laser Sharks
# Quarter:   Spring 2021
# Class:     CSE 138 (Distributed Systems)
# Project:   Assignment 2
# Professor: Lindsey Kuper
#
# app.py
#   Implementation file for httpserver
# ---------------------------------------------------------------------------------


# To run the server
#   flask run -p 8085

# to make a request to server
# curl --request GET --header "Content-Type: application/json" --write-out "\n%{http_code}\n" http://127.0.0.1:8086/key-value-store/course1
# curl --request PUT --header "Content-Type: application/json" --write-out "\n%{http_code}\n" --data "{\"value\": \"Distributed Systems\"}" http://127.0.0.1:8086/key-value-store/course1


# part 2
# docker network create --subnet=10.10.0.0/16 mynet
# docker build -t assignment2-img .
# docker run -p 8086:8085 --net=mynet --ip=10.10.0.2 --name="main-container" assignment2-img
# docker run -p 8087:8085 --net=mynet --ip=10.10.0.3 --name="forwarding-container" -e FORWARDING_ADDRESS=10.10.0.2:8085 assignment2-img


global_dictionary = dict()

import json
import flask
import os
import requests
import ast
from flask import request

app = flask.Flask(__name__)

RESPONSE_PING               = {"message":"I'm alive!!"}
RESPONSE_GET                = {"message":"Get Message Received"}
RESPONSE_BAD_REQUEST        = "Bad Request"
RESPONSE_METHOD_NOT_ALLOWED = "Method Not Allowed"

STATUS_OK                  = 200
STATUS_ADD_VALUE           = 201
STATUS_BAD_REQUEST         = 400
STATUS_NOT_FOUND           = 404
STATUS_NOT_ALLOWED         = 405
STATUS_SERVICE_UNAVAILABLE = 503

GET    = "GET"
POST   = "POST"
PUT    = "PUT"
DELETE = "DELETE"

def get(key):
    if key in global_dictionary.keys():
        return json.dumps(
               {"doesExist":True,
                "message":"Retrieved successfully",
                "value":global_dictionary[key]}), STATUS_OK
    else:
        return json.dumps(
               {"doesExist":False,
                "error":"Key does not exist",
                "message":"Error in GET"}) , STATUS_NOT_FOUND

def put(key, value):

    if len(key) > 50:
        return json.dumps(
            {"error":"Key is too long",
            "message":"Error in PUT"}), STATUS_BAD_REQUEST

    if key in global_dictionary.keys():
       global_dictionary[key] = value
       return json.dumps(
           {"message":"Updated successfully",
           "replaced": True}), STATUS_OK
    else:
       global_dictionary[key] = value
       return json.dumps(
              {"message":"Added successfully",
              "replaced": False }), STATUS_ADD_VALUE


def delete(key):
    global global_dictionary
    if key in global_dictionary.keys():
        global_dictionary.pop(key)
        return json.dumps({"doesExist":True,"message":"Deleted successfully"}), STATUS_OK
    else:
        return json.dumps({"doesExist":False,"error":"Key does not exist","message":"Error in DELETE"}), STATUS_NOT_FOUND


@app.route('/ping', methods=[GET, PUT, DELETE])
def ping():
    return json.dumps(RESPONSE_PING), STATUS_OK


@app.route('/key-value-store/<key>', methods=[GET, PUT, DELETE])
def route_request(key):
    response_check = 0
    forwarding_address = 0
    for k, v in os.environ.items():
        if k == "FORWARDING_ADDRESS":
            forwarding_address = v
        print(f"FORWARD ADDRESS:      {forwarding_address}", flush=True)

    # if we find the forwarding address, we are the forwarder
    if forwarding_address != 0:
        url         = "http://" + forwarding_address + "/"
        url_ping    = url + "ping"
        request_url = request.url
        parts       = request_url.split("/")

        for i in range(3, len(parts)):
            url += parts[i] + "/"

        url = url[:-1]

        try:
            response_ping = requests.get(url_ping)
            response_check = STATUS_OK
        except:
            response_check = 420

        if response_check == 420:
            return json.dumps({"error":"Main instance is down","message":f"Error in {request.method}"}), STATUS_SERVICE_UNAVAILABLE

        response = None
        if request.method == GET:
            response = requests.get(url, data=request.data)
        elif request.method == PUT:
            response = requests.put(url, data=request.data)
        elif request.method == DELETE:
            response = requests.delete(url, data=request.data)

        return response.json(), response.status_code

    # we are the main container
    else:
        if request.method == GET:
            return get(key)
        elif request.method == PUT:
            temp_dict = request.get_json()
            if temp_dict is None:
                temp_dict = request.data.decode("utf-8")
                temp_dict = ast.literal_eval(temp_dict)
            if temp_dict == {} or temp_dict is None:
                return json.dumps({"error":"Value is missing","message":"Error in PUT"}), STATUS_BAD_REQUEST
            return put(key, temp_dict["value"])
        elif request.method == DELETE:
            return delete(key)
