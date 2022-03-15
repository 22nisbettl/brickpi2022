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
    def quadrant_scan(self):
        ultra = self.get_ultra_sensor()
        if ultra < 10 and ultra != 0:
            GLOBALS.DATABASE.ModifyQuery('INSERT INTO TileTable (Straight) VALUES (1)')
        else:
            GLOBALS.DATABASE.ModifyQuery('INSERT INTO TileTable (Straight) VALUES (0)')
        self.rotate_power_degrees_IMU(17,-90)
        if ultra < 10 and ultra != 0:
            GLOBALS.DATABASE.ModifyQuery('INSERT INTO TileTable (Left) VALUES (1)')
        else:
            GLOBALS.DATABASE.ModifyQuery('INSERT INTO TileTable (Left) VALUES (0)')
        self.rotate_power_degrees_IMU(17,-90)
        if ultra < 10 and ultra != 0:
            GLOBALS.DATABASE.ModifyQuery('INSERT INTO TileTable (Back) VALUES (1)')
        else:
            GLOBALS.DATABASE.ModifyQuery('INSERT INTO TileTable (Back) VALUES (0)')
        self.rotate_power_degrees_IMU(17,-90)
        if ultra < 10 and ultra != 0:
            GLOBALS.DATABASE.ModifyQuery('INSERT INTO TileTable (Right) VALUES (1)')
        else:
            GLOBALS.DATABASE.ModifyQuery('INSERT INTO TileTable (Right) VALUES (0)')
        self.rotate_power_degrees_IMU(17,-90)
        return
    
    def maze_solve(self):
        GLOBALS.DATABASE.ModifyQuery('DELETE FROM TileTable')
        
        self.quadrant_scan()
        
    
    

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
