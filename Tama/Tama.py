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
                task('Tama',
                    False,
                    pluginInfo.name,
                    'set_tama_path',
                    self.TamaPath)
            )
            print("{} plugin activated.".format(pluginInfo.name))

    def get_tama_path(self, args):
        return self.TamaPath

    def work_task(self, task):
        if not task.is_done():
            task.set_result(getattr(self, task.get_func())(task.get_args()))
            task.set_done(True)
        return task

    def run(self):
        start_time = datetime.now()
        while self.alive:
            for plugin in self.plugin_manager.getAllPlugins():
                #every plugin's tick method must return the task pool, modified or not.
                self.task_pool = plugin.plugin_object.tick(self.task_pool)
                
                #take care of Tama-addressed tasks
                for idx in task.find_tasks('Tama', self.task_pool):
                    item = task_pool.pop(idx)
                    self.task_pool.append(self.work_task(item))

                #look for the EXIT TAMA escape message, if not found, purge the task_pool and continue.
                if 'EXIT TAMA' in self.task_pool:
                    self.alive = False
                    self.task_pool.remove('EXIT TAMA')
                else:
                    #purge the task pool of non-tasks and tasks labeled 'REMOVE', to prevent accidental appends from
                    #causing task pool to grow too big with useless data.
                    for item in self.task_pool:
                        if not task.is_valid_task(item):
                            self.task_pool.remove(item)
                        elif item.get_result() == 'REMOVE':
                            self.task_pool.remove(item)
        end_time = datetime.now()
        print("Tama lived for {} seconds".format((end_time - start_time).total_seconds()))

if __name__ == "__main__":
    tama = Tama()
    tama.run()
