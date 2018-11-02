"""Creates and handles operations for an object moving in space.

Provides a class for the moving objects problem. Depending on the type of
movement (constant or random), specific subclasses are used

Classes:
  MovingObject -- 
  ConstantMovingObject -- 
  RandomMovingObject -- 
"""

from graphics import Point, Circle, Text
import math, random


class MovingObject():

    # keeps track of count, used for ids
    count = 0

    """A point object moving in space"""
    def __init__(self, start_x, start_y, speed_x, speed_y):
        
        # keep track of created points
        self.id = str(MovingObject.count)
        MovingObject.count += 1

        self.pos_x = start_x
        self.pos_y = start_y
        self.speed_x = speed_x
        self.speed_y = speed_y

        self.out_of_bounds = False



    def draw(self, scale, win):
        """Handle the necessary actions to draw the point plus it's label"""

        self.scale = scale

        self.shape = Circle(Point(self.pos_x * scale, self.pos_y * scale), 4)
        self.shape.setFill('black')
        self.label = Text(Point(self.pos_x * scale, self.pos_y * scale - 18),
            self.id)

        self.shape.draw(win)
        self.label.draw(win)


    def update(self):
        """Update the object's graphic to match it's new position"""

        # calculate the movement offset
        dX = self.pos_x * self.scale - self.shape.getCenter().getX()
        dY = self.pos_y * self.scale - self.shape.getCenter().getY()

        # apply offset to visuals
        self.shape.move(dX, dY)
        self.label.move(dX, dY)


    # def __str__(self):
    #     """Serialize object"""
    #     return self.__class__.__name__ + "'" + self.id + "'"

    def __repr__(self):
        """Represent object as string"""
        return self.__class__.__name__ + "'" + self.id + "'"



class ConstantMovingObject(MovingObject):
    """A MovingObject with a constant velocity trajectory"""
    def __init__(self, start_x, start_y, speed_x, speed_y):
        super().__init__(start_x, start_y, speed_x, speed_y)


    def move(self):
        """Move the object in straight line with the same speed"""
    
        self.pos_x += self.speed_x
        self.pos_y += self.speed_y


class RandomMovingObject(MovingObject):
    """A MovingObject with a constant velocity trajectory"""
    def __init__(self, start_x, start_y, speed_x, speed_y, max_speed, rnd):
        super().__init__(start_x, start_y, speed_x, speed_y)

        self.max_speed = max_speed
        self.rnd = rnd


    def move(self):
        """Turn the object towards a random direction and move"""
    
        # pick a random velocity in a disk with radius max_speed
        angle = 2 * math.pi * random.random()
        radius = random.random() * (self.max_speed)

        # calculate the x,y components of the speed change
        change_x = radius * math.cos(angle)
        change_y = radius * math.sin(angle)


        # apply the change, multiplied by the rnd factor
        self.speed_x += change_x * self.rnd
        self.speed_y += change_y * self.rnd

        # limit speed (size of velocity vector) to max_speed
        new_angle = math.atan2(self.speed_y, self.speed_x)
        new_radius = self.speed_x / math.cos(new_angle)
        new_speed = min(new_radius, self.max_speed) 

        # apply speed limit and speed
        self.speed_x = new_speed * math.cos(new_angle)
        self.speed_y = new_speed * math.sin(new_angle)
        self.pos_x += self.speed_x
        self.pos_y += self.speed_y