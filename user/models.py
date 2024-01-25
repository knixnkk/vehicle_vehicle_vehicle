from flask import Flask, jsonify, request, render_template, redirect, flash, url_for, session
from passlib.hash import pbkdf2_sha256
import uuid
import user_database as db
import datetime
import requests

class User:
    def signup(self):
        mydate = datetime.datetime.now()
        timenow = (mydate.strftime("%X"))
        user = {
            "_id": uuid.uuid4().hex,
            "username": request.form.get('username'),
            "password": request.form.get('password'),
        }
        if db.check_for_user(user["username"]):
            return False
        else:
            db.add_user(user)
            return True
    def login(self):
        user_exists = db.check_for_user(request.form.get('username'))
        username = db.check_for_user(request.form.get('username'))
        password = db.check_for_user(request.form.get('password'))
        if user_exists:
            session['username'] = request.form.get('username')
            return True
        else:
            return False
    def logout(self):
        if 'username' in session:
            session.pop('username')
            return True
        else:
            return False
    def addTeacher(self):
        user_exists = db.check_for_user(request.form.get("username"))
        if not user_exists:
            username = request.form.get("username")
            password = request.form.get("password")
            vehicle = request.form.get('vehicle')
            db.createTeacher(username=username, password=password, role="teacher", vehicle=vehicle)
            return True
    def addVehicle(self):
        user_exists = db.check_for_user(request.form.get("vehicle-name"))
        if not user_exists:
            vehicle_name = request.form.get("vehicle-name")
            db.createVehicle(vehicle_name)
            return True