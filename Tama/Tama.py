'''
The Tama Main module is designed to:
- Iterate over the folders and files in the plugins folder
- Establish and control the main event loop
- Recieve and handle signals from each plugin file found in the plugins folder
- Establish and control connections between plugins so they may communicate with each other in real-time
- Maintain each plugin as a separate process
- Prevent race conditions by controlling access to resources
- Expose a way to safely terminate the program from any plugin
'''

import asyncio
import pathlib
import os
import importlib
from task import task
from datetime import datetime, timedelta
import asyncio
from yapsy.PluginManager import PluginManager
from yapsy.PluginFileLocator import PluginFileLocator
from yapsy.PluginInfo import PluginInfo

class Tama(object):
    
    def __init__(self):
        self.TamaPath = os.path.dirname(__file__)
        self.plugin_manager = PluginManager()
        self.task_pool = []
        self.alive = True
        self.loop = asyncio.get_event_loop()
        self.time_delta = timedelta()

        plugin_folders = []
        for folder in os.scandir(os.path.join(self.TamaPath, "Plugins")):
            if folder.is_dir() and folder.name != '__pycache__':
                plugin_folders.append(folder.path)
        self.plugin_manager.setPluginPlaces(plugin_folders)        
        self.plugin_manager.locatePlugins()
        self.plugin_manager.loadPlugins()
        # Activate all loaded plugins
        located_plugins = self.plugin_manager.getAllPlugins()
        for pluginInfo in located_plugins:
            self.plugin_manager.activatePluginByName(pluginInfo.name)
            self.task_pool.append(
                #This is a good example of a basic task.
                task('Tama',
                    False,
                    pluginInfo.name,
                    'set_tama_path',
                    self.TamaPath)
            )
            print("{} plugin activated.".format(pluginInfo.name))

    def get_tama_path(self, args):
        return self.TamaPath

    def get_time_delta(self, args):
        return self.time_delta

    """
    TODO: Write this function, find a good, modular way to add tasks to the task pool at their appointed times
    """
    def schedule_tasks(self, args):
        """
        There are multiple ways to schedule a task.
        args[0] = schedule mode
        Valid mode values: 1, 2, 3, 4

        Mode 1:
            To schedule a task once after x seconds
            args[1] = task object to call when executing
                task object.get_args()[0] must be datetime.now()
            args[2] = time to wait before executing (x) (in seconds)
            (optional) args[3] = task object to call after executing
        
        Mode 2:
            To schedule a list of tasks to execute once after x seconds
            args[1] = list of task objects
            args[2] = time to wait before executing (x) (in seconds)
            (optional) args[3] = task object called after executing any task in args[0]

        Mode 3:
            To schedule a task to reoccur every x seconds
            args[1] = task object
            args[2] = time to wait before executing (x) (in seconds)
            args[3] = task object called after each occurrance of args[0] task, 
                      that returns False when reoccurrance should end

        Mode 4:
            To schedule a list of tasks to reoccur every x seconds
            args[1] = list of task objects
            args[2] = time to wait before executing (x) (in seconds)
            args[3] = list of task objects 
                      args[2] requires a list of task objects with the same length as args[0]
                      args[2] at index is the task to call when the args[0] at index task finishes.
                      Each task func in args[2] should return false when you want to end reocurrence.
        """
        #Schedule using Mode 1
        if args[0] == 1:
            task_obj = args[1]
            timer = args[2]
            if len(args) == 4:
                return_task = args[3]
                self.task_pool.append(task_obj)
            pass
        #Schedule using Mode 2
        elif args[0] == 2:
            pass
        #Schedule using Mode 3
        elif args[0] == 3:
            pass
        #Schedule using Mode 4
        elif args[0] == 4:
            pass

    def work_task(self, task):
        if not task.is_done():
            task.set_result(getattr(self, task.get_func())(task.get_args()))
        return task

    def run(self):
        start_time = datetime.now()
        while self.alive:
            #You can use a get_time_delta task to recieve a timedelta object, which can then be
            #used to perform tasks at a set rate over time, such as gui refreshes, animation, 
            #setting something on a timer, etc.
            self.time_delta = datetime.now() - start_time
            for plugin in self.plugin_manager.getAllPlugins():
                #every plugin's tick method must return the task pool, modified or not,
                #and should generally run without any large or blocking operations.

                #attempt to split operations up enough that they can finish quickly
                #with a very small time delta.
                self.task_pool = plugin.plugin_object.tick(self.task_pool)
                
                #take care of Tama-addressed tasks
                #These can be used in the future as a pipeline for getting info from elsewhere
                for idx in task.find_tasks('Tama', self.task_pool):
                    item = task_pool.pop(idx)
                    self.task_pool.append(self.work_task(item))

                else:
                    #purge the task pool of 
                    #- non-tasks,
                    #- tasks containing a 'REMOVE' result
                    #- tasks not addressed to a valid plugin
                    #
                    #In order to prevent accidental appends from
                    #causing task pool to grow too big with useless data.
                    for item in self.task_pool:
                        if not task.is_valid_task(item):
                            self.task_pool.remove(item)
                        elif item.get_result() == 'REMOVE':
                            self.task_pool.remove(item)
                        elif item.get_result() == 'EXIT TAMA':
                            self.task_pool.remove(item)
                            self.alive = False
                        elif item.get_plugin() not in [plugin.name for plugin in self.plugin_manager.getAllPlugins()]\
                            and item.get_plugin != 'Tama':
                            self.task_pool.remove(item)
        end_time = datetime.now()
        print("Tama lived for {} seconds".format((end_time - start_time).total_seconds()))

if __name__ == "__main__":
    tama = Tama()
    tama.run()
