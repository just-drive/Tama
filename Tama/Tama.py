'''
The Tama Main module is designed to:
- Iterate over the folders and files in the plugins folder
- Establish and control the main event loop
- Recieve and handle signals from each plugin file found in the plugins folder
- Establish and control connections between plugins so they may communicate with each other in real-time
- Maintain each plugin as a separate process
- Prevent race conditions by controlling access to resources
- Expose a way to safely terminate the program from any plugin
- Handle outer-level GUI processes.
'''

import wx
import wx.aui as aui
import json
import asyncio
import pathlib
import os
import importlib
import multiprocessing as multiproc
from task import task
from datetime import datetime, timedelta
import asyncio
from yapsy.PluginManager import PluginManager
from yapsy.PluginFileLocator import PluginFileLocator
from yapsy.PluginInfo import PluginInfo

class Tama(wx.App):
    """
    The Tama object inherits from wx.App and is capable of multiprocessing.
    Template code for multiprocessing handling is incorporated from https://wiki.wxpython.org/MultiProcessing
    
    """
    def __init__(self, processes=[ ], task_queue=[ ]):
        #see wx.App __init__ function for the following statement
        super(Tama, self).__init__(redirect = True, filename = 'tama.stderr.log', useBestVisual = True, clearSigInt = True)
        self.TamaPath = os.path.dirname(__file__)
        self.plugin_manager = PluginManager()
        self.task_pool = []
        self.processes = processes
        self.task_queue = task_queue
        self.alive = True
        self.app = wx.App()
        self.timer = wx.Timer(self.app, 0)
        self.start_time = datetime.now()
        self.app.Bind(wx.EVT_TIMER, self.OnTimer)
        self.timer.Start(20)
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
            print("{} plugin activated.".format(pluginInfo.name))

    def OnTimer(self, event):
        #You can use a get_time_delta task to recieve a timedelta object, which can then be
        #used to perform tasks at a set rate over time, such as gui refreshes, animation, 
        #setting something on a timer, etc.
        self.time_delta = datetime.now() - self.start_time

        for plugin in self.plugin_manager.getAllPlugins():
            
            self.task_queue.put(plugin.plugin_object.tick(self.task_pool))

            #take care of Tama-addressed tasks
            #These can be used in the future as a pipeline for getting info from elsewhere
            #but they will be blocking operations for now.
            for idx in task.find_tasks('Tama', self.task_pool):
                item = self.task_pool.pop(idx)
                self.task_pool.insert(idx, self.work_task(item))
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
                    #I love python cause you can do stuff like this succinctly
                    elif item.get_plugin() not in [plugin.name for plugin in self.plugin_manager.getAllPlugins()] \
                        and item.get_plugin != 'Tama':
                        self.task_pool.remove(item)

    # [task] create_tama_frames(self, args)
    # args[0] is the name to be associated with the panel, unique, as per dictionary rules.
    # args[1] is an AuiPaneInfo object if supplied by the plugin
    def create_tama_frame(self, args):
        # args[0] Will be the pane name to use in the panes dictionary
        # if it's blank, return None.
        if args[0] is None:
            return None
        
        new_frame = None
        # if args[1] is None, create a AuiPaneInfo object and use it to create a floating frame
        # for the pane_manager to handle
        if args[1] is None:
            new_frame = aui.AuiFloatingFrame()
        # else use the AuiPaneInfo object to create the pane
        else:
            pass
        
        # and then insert it into the manager
        pane_manager.AddPane(new_frame)
        return 

    # [task] remove_tama_frame(self, args)
    # Will eventually remove a frame from the frame array, as well as handle any OnExit Events
    # that occur in a frame.
    def remove_tama_frame(self, args):
        pass

    # [task]update_tama_frames(self)
    # Adds an update_tama_frames() task to the task_pool for every plugin
    # that is using wxPython to generate graphics.
    #
    # Receives these tasks when they are sent back with a wxPython Frame as args[0]
    # Replaces the current frame owned by /plugin.name/ with the new Frame
    #
    # Will eventually handle updating the Frames that have been initiated
    # it will do this by creating a task with feedback required for each 
    # plugin that creates a frame and needs to update it.
    def update_tama_frames(self, args):
        pass

    def get_tama_path(self, args):
        return self.TamaPath

    def get_time_delta(self, args):
        return self.time_delta

    def die(self, args):
        end_time = datetime.now()
        print("Tama lived for {} seconds".format((end_time - self.start_time).total_seconds()))
        self.task_pool = [task('Tama', False, 'Tama', 'shutdown')]

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

    def create_app(self):
        app = Tama(redirect=True, filename='wxsimpler_mp.stderr.log', processes=Processes, taskqueue=taskQueue, donequeue=doneQueue, tasks=Tasks)

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

    def worker(self, input):
        """
        Create a TaskProcessor object and calculate the result.
        """
        while True:
            try:
                args = input.get_nowait()
                self.task_pool.append(work_task(args[0]))
            except:
                pass

    worker = classmethod(worker)

if __name__ == "__main__":
    multiproc.freeze_support()
    # Determine the number of CPU's/cores
    numproc = multiproc.cpu_count()
    
    # Create the queues
    task_queue = multiproc.Queue()
    
    processes = [ ]
    
    # The worker processes must be started before initializing Tama.
    for n in range(numproc):
        process = multiproc.Process(target=Tama.worker, args=[task_queue])
        process.start()
        processes.append(process)

    tama = Tama(processes=processes, task_queue=task_queue)
    tama.MainLoop()