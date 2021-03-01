from datetime import datetime, timedelta
from task import task
from yapsy.IPlugin import IPlugin
import time

class BasicNeeds(IPlugin):

    def __init__(self):
        super().__init__()
        #Tama's stats begin at maximum when Tama is initialized, and will change each time the tick() function is run.
        self.happiness_max = self.happiness = 5
        self.satiation_max = self.satiation = 5
        self.energy_max = self.energy = 5
        self.health_max = self.health = 5

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
        if mood["Happiness"] == "Ecstatic":
            energy_rate += -0.5
            health_rate += 0.5
        elif mood["Happiness"] == "Happy":
            energy_rate += -0.3
        elif mood["Happiness"] == "Sad":
            energy_rate += -0.5
        elif mood["Happiness"] == "Depressed":
            energy_rate += -0.8
            health_rate += -0.5

        #Satiation directly affects happiness and health
        if mood["Satiation"] == "Full":
            happiness_rate += .5
            health_rate += 1
        elif mood["Satiation"] == "Sated":
            happiness_rate += .3
            health_rate += .3
        elif mood["Satiation"] == "Hungry":
            happiness_rate += -.1
            health_rate += -.1
        elif mood["Satiation"] == "Starving":
            happiness_rate += -.5
            health_rate += -.5

        #Energy directly affects satiation
        if mood["Energy"] == "Excited":
            satiation_rate += -0.8
        elif mood["Energy"] == "Playful":
            satiation_rate += -0.5
        elif mood["Energy"] == "Tired":
            satiation_rate += -0.1
        elif mood["Energy"] == "Sleeping":
            satiation_rate += 0

        #Health directly affects energy and happiness
        if mood["Health"] == "Pristeen":
            energy_rate += .3
            happiness_rate += .1
        elif mood["Health"] == "Healthy":
            energy_rate += .1
        elif mood["Health"] == "Unhealthy":
            energy_rate += -.2
            happiness_rate += -.2
        elif mood["Health"] == "Sick":
            energy_rate += -.8
            happiness_rate += -.5

        #now that all the rates have been calculated, set class variables
        self.happiness_rate = happiness_rate
        self.satiation_rate = satiation_rate
        self.energy_rate = energy_rate
        self.health_rate = health_rate
        
    def calc_mood(self):
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

        #Zeroes cause the above for loops to not assign a key to a mood, if so, default to lowest mood
        self.current_mood = {
            "Happiness": happiness_mood if happiness_mood is not None else 'Depressed', 
            "Satiation": satiation_mood if satiation_mood is not None else 'Starving', 
            "Energy": energy_mood if energy_mood is not None else 'Sleeping', 
            "Health": health_mood if health_mood is not None else 'Sick'
        }


    def work_task(self, task):
        return getattr(self, task.get_func())(task.get_args())

    def tick(self, task_pool):
        if self.calculate_needs():
            idxlist = task.find_tasks('Basic Needs', task_pool)
            for idx in idxlist:
                item = task_pool.pop(idx)
                task_pool.append(self.work_task(item))
            #this print statement is for debugging purposes only
            print_str = 'Happiness: {} - {}, Satiation: {} - {}, Energy: {} - {}, Health: {} - {}               '.format(
                    self.current_mood["Happiness"],
                    round(self.happiness),
                    self.current_mood["Satiation"],
                    round(self.satiation),
                    self.current_mood["Energy"],
                    round(self.energy),
                    self.current_mood["Health"],
                    round(self.health))
            print(print_str)
            return task_pool
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
    