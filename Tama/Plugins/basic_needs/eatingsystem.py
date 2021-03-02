import pathlib
from zipfile import ZipFile
from send2trash import send2trash
import os

class EatingSystem(object):

    def __init__(self, food_bowl):
        self.food_bowl = food_bowl
        #waste size is the configurable number used to know when a stomach is full enough
        #to create slime waste (it is in kB)
        self.waste_size = 1024
        #Number of kBs required to raise Tama's hunger by 1 point
        self.kb_per_hunger_pt = 1
        #stomach will contain files that are currently being "eaten", as well as their current size
        #tuple(file path, uneaten file size)
        self.stomach = []
        #waste will hold files that have been eaten, until reaching waste_size, in which the files will
        #be zipped up and moved to the recycling bin.
        self.waste = []
        self.regained_hunger = 0

    def add_food(self, file):
        new_food_flag = True
        for food in self.stomach:
            if food[0] == file:
                new_food_flag = False
        for waste in self.waste:
            if waste[0] == file:
                new_food_flag = False
        if new_food_flag:
            self.stomach.append((file, os.path.getsize(file) / 1024))
        return
    
    def check_food_bowl(self):
        files = []
        for (dirpath, dirnames, filenames) in os.walk(self.food_bowl):
            check_files = [os.path.join(dirpath, file) for file in filenames]
            if len(check_files) > 0:
                for file in check_files:
                    self.add_food(file)
                if len(self.stomach) > 0:
                    return True
                else:
                    return False

    def nibble(self, food):
        food = (food[0], food[1] - self.kb_per_hunger_pt)
        kb_consumed = self.kb_per_hunger_pt + (food[1] if food[1] < 0 else 0)
        self.regained_hunger += kb_consumed / self.kb_per_hunger_pt
        return food

    def deal_with_waste(self):
        waste_size = 0
        for waste_item in self.waste:
            waste_size += os.path.getsize(waste_item[0]) / 1024
            if waste_size > self.waste_size:
                self.zip_eaten_food()
                self.recycle_waste('Slime Waste.zip')

    def eat(self):
        """
        This function will be treated like a tick function, as it is called in the basic needs tick function
        """
        #regained hunger will be returned to basic needs to add to Tama's hunger level
        self.regained_hunger = 0
        if self.check_food_bowl():
            food = self.stomach[0]
            if food[1] > 0:
                food = self.nibble(food)
                self.stomach[0] = food
            elif food[1] <= 0:
                self.waste.append(self.stomach.pop(0))
        self.deal_with_waste()
        return self.regained_hunger

    def zip_eaten_food(self):
        waste = ZipFile('Slime Waste.zip', 'w')
        for waste_item in self.waste:
            waste.write(waste_item[0])
            os.remove(waste_item[0])
        self.waste.clear()
        waste.close()
        return
    
    def recycle_waste(self, file):
        send2trash(file)
        pass