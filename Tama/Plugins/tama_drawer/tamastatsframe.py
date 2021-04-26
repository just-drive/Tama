from win32ctypes.pywin32 import win32api
import win32.lib.win32con as win32con
import win32.win32gui as win32gui
from wx.lib.delayedresult import startWorker
import wx
import wx.aui as aui
import wx.adv as adv
import wx.lib.newevent
import os
import threading
import random
import Plugins.tama_drawer.tama_drawer_events
from Plugins.tama_drawer.tama_drawer_events import TamaMoodEvent
from Plugins.tama_drawer.tama_drawer_events import EVT_TAMA_MOOD

class TamaStatsFrame(wx.Frame):
    def __init__(self, parent):
        """
        The TamaFrame inherits from wx.Frame, and thus receives the ability to be used in a wxpython (wx) app
        This is the window that is created for the application, Tama's actual form will be inside of this frame,
        and the frame itself is only slightly visible (This can be tweaked).
        """
        #This style of frame has no taskbar or border, and will always stay on top of other windows
        style = (wx.STAY_ON_TOP | wx.FRAME_SHAPED )
        wx.Frame.__init__(self, parent, wx.ID_ANY, title = 'Tama', name = 'Tama')
        self.parent = parent
        self.bounding_box = parent.get_bounding_box()
        self.SetTitle('Tama')
        #self.SetWindowStyle(style)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.SetSize( (900, 900) )
        self.SetPosition( (self.bounding_box.GetX(), self.bounding_box.GetY()) )
        self.current_mood = None
        self.last_mouse_pos = wx.Point(0,0)

        # TamaStatsWidget contains the actual stat data and operations, as well as the gauges that are displayed.
        self.stats = TamaStatsWidget(self)
        self.vSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.vSizer.Add(self.stats, proportion = 1)
        self.SetSizer(self.vSizer)

        #Linux and Windows will have different ways to create this kind of transparent frame.
        #if wx.Platform == '__WXMSW__':
        #    hwnd = self.GetHandle()
        #    extendedStyleSettings = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        #    win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, extendedStyleSettings  | win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT | win32con.WS_EX_COMPOSITED | win32con.WS_EX_APPWINDOW)
        #    win32gui.SetLayeredWindowAttributes(hwnd, 0, 255, win32con.LWA_COLORKEY)
        #    self.SetTransparent(200)
        #    win32gui.SetActiveWindow(hwnd)
        #elif wx.Platform == '__WXGTK__':
        #    pass
        #else:
        #    pass

        self.Show()

    #This frame will update every time a mood is received, as Tama's stats are constantly changing.
    def needs_update(self):
        return True
        
    def needs_mood(self):
        if self.current_mood is None:
            return True
        return False

    def generate(self, event):
        self.stats.generate(event)
        return

    def set_current_mood(self, current_mood):
        self.stats.set_current_mood(current_mood)
        return

    def closeWindow(self, e):
        self.Destroy()

# Will eventually need to work this out to display stats near Tama.
class TamaStatsWidget(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, wx.ID_ANY)
        self.parent = parent
        self.current_mood = None
        self.gauges = {}
        self.gauge_sizers = []
        #self.SetSize()
        self.vSizer = wx.BoxSizer(wx.VERTICAL)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)

        ##Linux and Windows will have different ways to create this kind of transparent frame.
        #if wx.Platform == '__WXMSW__':
        #    hwnd = self.GetHandle()
        #    extendedStyleSettings = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        #    win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, extendedStyleSettings | win32con.WS_CHILD | win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT)
        #    win32gui.SetLayeredWindowAttributes(hwnd, 0, 255, win32con.LWA_COLORKEY)
        #    win32gui.SetParent(hwnd, self.parent.GetHandle())
        #    self.SetTransparent(0)
        #elif wx.Platform == '__WXGTK__':
        #    pass
        #else:
        #    pass

        self.Layout
        return

    def generate(self, event):
        if len(self.gauges) < 1 and self.current_mood is not None:
            self.set_gauges(self.create_stat_gauges(self.current_mood))
        for stat in event.get_current_mood().get('Conditions').keys():
            valuefunc = getattr(event, 'get_' + stat.lower() + '_value')
            self.gauges.get(stat).SetValue(valuefunc())
        self.Update()
        return

    def create_stat_gauges(self, current_mood):
        
        satiation_gauge = wx.Gauge( 
            parent = self, 
            id = 1,
            range = current_mood.get('Max').get('Satiation'),
            pos = [(tuple[0] + 60, tuple[1] + 115) for tuple in [self.GetScreenPosition()]].pop(),
            size = (500, 15),
            style = wx.GA_HORIZONTAL,
            validator = wx.DefaultValidator,
            name = "satiation gauge"
        )

        happiness_gauge = wx.Gauge(
            parent = self, 
            id = 2,
            range = current_mood.get('Max').get('Happiness'),
            pos = [(tuple[0] + 60, tuple[1] + 125) for tuple in [self.GetScreenPosition()]].pop(),
            size = (200, 15),
            style = wx.GA_HORIZONTAL,
            validator = wx.DefaultValidator,
            name = "happiness gauge"
        )

        energy_gauge = wx.Gauge(
            parent = self, 
            id = 3,
            range = current_mood.get('Max').get('Energy'),
            pos = [(tuple[0] + 60, tuple[1] - 135) for tuple in [self.GetScreenPosition()]].pop(),
            size = (200, 15),
            style = wx.GA_HORIZONTAL,
            validator = wx.DefaultValidator,
            name = "energy gauge"
        )

        health_gauge = wx.Gauge(
            parent = self, 
            id = 0,
            range = current_mood.get('Max').get('Health'),
            pos = [(tuple[0] + 60, tuple[1] - 145) for tuple in [self.GetScreenPosition()]].pop(),
            size = (200, 15),
            style = wx.GA_HORIZONTAL,
            validator = wx.DefaultValidator,
            name = "health gauge"
        )

        return {"Happiness": happiness_gauge, "Satiation": satiation_gauge, "Energy": energy_gauge, "Health": health_gauge}

    def set_gauges(self, gauge_dict):
        self.gauges = gauge_dict
        for statname, gauge in enumerate(self.gauges):
            gauge_sizer = wx.BoxSizer(wx.HORIZONTAL)
            gauge_sizer.Add(gauge, proportion = 1, flag = wx.RIGHT, border = 10)
            self.vSizer.Add(gauge_sizer, proportion = 1, flag = wx.ALIGN_TOP)
        self.SetSizer(self.vSizer)

    def set_current_mood(self, current_mood):
        self.current_mood = current_mood
        return

    def OnPaint(self, event):
        b = wx.EmptyBitmap(self.GetSize().GetWidth(), self.GetSize.GetHeight())
        dc = wx.MemoryDC()
        dc.SelectObject(b)
        dc.SetBackground(wx.Brush("White"))
        dc.Clear()
        dc.SelectObject(wx.NullBitmap)
        b.SetMaskColour("White")
        dc = wx.ClientDC(self)
        dc.DrawBitmap(b, self.GetSize().GetWidth(), self.GetSize.GetHeight(), True)