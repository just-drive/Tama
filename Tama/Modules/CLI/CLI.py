from datetime import datetime, timedelta
import asyncio

class CLI:
    def __init__(self):
        return

    def tick(self, task):
        return getattr(self, task.get_func())(task.get_args())

    def print_welcome(self, args):
        print('Welcome to Tama')
        return 'EXIT TAMA'

    def print_messages(self, args):
        for arg in args:
            print(arg)
        return None

    def take_input(self, args):
        return task(input("Module Name: "), 
                    input("Module Function: "), 
                    [int(e) if e.isdigit() else e for e in 
                     input("Comma Separated Arguments: ")
                     .replace(', ', ',')
                     .split(',')])