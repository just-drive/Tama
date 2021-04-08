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
import Plugins.tama_drawer.tama_drawer_events
from Plugins.tama_drawer.tama_drawer_events import TamaMoodEvent
from Plugins.tama_drawer.tama_drawer_events import EVT_TAMA_MOOD
import Plugins.tama_drawer.ImgConv    # wxImage <==> PilImage
import Plugins.tama_drawer.BitmapManip  # mask wxBmap  <==> PilImage <== file
from PIL import Image, ImageDraw, ImageChops, ImageSequence        # Pil

#------------------------------------------------------------------------------

"""
On MSW the actual available client area in frameless windows seems to be 
   [(0, 0) to (w-2, h-2)] in relation to the requesred frame size. 
There is an unseen surrounding 1-pixel border.
The origin of the client area is at (0, 0).

A wxFrame without a frame is just a wxWwindow ! But, "wx.Window" can not
be specified with "wx.FRAME_SHAPED" and there is no setting "wx.WINDOW_SHAPED".
"""
CLIENT_SIZE_ADJUST = 0      # Non-MSW platforms may need their own fudge factors.
if wx.Platform == '__WXMSW__' :     # MSW "fudge factor", unfortunately.
    #CLIENT_SIZE_ADJUST = 2
    pass

#------------------------------------------------------------------------------

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
                        posn=(0, 0), bgTransparency=0 ) :
        style = ( wx.STAY_ON_TOP | wx.FRAME_SHAPED )
        """
        The TamaFrame inherits from wx.Frame, and thus receives the ability to be used in a wxpython (wx) app
        This is the window that is created for the application, Tama's actual form will be inside of this frame,
        and the frame itself is only slightly visible (This can be tweaked).
        """        
        wx.Frame.__init__(self, parent, wx.ID_ANY, style=style, title = 'Tama', name = 'Tama') 
        self.SetPosition( posn )
        self.bgTransparency = bgTransparency
        self.SetBackgroundStyle(wx.BG_STYLE_ERASE)
        self.image_filename = image_filename
        self.image_wxBitmap = None
        self.parent = parent
        self.combined_image = wx.MemoryDC()
        self.timer = wx.Timer(self, wx.ID_ANY)
        self.timer.Start(40)
        self.bounding_box = parent.get_bounding_box()
        self.SetTitle('Tama')
        self.SetSize( (250, 250) )
        self.SetPosition( parent.DoGetPosition() )
        self.current_mood = None
        self.last_mouse_pos = wx.Point(0,0)
        self.tama_widget = TamaWidget(self)
        self.previous_update = datetime.datetime.now()
        self.screenContext = None

        self.is_border_window =    outer_or_inner_window
        self.is_inner_window = not outer_or_inner_window
        
        if wx.Platform == '__WXGTK__' :     # GTK-only, use as an event handler.
            self.Bind( wx.EVT_WINDOW_CREATE, self.DrawWindow )
        #end if
        
        #------------------------------
        
        # This handler is always required.
        self.Bind(wx.EVT_PAINT, self.OnPaint)

        self.Bind(wx.EVT_TIMER, self.OnTimer)

        self.Bind(wx.EVT_ERASE_BACKGROUND, self.DoNothing)
        
        # Enable the user to quit the app by pressing <ESC>.
        self.Bind( wx.EVT_KEY_UP, self.OnKeyDown )  # Comment this to disable.
        self.Bind( wx.EVT_RIGHT_UP, self.ShowRightMenu )
        
        # Enable window dragging.
        self.Bind( wx.EVT_MOTION, self.OnMotion )    # Comment this to disable.

        self.Bind(wx.EVT_LEFT_UP, self.OnRelease)

        self.Bind(wx.EVT_CLOSE, parent.OnClose)

        #Linux and Windows will have different ways to create this kind of transparent frame.
        if wx.Platform == '__WXMSW__':
            hwnd = self.GetHandle()
            extendedStyleSettings = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, extendedStyleSettings  | win32con.WS_EX_LAYERED | win32con.WS_CHILD)
            win32gui.SetLayeredWindowAttributes(hwnd, 0, 255, win32con.LWA_COLORKEY)
            self.SetTransparent(1)
            
        elif wx.Platform == '__WXGTK__':
            pass
        else:
            pass

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
    
    #--------------------------------------------
    
    def SetImage(self, pil_image):
        if pil_image:
            width, height = pil_image.size
            self.image_wxBitmap = wx.BitmapFromBuffer(width, height, pil_image.convert('RGB').tobytes(), pil_image.convert('RGBA').getchannel('A').tobytes())
            return

    def OnPaint( self, event ) :
        self.DrawWindow()
        event.Skip()
        return  # Very important to let all higher level handlers be called.
    #end def
    
    def DoNothing(self, event):
        pass

    def DrawWindow( self ) :
        """Implement window drawing at any time."""
        pos = self.GetPosition()
        # screenContext will be drawn to after memoryContext is given the right combined bitmap
        screenContext = wx.ScreenDC()
        #   Blit will copy the pixels from self.combined_image, which is a 
        #   MemoryDC that contains the current Tama Image to be displayed.
        #   This image is newly generated within the Tama task system, in order to
        #   reduce image display time.
        if self.image_wxBitmap and screenContext.CanDrawBitmap():
            screenContext.DrawBitmap(self.image_wxBitmap, self.GetPosition())
        del screenContext
        self.Update()
    #end def DrawWindow
    
    #--------------------------------------------
    
    def OnTimer(self, event):
        if self.tama_widget.is_moving():
            self.move_direction(self.tama_widget.get_movement_direction())
        self.SetImage(self.tama_widget.next())
        self.OnPaint(event)
        return

    def ShowRightMenu( self, event ) :
        wx.Exit()
    #end def
    
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
            self.tama_widget.is_grabbed(True)
            currPosn = event.GetPosition()
            displacement = self.dragPosn - currPosn     # always nonzero
            newPosn = self.GetPosition() - displacement
            self.SetPosition( newPosn )
            self.DrawWindow()
        #end if
        
        event.Skip()

    def move_direction(self, dir):
        if dir == 0:
            if self.bounding_box.Contains(wx.Point(self.DoGetPosition()[0], self.DoGetPosition()[1])):
                self.SetPosition(wx.Point(self.DoGetPosition()[0]-2, self.DoGetPosition()[1]))
            else:
                pass
        elif dir == 1:
            if self.bounding_box.Contains(wx.Point(self.DoGetPosition()[0]+250, self.DoGetPosition()[1])):
                self.SetPosition(wx.Point(self.DoGetPosition()[0]+2, self.DoGetPosition()[1]))
            else:
                pass
        elif dir == 2:
            if self.bounding_box.Contains(wx.Point(self.DoGetPosition()[0], self.DoGetPosition()[1]+250)):
                pass
        else:
            pass
        self.DrawWindow()

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
        return

    def set_current_mood(self, current_mood):
        self.tama_widget.set_current_mood(current_mood)
        return

    def OnClose(self, e):
        self.Destroy()

