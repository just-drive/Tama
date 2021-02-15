class task:
    def __init__(self, module, func, args):
        self.module = module
        self.func = func
        self.args = args

    def get_module(self):
        return self.module

    def get_func(self):
        return self.func

    def get_args(self):
        return self.args
    