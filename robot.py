#This is where your main robot code resides. It extendeds from the BrickPi Interface File
#It includes all the code inside brickpiinterface. The CurrentCommand and CurrentRoutine are important because they can keep track of robot functions and commands. Remember Flask is using Threading (e.g. more than once process which can confuse the robot)
from sqlite3 import DataError
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
            ultra = self.get_ultra_sensor()
            print(ultra, i)
            if ultra < 20 and ultra != 0:
                self.log('UPDATE TileTable SET ' + i + ' = 1 WHERE TileID = ?')
                GLOBALS.DATABASE.ModifyQuery('UPDATE TileTable SET ' + i + ' = 1 WHERE TileID = ?', (tile,))
            else:
                GLOBALS.DATABASE.ModifyQuery('UPDATE TileTable SET ' + i + ' = 0 WHERE TileID = ?', (tile,))
            self.rotate_power_degrees_IMU(17,-90)
        '''
        ultra = self.get_ultra_sensor()
        if ultra < 20 and ultra != 0 and self.CurrentRoutine == "Searching":
            GLOBALS.DATABASE.ModifyQuery('UPDATE TileTable SET North = 1 WHERE TileID = ?', (tile,))
        else:
            GLOBALS.DATABASE.ModifyQuery('UPDATE TileTable SET North = 0 WHERE TileID = ?', (tile,))
        self.rotate_power_degrees_IMU(17,-90)
        ultra = self.get_ultra_sensor()
        if ultra < 20 and ultra != 0 and self.CurrentRoutine == "Searching":
            GLOBALS.DATABASE.ModifyQuery('UPDATE TileTable SET West = 1 WHERE TileID = ?', (tile,))
        else:
            GLOBALS.DATABASE.ModifyQuery('UPDATE TileTable SET West = 0 WHERE TileID = ?', (tile,))
        self.rotate_power_degrees_IMU(17,-90)
        ultra = self.get_ultra_sensor()
        if ultra < 20 and ultra != 0 and self.CurrentRoutine == "Searching":
            GLOBALS.DATABASE.ModifyQuery('UPDATE TileTable SET South = 1 WHERE TileID = ?', (tile,))
        else:
            GLOBALS.DATABASE.ModifyQuery('UPDATE TileTable SET South = 0 WHERE TileID = ?', (tile,))
        self.rotate_power_degrees_IMU(17,-90)
        ultra = self.get_ultra_sensor()
        if ultra < 20 and ultra != 0 and self.CurrentRoutine == "Searching":
            GLOBALS.DATABASE.ModifyQuery('UPDATE TileTable SET East = 1 WHERE TileID = ?', (tile,))
        else:
            GLOBALS.DATABASE.ModifyQuery('UPDATE TileTable SET East = 0 WHERE TileID = ?', (tile,))
        self.rotate_power_degrees_IMU(17,-90)
        '''
        return
    
    def maze_solve(self):
        GLOBALS.DATABASE.ModifyQuery('DELETE FROM TileTable')
        self.CurrentRoutine = "Searching"
        tile = 1
        startcompass = self.get_compass_IMU()
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
            self.rotate_power_heading_IMU(17,startcompass)
            if North == 0 and self.CurrentRoutine == "Searching":
                #GLOBALS.CAMERA.get_camera_colour((50,50,150),(128,128,255))
                GLOBALS.DATABASE.ModifyQuery('INSERT INTO MapMovementTable (TileID, Wall) VALUES (?,?)', (tile,"North"))
                self.move_power_until_detect(20,5)
                tile += 1
            elif North == 1 and West == 0 and self.CurrentRoutine == "Searching":
                self.rotate_power_degrees_IMU(17,-90)
                GLOBALS.DATABASE.ModifyQuery('INSERT INTO MapMovementTable (TileID, Wall) VALUES (?,?)', (tile,"West"))
                self.move_power_until_detect(20,5)
                tile += 1
            elif North == 1 and West == 1 and East == 0 and self.CurrentRoutine == "Searching":
                self.rotate_power_degrees_IMU(17,90)
                GLOBALS.DATABASE.ModifyQuery('INSERT INTO MapMovementTable (TileID, Wall) VALUES (?,?)', (tile,"East"))
                self.move_power_until_detect(20,5)
                tile += 1
            elif North == 1 and West == 1 and East == 1 and South == 0 and self.CurrentRoutine == "Searching":
                self.rotate_power_degrees_IMU(17,-1800)
                GLOBALS.DATABASE.ModifyQuery('INSERT INTO MapMovementTable (TileID, Wall) VALUES (?,?)', (tile,"South"))
                self.move_power_until_detect(20,5)
                tile += 1
            elif self.CurrentRoutine != "Searching":
                self.stop_routine()
            else:
                self.quadrant_scan(tile)

    def stop_routine(self):
        self.CurrentRoutine = "Stop"
        self.stop_all()
        return

    #moves for the specified time (seconds) and power - use negative power to reverse
    def move_power_until_detect(self, power, t, deviation=-1.5):
        self.interrupt_previous_command()
        bp = self.BP
        self.CurrentCommand = "move_power_time"
        timelimit = time.time() + t
        bp.set_motor_power(self.rightmotor, power)
        bp.set_motor_power(self.leftmotor, power + deviation)
        t = time.time()
        data = {}
        while (t < timelimit) and (self.CurrentCommand == "move_power_time"):
            if self.get_colour_sensor == "black":
                data['color'] = 'black'
                self.move_power_time(-power, elapsed)
                break
            distance = self.get_ultra_sensor
            if distance < 20 and distance != 0:
                data['distance'] = distance
                break
            elapsed = time.time() - t
        data['elapsed'] = elapsed
        self.stop_all()
        return data

# Only execute if this is the main file, good for testing code
if __name__ == '__main__':
    logging.basicConfig(filename='logs/robot.log', level=logging.INFO)
    ROBOT = Robot(timelimit=0)  #10 second timelimit before
    bp = ROBOT.BP
    GLOBALS.CAMERA = camerainterface.CameraInterface()
    GLOBALS.CAMERA.start()
    ROBOT.configure_sensors() #This takes 4 seconds
    value = GLOBALS.CAMERA.get_camera_colour((50,50,150),(128,128,255))
    print(value)
    ROBOT.safe_exit()