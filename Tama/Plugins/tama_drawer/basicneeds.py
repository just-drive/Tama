from datetime import datetime, timedelta
from task import task
from yapsy.IPlugin import IPlugin
import time
import os
from Plugins.basic_needs.eatingsystem import EatingSystem

class BasicNeeds(IPlugin):
    """
    The BasicNeeds object doesn't require anything to start, except for a path to Tama, or the root folder Tama is located in.
    Right now this is done by passing the information to the module with a task object generated in the __init__ of Tama, but
    in the future I would like to see plugins ask for information through tasks instead.
    """
    def __init__(self):
        """
        super().__init__() must be called by a plugin class's own __init__ or the load might not work properly.

        Tama's stats begin at maximum when Tama is initialized, and will change according to a time delta each time the 
        tick() function is run.

        There are four main stats carried by BasicNeeds currently.
        -Happiness
        -Satiation (The opposite of hunger)
        -Energy
        -Health

        These stats use 'reverse threshold dictionaries' which map certain value of Tama's core stats to certain rate variability.

        Adding more stats is possible, so if you feel inclined to modify the source, follow the four that already exist.
        """
        super().__init__()
        #Tama's stats begin at maximum when Tama is initialized, and will change each time the tick() function is run.
        self.happiness_max = self.happiness = 100
        self.satiation_max = self.satiation = 100
        self.energy_max = self.energy = 100
        self.health_max = self.health = 100
        #Tama path will be read later, as it requires info from Tama to become useful.
        self.tama_path = None

        #The thresholds for each of Tama's stats represent the lowest each stat can be before changing to the next level down.
        #These are calculated using a proportion of each stat, in order to allow scaling of Tama's stat maximums.
        self.happiness_thresholds = {
            #The happier Tama is, the more energy Tama will use,
            #and the more Tama will send happy signals
            'Ecstatic': (self.happiness_max, self.happiness_max * .8),
            'Happy': (self.happiness_max * .8, self.happiness_max * .4), 
            'Sad': (self.happiness_max * .4, self.happiness_max * .2),
            'Depressed': (self.happiness_max * .2, 0)
        }
        self.satiation_thresholds = {
            #The less hungry (more sated) Tama is, the more health will be replenished
            #and the more happy Tama will get
            #Hungry and Starving stats will deplete Tama's health
            'Full': (self.satiation_max, self.satiation_max * .8), 
            'Sated': (self.satiation_max * .8, self.satiation_max * .6), 
            'Hungry': (self.satiation_max * .6, self.satiation_max * .2), 
            'Starving': (self.satiation_max * .2, 0), 
        }
        self.energy_thresholds = {
            #The more energetic Tama is, the more hungry Tama will get
            #and the more Tama will move around
            'Excited': (self.energy_max, self.energy_max * .7), 
            'Playful': (self.energy_max * .7, self.energy_max * .4), 
            'Tired': (self.energy_max * .4, self.energy_max * .1), 
            'Sleeping': (self.energy_max * .1, 0)
        }
        self.health_thresholds = {
            #Health will go down if Tama is Hungry, Starving, or Depressed
            'Pristeen': (self.health_max, self.health_max * .7), 
            'Healthy': (self.health_max * .7, self.health_max * .4), 
            'Unhealthy': (self.health_max * .4, self.health_max * .2), 
            'Sick': (self.health_max * .2, 0)
        }

        #A time delta will be used to calculate stats when the tick function is ran. 
        self.time_delta = None
        self.time_of_previous_tick = datetime.today()

        #The units for each rate is '{stat name} per second'
        #Each stat has a rate that will be calculated based on the current stats of Tama
        self.happiness_rate = None
        self.satiation_rate = None
        self.energy_rate = None
        self.health_rate = None

        #Tama will have a "mood" which is a combination of each of the above threshold values. The current mood will be stored internally, and will
        #later be sent to the animation plugin so that it can be represented graphically back to the user.
        self.current_mood = None

        #This path will contain the path to the food bowl that we will need in the tick function
        #If there is no "Food Bowl" folder under Tama path, we will create one.
        self.food_bowl = None

        #after getting the food bowl location, we will instanciate an eating system here.
        #this process can be seen by looking at set_tama_path
        self.eating_system = None

        return

    def check_if_alive(self):
        '''
        Returns true if Tama's health is above 0
        '''
        return True if round(self.health) > 0 else False

    def calculate_needs(self):

        #calculate time delta and update previous tick time, for use in calculating the stat change from previous tick to now.
        current_time = datetime.today()
        self.time_delta = (current_time - self.time_of_previous_tick).total_seconds()
        self.time_of_previous_tick = current_time

        #with the time_delta updated, calculate changes in mood, then update the rates and stats. Current mood will be behind current stats
        #by one tick after this function finishes, but this is okay.
        self.calc_mood()
        self.calc_rates()
        self.calc_stats()

        #if Tama dies, this will return false, and no more calculate_needs tasks will be created in the task pool
        return self.check_if_alive()

    def calc_stats(self):
        """
        This function simply multiplies the rate by time to get a solid stat value according to how long Tama has been ran.
        It also sets tolerances for the values as soon as they have been changed.

        Todo: add levels to each, if gamifying is an option, or create a leveling module that can track Tama's xp over many runs.
        """
        self.happiness += (self.time_delta * self.happiness_rate)
        if self.happiness > self.happiness_max:
            self.happiness = self.happiness_max
        elif self.happiness < 0:
            self.happiness = 0

        self.satiation += (self.time_delta * self.satiation_rate)
        if self.satiation > self.satiation_max:
            self.satiation = self.satiation_max
        elif self.satiation < 0:
            self.satiation = 0

        self.energy += (self.time_delta * self.energy_rate)
        if self.energy > self.energy_max:
            self.energy = self.energy_max
        elif self.energy < 0:
            self.energy = 0

        self.health += (self.time_delta * self.health_rate)
        if self.health > self.health_max:
            self.health = self.health_max
        elif self.health < 0:
            self.health = 0
        return
    
    def calc_rates(self):
        mood = self.current_mood
        
        #define temporary rate variables that will be used to set the class rate variables after calculations are done.
        happiness_rate = 0
        satiation_rate = 0
        energy_rate = 0
        health_rate = 0

        #Each mood value places a modifier on one or more rate values.
        #This ensures that the same mood will result in the same rates later, while also allowing interplay between moods
        
        #Happiness directly affects energy and health
        if mood.get('Conditions').get('Happiness') == "Ecstatic":
            energy_rate += -0.5
            health_rate += 0.5
        elif mood.get('Conditions').get('Happiness') == "Happy":
            energy_rate += -0.3
        elif mood.get('Conditions').get('Happiness') == "Sad":
            energy_rate += -0.5
        elif mood.get('Conditions').get('Happiness') == "Depressed":
            energy_rate += -0.8
            health_rate += -0.5

        #Satiation directly affects happiness,
        #Eating restores satiation and health
        if mood.get('Conditions').get('Satiation') == "Full":
            happiness_rate += .5
        elif mood.get('Conditions').get('Satiation') == "Sated":
            happiness_rate += .3
        elif mood.get('Conditions').get('Satiation') == "Hungry":
            happiness_rate += -.1
            health_rate += -.1
        elif mood.get('Conditions').get('Satiation') == "Starving":
            happiness_rate += -.5
            health_rate += -.5

        #Energy directly affects satiation
        if mood.get('Conditions').get('Energy') == "Excited":
            satiation_rate += -0.8
        elif mood.get('Conditions').get('Energy') == "Playful":
            satiation_rate += -0.5
        elif mood.get('Conditions').get('Energy') == "Tired":
            satiation_rate += -0.1
        elif mood.get('Conditions').get('Energy') == "Sleeping":
            satiation_rate += 0

        #Health directly affects energy and happiness
        if mood.get('Conditions').get('Health') == "Pristeen":
            energy_rate += .3
            happiness_rate += .1
        elif mood.get('Conditions').get('Health') == "Healthy":
            energy_rate += .1
        elif mood.get('Conditions').get('Health') == "Unhealthy":
            energy_rate += -.2
            happiness_rate += -.2
        elif mood.get('Conditions').get('Health') == "Sick":
            energy_rate += -.8
            happiness_rate += -.5

        #modifiers change how rates work
        if "Eating" in mood.get('Modifiers'):
            health_rate += 1
        if "Sleeping" in mood.get('Modifiers'):
            energy_rate = 0
            happiness_rate = 0
            health_rate += 1
            satiation_rate += .1

        #now that all the rates have been calculated, set class variables
        #this method needs to be called in a conistent matter, as it is where
        #rates are overwritten.
        self.happiness_rate = happiness_rate
        self.satiation_rate = satiation_rate
        self.energy_rate = energy_rate
        self.health_rate = health_rate
        return
        
    def get_current_mood(self, args):
        return self.current_mood

    def calc_mood(self, args = None):
        happiness_mood = None
        satiation_mood = None
        energy_mood = None
        health_mood = None

        #These four for loops get the current mood value for each stat, using the thresholds dictionaries defined internally.
        for key, value in self.happiness_thresholds.items():
            if value[0] >= self.happiness > value[1]:
                happiness_mood = key

        for key, value in self.satiation_thresholds.items():
            if value[0] >= self.satiation > value[1]:
                satiation_mood = key

        for key, value in self.energy_thresholds.items():
            if value[0] >= self.energy > value[1]:
                energy_mood = key

        for key, value in self.health_thresholds.items():
            if value[0] >= self.health > value[1]:
                health_mood = key

        if self.current_mood is not None:
            if self.current_mood.get('Modifiers') is not None:
                modifiers = self.current_mood.get('Modifiers')
        else:
            modifiers = []
        #Zeroes cause the above for loops to not assign a key to a mood, if so, default to lowest mood
        self.current_mood = {
            "Conditions": {
                "Happiness": happiness_mood if happiness_mood is not None else 'Depressed', 
                "Satiation": satiation_mood if satiation_mood is not None else 'Starving', 
                "Energy": energy_mood if energy_mood is not None else 'Sleeping', 
                "Health": health_mood if health_mood is not None else 'Sick'
            },
            "Stats": {
                "Happiness": self.happiness, 
                "Satiation": self.satiation,
                "Energy": self.energy, 
                "Health": self.health
            },
            "Max": {
                "Happiness": self.happiness_max, 
                "Satiation": self.satiation_max,
                "Energy": self.energy_max, 
                "Health": self.health_max
            },
            "Modifiers": modifiers
        }
        return self.current_mood
    
    def calc_mood_override(self,args=None):
        if arg[0] == False:
            return None
        
        self.current_mood = {
            "Conditions": {
                "Happiness": 'Estatic', 
                "Satiation": 'Full', 
                "Energy": 'Excited', 
                "Health": 'Pristeen'
            },
            "Stats": {
                "Happiness": self.happiness_max, 
                "Satiation": self.satiation_max,
                "Energy": self.energy_max, 
                "Health": self.health_max
            },
            "Max": {
                "Happiness": self.happiness_max, 
                "Satiation": self.satiation_max,
                "Energy": self.energy_max, 
                "Health": self.health_max
            },
            "Modifiers": []
        }
        return None
   


    def add_stat_after_seconds(self, args):
        """
        This is a task method.

        This method sits in the task pool for a certain number of seconds. Args is a list that looks like:
        args[0] = Stat you wish to modify (Either "Happiness", "Satiations", "Energy", "Health")
        args[1] = Amount you wish to modify the stat by (can be negative and/or float value)
        args[2] = The amount of time until this task takes effect, in seconds.
        args[3] = a datetime.today() call, which must be used when the task is created.
        """
        time_delta = datetime.today() - args[3]
        if time_delta >= timedelta(seconds = args[2]):
            if args[0] == "Happiness":
                self.happiness += args[1]
            elif args[0] == "Satiation":
                self.satiation += args[1]
            elif args[0] == "Energy":
                self.energy += args[1]
            elif args[0] == "Satiation":
                self.health += args[1]
            #This line is needed, or this method will be called repeatedly
            #due to its position in the task handling section.
            self.calculate_needs()
        return

    def set_food_bowl(self, path):
        for folder in os.scandir(path):
            if folder.is_dir():
                if folder.name == "Food Bowl":
                    self.food_bowl = folder.path
        if self.food_bowl is None:
            os.mkdir(os.path.join(self.tama_path, "Food Bowl"))
            self.food_bowl = os.path.join(self.tama_path, "Food Bowl")
        return

    def get_tama_path(self, path):
        """
        This is a task method.

        It recieves the path to the directory where Tama.py resides, and then:
        - Sets the path in BasicNeeds
        - Either finds or creates the food bowl
        - Instanciates the eating system
        """
        self.tama_path = path
        self.set_food_bowl(self.tama_path)
        self.eating_system = EatingSystem(self.food_bowl)
        #This task can safely be removed once it is complete
        return

    def work_task(self, task):
        if task.is_done():
            #This bit means a task that is done has been received.
            #So call the function in the task with the result to work with it.
            #Then set the task for removal
            getattr(self, task.get_func())(task.get_result())
            task.set_result('REMOVE')
        else:
            #This bit means a task needs to be done, and this method
            #might need to repackage the task so it gets returned.
            task.set_result(getattr(self, task.get_func())(task.get_args()))
            task.set_done(True)
            if task.get_requires_feedback():
                sender = task.get_sender()
                task.set_sender(task.get_plugin())
                task.set_plugin(sender)
            else:
                task.set_result('REMOVE')
        return task

    def tick(self, task_pool):
        """
        This method is run every time this plugin is activated, and should be treated as an entry point to the module.
        You've received a task pool called task_pool. Look through the task pool for stuff you can do. schedule tasks for them, or otherwise process them,
        and put any number of new tasks in the task_pool if you need something else done.


        """
        
        #This bit is called first and until self.tama_path exists,
        #Some form of this statement can be used to get startup values
        #That couldn't have been included in the __init__ call.
        if self.tama_path is None:
            for idx in task.find_tasks('Basic Needs', task_pool):
                item = task_pool.pop(idx)
                task_pool.insert(idx, self.work_task(item))
            if self.tama_path is None:
                task_pool.insert(0, task('Basic Needs', True, 'Tama', 'get_tama_path', []))
            return task_pool

        #Now take care of eating, Tama cannot eat while sleeping.
        if self.current_mood is not None:
            if self.current_mood.get('Conditions').get('Energy') != 'Sleeping':
                if self.current_mood.get('Conditions').get('Satiation') == 'Sated' \
                or self.current_mood.get('Conditions').get('Satiation') == 'Hungry' \
                or self.current_mood.get('Conditions').get('Satiation') == 'Starving':
                    prev_hunger = self.satiation
                    self.satiation += self.eating_system.eat()

                    #if satiation didn't go up after the eat call, Tama is not eating,
                    #and if it did, tama is eating.
                    if self.satiation <= prev_hunger:
                        if 'Eating' in self.current_mood.get('Modifiers'):
                            self.current_mood.get('Modifiers').remove('Eating')
                        #Tama will only think of food when hungry or starving.
                        if ('Hungry' or 'Starving' in self.current_mood.get('Conditions').get('Satiation')) \
                            and ('Thinking_of_Food' not in self.current_mood.get('Modifiers')):
                            self.current_mood.get('Modifiers').append('Thinking_of_Food')
                    else:
                        if 'Thinking_of_Food' in self.current_mood.get('Modifiers'):
                            self.current_mood.get('Modifiers').remove('Thinking_of_Food')
                            self.current_mood.get('Modifiers').append('Eating')

                    #finally make sure satiation completes within bounds
                    if self.satiation > self.satiation_max:
                        self.satiation = self.satiation_max
            else:
                #This means Tama is sleeping, if this is the first tick he started sleeping, create a task to wake him up later
                sleeping_benefit = task('Basic Needs', False, 'Basic Needs', 'add_stat_after_seconds', ['Energy', self.energy_max*.9, 5, datetime.today()])
                #add the sleeping benefit once if Tama falls asleep, it will take effect after a certain number of seconds
                sleep_flag = True
                idxlist = task.find_tasks('Basic Needs', task_pool)
                for idx in idxlist:
                    item = task_pool[idx]
                    if item.get_func() == 'add_stat_after_seconds':
                        sleep_flag = False
                if sleep_flag:
                    #Only append this task if it's not already in the task pool
                    task_pool.append(sleeping_benefit)
                
            
        """
        Now for taking care of the task_pool, starting off by calculating needs
        """
        if self.calculate_needs():
            idxlist = task.find_tasks('Basic Needs', task_pool)
            for idx in idxlist:
                item = task_pool.pop(idx)
                task_pool.insert(idx, self.work_task(item))
            return task_pool
        #If self.calculate_needs() returns false, then tama dies, and this is all that can be run.
        else:
            idxlist = task.find_tasks('Basic Needs', task_pool)
            for idx in idxlist:
                task_pool.pop(idx)
            task_pool.append(
                task('Basic Needs', 
                     False, 
                     'CLI', 
                     'print_death_message', 
                     ['Tama has died. Please take better care of him next time...', 'Please restart the program to revive Tama.']
                ))
            return task_pool
    