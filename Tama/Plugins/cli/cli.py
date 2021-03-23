from task import task
from yapsy.IPlugin import IPlugin

class CLI(IPlugin):
    def __init__(self):
        super().__init__()
        self.tama_path = None
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

    def set_tama_path(self, path):
        self.tama_path = path
        return

    def tick(self, task_pool):
        idxlist = task.find_tasks('CLI', task_pool)
        for idx in idxlist:
            item = task_pool.pop(idx)
            task_pool.insert(idx, self.work_task(item))
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