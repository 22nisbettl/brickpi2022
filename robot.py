#This is where your main robot code resides. It extendeds from the BrickPi Interface File
#It includes all the code inside brickpiinterface. The CurrentCommand and CurrentRoutine are important because they can keep track of robot functions and commands. Remember Flask is using Threading (e.g. more than once process which can confuse the robot)
from interfaces.brickpiinterface import *
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
        ultra = self.get_ultra_sensor()
        if ultra < 20 and ultra != 0:
            GLOBALS.DATABASE.ModifyQuery('UPDATE TileTable SET North = 1 WHERE TileID = ?', (tile,))
        else:
            GLOBALS.DATABASE.ModifyQuery('UPDATE TileTable SET North = 0 WHERE TileID = ?', (tile,))
        self.rotate_power_degrees_IMU(17,-90)
        ultra = self.get_ultra_sensor()
        if ultra < 20 and ultra != 0:
            GLOBALS.DATABASE.ModifyQuery('UPDATE TileTable SET West = 1 WHERE TileID = ?', (tile,))
        else:
            GLOBALS.DATABASE.ModifyQuery('UPDATE TileTable SET West = 0 WHERE TileID = ?', (tile,))
        self.rotate_power_degrees_IMU(17,-90)
        ultra = self.get_ultra_sensor()
        if ultra < 20 and ultra != 0:
            GLOBALS.DATABASE.ModifyQuery('UPDATE TileTable SET South = 1 WHERE TileID = ?', (tile,))
        else:
            GLOBALS.DATABASE.ModifyQuery('UPDATE TileTable SET South = 0 WHERE TileID = ?', (tile,))
        self.rotate_power_degrees_IMU(17,-90)
        ultra = self.get_ultra_sensor()
        if ultra < 20 and ultra != 0:
            GLOBALS.DATABASE.ModifyQuery('UPDATE TileTable SET East = 1 WHERE TileID = ?', (tile,))
        else:
            GLOBALS.DATABASE.ModifyQuery('UPDATE TileTable SET East = 0 WHERE TileID = ?', (tile,))
        self.rotate_power_degrees_IMU(17,-90)
        return
    
    def maze_solve(self):
        GLOBALS.DATABASE.ModifyQuery('DELETE FROM TileTable')
        self.CurrentRoutine = "Searching"
        tile = 1
        while self.CurrentRoutine == "Searching":
            GLOBALS.DATABASE.ModifyQuery('INSERT INTO TileTable (TileID, North, West, South, East) VALUES (?,0,0,0,0)', (tile,))
            self.quadrant_scan(tile)
            walls = GLOBALS.DATABASE.ViewQuery('SELECT * FROM TileTable WHERE TileID = ?', (tile,))
            tilewalls = walls[0]
            #0 means no wall
            #1 means wall
            print(tilewalls)
            North = tilewalls['North']
            West = tilewalls['West']
            South = tilewalls['South']
            East = tilewalls['East']
            print(North, West, South, East)
            if North == 0:
                self.move_power_time(20,2)
                tile += 1
            elif North == 1 and West == 0:
                self.rotate_power_degrees_IMU(17,-90)
                self.move_power_time(20,2)
                tile += 1
            elif North == 1 and West == 1 and South == 0:
                self.rotate_power_degrees_IMU(17,-180)
                self.move_power_time(20,2)
                tile += 1
            elif North == 1 and West == 1 and South == 1 and East == 0:
                self.rotate_power_degrees_IMU(17,90)
                self.move_power_time(20,2)
                tile += 1
            else:
                self.quadrant_scan(tile)

    
    def stop_routine(self):
        self.CurrentRoutine = "Stop"
        self.stop_all()
        return
    
    

    #Create a function to search for victim
    

    
    
    
    #Create a routine that will effective search the maze and keep track of where the robot has been.






# Only execute if this is the main file, good for testing code
if __name__ == '__main__':
    logging.basicConfig(filename='logs/robot.log', level=logging.INFO)
    ROBOT = Robot(timelimit=0)  #10 second timelimit before
    bp = ROBOT.BP
    ROBOT.configure_sensors() #This takes 4 seconds
    ROBOT.rotate_power_degrees_IMU(20,-90)
    start = time.time()
    limit = start + 10
    while (time.time() < limit):
        compass = ROBOT.get_compass_IMU()
        print(compass)
    sensordict = ROBOT.get_all_sensors()
    ROBOT.safe_exit()
