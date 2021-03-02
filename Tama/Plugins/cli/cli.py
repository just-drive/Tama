from task import task
from yapsy.IPlugin import IPlugin

class CLI(IPlugin):
    def __init__(self):
        super().__init__()
        self.tama_path = None
        return

    def work_task(self, task):
        if not task.is_done():
            task.set_result(getattr(self, task.get_func())(task.get_args()))
            task.set_done(True)
        return task

    def set_tama_path(self, path):
        self.tama_path = path
        return 'REMOVE'

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