import wx
from wx import AppTraits
import mouse
import keyboard
import wx.adv as adv
import json
import threading
import time
import webbrowser
from win32ctypes.pywin32 import win32api
import win32.lib.win32con as win32con
import win32.win32gui as win32gui
from yapsy.IPlugin import IPlugin
from datetime import timedelta
from task import task
import Plugins.tama_drawer as Drawer
from Plugins.tama_drawer.window_pinning import WindowPinning
from Plugins.tama_drawer.copy_x import CopyX
from Plugins.tama_drawer.macro_recorder import MacroRecorder
from Plugins.tama_drawer.window_pinning import WindowPinning
from Plugins.tama_drawer.settings import Settings 
from Plugins.tama_drawer.tamaframe import TamaFrame
from Plugins.tama_drawer.tamastatsframe import TamaStatsFrame
from Plugins.tama_drawer.tama_drawer_events import TamaMoodEvent
import os
from datetime import datetime

#Define all events that will be used by wx for various states of Tama

#EVT_TAMA_MOOD_* Events are internally driven events, used to change how Tama is depicted
EVT_TAMA_MOOD = wx.NewEventType()
EVT_TAMA_IDLE = wx.PyEventBinder(EVT_TAMA_MOOD, 1)
EVT_TAMA_SLEEP = wx.PyEventBinder(EVT_TAMA_MOOD, 1)
EVT_TAMA_HUNGRY = wx.PyEventBinder(EVT_TAMA_MOOD, 1)
EVT_TAMA_TEASE_FOOD = wx.PyEventBinder(EVT_TAMA_MOOD, 1)
EVT_TAMA_EAT = wx.PyEventBinder(EVT_TAMA_MOOD, 1)
EVT_TAMA_SICK = wx.PyEventBinder(EVT_TAMA_MOOD, 1)

#EVT_TAMA_MOVE_* Events are AI controlled events that involve manipulating Tama's frame.
EVT_TAMA_MOVE = wx.NewEventType()
EVT_TAMA_THINK_OF = wx.PyEventBinder(EVT_TAMA_MOVE, 1)
EVT_TAMA_MOVE_LEFT = wx.PyEventBinder(EVT_TAMA_MOVE, 1)
EVT_TAMA_MOVE_RIGHT = wx.PyEventBinder(EVT_TAMA_MOVE, 1)
EVT_TAMA_SQUISHED_LEFT = wx.PyEventBinder(EVT_TAMA_MOVE, 1)
EVT_TAMA_SQUISHED_RIGHT = wx.PyEventBinder(EVT_TAMA_MOVE, 1)
EVT_TAMA_SQUISHED_BOTTOM = wx.PyEventBinder(EVT_TAMA_MOVE, 1)
EVT_TAMA_SQUISHED_TOP = wx.PyEventBinder(EVT_TAMA_MOVE, 1)
EVT_TAMA_FALLING = wx.PyEventBinder(EVT_TAMA_MOVE, 1)

#USER_* Events are externally driven events, used to interact with the Tama character
#Many of these events will not be called until we have an animation style that works,
#or if we've managed to incorporate physics into Tama's TamaFrame
EVT_USER = wx.NewEventType()
USER_CLICK = wx.PyEventBinder(EVT_USER, 1)
USER_DRAG = wx.PyEventBinder(EVT_USER, 1)
USER_RELEASE = wx.PyEventBinder(EVT_USER, 1)
USER_TOSS = wx.PyEventBinder(EVT_USER, 1)
USER_DRAG_FOOD = wx.PyEventBinder(EVT_USER, 1)
USER_DROP_FOOD = wx.PyEventBinder(EVT_USER, 1)
USER_KEYPRESS_QUIT = wx.PyEventBinder(EVT_USER, 1)

