from win32ctypes.pywin32 import win32api
import win32.lib.win32con as win32con
import win32.win32gui as win32gui
from wx.lib.delayedresult import startWorker
import PIL
import wx
import wx.aui as aui
import wx.adv as adv
import wx.lib.newevent
import os
import threading
import datetime
import random
import mouse
from screeninfo import get_monitors
import Plugins.tama_drawer.tama_drawer_events
from Plugins.tama_drawer.tama_drawer_events import TamaMoodEvent
from Plugins.tama_drawer.tama_drawer_events import EVT_TAMA_MOOD
#
# The two tools below were acquired from the below wxPythonWiki tutorial: 
# -- Insert Here --
#
import Plugins.tama_drawer.ImgConv    # wxImage <==> PilImage
import Plugins.tama_drawer.BitmapManip  # mask wxBmap  <==> PilImage <== file
from PIL import Image, ImageDraw, ImageChops, ImageSequence

def GetRamdomWxColorAndInverse() :
    
    r, g, b = (random.randint(0, 127), random.randint(0, 127), random.randint(0, 127))
    
    if random.randint(0, 1) :       # Gaurantee a large contrast
        r, g, b = (255-r, 255-g, 255-b)
    #end if
    
    R, G, B, = (255-r, 255-g, 255-b)        # The inverse
    
    return (wx.Colour(r, g, b), wx.Colour(R, G, B))

def CreateInnerMaskBmapFromOuterMask( srcBmap ) :
    """ 
    Derive the inner mask wxBitmap from the Outer mask wxBitmap.
    
    The srcBmap must be "well behaved" in that a continuous border 
    must present so that a floodfill to the perimeter area will not reach 
    into the inner area. The border color must be >=128. So, 
    the srcBmap consists of a transparent/BLACK perimeter, an white/opaque
    frame border and a transparent/BLACK inner area.
    
    When completed, the outer_area+border will be transparent/BLACK, 
    the parent's frame border will be transparent/BLACK and the inner area 
    will be opaque/WHITE.
    
    1. outer perimeter (black) --> Floodfill to white/255
                                   Now both perimeter and border are white).
    2. Invert the image and return as a wxBitmap..
    
    """
    # Start with an 'L' Pil copy of the RGB input wxBitmap.
    dstPilImage = ImgConv.PilImageFromWxBitmap( srcBmap ).convert( 'L' )
    
    # Make sure the image is quantized to binary.
    dstPilImage = dstPilImage.point(lambda i: (i / 128) * 255)
    size = dstPilImage.size
    ImageDraw.floodfill( dstPilImage, (0, 0), (255) )
    
    return ImgConv.WxBitmapFromPilImage( ImageChops.invert( dstPilImage ) )
#end def

#------------------------------------------------------------------------------

