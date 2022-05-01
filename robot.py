#This is where your main robot code resides. It extendeds from the BrickPi Interface File
#It includes all the code inside brickpiinterface. The CurrentCommand and CurrentRoutine are important because they can keep track of robot functions and commands. Remember Flask is using Threading (e.g. more than once process which can confuse the robot)
from sqlite3 import DataError
from tracemalloc import start
from urllib.request import DataHandler
from interfaces.brickpiinterface import *
from interfaces import camerainterface
import global_vars as GLOBALS
import logging

class Robot(BrickPiInterface):
    
    def __init__(self, timelimit=10, logger=logging.getLogger()):
        super().__init__(timelimit, logger)
        self.CurrentCommand = "stop" #use this to stop or start functions
        self.CurrentRoutine = "stop" #use this stop or start routines
        return
        
    #Create a function to move time and power which will stop if colour is detected or wall has been found
    def quadrant_scan(self, tile):
        direction = ["North","West","South","East"]
        for i in direction:
            if self.CurrentRoutine != 'Searching':
                self.stop_routine()
            self.search_harmed((14,143,134),(17,145,134))
            ultra = self.get_ultra_sensor()
            print(ultra, i)
            if ultra < 20 and ultra != 0:
                self.log('UPDATE TileTable SET ' + i + ' = 1 WHERE TileID = ?')
                GLOBALS.DATABASE.ModifyQuery('UPDATE TileTable SET ' + i + ' = 1 WHERE TileID = ?', (tile,))
            else:
                GLOBALS.DATABASE.ModifyQuery('UPDATE TileTable SET ' + i + ' = 0 WHERE TileID = ?', (tile,))
            start_rotate_time = time.time()
            self.rotate_power_degrees_IMU(17,-90)
            finish_rotate_time = start_rotate_time - time.time()
            self.recordaction((self.missionid), "Left and Right", "17", (self.get_orientation_IMU()), start_rotate_time, finish_rotate_time, "Rotated -90 degrees")
        return
    
    def maze_solve(self, missionid):
        GLOBALS.DATABASE.ModifyQuery('DELETE FROM TileTable')
        self.missionid = missionid
        self.CurrentRoutine = "Searching"
        tile = 1
        time.sleep(2)
        orient = self.get_orientation_IMU()[0]
        print(orient)
        while self.CurrentRoutine == "Searching":
            GLOBALS.DATABASE.ModifyQuery('INSERT INTO TileTable (TileID, North, West, South, East) VALUES (?,0,0,0,0)', (tile,))
            self.quadrant_scan(tile)
            walls = GLOBALS.DATABASE.ViewQuery('SELECT * FROM TileTable WHERE TileID = ?', (tile,))
            tilewalls = walls[0]
            #0 means no wall
            #1 means wall
            North = tilewalls['North']
            West = tilewalls['West']
            South = tilewalls['South']
            East = tilewalls['East']
            print(North, West, South, East)
            start_rotate_time = time.time()
            self.rotate_power_heading_IMU(17,orient)
            finish_rotate_time = start_rotate_time - time.time()
            self.recordaction(self.missionid, "Left and Right", "17", self.get_orientation_IMU(), start_rotate_time, finish_rotate_time, "Rotated to beginning heading")
            if North == 0 and self.CurrentRoutine == "Searching":
                #camval = GLOBALS.CAMERA.get_camera_colour((50,50,150),(128,128,255)) Red detection
                self.search_harmed((14,143,134),(17,145,134)) #Yeloow detection
                print("Going North")
                self.move_power_until_detect(20,5)
                tile += 1
            elif North == 1 and West == 0 and self.CurrentRoutine == "Searching":
                starttime = time.time()
                self.rotate_power_degrees_IMU(17,-90)
                finish_rotate_time = start_rotate_time - time.time()
                self.recordaction(self.missionid, "Left and Right", "17", self.get_orientation_IMU(), starttime, finish_rotate_time, "Rotated -90 degrees")
                self.search_harmed((14,143,134),(17,145,134))
                print("Going West")
                self.move_power_until_detect(20,5)
                tile += 1
            elif North == 1 and West == 1 and East == 0 and self.CurrentRoutine == "Searching":
                starttime = time.time()
                self.rotate_power_degrees_IMU(17,90)
                finish_rotate_time = start_rotate_time - time.time()
                self.recordaction(self.missionid, "Left and Right", "17", self.get_orientation_IMU(), starttime, finish_rotate_time, "Rotated 90 degrees")
                self.search_harmed((14,143,134),(17,145,134))
                print("Going East")
                self.move_power_until_detect(20,5)
                tile += 1
            elif North == 1 and West == 1 and East == 1 and South == 0 and self.CurrentRoutine == "Searching":
                starttime = time.time()
                self.rotate_power_degrees_IMU(17,-180)
                finish_rotate_time = start_rotate_time - time.time()
                self.recordaction(self.missionid, "Left and Right", "17", self.get_orientation_IMU(), starttime, finish_rotate_time, "Rotated -180 degrees")
                self.search_harmed((14,143,134),(17,145,134))
                print("Going South")
                self.move_power_until_detect(20,5)
                tile += 1
            elif self.CurrentRoutine != "Searching":
                self.stop_routine()
            else:
                self.quadrant_scan(tile)
            start_rotate_time = time.time()
            self.rotate_power_heading_IMU(17,orient)
            finish_rotate_time = start_rotate_time - time.time()
            self.recordaction(self.missionid, "Left and Right", "17", self.get_orientation_IMU(), start_rotate_time, finish_rotate_time, "Rotated to beginning heading")
        return

    def stop_routine(self):
        self.CurrentRoutine = "Stop"
        self.stop_all()
        return

    def recordaction(self, missionid, motor, power, orientation, starttime, elapsedtime, typetext):
        GLOBALS.DATABASE.ModifyQuery('INSERT INTO MovementHistoryTable (MissionID, Motor, Power, Orientation, StartTime, ElapsedTime, Type) VALUES (?,?,?,?,?,?,?)', (missionid, motor, power, orientation, starttime, elapsedtime, typetext))
        return

    def search_harmed(self, low, high):
        print("Checking for coloured pixels within range")
        camval = GLOBALS.CAMERA.get_camera_colour(low, high)
        if camval == "True":
            self.spin_medium_motor(-360)
            self.spin_medium_motor(-360)
            self.spin_medium_motor(-360)
            self.recordaction(self.missionid, "Medium", "-360", self.get_orientation_IMU(), time.time(), 0, "Shot cannon using medium motor. Victim Found!")
        return

    #moves for the specified time (seconds) and power - use negative power to reverse
    def move_power_until_detect(self, power, t, deviation=-0.8):
        self.interrupt_previous_command()
        self.CurrentCommand = "move_power_until_detect"
        currenttime = time.time()
        bp = self.BP
        timelimit = currenttime + t
        data = {}
        while (time.time() < timelimit) and (self.CurrentCommand == "move_power_until_detect"):
            bp.set_motor_power(self.rightmotor, power)
            bp.set_motor_power(self.leftmotor, power + deviation)
            if self.get_colour_sensor == "brown":
                data['color'] = 'brown'
                elapsedt = time.time() - currenttime
                self.move_power_time(-20,elapsedt, -(deviation))
                break
            distance = self.get_ultra_sensor()
            print(distance)
            if distance < 20 and distance not in [0,999]:
                data['distance'] = distance
                break
        elapsed = time.time() - currenttime
        data['elapsed'] = elapsed
        self.recordaction(self.missionid, "Left and Right", power, self.get_orientation_IMU(), currenttime, elapsed, ("Moved power until detect for " + str(t)))
        self.stop_all()
        return data

    def move_forward(self, distance, speed=100, power=100):
        distance = distance * 360 / (numpy.pi * 5.6)
        starttime = time.time()
        BP = self.BP
        try:
            BP.offset_motor_encoder(BP.PORT_A, BP.get_motor_encoder(BP.PORT_A)) # reset encoder A
            BP.offset_motor_encoder(BP.PORT_D, BP.get_motor_encoder(BP.PORT_D)) # reset encoder D
            BP.set_motor_limits(BP.PORT_A, power, speed)          # optionally set a power limit (in percent) and a speed limit (in Degrees Per Second)
            BP.set_motor_limits(BP.PORT_D, power, speed)      
            while True:
                BP.set_motor_position(BP.PORT_A, distance-10)
                BP.set_motor_position(BP.PORT_D, distance-10)
                time.sleep(0.02)
                if BP.get_motor_encoder(BP.PORT_D) <= distance or BP.get_motor_encoder(BP.PORT_A) <= distance:
                    break
        except KeyboardInterrupt: # except the program gets interrupted by Ctrl+C on the keyboard.
            BP.reset_all()
        elapsedtime = time.time() - starttime
        return elapsedtime

    def move_backward(self, distance, speed=100, power=100):
        distance = -distance * 360 / (numpy.pi * 5.6)
        BP = self.BP
        try:
            BP.offset_motor_encoder(BP.PORT_A, BP.get_motor_encoder(BP.PORT_A)) # reset encoder A
            BP.offset_motor_encoder(BP.PORT_D, BP.get_motor_encoder(BP.PORT_D)) # reset encoder D
            BP.set_motor_limits(BP.PORT_A, power, speed)          # optionally set a power limit (in percent) and a speed limit (in Degrees Per Second)
            BP.set_motor_limits(BP.PORT_D, power, speed)      
            while True:
                BP.set_motor_position(BP.PORT_A, distance+10)
                BP.set_motor_position(BP.PORT_D, distance+10)
                time.sleep(0.02)
                if BP.get_motor_encoder(BP.PORT_D) >= distance or BP.get_motor_encoder(BP.PORT_A) >= distance:
                    break

        except KeyboardInterrupt: # except the program gets interrupted by Ctrl+C on the keyboard.
            BP.reset_all() 

    def rotate_left(self, angle, speed=100, power=100):
        degrees = angle * 2
        BP = self.BP
        try:
            BP.offset_motor_encoder(BP.PORT_A, BP.get_motor_encoder(BP.PORT_A))
            BP.offset_motor_encoder(BP.PORT_D, BP.get_motor_encoder(BP.PORT_D))
            BP.set_motor_limits(BP.PORT_D, -power, speed)
            BP.set_motor_limits(BP.PORT_A, power, speed)      
            while True:
                BP.set_motor_position(BP.PORT_D, degrees+5)
                BP.set_motor_position(BP.PORT_A, -degrees-5)
                time.sleep(0.02)
                if BP.get_motor_encoder(BP.PORT_D) >= degrees or BP.get_motor_encoder(BP.PORT_A) <= -degrees:
                    break

        except KeyboardInterrupt:
            BP.reset_all() 

    def rotate_right(self, angle, speed=100, power=100):
        degrees = angle * 2 + 5
        BP = self.BP
        try:
            BP.offset_motor_encoder(BP.PORT_A, BP.get_motor_encoder(BP.PORT_A))
            BP.offset_motor_encoder(BP.PORT_D, BP.get_motor_encoder(BP.PORT_D))
            BP.set_motor_limits(BP.PORT_D, -power, speed)
            BP.set_motor_limits(BP.PORT_A, power, speed)      
            while True:
                BP.set_motor_position(BP.PORT_D, degrees+10)
                BP.set_motor_position(BP.PORT_A, -degrees-10)
                time.sleep(0.02)
                if BP.get_motor_encoder(BP.PORT_D) >= degrees or BP.get_motor_encoder(BP.PORT_A) <= -degrees:
                    break

        except KeyboardInterrupt:
            BP.reset_all() 

# Only execute if this is the main file, good for testing code
if __name__ == '__main__':
    logging.basicConfig(filename='logs/robot.log', level=logging.INFO)
    ROBOT = Robot(timelimit=0)
    bp = ROBOT.BP
    GLOBALS.CAMERA = camerainterface.CameraInterface()
    GLOBALS.CAMERA.start()
    ROBOT.configure_sensors()
    ROBOT.rotate_left(90)
    ROBOT.safe_exit()