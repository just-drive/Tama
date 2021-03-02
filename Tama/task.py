class task:
    def __init__(self, sender, requires_feedback, target_plugin, func, args):
        self.sender = sender
        self.requires_feedback = requires_feedback
        self.plugin = target_plugin
        self.func = func
        self.args = args
        self.working = False
        self.done = False
        self.result = None
    
    def get_sender(self):
        return self.sender

    def set_sender(self, new_sender):
        self.sender = new_sender
        return self

    def get_requires_feedback(self):
        return self.requires_feedback

    def set_requires_feedback(self, new_feedback):
        self.requires_feedback = new_feedback
        return self

    def get_plugin(self):
        return self.plugin

    def set_plugin(self, new_plugin):
        self.plugin = new_plugin
        return self

    def get_func(self):
        return self.func

    def set_func(self, new_func):
        self.func = new_func
        return self

    def get_args(self):
        return self.args

    def set_args(self, new_args):
        self.args = new_args
        return self

    def get_result(self):
        return self.result

    def set_result(self, new_result):
        self.result = new_result
        return self

    def is_working(self):
        return self.working

    def set_working(self, boolval):
        self.working = boolval
        return self

    def is_done(self):
        return self.done

    def set_done(self, boolval):
        self.done = boolval
        return self

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
    