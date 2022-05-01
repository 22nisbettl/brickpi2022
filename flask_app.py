from flask import Flask, render_template, session, request, redirect, flash, url_for, jsonify, Response, logging
from itsdangerous import JSONWebSignatureSerializer
from interfaces import databaseinterface
import global_vars as GLOBALS #load global variables
import logging, time
#from datetime import *
try:
    import robot #robot is class that extends the brickpi class
    from interfaces import camerainterface, soundinterface, brickpiinterface
except:
    print("Failed")

#Creates the Flask Server Object
app = Flask(__name__); app.debug = True
SECRET_KEY = 'my random key can be anything' #this is used for encrypting sessions
app.config.from_object(__name__) #Set app configuration using above SETTINGS
logging.basicConfig(filename='logs/flask.log', level=logging.INFO)
GLOBALS.DATABASE = databaseinterface.DatabaseInterface('databases/RobotDatabase.db', app.logger)

#Log messages
def log(message):
    app.logger.info(message)
    return

#create a login page
@app.route('/', methods=['GET','POST'])
def login():
    if 'UserID' in session:
        return redirect('/dashboard')
    message = ""
    if request.method == "POST":
        Email = request.form.get("Email")
        Userdetails = GLOBALS.DATABASE.ViewQuery("SELECT * FROM UserTable WHERE Email = ?", (Email,))
        log(Userdetails)
        if Userdetails:
            User = Userdetails[0] #get first row in results
            if User['Password'] == request.form.get("Password"):
                session['UserID'] = User['UserID']
                session['Permission'] = User['Permission']
                session['FirstName'] = User['FirstName']
                session['Surname'] = User['Surname']
                return redirect('/dashboard')
            '''else:
                message = "Login Unsuccessful"
                password = GLOBALS.DATABASE.ViewQuery("SELECT password FROM UserTable WHERE Email = ?", ('admin@admin',))
                print(password)'''
        else:
            message = "Login Unsuccessful"
    return render_template('login.html', data = message)    

# Load the ROBOT
@app.route('/robotload', methods=['GET','POST'])
def robotload():
    sensordict = None
    if not GLOBALS.CAMERA:
        log("LOADING CAMERA")
        try:
            GLOBALS.CAMERA = camerainterface.CameraInterface()
            GLOBALS.CAMERA.start()
        except:
            print("Camera is a NO LOAD")
    if not GLOBALS.ROBOT: 
        log("LOADING THE ROBOT")
        try:
            GLOBALS.ROBOT = robot.Robot(20, app.logger)
            GLOBALS.ROBOT.configure_sensors() #defaults have been provided but you can 
            GLOBALS.ROBOT.reconfig_IMU()
        except:
            print("Robot is a NO LOAD")
    if not GLOBALS.SOUND:
        log("LOADING THE SOUND")
        try:
            GLOBALS.SOUND = soundinterface.SoundInterface()
            GLOBALS.SOUND.say("I am ready")
        except:
            print("Sound is a NO LOAD")
    if GLOBALS.ROBOT:
        sensordict = GLOBALS.ROBOT.get_all_sensors()
    else:
        sensordict = {}
    return jsonify(sensordict)

# ---------------------------------------------------------------------------------------
# Dashboard
@app.route('/dashboard', methods=['GET','POST'])
def robotdashboard():
    if not 'UserID' in session:
        return redirect('/')
    enabled = int(GLOBALS.ROBOT != None)
    MissionID = GLOBALS.DATABASE.ViewQuery('SELECT MissionID FROM MissionTable WHERE EndTime IS NULL')
    session['MissionID'] = MissionID
    print(session['MissionID'])
    return render_template('dashboard.html', robot_enabled = enabled)

@app.route('/admin', methods=["POST","GET"])
def admin():
    UserResults = GLOBALS.DATABASE.ViewQuery('SELECT * FROM UserTable')
    MissionResults = GLOBALS.DATABASE.ViewQuery('SELECT * FROM MissionTable')
    TileResults = GLOBALS.DATABASE.ViewQuery('SELECT * FROM TileTable')
    MovementResults = GLOBALS.DATABASE.ViewQuery('SELECT * FROM MovementHistoryTable')
    if 'Permission' in session:
        if session['Permission'] != 'admin':
            return redirect('/dashboard')
    else:
        return redirect('/')
    return render_template('admin.html', UserData = UserResults, MissionData = MissionResults, TileData = TileResults, MovementData = MovementResults)

