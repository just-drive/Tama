import wx
import PIL
from PIL import Image
import wx.aui as aui
import wx.lib.newevent
import os
import threading

#Define all events that will be used by wx for various states of Tama
# STARTUP and END Enums that handle entry and exit functions for Tama's form
STARTUP = wx.PyEventBinder(wx.NewEventType(), 0)
END = wx.PyEventBinder(wx.NewEventType(), 0)

#TAMA_* Events are internally driven events, used to change how Tama is depicted
TAMA_IDLE = wx.PyEventBinder(wx.NewEventType(), 0)
TAMA_SLEEP = wx.PyEventBinder(wx.NewEventType(), 0)
TAMA_HUNGRY = wx.PyEventBinder(wx.NewEventType(), 0)
TAMA_TEASE_FOOD = wx.PyEventBinder(wx.NewEventType(), 0)
TAMA_EAT = wx.PyEventBinder(wx.NewEventType(), 0)
TAMA_SICK = wx.PyEventBinder(wx.NewEventType(), 0)
TAMA_THINK_OF = wx.PyEventBinder(wx.NewEventType(), 0)
TAMA_MOVE_LEFT = wx.PyEventBinder(wx.NewEventType(), 0)
TAMA_MOVE_RIGHT = wx.PyEventBinder(wx.NewEventType(), 0)
TAMA_SQUISHED_LEFT = wx.PyEventBinder(wx.NewEventType(), 0)
TAMA_SQUISHED_RIGHT = wx.PyEventBinder(wx.NewEventType(), 0)
TAMA_SQUISHED_BOTTOM = wx.PyEventBinder(wx.NewEventType(), 0)
TAMA_SQUISHED_TOP = wx.PyEventBinder(wx.NewEventType(), 0)
TAMA_FALLING = wx.PyEventBinder(wx.NewEventType(), 0)

#USER_* Events are externally driven events, used to interact with the Tama character
#Many of these events will not be called until we have an animation style that works,
#or if we've managed to incorporate physics into Tama's TamaFrame
USER_CLICK = wx.PyEventBinder(wx.NewEventType(), 0)
USER_CLICK_DRAG = wx.PyEventBinder(wx.NewEventType(), 0)
USER_RELEASE_HOLD = wx.PyEventBinder(wx.NewEventType(), 0)
USER_TOSS = wx.PyEventBinder(wx.NewEventType(), 0)
USER_DRAG_FOOD = wx.PyEventBinder(wx.NewEventType(), 0)
USER_DROP_FOOD = wx.PyEventBinder(wx.NewEventType(), 0)
USER_KEYPRESS_QUIT = wx.PyEventBinder(wx.NewEventType(), 0)

STATS_ON_CHANGE = wx.PyEventBinder(wx.NewEventType(), 0)

class TamaFrame(wx.Frame):
    def __init__(self):
        """
        The TamaFrame inherits from wx.Frame, and thus receives the ability to be used in a wxpython (wx) app
        This is the window that is created for the application, Tama's actual form will be inside of this frame,
        and the frame itself is only slightly visible (This can be tweaked).
        """
        #This style of frame has no taskbar or border, and will always stay on top of other windows
        style = ( wx.CLIP_CHILDREN | wx.STAY_ON_TOP |
                  wx.NO_BORDER | wx.FRAME_SHAPED  )
        super().__init__(None, title = "Tama", style = style)
        self.SetSize( (300, 120) )
        self.SetPosition( (400,300) )
        self.SetTransparent( 255 )
        # [Not implemented yet] Create a floating frame to hold Tama's stats. In the future this will float around Tama as he moves
        # around the screen.
        # self.manager.CreateFloatingFrame(self.tama_widget, TamaStatsWidget(self))

        self.tama_widget = TamaWidget(self, None)

        if wx.Platform == '__WXGTK__':
            self.Bind(wx.EVT_WINDOW_CREATE, self.SetRoundShape)
        else:
            self.SetRoundShape()

        self.Bind(wx.EVT_MOUSE_EVENTS, self.OnMouse)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        

    def GetRoundBitmap(self, w, h, r ):
        maskColour = wx.Colour(0,0,0)
        shownColour = wx.Colour(0,0,0)
        b = wx.Bitmap(w,h)
        dc = wx.MemoryDC(b)
        dc.SetBrush(wx.Brush(maskColour))
        dc.DrawRectangle(0,0,w,h)
        dc.SetBrush(wx.Brush(shownColour))
        dc.SetPen(wx.Pen(shownColour))
        dc.DrawRoundedRectangle(0,0,w,h,r)
        dc.SelectObject(wx.NullBitmap)
        b.SetMaskColour(maskColour)
        return b

    def GetRoundShape(self, w, h, r ):
        return wx.Region( self.GetRoundBitmap(w,h,r) )

    def SetRoundShape(self, event=None):
        w, h = self.GetSizeTuple()
        self.SetShape(self.GetRoundShape( w,h, 10 ) )

    def Update(self, current_mood):
        self.tama_widget.set_current_mood(current_mood)
        return self.tama_widget.get_current_image()

    def OnPaint(self):
        dc = wx.PaintDC(self)
        dc = wx.GCDC(dc)
        w, h = self.GetSize()
        r = 10
        dc.SetPen( wx.Pen("#806666", width = 2 ) )
        dc.SetBrush( wx.Brush("#80A0B0") )
        dc.DrawRoundedRectangle( 0,0,w,h,r )

    def OnKeyDown(self, event):
        """quit if user press q or Esc"""
        if event.GetKeyCode() == 27 or event.GetKeyCode() == ord('Q'): #27 is Esc
            self.Destroy()
        else:
            event.Skip()

    def OnMouse(self, event):
        """implement dragging"""
        if not event.Dragging():
            self._dragPos = None
            return
        
        if not self._dragPos:
            self._dragPos = event.GetPosition()
        else:
            pos = event.GetPosition()
            displacement = self._dragPos - pos
            self.SetPosition( self.GetPosition() - displacement )

