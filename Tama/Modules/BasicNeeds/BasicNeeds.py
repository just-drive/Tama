
import time

def get_dependencies(self):
    return ['']

def setup_comms(in_port, out_port):
    pass

def temp_loop(loop,hunger,happiness):
    while loop > 0:   
        happiness_state = ''
        hunger_state = ''
        time.sleep(2)
        loop = loop - 5
        happiness = happiness - 5
        hunger = hunger - 4
        if hunger == 0:
            return
        if hunger >= 80:
            hunger_state = 'MERRY'
        elif hunger >= 65 and hunger <= 80:
            hunger_state = 'FULL'
        elif hunger >= 50 and hunger <= 65:
            hunger_state = 'SECONDS?'
        elif hunger >= 25 and hunger <= 50:
            hunger_state = 'HUNGRY'
        elif hunger <= 25:
            hunger_state = 'STARVING'


        if happiness >= 80:
            happiness_state = 'VERY HAPPY'
        elif happiness >= 60 and happiness <= 80:
            happiness_state = 'SORTA HAPPY'
        elif happiness >= 40 and happiness <= 60:
            happiness_state = 'SORTA UNHAPPY'
        elif happiness >= 30 and happiness <= 40:
            happiness_state = 'UNHAPPY'
        elif happiness >= 25 and happiness <= 30:
            happiness_state = 'DEEPLY UNHAPPY'
        elif happiness <= 20:
            happiness_state = 'BEYOND UNHAPPY'
        print("" +str(loop)+". Hunger: "+str(hunger_state)+" Happiness: "+happiness_state)
    if loop == 0:
        return
    else:
        temp_loop(loop,hunger,happiness)

loop = 100
hunger = 100
happiness = 100
def run():
    print('Hello from Basic Needs')
    temp_loop(loop,hunger,happiness)
    