class TamaFrame(wx.Frame):

    """
    Shaped window from disk image files and optional disk transparency mask files. 

    The user cannot resize the window because there are no resizing decorations !
    The entire popup is just a control-less bitmap image.
    However, all that is visible (opaque) can be repositioned by dragging.
    """
    def __init__( self, parent, image_filename=None, mask_filename=None, 
                        outer_or_inner_window=1,            # default to a shaped frame window
                        posn=(0, 0), bgTransparency=100 ) :
        style = ( wx.STAY_ON_TOP )
        """
        The TamaFrame inherits from wx.Frame, and thus receives the ability to be used in a wxpython (wx) app
        This is the window that is created for the application, Tama's actual form will be inside of this frame,
        and the frame itself is only slightly visible (This can be tweaked).
        """        
        wx.Frame.__init__(self, parent, wx.ID_ANY, style=style, title = 'Tama', name = 'Tama')
        self.bgTransparency = bgTransparency
        self.SetBackgroundStyle(wx.BG_STYLE_ERASE)
        self.image_filename = image_filename
        self.image_wxBitmaps = []
        self.parent = parent
        self.current_bitmap = None
        self.timer = wx.Timer(self, wx.ID_ANY)
        self.timer.Start(60)
        #Will be used to get locations of screens, so that the correct
        #screen is drawn to when drawing with a ScreenDC
        self.screens = []
        self.screen_positions = []
        for screen in get_monitors():
            self.screens.append(screen)
        #Bounding_boxes is a list of rect objects where bounding_boxes[0]
        #Represents the client size of screen[0]
        #This will be used to draw with a ScreenDC, which considers all
        #monitors to be one screen.
        self.bounding_boxes = []
        for screen_idx in range(len(self.screens)):
            self.bounding_boxes.append(wx.Display(screen_idx).GetClientArea())
            
        self.SetTitle('Tama')
        self.SetSize( (250, 250) )
        self.current_screen = wx.Display().GetFromPoint((self.bounding_boxes[0].GetX(), self.bounding_boxes[0].GetY()))
        self.SetPosition((self.bounding_boxes[0].GetX(), self.bounding_boxes[0].GetY()))
        self.current_mood = None
        self.last_mouse_pos = wx.Point(0,0)
        self.tama_widget = TamaWidget(self)
        self.previous_update = datetime.datetime.now()
        self.screenContext = None
        self.is_border_window = outer_or_inner_window
        self.is_inner_window = not outer_or_inner_window
        
        if wx.Platform == '__WXGTK__' :     # GTK-only, use as an event handler.
            self.Bind( wx.EVT_WINDOW_CREATE, self.DrawWindow )
        #end if
        
        #------------------------------
        
        # This handler is always required.
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_TIMER, self.OnTimer)
        #self.Bind(wx.EVT_ERASE_BACKGROUND, self.DoNothing)
        # Enable the user to quit the app by pressing <ESC>.
        self.Bind( wx.EVT_KEY_UP, self.OnKeyDown )  # Comment this to disable.
        # Enable window dragging.
        self.Bind( wx.EVT_MOTION, self.OnMotion )    # Comment this to disable.
        self.Bind(wx.EVT_LEFT_UP, self.OnRelease)
        self.Bind(wx.EVT_CLOSE, parent.OnClose)
        #mouse.on_right_click(self.ShowRightMenu)
        self.Bind(wx.EVT_CONTEXT_MENU, self.ShowRightMenu)

        #Linux and Windows will have different ways to create this kind of transparent frame.
        if wx.Platform == '__WXMSW__':
            hwnd = self.GetHandle()
            extendedStyleSettings = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, extendedStyleSettings  | win32con.WS_EX_LAYERED | win32con.WS_CHILD)
            win32gui.SetLayeredWindowAttributes(hwnd, 0, 255, win32con.LWA_COLORKEY)
            self.SetTransparent(190)
            
        elif wx.Platform == '__WXGTK__':
            pass
        else:
            pass
        
        self.SetDoubleBuffered(True)
        self.Layout()
        self.Show()

    #--------------------------------------------
    
    def SetOtherWindow( self, otherWindow ) :
        """ Allow the other ShapedWindow to be referenced in this instantiation. """
        self.otherWindow = otherWindow
    #end def
    
    def SetMyPosition( self, posn ) :
        """ This is for "OtherWindow" to call, never "self"."""
        self.SetPosition( posn )
    #end def
    
    def OnPaint( self, event ) :
        self.DrawWindow()
        event.Skip()
        return  # Very important to let all higher level handlers be called.
    #end def
    
    def DoNothing(self, event):
        pass

    def SetImage(self, pil_image):
        if pil_image:
            width, height = pil_image.size
            self.image_wxBitmaps.append(wx.BitmapFromBuffer(width, height, pil_image.convert('RGB').tobytes(), pil_image.convert('RGBA').getchannel('A').tobytes()))
            return

    def DrawWindow(self) :
        """Implement window drawing at any time."""
        # screenContext will be drawn to after memoryContext is given the right combined bitmap
        context = wx.PaintDC(self)
        #   Blit will copy the pixels from self.combined_image, which is a 
        #   MemoryDC that contains the current Tama Image to be displayed.
        #   This image is newly generated within the Tama task system, in order to
        #   reduce image display time.
        if len(self.image_wxBitmaps) and context.CanDrawBitmap():
            context.DrawBitmap(self.image_wxBitmaps.pop(), 0, 0, False)
        del context
    #end def DrawWindow
    
    #--------------------------------------------
    
    def OnTimer(self, event):
        if not self.tama_widget.is_grabbed() and self.tama_widget.is_moving():
            self.move_direction()
        self.SetImage(self.tama_widget.next())
        self.Refresh()
        return

    def show_window_pinning(self, event):
        self.parent.frames[2].Show()
        return

    def show_copyx(self, event):
        self.parent.frames[3].Show()
        return

    def show_macro_recorder(self, event):
        self.parent.frames[4].Show()
        return

    def show_settings(self, event):
        self.parent.frames[5].Show()
        return

    def ShowRightMenu(self, *args) :
        """
        Create and show a Context Menu
        """
        # only do this part the first time so the events are only bound once 
        if not hasattr(self, "itemOneId"):
            self.itemOneId = wx.NewId()
            self.itemTwoId = wx.NewId()
            self.itemThreeId = wx.NewId()
            self.itemFourId = wx.NewId()
            self.itemFiveId = wx.NewId()
            self.Bind(wx.EVT_MENU, self.show_window_pinning, id=self.itemOneId)
            self.Bind(wx.EVT_MENU, self.show_copyx, id=self.itemTwoId)
            self.Bind(wx.EVT_MENU, self.show_macro_recorder, id=self.itemThreeId)
            self.Bind(wx.EVT_MENU, self.show_settings, id=self.itemFourId)
            self.Bind(wx.EVT_MENU, self.parent.OnClose, id=self.itemFiveId)
 
        # build the menu
        menu = wx.Menu()
        itemOne = menu.Append(self.itemOneId, "Pin a Window...")
        itemTwo = menu.Append(self.itemTwoId, "Copy X...")
        itemThree = menu.Append(self.itemThreeId, "Record Mouse Events...")
        itemFour = menu.Append(self.itemFourId, "Settings")
        itemFive = menu.Append(self.itemFiveId, "Exit")
 
        # show the popup menu
        self.PopupMenu(menu)
        menu.Destroy()
    
    def OnKeyDown( self, event ) :
        """Quit the app if the user presses Q, q or Esc"""
        
        keyCode = event.GetKeyCode()
        quitCodes = [27, ord('Q'), ord('q')]
        
        event.Skip()        # Allow any following event processing.
        if (keyCode in quitCodes) :
            self.Close( force=True )
        #end if
        
    #end def
    
    #--------------------------------------------
    
    def OnMotion( self, event ) :
        """Implement window client area dragging since this window has no frame to grab."""
        
        if not event.Dragging() :    # Mouse is moving but no button is down.
            self.dragPosn = None
            return
        #end if
            
        #self.CaptureMouse()
        
        if self.dragPosn == None :      # Previous non-dragging mouse position
            # Capture the first mouse coord after pressing any button
            self.dragPosn = event.GetPosition()
        else:
            if not self.tama_widget.is_grabbed():
                self.tama_widget.is_grabbed(True)
            currPosn = event.GetPosition()
            self.current_screen = wx.Display().GetFromWindow(self)
            displacement = self.dragPosn - currPosn
            newPosn = self.GetPosition() - displacement
            self.SetPosition( newPosn )
            self.Update()

    def move_direction(self):
        window_pos = self.GetScreenPosition()
        if self.tama_widget.is_moving():
            #box represents the client area of the current screen that Tama is located on.
            #and the upper left corner does not have to be 0,0
            box = self.bounding_boxes[self.current_screen]
            if self.tama_widget.get_movement_direction() == 'Move Left':
                if self.bounding_boxes[self.current_screen].Contains(
                wx.Point(window_pos[0]-2, window_pos[1])):
                    self.Move(window_pos[0]-2, window_pos[1])
                else:
                    self.tama_widget.is_moving(False)
                    
            elif self.tama_widget.get_movement_direction() == 'Move Right':
                if self.bounding_boxes[self.current_screen].Contains(
                wx.Point(window_pos[0] + self.GetSize().GetWidth(), window_pos[1])):
                    self.Move(window_pos[0]+2, window_pos[1])
                else:
                    self.tama_widget.is_moving(False)
            else:
                pass
        self.Update()

    def OnRelease(self, event):
        if self.tama_widget.is_grabbed():
            self.tama_widget.is_grabbed(False)

    def needs_update(self):
        return self.tama_widget.needs_update()

    def needs_mood(self):
        if self.current_mood is None:
            return True
        return False

    def generate(self, event):
        if self.tama_widget.is_moving():
            self.tama_widget.is_moving(False, None)

        if 'Sleeping' in event.get_modifiers():
            self.tama_widget.set_animation('Sleeping')
        elif 'Eating' in event.get_modifiers():
            self.tama_widget.set_animation('Eating')
        elif 'Thinking_of_Food' in event.get_modifiers():
            self.tama_widget.set_animation('Thinking_of_Food')
        else:
            self.tama_widget.set_animation('Idle')
        self.Refresh()
        return

    def set_current_mood(self, current_mood):
        self.tama_widget.set_current_mood(current_mood)
        self.Show()
        return

    def get_bounding_boxes(self):
        return self.bounding_boxes

    def OnClose(self, e):
        e.Skip()

