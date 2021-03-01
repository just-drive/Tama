class task:
    def __init__(self, sender, requires_feedback, plugin, func, args):
        self.sender = sender
        self.requires_feedback = requires_feedback
        self.plugin = plugin
        self.func = func
        self.args = args
        self.working = False
        self.done = False
        self.result = None
    
    def get_sender(self):
        return self.sender

    def get_requires_feedback(self):
        return self.requires_feedback

    def get_plugin(self):
        return self.plugin

    def get_func(self):
        return self.func

    def get_args(self):
        return self.args

    def get_result(self):
        return self.result

    def is_working(self):
        return self.working

    def is_done(self):
        return self.done

    #searches the task pool for the first task where target_plugin is plugin, and returns the index.
    @staticmethod
    def find_tasks(plugin, task_pool):
        idxlist = []
        for idx, item in enumerate(task_pool):
            if str(item.get_plugin()) == plugin:
                idxlist.append(idx)
        return idxlist

    @staticmethod
    def is_valid_task(item):
        if isinstance(item, task):
            return True
        return False
    