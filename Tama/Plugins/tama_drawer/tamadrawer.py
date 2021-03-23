import wx
from wx import AppTraits
import json
import threading
import time
from yapsy.IPlugin import IPlugin
from datetime import timedelta
from task import task
from Plugins.tama_drawer.tamaframe import TamaFrame, TamaWidget, ImageIn
import os
from datetime import datetime

class TamaDrawer(IPlugin):
    """
    This class will handle Tama's animations and graphics processing.
    It also has the ability to draw from the task pool. This is how you
    will pass animation logic commands to this module.
    """

    def __init__(self):
        super().__init__()
        #Assets used will be placed in the same directory as this folder, to make draw logic easier.
        self.asset_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Assets')

        #not sure if this will need to be used in the future, but it's getting set up.
        self.tama_path = None
        self.current_mood = None
        self.sizer = wx.BoxSizer()
       

        #Tama generation will be the step before adding physics to the animations.
        #The idea would be to intake a set of png files and output a single image object that is all the pngs combined.
        #In the future the positions of the pngs could be cached in something like a hashtable so that less time 
        #is spent generating, to reduce lag in Tama's UI relatively quickly after startup.
        #self.tama_generator = TamaGenerator()

        #For now, we will act within a main Frame that contains Tama at all times.
        self.tama_frame = TamaFrame()
        dirlist = []
        for dir in os.scandir(self.asset_path):
            if dir.is_dir():
                dirlist.append(dir.name)

        self.current_time = datetime.now()
        self.previous_time = None
        self.time_delta = None

        self.available_folders = dirlist
        self.image = wx.StaticBitmap(self.tama_frame, 0)
        return None

    def set_tama_path(self, path):
        """
        This is a task method.

        It recieves the path to the directory where Tama.py resides, and then:
        """
        self.tama_path = path
        #This task can safely be removed once it is complete
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

    def calc_mood(self, current_mood):
        self.current_mood = current_mood
        return

    def get_time_delta(self, time_delta):
        """
        receiving method for the Tama get_time_delta task.
        """
        self.time_delta = time_delta
        return

    def tick(self, task_pool):
        """
        This method will operate off of Tama's time delta in order to handle animation transitioning.
        Use the task pool to get relevant information, and process it accordingly, with variable refresh rates.
        """
        #begin by reading from the task pool for necessary information, if it's not found (happens on first few ticks) then
        #wait until all is found before beginning to animate.
        idxlist = task.find_tasks('Tama Drawer', task_pool)
        for idx in idxlist:
            item = task_pool.pop(idx)
            task_pool.insert(idx, self.work_task(item))

        task_pool.append(task('Tama Drawer', True, 'Basic Needs', 'calc_mood', []))

        if self.previous_time is None:
            self.previous_time = self.current_time
            return task_pool
        elif self.current_mood is None:
            return task_pool
        else:
            self.image.SetBitmap(self.tama_frame.Update(self.current_mood))
            self.tama_frame
            self.sizer.Clear()
            self.sizer.Add(self.image, 1, wx.SHAPED)
            self.tama_frame.SetSizer(self.sizer)
            self.sizer.Fit(self.tama_frame)
            self.tama_frame.Show()
        return task_pool
        
        