class TamaWidget():
    """
    Holds the processes that handle generating Tama from a stack of layers that are provided via (tama_stream)
    It will yield images from tama_generate() as the animation is changed by a current_mood update.
    """
    def __init__(self, parent):
        self.assets_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Assets")
        self.parent = parent
        self.available_folders = []
        self.current_mood = None
        self.animation_duration = 0
        self.frame_idx = 0
        #self.tama_generator = wx.Process()
        self.current_animation_name = 'Idle'
        self.idle_animation_path = os.path.join(os.path.join(self.assets_folder, 'Idle'), 'Idle_0.gif')
        self.current_folder_animations = [self.idle_animation_path]
        #GenericAnimationCtrl is used here in order to detect when an animation is done playing.
        self.current_gif = Image.open(self.idle_animation_path)
        self.current_animation = []
        self.prev_animation = None
        self.grabbed = False
        self.moving = False
        self.direction = None

    def set_current_mood(self, current_mood):
        self.current_mood = current_mood
        return

    def get_movement_direction(self):
        return self.direction

    def needs_update(self):
        if (self.is_grabbed() and self.current_animation_name != 'Grabbed') \
        or (not self.is_grabbed() and self.current_animation_name == 'Grabbed'):
            return True
        elif self.frame_idx - self.animation_duration >= -1:
            return True
        return False

    def get_current_animation(self):
        if self.current_animation:
            return self.current_animation[self.frame_idx]
        return None

    # Returns the current frame and increments the frame_idx by one.
    def next(self):
        if self.frame_idx >= self.animation_duration-1:
            self.set_animation(self.current_animation_name)
        im = self.get_current_animation()
        if im:
            self.frame_idx += 1
            return im
        else:
            return None

    def is_grabbed(self, ishe = None):
        '''
        This allows other classes to "grab" Tama as well.
        Returns whether or not 'grabbed' animations will play if used without the bool
        Sets grabbed animations to play and returns the screen position if used with the bool
        '''
        
        if ishe is None:
            return self.grabbed
        
        self.grabbed = ishe
        if self.is_moving():
            if ishe == True:
                if 'Move' not in self.current_animation_name \
                and 'Grabbed' not in self.current_animation_name:
                    self.prev_animation = self.current_animation_name
                self.set_animation('Grabbed')
                self.is_moving(False)
            if ishe == False:
                return
        else:
            if ishe == True:
                if 'Move' not in self.current_animation_name \
                and 'Grabbed' not in self.current_animation_name:
                    self.prev_animation = self.current_animation_name
                self.set_animation('Grabbed')
            if ishe == False:
                self.set_animation(self.prev_animation)

    def is_moving(self, ishe = None, dir = -1):
        '''
        This allows other classes to trigger Tama left-right movements
        Returns whether or not moving animations are playing
        Sets moving animations to play
        '''
        if ishe is None:
            return self.moving

        self.moving = ishe
        if dir == 0: 
            self.direction = 'Move Left'
        elif dir == 1: 
            self.direction = 'Move Right'
        else: 
            self.direction = "Idle"
            self.moving = False

        if not self.is_grabbed():
            self.moving = ishe
            if ishe == True:
                if 'Move' not in self.current_animation_name \
                and 'Grabbed' not in self.current_animation_name:
                    self.prev_animation = self.current_animation_name
                self.set_animation(self.direction)
            elif ishe == False:
                self.set_animation(self.prev_animation)
        else:
            self.moving = False

    def pngs_exist(self, gif_idx, anim_name):
        if os.path.exists(os.path.join(os.path.join(self.assets_folder, anim_name), 'Gen')):
            pngs = [file.name for file in os.scandir(os.path.join(os.path.join(self.assets_folder, anim_name), 'Gen')) if file.is_dir() != True and '.png' in file.name.lower()]
            for png in pngs:
                if str(gif_idx) + "_" in png:
                    return True
        return False

    def set_animation(self, anim_name):
        #This has to happen every time set_animation is called, or indices will go out of range when calling self.next()
        self.frame_idx = 0
        if self.is_grabbed():
            #in the future, we can set a grabbed + anim_name animation here, and rotate the animation on user drag.
            anim_name = 'Grabbed'
        elif random.randrange(0, 2) == 0:
            if not self.is_moving():
                dir = random.randrange(0, 2)
                self.is_moving(True, dir)
            else:
                self.is_moving(False)
            return

        gifs = [file.path for file in os.scandir(os.path.join(self.assets_folder, anim_name)) if file.is_dir() != True and '.gif' in file.name.lower()]
        if os.path.exists(os.path.join(os.path.join(self.assets_folder, anim_name), 'Gen')):
            pngs = [file.path for file in os.scandir(os.path.join(os.path.join(self.assets_folder, anim_name), 'Gen')) if file.is_dir() != True and '.png' in file.name.lower()]
        else:
            pngs = []
        
        if len(gifs) < 1:
            self.current_animation_name = 'Idle'
            current_gif = Image.open(self.idle_animation_path)
            if not os.path.exists(os.path.join(os.path.join(self.assets_folder, anim_name), 'Gen')):
                os.mkdir(os.path.join(os.path.join(self.assets_folder, anim_name), 'Gen'), 0)
            for frame in ImageSequence.Iterator(current_gif):
                combined_anim_name = "" + str(0) + "_" + anim_name + "_frame" + str(self.animation_duration) + ".png"
                path_to_frame = os.path.join(os.path.join(os.path.join(self.assets_folder, anim_name), 'Gen'), combined_anim_name)
                gif_info = frame.info
                frame.save(path_to_frame, **gif_info)
                self.current_animation.append(Image.open(path_to_frame))
                self.animation_duration += 1
        else:
            self.animation_duration = 0
            self.current_animation_name = anim_name
            self.current_animation = []
            gif_idx = random.randrange(0, len(gifs), 1)
            #if there aren't any pngs yet for this animation, create them
            if self.pngs_exist(gif_idx, anim_name):
                pngs = [file.path for file in os.scandir(os.path.join(os.path.join(self.assets_folder, anim_name), 'Gen')) if file.is_dir() != True and '.png' in file.name.lower() and str(gif_idx) + "_" + anim_name + "_frame" in file.name]
                for png in pngs:
                    combined_anim_name = "" + str(gif_idx) + "_" + anim_name + "_frame" + str(self.animation_duration) + ".png"
                    path_to_frame = os.path.join(os.path.join(self.assets_folder, anim_name), 'Gen')
                    self.current_animation.append(Image.open(pngs[pngs.index(os.path.join(path_to_frame, combined_anim_name))]))
                    self.animation_duration += 1
            else:
                current_gif = Image.open(gifs[gif_idx])
                if not os.path.exists(os.path.join(os.path.join(self.assets_folder, anim_name), 'Gen')):
                    os.mkdir(os.path.join(os.path.join(self.assets_folder, anim_name), 'Gen'), 0)
                for frame in ImageSequence.Iterator(current_gif):
                    combined_anim_name = "" + str(gif_idx) + "_" + anim_name + "_frame" + str(self.animation_duration) + ".png"
                    path_to_frame = os.path.join(os.path.join(os.path.join(self.assets_folder, anim_name), 'Gen'), combined_anim_name)
                    gif_info = frame.info
                    frame.save(path_to_frame, **gif_info)
                    self.current_animation.append(Image.open(path_to_frame))
                    self.animation_duration += 1
        
        return