class TamaWidget(wx.Panel):
    def __init__(self, parent, current_mood):
        super().__init__(parent = parent)
        self.assets_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Assets")
        self.current_mood = current_mood
        self.current_image = None
        self.animation_index = 0
        self.current_animation = []
        self.current_animation_name = 'Idle'
        self.eventLock = threading.Lock()
        self.set_tama()

    def set_current_mood(self, current_mood):
        self.current_mood = current_mood
        return

    def set_tama(self):
        """
        provide the TamaWidget a mood and it will 
        return the best animation match for the mood.
        """
        if self.current_mood is not None:
            if 'Sleeping' in self.current_mood['Modifiers']:
                self.set_animation('Sleeping')
            elif 'Eating' in self.current_mood['Modifiers']:
                self.set_animation('Eating')
            elif 'Thinking_of_Food' in self.current_mood['Modifiers']:
                self.set_animation('Thinking_of_Food')
            else:
                self.set_animation('Idle')
        else:
            self.set_animation('Idle')

    def get_current_image(self):
        self.set_tama()
        return self.current_image

    def OnPaint(self):
        dc = wx.PaintDC(self.current_image)
        dc.DrawBitmap(png)

    def set_animation(self, anim_name):
        if anim_name != self.current_animation_name \
        or len(self.current_animation) < 1:
            for folder in os.scandir(self.assets_folder):
                if folder.is_dir():
                    if folder.name == anim_name:
                        self.current_animation = [file.path for file in os.scandir(os.path.join(self.assets_folder, anim_name))]
            self.animation_index = 0
            self.current_animation_name = anim_name
        else:
            if self.animation_index + 1 >= len(self.current_animation):
                self.animation_index = 0
            else:
                self.animation_index += 1
        
        self.current_image = wx.Image(self.current_animation[self.animation_index], wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        

# Will eventually need to work this out to display stats near Tama.
class TamaStatsWidget(wx.Panel):
    def __init__(self, parent):
        super(TamaWidget, self).__init__(parent)
        self.current_stats = None
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.eventLock = threading.Lock()

    def set_current_stats(self, current_stats):
        self.current_stats = current_stats
        return

    def create_stat_gauges(self):
        
        health_gauge = wx.Gauge(
            parent = super(TamaStatsWidget, self), 
            id = 0,
            range = self.current_maxes[0],
            pos = super(TamaStatsWidget, self).GetPosition(),
            size = (20, 200),
            style = wx.GA_HORIZONTAL,
            validator = wx.DefaultValidator,
            name = "Health Gauge"
       )

        hunger_gauge = wx.Gauge(
            parent = super(TamaStatsWidget, self), 
            id = 1,
            range = self.current_maxes[1],
            pos = super(TamaStatsWidget, self).GetPosition(),
            size = (20, 200),
            style = wx.GA_HORIZONTAL,
            validator = wx.DefaultValidator,
            name = "Hunger Gauge"
       )

        happiness_gauge = wx.Gauge(
            parent = super(TamaStatsWidget, self), 
            id = 2,
            range = self.current_maxes[2],
            pos = super(TamaStatsWidget, self).GetPosition(),
            size = (20, 200),
            style = wx.GA_HORIZONTAL,
            validator = wx.DefaultValidator,
            name = "health gauge"
       )

        energy_gauge = wx.Gauge(
            parent = super(TamaStatsWidget, self), 
            id = 3,
            range = self.current_maxes[3],
            pos = super(TamaStatsWidget, self).GetPosition(),
            size = (20, 200),
            style = wx.GA_HORIZONTAL,
            validator = wx.DefaultValidator,
            name = "health gauge"
        )

    def OnPaint(self):
        pass

class ImageIn:
    """Interface for sending images to the wx application."""
    def __init__(self, parent):
        self.parent = parent
        self.eventLock = threading.Lock()

    def SetData(self, arr):
        #create a wx.Image from the array
        h,w = arr.shape[0], arr.shape[1]

        #Format numpy array data for use with wx Image in RGB
        b = arr.copy()
        b.shape = h, w, 1
        bRGB = numpy.concatenate((b,b,b), axis=2)
        data = bRGB.tostring()

        img = wx.ImageFromBuffer(width=w, height=h, dataBuffer=data)

        #Create the event
        event = ImageEvent()
        event.img = img
        event.eventLock = self.eventLock

        #Trigger the event when app releases the eventLock
        event.eventLock.acquire() #wait until the event lock is released
        self.parent.AddPendingEvent(event)
