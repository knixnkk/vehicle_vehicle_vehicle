from flask import Flask, render_template, request, redirect, flash, url_for, session, jsonify
from datetime import timedelta
from user.models import User
import os
import user_database as db
from flask import Flask, session
import pymongo
from pymongo import MongoClient
import requests
import socket
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['STATIC_FOLDER'] = 'static'
@app.route('/')
def first():
    if 'username' not in session:
        return render_template('signin.html')

    user_exists = db.check_for_user(session['username'])

    if not user_exists:
        return render_template('signin.html')
    else:
        role = db.getRole(session['username'])

        if role is None:
            return render_template('error.html', error_message="Role not found for the user.")

        if role == "student":
            try:
                getVehiclePlate = db.getVehiclePlate(session["username"])
                getStatus = db.getStatus(session["username"])
                getDisplay = db.get_display_from_name(session["username"])
                getUsername = db.getUsername(session["username"])
                stat = ""
                if db.get_status_from_vehicle(getVehiclePlate, getUsername) == "up":
                    stat = "ขึ้นรถ"
                elif db.get_status_from_vehicle(getVehiclePlate, getUsername) == "down":
                    stat = "ลงรถ"
                elif db.get_status_from_vehicle(getVehiclePlate, getUsername) == "members":
                    stat = "ไม่ทราบ"
                else:
                    stat = "ERROR"
            except Exception as e:
                return render_template('error.html', error_message=str(e))

            return render_template('index-student.html', VehiclePlate=getVehiclePlate, status=stat, display=getDisplay, username=getUsername, image_path = db.get_image_path(getVehiclePlate))

        elif role == 'teacher':
            getVehiclePlate = db.getVehicle(session["username"])
            vehicleDict = {str(i + 1): value for i, value in enumerate(getVehiclePlate)}
            return render_template('index-teacher.html', data=vehicleDict)

        elif role == 'admin':
            try:
                options = db.getVehicle(session['username'])
            except Exception as e:
                return render_template('error.html', error_message=str(e))

            return render_template('index-admin.html', options=options)

        else:
            return render_template('error.html', error_message="Invalid role")

@app.route('/signin', methods = ['POST', 'GET'])
def signin():
    if(request.method == 'POST'):
        user = User()
        success_flag = user.login()
        if(success_flag):
            return redirect('/')
        else:
            return redirect('/')


@app.route('/setting', methods=['GET', 'POST'])
def setting():
    role = db.getRole(session['username'])
    if role == "teacher":
        options = db.getVehicle(session['username'])
        l_data = {}
        if request.method == 'POST':
            l_data = {}
            #print("Called")
            plate = request.form.get("vehicle-select")
            cls = request.form.get("class")
            subclass = request.form.get("subclass")
            #print(f"cls : {cls}")
            #print(f"subcls : {subclass}")
            #print(f"plate : {plate}")
            data = db.getClass(cls, subclass)
            for i in data:
                l_data[i['password']] = [i['display'], i['checkbox']]            
            return render_template('setting.html', options=options, data=l_data, merge=f"{cls}-{subclass}", class_hidden=f"{cls}-{subclass}", plate_hidden=plate)
        
        return render_template('setting.html', options=options, data=l_data)
    else:
        return redirect('/')

@app.route('/sendchb', methods=['POST'])
def sendchb():
    if request.method == 'POST':
        selected_checkboxes = []

        for key in request.form:
            if key.startswith('status_checkbox_') and request.form[key] == 'on':
                checkbox_number = key.replace('status_checkbox_', '')
                selected_checkboxes.append(checkbox_number)

        plate_hidden = request.form.get('plate-hidden')
        class_hidden = request.form.get('class-hidden')

        #print(f'Selected checkboxes: {selected_checkboxes}')
        new_member = []
        for i in selected_checkboxes:
            user = db.get_name_from_number(i)
            new_member.append(user)
        if new_member:
            db.add_members_to_vehicle(plate_hidden, new_member)
        #print(f'Plate hidden value: {plate_hidden}')
        #print(f'Class hidden value: {class_hidden}')
    return redirect('/setting')

     
     
