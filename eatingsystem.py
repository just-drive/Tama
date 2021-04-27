import pathlib
from zipfile import ZipFile
from send2trash import send2trash
import os

class EatingSystem(object):

    def __init__(self, food_bowl):
        self.food_bowl = food_bowl
        #waste size is the configurable number used to know when a stomach is full enough
        #to create slime waste (it is in kB)
        #default waste_size is 100 mb of data. 1kB * 1024 * 100 = 100 mb
        self.waste_size = 1024 * 100
        #Number of kBs required to raise Tama's hunger by self.points_per_hunger point(s)
        self.kb_per_hunger = 100
        self.points_per_hunger = 10
        #stomach will contain files that are currently being "eaten", as well as their current size
        #tuple(file path, uneaten file size)
        self.stomach = []
        #waste will hold files that have been eaten, until reaching waste_size, in which the files will
        #be zipped up and moved to the recycling bin.
        self.waste = []
        self.regained_hunger = 0

    def add_food(self, file):
        """
        Checks both the stomach and the waste lists against an incoming file.
        If the file is in either of these lists, do nothing,
        else add the file to the stomach so it can be eaten.
        """
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
        """
        This method gathers a list of all files currently in the Food Bowl
        Begin by detecting if any files have been removed, so they can be
        removed from the stomach and waste lists.
        """
        files = []
        has_food = False
        for (dirpath, dirnames, filenames) in os.walk(self.food_bowl):
            check_files = [os.path.join(dirpath, file) for file in filenames]
            files.append(check_files)
            if len(check_files) > 0:
                for file in check_files:
                    self.add_food(file)
                if len(self.stomach) > 0:
                    has_food = True
        return has_food

    def nibble(self, food):
        """
        Consumes a small amount of food per eat() call in order to prevent this functionality from blocking work elsewhere.
        """
        food = (food[0], food[1] - self.kb_per_hunger)
        kb_consumed = self.kb_per_hunger + (food[1] if food[1] < 0 else 0)
        self.regained_hunger += kb_consumed / self.kb_per_hunger * self.points_per_hunger
        return food

    def deal_with_waste(self):
        """
        This method allows waste to exist until enough data is added to create a slime waste zip file.
        Once there is enough waste, this method moves the waste to the recycling bin.
        """
        waste_size = 0
        for waste_item in self.waste:
            waste_size += os.path.getsize(waste_item[0]) / 1024
            if waste_size > self.waste_size:
                self.zip_eaten_food()
                self.recycle_waste('Slime Waste.zip')

    def eat(self):
        """
        This function will be treated like a tick function, as it is called in the basic needs tick function
        Regained hunger is added to in small increments by the nibble function, and then returned after a
        nibble completes.

        If the previous nibble removed the last bit of data from the food, then move the food into the waste
        and deal with that waste if you need to.
        """
        self.regained_hunger = 0
        if self.check_food_bowl():
            food = self.stomach[0]
            if food[1] > 0:
                food = self.nibble(food)
                self.stomach[0] = food
            elif food[1] <= 0:
                self.waste.append(self.stomach.pop(0))

        #this try except block catches errors thrown when the user removes files from the food folder manually.
        #If an error is thrown, clear the stomach and waste lists, they will be rebuilt automatically.
        try:
            self.deal_with_waste()
        except Exception as e:
            self.stomach.clear()
            self.waste.clear()
            pass
        finally:
            return self.regained_hunger

    def zip_eaten_food(self):
        """
        This function does the ugly os.remove() deletion, but makes sure the waste item is zipped first.
        """
        waste = ZipFile('Slime Waste.zip', 'w')
        for waste_item in self.waste:
            waste.write(waste_item[0])
            os.remove(waste_item[0])
        self.waste.clear()
        waste.close()
        return
    
    def recycle_waste(self, file):
        """
        Convenience method calls send2trash with a given path
        """
        send2trash(file)
        pass