class TamaWidget():
    """
    Holds the processes that handle generating Tama from a stack of layers that are provided via (tama_stream)
    It will yield images from tama_generate() as the animation is changed by a current_mood update.
    """
    def __init__(self, parent):
        self.assets_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Assets")
        self.parent = parent
        self.bounding_box = parent.bounding_box
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
        if ishe:
            self.prev_animation = self.current_animation_name
            self.set_animation('Grabbed')
        else:
            self.set_animation(self.prev_animation)
        return

    def is_moving(self, ishe = None, dir = -1):
        '''
        This allows other classes to trigger Tama left-right movements
        Returns whether or not moving animations are playing
        Sets moving animations to play
        '''
        if ishe is None:
            return self.moving
        if self.is_grabbed():
            self.direction = None
            self.moving = False
            return False

        if dir == 0: direction = 'Move Left'
        elif dir == 1: direction = 'Move Right'
        elif dir == 2: direction = 'Falling'
        else: 
            self.moving = False
            return False
        self.direction = dir
        self.moving = ishe
        if ishe:
            self.moving = True
            self.prev_animation = self.current_animation_name
            self.set_animation(direction)
        else:
            self.moving = False
            self.set_animation(self.prev_animation)
        return

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
            self.prev_animation = anim_name
            self.is_moving(False, None)
            return
        if not self.is_moving() and random.randrange(0, 10) == 0:
            dir = random.randint(0,1)
            self.is_moving(True, dir)
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