import pymongo
from pymongo import MongoClient
import os
import datetime
import pandas as pd
import json
import time
user = os.environ.get("DB_USER")
secret = os.environ.get("DB_PASS")
cluster = pymongo.MongoClient(f"mongodb://localhost:27017")
db = cluster["data"]
memberdata = db["localdata"]
vehicledata = db["vehicle"]
def add_user(user):
    return memberdata.insert_one(user)

def check_for_user(username):
    if memberdata.find_one({"username" : username}):
        return True
    else:
        return False

def getRole(username):
    user = memberdata.find_one({"username": username})
    if user:
        return user.get("role")
    else:
        return None
def getVehiclePlate(username):
    query = {"members": username}
    vehicle_plate = vehicledata.find_one(query, {"vehicle_plate": 1})

    if vehicle_plate:
        return vehicle_plate.get("vehicle_plate")
    else:
        return None

def getStatus(username):
    user = memberdata.find_one({"username" : username})
    if user:
        return user.get("status")
    else:
        return None
    
def getUsername(username):
    user = memberdata.find_one({"username" : username})
    if user:
        return user.get("username")
    else:
        return None
    
def addStudent(file):
    try:
        data = pd.read_excel(file)
        DataStore = {}
        count = 0
        #print(file.filename)
        filename = file.filename.rsplit(".", 1)[0]
        #print(data.head())
        for i in data["Unnamed: 1"]:
            count += 1
            if str(i) != "nan" and str(i) != "เลขที่":
                DataStore[data["Unnamed: 4"][count-1]] = [str(i), data["Unnamed: 7"][count-1]]

        with open(f"class_list/{filename}.json", "w+") as json_file:
            json_file.write(json.dumps(DataStore))
        with open(f"class_list/{filename}.json", "r") as f:
            data = json.load(f)
        for i in data:
            unique_num = i
            no = data[i][0]
            name = data[i][1]
            createStudent(display=name, username=unique_num, password=no, role="student", cls=filename)
        return True
    except Exception as e:
        print(f"Error in addStudent function: {str(e)}")
        return False


def getVehicle(username):
    user = memberdata.find_one({"username": username})
    if user and (user.get("role") == "teacher" or user.get("role") == "admin"):
        veh = []
        vehicles = vehicledata.find({})
        for vehicle in vehicles:
            veh.append(vehicle["vehicle_plate"])
        return veh
    else:
        return None

def createTeacher(username, password, role, vehicle):
    if role == "teacher":
        userelement = {
            "role" : "teacher",
            "username" : username,
            "password" : password,
            "manage" : vehicle
        }
        memberdata.insert_one(userelement)
def createVehicle(vehicle_plate):
    userelement = {
        "vehicle_plate": vehicle_plate,
        "image" : "",
        "members": [],
        "up" : [],
        "down" : []
        }
    vehicledata.insert_one(userelement)
def createStudent(display,username, password, role, cls):
    if role == "student":
        userelement = {
            "display" : display,
            "role" : "student",
            "username" : username,
            "password" : password,
            "class" : cls,
            "status" : "",
            "checkbox" : False
        }
        memberdata.insert_one(userelement)
        
def getClass(cls, subcls):
    merge = f"{cls}-{subcls}"
    data = memberdata.find({"class" : merge})
    return data

def updateStatus(username, new_status):
    result = memberdata.update_one(
        {"username": username},
        {"$set": {"status": new_status}}
    )
    return result.modified_count > 0

def duplicate(username):
    cursor = vehicledata.find()
    for document in cursor:
        if username in document["members"]:
            return True
    return False

def add_members_to_vehicle(vehicle_plate, new_members):
    for name in new_members:
        if not duplicate(name):
            query = {"vehicle_plate": vehicle_plate}
            result = vehicledata.update_one(query, {"$push": {"members": name}})
            if result.modified_count > 0:
                print(f"Members added to vehicle {vehicle_plate} successfully.")
            else:
                print(f"No documents were updated. Vehicle {vehicle_plate} not found.")
        else:
            print("Duplicate")
    return True

  
def get_name_from_number(number):
    data = memberdata.find_one({"password" : str(number)})
    if data:
        return data.get("username")
    return None

def get_number_from_name(id):
    data = memberdata.find_one({"username" : str(id)})
    if data:
        return data.get("password")
    return None

def get_display_from_name(id):
    data = memberdata.find_one({"username" : str(id)})
    if data:
        return data.get("display")
    return None

def check_for_vehicle(vehicle_plate):
    if vehicledata.find_one({"vehicle_plate" : vehicle_plate}):
        return True
    else:
        return False
    
def getMembers(vehicle_plate):
    if check_for_vehicle(vehicle_plate):
        vehicle = vehicledata.find_one({"vehicle_plate" : vehicle_plate})
        return vehicle.get("members"), vehicle.get('up'), vehicle.get('down')
    return None

def filters(members, up, down):
    unknown_members = [i for i in members if (i not in up) and (i not in down)]
    return unknown_members

def move_up_to_down(vehicle_plate, element):
    filter_criteria = {"vehicle_plate": vehicle_plate}
    update_query = {
        "$pull": {"up": element},
        "$push": {"down": element}
    }

    result = vehicledata.update_one(filter_criteria, update_query)

    if result.modified_count > 0:
        print(f"Element {element} moved from 'up' to 'down' for vehicle {vehicle_plate}.")
        return True
    else:
        print(f"No documents were updated. Vehicle {vehicle_plate} not found.")
        return False
    
def isMembers(vehicle_plate, element):
    try:
        find_one = vehicledata.find_one({"vehicle_plate" : vehicle_plate})
        if element in find_one.get("members"):
            return True
        else:
            return False
    except:
        return False
def move_down_to_up(vehicle_plate, element):
    filter_criteria = {"vehicle_plate": vehicle_plate}
    update_query = {
        "$pull": {"down": element},
        "$push": {"up": element}
    }

    result = vehicledata.update_one(filter_criteria, update_query)

    if result.modified_count > 0:
        print(f"Element {element} moved from 'down' to 'up' for vehicle {vehicle_plate}.")
        return True
    else:
        print(f"No documents were updated. Vehicle {vehicle_plate} not found.")
        return False
def get_status_from_vehicle(vehicle_plate, username):
    find_one = vehicledata.find_one({"vehicle_plate": vehicle_plate})
    
    if find_one:
        if username in find_one.get("up", []):
            return "up"
        elif username in find_one.get("down", []):
            return "down"
        elif username in find_one.get("members", []):
            return "members"
        else:
            return "not_found"
    else:
        return "not_found"
def updateImg(vehicle_plate, data):
    new_image_filename = data 
    find_one = vehicledata.find_one({"vehicle_plate": vehicle_plate})

    if find_one:
        vehicledata.update_one({"vehicle_plate": vehicle_plate}, {"$set": {"image": new_image_filename}})
        return True
    else:
        print(f"Vehicle {vehicle_plate} not found.")
        return False
def get_image_path(vehicle_plate):
    find_one = vehicledata.find_one({"vehicle_plate": vehicle_plate})
    if find_one:
        return find_one.get("image")
    return ""
def deleteVehicle(vehicle_plate):
    find_one = vehicledata.find_one({"vehicle_plate": vehicle_plate})

    if find_one:
        vehicledata.delete_one({"vehicle_plate": vehicle_plate})
        return True
    return False

def delete_by_role(role):
    find_all = memberdata.find({})
    for element in find_all:
        if element["role"] == role:
            memberdata.delete_one(element)