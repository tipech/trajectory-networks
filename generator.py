"""Randomly generate moving object trajectories in space.

Provides a generator class for the moving objects problem. Moreover, this can
be executed as a script to actually generate the data.


"""
import random, argparse, csv, os
from graphics import Point, Line, Rectangle, Text, GraphWin
from movingpoint import *
from datetime import datetime
from time import sleep



def main():
    """Run the generator with command-line parameters."""

    window = 1200

    # parser for command line arguments
    parser = argparse.ArgumentParser(
        description="Randomly generate moving objects in space.")

    # trajectories type argument: constant or random velocity
    parser.add_argument("type", choices=["constant", "random"],
        help="type of trajectories")

    # optional arguments: print/store/draw results with graphics
    parser.add_argument("-p", "--print", action="store_true",
        help="print results to console")
    parser.add_argument("-g", "--graphics", action="store_true",
        help="display graphics and draw results")
    parser.add_argument("-s", "--store", action="store_true",
        help="store data to file")
    
    # extra arguments: rate of objects, area, time
    parser.add_argument("--rate", metavar="N", type=float, default=0.1,
        help="rate of generated objects per step(default: 0.1)")
    parser.add_argument("--area", type=int, default=1000,
        help="size of generated area (default: 1000)")
    parser.add_argument("--time", type=int, default=1000,
        help="simulation time (default: 1000)")
    parser.add_argument("--seed", type=int, default=None,
        help="seed for random generator, for reproducible results")

    # extra arguments for random motion: max speed and randomness
    parser.add_argument("--max", type=float, default=2,
        help="max speed of objects (def: 2)")
    parser.add_argument("--rnd", type=float, default=0.1,
        help="percent randomness of object motion (def: 0.01)")

    args = parser.parse_args() # parse the arguments


    # check for invalid numbers
    if args.rate < 0 or args.area < 0 or args.time < 0 or args.max < 0:
        parser.error("Invalid number argument.")

    # run generator
    if args.type not in ["constant", "random"]:
        parser.error("invalid trajectory type")
    
    generator = Generator(args.rate, args.area, args.time, args.graphics,
        args.seed, window, args.type, args.max, args.rnd)

    if args.print:  # print results
        print(generator)
        
    if args.store:
        generator.export_data()



class Generator():
    """Randomly generate moving point objects in a defined space.

    Class that handles the common methods required for the generation,
    regardless of trajectory type (constant or random).
    

    """


    def __init__(self, object_rate, area, time, draw, seed, window,
        movement_type, max_speed, rnd):
        """Prepare space and initialize generation of new objects and data"""

        self.object_rate = object_rate
        self.area = area
        self.window = window
        self.scale = window / area
        self.time = time

        self.type = movement_type
        self.max_speed = max_speed
        self.rnd = rnd

        self.win = None         # controller for graphics window
        self.objects_dict = {}  # will hold the generated objects
        self.time_data = []     # will hold output data indexed by time

        if seed != None:
            random.seed(seed)   # seed random number generator
        else:
            random.seed()


        # simulation pre-execution, to make sure points have spread in space
        for t in range(0, time):
            
            # generate and move points, don't draw anything
            self.generate_objects(False)
            self.move_objects(False)                    

        # actual simulation's about to start, draw if required
        if draw:

            # setup window
            self.win = GraphWin("Moving Points", self.window, self.window)

            # draw objects
            for point in self.objects_dict.values():
                point.draw(self.scale, self.win)

        # run actual simulation
        for t in range(0, time):
            
            # generate and move points
            self.generate_objects(draw)
            self.move_objects(draw)

            # append an entry with all point positions for this moment
            self.time_data.append([(p.pos_x, p.pos_y, p.id) for p in
                self.objects_dict.values() if not p.out_of_bounds])



    def generate_objects(self, draw_objects):
        """Generate all the moving objects"""

        # if rate is more than one
        if self.object_rate >= 1:
            for i in range(0, int(self.object_rate)):
                
                # generate and store object
                new_object = self._generate_single_object()
                self.objects_dict[new_object.id] = new_object

                if draw_objects:
                    new_object.draw(self.scale, self.win)
        
        # for decimal part of rate
        if random.random() < self.object_rate % 1:

            # generate and store object
            new_object = self._generate_single_object()
            self.objects_dict[new_object.id] = new_object

            if draw_objects:
                new_object.draw(self.scale, self.win)


    def move_objects(self, draw_objects):
        """Execute one motion step for all objects"""

        for point in self.objects_dict.values():
            
            # only move the points inside the area
            if not point.out_of_bounds:

                point.move()   # execute motion

                if draw_objects:
                    point.update() # update visuals

                # if movement caused point to go off bounds
                if (point.pos_x < 0 or point.pos_x > self.area or
                    point.pos_y < 0 or point.pos_y > self.area):

                    point.out_of_bounds = True
            
            # remove visuals od objects out of bounds
            elif point.out_of_bounds and draw_objects:
                point.shape.undraw()
                point.label.undraw()  

        # allow some time between drawing for smooth movement 
        if draw_objects:
            sleep(0.001)


    def export_data(self):
        """Store the saved time data as csv file"""        

        # check if data storage exists and if not, create it
        if not os.path.isdir("data"):
            os.mkdir("data")

        # open file for storage, filename is timestamp
        filename = "data/%s_%s.csv"% (self.type, datetime.now())
        with open(filename,"w+") as file:

            writer = csv.writer(file)
            writer.writerow(["timestamp", "x", "y", "id"])

            for time, entry in enumerate(self.time_data):
                for point in entry:
                    writer.writerow([time, point[0], point[1], point[2]])

        return filename


    def _generate_single_object(self):
        """Generate a single moving point object at a random edge"""

        # pick side to be generated at, 0:bottom, 1:right, 2:top, 3:left
        side = random.randint(0,3)

        # pick start position according to side
        if (side == 0): # bottom
            start_x = 0
            start_y = random.random() * self.area
        
        elif (side == 1): # right 
            start_x = self.area
            start_y = random.random() * self.area
        
        elif (side == 2): # top 
            start_x = random.random() * self.area
            start_y = 0
        
        else: # left 
            start_x = random.random() * self.area
            start_y = self.area

        # pick speed (size) and angle between 0' and 180' for velocity
        velocity_angle = math.pi * random.random()
        velocity_size = random.random() * self.max_speed

        # rotate velocity according to side in order to face inwards
        velocity_angle += side * math.pi / 2

        speed_x = velocity_size * math.cos(velocity_angle)
        speed_y = velocity_size * math.sin(velocity_angle)


        # create the object using the appropriate class
        if self.type == "constant":
            return ConstantMovingObject(start_x, start_y, speed_x, speed_y)

        elif self.type == "random":
            return RandomMovingObject(start_x, start_y, speed_x, speed_y,
                self.max_speed, self.rnd)


    def __repr__(self):
        """Convert to string."""

        s = ",\n".join(" %s: %r" % (id_, object_) # stringify dictionary
            for id_, object_ in self.objects_dict.items())        
        return("Generator(objects={%s}\n,count=%d)" %
            (s, len(self.objects_dict)))



if __name__ == "__main__":
    # Run the module with command-line parameters.
    main()