class TamaDrawer(IPlugin, wx.Frame):
    """
    This class will handle Tama's animations and graphics processing.
    It also has the ability to draw from the task pool. This is how you
    will pass animation logic commands to this module.
    """

    def __init__(self):
        style = (wx.STAY_ON_TOP )
        IPlugin.__init__(self)
        wx.Frame.__init__(self, None, -1, title = 'Tama', name = 'Tama')
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        #Assets used will be placed in the same directory as this folder, to make draw logic easier.
        self.asset_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Assets')
        self.tasks = []

        #not sure if this will need to be used in the future, but it's getting set up.
        self.tama_path = None

        #current_mood is passed to widgets that need it
        self.current_mood = None

        #get display information in order to set bounding boxes for Tama and his widgets
        num_displays = wx.Display().GetCount()
        self.displays = []
        for disnum in range(num_displays):
            self.displays.append(wx.Display(disnum))

        #This gives us bounding boxes to keep Tama off of the task bar.
        self.bounding_boxes = []
        for disnum in range(num_displays):
            self.bounding_boxes.append(self.displays[disnum].GetClientArea())
        
        self.SetSize(self.bounding_boxes[0])

        #For now, we will act within a main Frame that contains Tama at all times.
        self.frames = [
                TamaFrame(self), 
                TamaStatsFrame(self), 
                WindowPinning(self),
                CopyX(),
                MacroRecorder(),
                Settings()
            ]
        for frame in self.frames:
            frame.Hide()
        self.frames[0].Show()

        self.current_display = wx.Display().GetFromPoint(self.GetPosition())
        self.Bind(EVT_TAMA_IDLE, self.on_tama_mood)

        #Linux and Windows will have different ways to create this kind of transparent frame.
        if wx.Platform == '__WXMSW__':
            hwnd = self.GetHandle()
            extendedStyleSettings = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, extendedStyleSettings | win32con.WS_EX_APPWINDOW | win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT)
            win32gui.SetLayeredWindowAttributes(hwnd, 0, 255, win32con.LWA_COLORKEY)
            self.SetTransparent(0)
        elif wx.Platform == '__WXGTK__':
            pass
        else:
            pass
        self.Show()

    def OnClose(self, event):
        for frame in self.frames:
            frame.Destroy()
        self.Destroy()

    def get_bounding_box(self, screen_num = 1):
        return self.bounding_boxes[screen_num - 1]

    def set_tama_path(self, path):
        """
        This is a task method.

        It recieves the path to the directory where Tama.py resides, and then:
        """
        self.tama_path = path
        #This task can safely be removed once it is complete
        return
    
    def on_tama_mood(self, event):
        this_event_mood = event.get_current_mood()
        for frame in self.frames:
            if callable(frame.needs_mood) and frame.needs_mood():
                frame.set_current_mood(this_event_mood)
            if callable(frame.needs_update) and frame.needs_update():
                frame.generate(event)
            #This could cause problems if a lot of graphical processing goes on in more than a couple of frames on Update.
            frame.Update()

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

    def UpdateMood(self, current_mood):
        mood_update = TamaMoodEvent(EVT_TAMA_MOOD, self.GetId(), current_mood)
        self.GetEventHandler().ProcessEvent(mood_update)

    def get_created_tasks(self):
        tasks = self.tasks
        self.tasks.clear()
        return tasks

    def tick(self, task_pool):
        """
        This method will operate off of Tama's time delta in order to handle animation transitioning.
        Use the task pool to get relevant information, and process it accordingly, with variable refresh rates.
        """
        #begin by reading from the task pool for necessary information, if it's not found (happens on first few ticks) then
        #wait until all is found before beginning to animate.
        for item in self.tasks:
            task_pool.append(self.tasks.pop())
        idxlist = task.find_tasks('Tama Drawer', task_pool)
        for idx in idxlist:
            item = task_pool.pop(idx)
            task_pool.insert(idx, self.work_task(item))

        task_pool.append(task('Tama Drawer', True, 'Basic Needs', 'calc_mood', []))
        task_pool.append(task('Tama Drawer', False, 'Basic Needs', 'calc_mood_override', [self.frames[5].is_csm_on()]))

        if self.current_mood is None:
            return task_pool
        elif self.frames[0] is None:
            return task_pool

        self.UpdateMood(self.current_mood)

        return task_pool
