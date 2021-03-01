from task import task
from yapsy.IPlugin import IPlugin

class CLI(IPlugin):
    def __init__(self):
        super().__init__()
        return

    def work_task(self, item):
        return getattr(self, item.get_func())(item.get_args())

    def tick(self, task_pool):
        idxlist = task.find_tasks('CLI', task_pool)
        for idx in idxlist:
            item = task_pool.pop(idx)
            task_pool.append(self.work_task(item))
        return task_pool

    def print_messages(self, args):
        for arg in args:
            print(arg)
        return None

    def print_death_message(self, args):
        for arg in args:
            print(arg)
        return 'EXIT TAMA'

    def take_input(self, args):
        return task(input("plugin Name: "), 
                    input("plugin Function: "), 
                    [int(e) if e.isdigit() else e for e in 
                     input("Comma Separated Arguments: ")
                     .replace(', ', ',')
                     .split(',')])