@app.route('/maze', methods=['GET','POST'])
def maze():
    data = {}
    GLOBALS.ROBOT.maze_solve(session['MissionID'])
    return data

@app.route('/mazestop', methods=['GET','POST'])
def mazestop():
    data = {}
    GLOBALS.ROBOT.stop_routine()
    return data

#Used for reconfiguring IMU
@app.route('/reconfig_IMU', methods=['GET','POST'])
def reconfig_IMU():
    if GLOBALS.ROBOT:
        GLOBALS.ROBOT.reconfig_IMU()
        sensorconfig = GLOBALS.ROBOT.get_all_sensors()
        return jsonify(sensorconfig)
    return jsonify({'message':'ROBOT not loaded'})

#calibrates the compass but takes about 10 seconds, rotate in a small 360 degrees rotation
@app.route('/compass', methods=['GET','POST'])
def compass():
    data = {}
    if GLOBALS.ROBOT:
        data['message'] = GLOBALS.ROBOT.calibrate_imu(10)
    return jsonify(data)

@app.route('/sensors', methods=['GET','POST'])
def sensors():
    data = {}
    if GLOBALS.ROBOT:
        data = GLOBALS.ROBOT.get_all_sensors()
    return jsonify(data)

@app.route('/forward', methods=['GET','POST'])
def forward():
    data = {}
    if GLOBALS.ROBOT:
        start_time = time.time()
        data['elapsedtime'] = GLOBALS.ROBOT.move_forward(10)
        data['heading'] = GLOBALS.ROBOT.get_orientation_IMU()
        GLOBALS.ROBOT.recordaction(session['MissionID'], "Left and Right", "20", data['heading'], start_time, data['elapsedtime'], "Robot manually moved forward")
    return jsonify(data)

@app.route('/reverse', methods=['GET','POST'])
def reverse():
    data = {}
    if GLOBALS.ROBOT:
        start_time = time.time()
        data['elapsedtime'] = GLOBALS.ROBOT.move_power(-20, 3.17)
        data['heading'] = GLOBALS.ROBOT.get_orientation_IMU()
        GLOBALS.ROBOT.recordaction(session['MissionID'], "Left and Right", "-20", data['heading'], start_time, data['elapsedtime'], "Robot manually reversed")
    return jsonify(data)

@app.route('/stopall', methods=['GET','POST'])
def stopall():
    if GLOBALS.ROBOT:
        GLOBALS.ROBOT.stop_all()
    return jsonify()

@app.route('/shootup', methods=['GET','POST'])
def shootup():
    if GLOBALS.ROBOT:
        start_time = time.time()
        GLOBALS.ROBOT.spin_medium_motor(360)
        GLOBALS.ROBOT.spin_medium_motor(360)
        GLOBALS.ROBOT.spin_medium_motor(360)
        GLOBALS.ROBOT.recordaction(session['MissionID'], "Medium", "360", GLOBALS.ROBOT.get_orientation_IMU(), start_time, 0, "Manually shot cannon upwards")
    return jsonify()

@app.route('/shootdown', methods=['GET','POST'])
def shootdown():
    if GLOBALS.ROBOT:
        start_time = time.time()
        GLOBALS.ROBOT.spin_medium_motor(-360)
        GLOBALS.ROBOT.spin_medium_motor(-360)
        GLOBALS.ROBOT.spin_medium_motor(-360)
        GLOBALS.ROBOT.recordaction(session['MissionID'], "Medium", "-360", GLOBALS.ROBOT.get_orientation_IMU(), start_time, 0, "Manually shot cannon downwards")
    return jsonify()

@app.route('/left', methods=['GET','POST'])
def left():
    if GLOBALS.ROBOT:
        starttime = time.time()
        GLOBALS.ROBOT.rotate_left(90)
        #GLOBALS.ROBOT.rotate_power_degrees_IMU(17,-90)
        finish_rotate_time = starttime - time.time()
        GLOBALS.ROBOT.recordaction(session['MissionID'], "Left and Right", "17", GLOBALS.ROBOT.get_orientation_IMU(), starttime, finish_rotate_time, "Rotated -90 degrees")
    return jsonify()