@app.route('/addTeacher', methods=["POST"])
def addTeacher():
    if(request.method == "POST"):
        user = User()
        user.addTeacher()
        return redirect('/')

@app.route('/addVehicle', methods=["POST"])
def addVehicle():
    if(request.method == "POST"):
        user = User()
        user.addVehicle()
        return redirect('/')


@app.route('/upload_students', methods=['POST'])
def upload_students():
    if request.method == "POST":
        if 'fileUpload' not in request.files:
            return "No file part"

        file = request.files['fileUpload']

        if not file:
            return "No selected file"

        filename = secure_filename(file.filename)

        allowed_extensions = {'csv', 'xlsx', 'xls'}
        if '.' not in filename or filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
            return "Invalid file format"

        try:
            db.addStudent(file)

            return redirect('/')
        except Exception as e:
            return f"Error processing file: {str(e)} \n Contact Admin !!!"
@app.route('/selectVehicle', methods=["POST"])
def selectVehicle():
    if request.method == "POST":
        getVehiclePlate = db.getVehicle(session["username"])
        vehicleDict = {str(i + 1): value for i, value in enumerate(getVehiclePlate)}
        vehicle_plate = vehicleDict[request.form.get("selectVehicleNumber")]
        data = db.getMembers(vehicle_plate=vehicle_plate)
        #print(f"members : {len(data[0])} ; up : {len(data[1])} ; down : {len(data[2])}")
        return render_template('teacher-label.html', main_content=vehicle_plate, up=str(len(data[1])), down=str(len(data[2])), unknow=str((len(data[0])-len(data[1]) - len(data[2]))), image_path = db.get_image_path(vehicle_plate))
    return redirect('/')

@app.route('/list/<item>', methods=["GET"])
def listpeople(item):
    if request.method == "GET":
        members, up, down = db.getMembers(vehicle_plate=item)
        up_members = {}
        for i in up:
            up_members[db.get_number_from_name(i)] = db.get_display_from_name(i)
        down_members = {}
        for i in down:
            down_members[db.get_number_from_name(i)] = db.get_display_from_name(i)
        unknow = db.filters(members, up, down)
        unknow_members = {}
        for i in unknow:
            unknow_members[db.get_number_from_name(i)] = db.get_display_from_name(i)
        #print(up_members)
        #print(down_members)
        #print(unknow_members) 
        return render_template('teacher-table.html', up_member=up_members, down_member=down_members, unknow_member=unknow_members)
@app.route('/up/<item>')
def up(item):
    vehicleplate, username = item.split('-')
    db.move_down_to_up(vehicleplate, username)
    return redirect('/')

@app.route('/down/<item>')
def down(item):
    vehicleplate, username = item.split('-')
    db.move_up_to_down(vehicleplate, username)
    return redirect('/')

@app.route('/logout')
def logout():
    if session:
        session.clear()
    return redirect('/')
@app.route('/upload', methods=['POST'])
def upload():
    if 'imageUpload' in request.files:
        file = request.files['imageUpload']
        #print(file)
        selected_vehicle = request.form.get("vehicle-select")
        if selected_vehicle and file.filename != '':
            upload_directory = 'static/images/'
            new_filename = secure_filename(selected_vehicle+"."+file.filename.split('.')[-1])
            file.save(os.path.join(upload_directory, new_filename))
            db.updateImg(selected_vehicle, new_filename)

            return redirect('/') 

    return 'File upload failed.'
@app.route('/deleteVehicle', methods=['POST'])
def deleteVehicle():
    if session:
        selected_vehicle = request.form.get("deleteVehicleSelect")
        db.deleteVehicle(selected_vehicle)

        return redirect('/') 

    return 'failed.'

@app.route('/deleteRole', methods=["POST"])
def deleteRole():
    if session:
        role = request.form.get("roleSelect")
        db.delete_by_role(role)
        return redirect('/')
    return redirect('/')
    return redirect('/')
if __name__ == "__main__":
    app.secret_key="anystringhere"
    app.config['SESSION_TYPE'] = 'filesystem'
    app.run(host=socket.gethostbyname(socket.gethostname()),debug=True)