@app.route('/right', methods=['GET','POST'])
def right():
    if GLOBALS.ROBOT:
        starttime = time.time()
        GLOBALS.ROBOT.rotate_power_degrees_IMU(17,90)
        finish_rotate_time = starttime - time.time()
        GLOBALS.ROBOT.recordaction(session['MissionID'], "Left and Right", "17", GLOBALS.ROBOT.get_orientation_IMU(), starttime, finish_rotate_time, "Rotated 90 degrees")
    return jsonify()

@app.route('/sensorview', methods=['GET','POST'])
def sensorview():
    data = None
    if GLOBALS.ROBOT:
        data = GLOBALS.ROBOT.get_all_sensors()
    else:
        return redirect('/dashboard')
    return render_template("sensors.html", data=data)

@app.route('/mission', methods=['GET','POST'])
def mission():
    data = None
    NonMiss = GLOBALS.DATABASE.ViewQuery('SELECT * FROM MissionTable WHERE Completed = 0')
    if request.method == "POST":
        query = request.form.get('query')
        if query == 'create':
            UserID = session["UserID"]
            Notes = request.form.get('notes')
            Location = request.form.get('location')
            StartTime = datetime.now()
            GLOBALS.DATABASE.ModifyQuery('INSERT INTO MissionTable (Location, Notes, UserID, StartTime, Completed) VALUES (?,?,?,?,0)', (Location, Notes, UserID, StartTime))
        elif query == 'complete':
            completemission = request.form.getlist('selectedmissions')
            for mission in completemission:
                endtime = datetime.now()
                GLOBALS.DATABASE.ModifyQuery('UPDATE MissionTable SET Completed = 1, EndTime = ? WHERE MissionID = ?', (endtime, mission))
                misid = session['MissionID']
                print(misid)
    return render_template("mission.html", NonMiss = NonMiss)

@app.route('/sounds', methods=['GET','POST'])
def sounds():
    speaker = False
    if request.method == 'POST':
        try:
            GLOBALS.SOUND = soundinterface.SoundInterface()
            speaker = True
            song = request.form.get('song')
            if song == 'None':
                pass
            else:
                log(song)
                GLOBALS.SOUND.load_mp3("static/music/" + song + ".mp3")
                GLOBALS.SOUND.play_music(1)
                GLOBALS.SOUND.set_volume(1)
        except:
            speaker = False
    return redirect('/dashboard')

@app.route('/stopsounds', methods=['GET','POST'])
def stopsounds():
    if request.method == 'POST':
        GLOBALS.SOUND.stop_music()
    return jsonify()

# -----------------------------------------------------------------------------------
# CAMERA CODE-----------------------------------------------------------------------
# Continually gets the frame from the pi camera
def videostream():
    """Video streaming generator function."""
    while True:
        if GLOBALS.CAMERA:
            frame = GLOBALS.CAMERA.get_frame()
            if frame:
                yield (b'--frame\r\n'
                        b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n') 
            else:
                return '', 204
        else:
            return '', 204 

#embeds the videofeed by returning a continual stream as above
@app.route('/videofeed')
def videofeed():
    log("READING CAMERA")
    if GLOBALS.CAMERA:
        """Video streaming route. Put this in the src attribute of an img tag."""
        return Response(videostream(), mimetype='multipart/x-mixed-replace; boundary=frame') 
    else:
        return '', 204
        
#----------------------------------------------------------------------------
#Shutdown the robot, camera and database
def shutdowneverything():
    log("SHUT DOWN EVERYTHING")
    if GLOBALS.CAMERA:
        GLOBALS.CAMERA.stop()
    if GLOBALS.ROBOT:
        GLOBALS.ROBOT.safe_exit()
    GLOBALS.CAMERA = None; GLOBALS.ROBOT = None; GLOBALS.SOUND = None
    return

#Ajax handler for shutdown button
@app.route('/robotshutdown', methods=['GET','POST'])
def robotshutdown():
    shutdowneverything()    
    return jsonify({'message':'robot shutdown'})

#Shut down the web server if necessary
@app.route('/shutdown', methods=['GET','POST'])
def shutdown():
    shutdowneverything()
    func = request.environ.get('werkzeug.server.shutdown')
    func()
    return jsonify({'message':'Shutting Down'})

@app.route('/logout')
def logout():
    shutdowneverything()
    session.clear()
    return redirect('/')

#---------------------------------------------------------------------------
#main method called web server application
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True) #runs a local server on port 5000