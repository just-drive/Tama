import wx
import ctypes
import keyboard
import ctypes
import keyboard
import time
import win32gui
import win32.lib.win32con as win32con

EnumWindows = ctypes.windll.user32.EnumWindows
EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))
GetWindowText = ctypes.windll.user32.GetWindowTextW
GetWindowTextLength = ctypes.windll.user32.GetWindowTextLengthW
IsWindowVisible = ctypes.windll.user32.IsWindowVisible

titles = []
def foreach_window(hwnd, lParam):
    if IsWindowVisible(hwnd):
        length = GetWindowTextLength(hwnd)
        buff = ctypes.create_unicode_buffer(length + 1)
        title = GetWindowText(hwnd, buff, length + 1)
        if title > 0:
            hwnd = win32gui.FindWindow(None,buff.value)
            rect = win32gui.GetWindowRect(hwnd)
            if len(buff.value) >= 1 and buff.value != 'Microsoft Text Input Application' and buff.value != 'Program Manager':
                titles.append(buff.value)


    return True

class MainPanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        self.cb_value = 'Select App'
        EnumWindows(EnumWindowsProc(foreach_window), 0)
        for title in titles:
            hwnd = win32gui.FindWindow(None,title)
            rect = win32gui.GetWindowRect(hwnd)
            try:
                if (rect[0] > 0) and (rect[1] > 0):
                    win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, rect[0], rect[1], (rect[2] - rect[0]) , (rect[3]-rect[1]) , 0)
            except:
                pass
        self.timer = wx.Timer(self, wx.ID_ANY)
        self.Bind(wx.EVT_TIMER, self.OnTimer)
        self.timer.Start(5000)
        self.combo_contents = titles
        self.cb = wx.ComboBox(self, choices=self.combo_contents,
                          value=self.cb_value, pos=(30, 10), size=(200, -1))
        gbBtn_s = wx.Button(self, label="Pin Window",pos=(90, 40))
        gbBtn_s.Bind(wx.EVT_BUTTON, self.on_selection)
        gbBtn_t = wx.Button(self, label="Unpin Window",pos=(83, 70))
        gbBtn_t.Bind(wx.EVT_BUTTON, self.on_unpin)

    def OnTimer(self,event):
        titles.clear()
        EnumWindows(EnumWindowsProc(foreach_window), 0)
        self.cb.SetItems(titles)
        self.Update()

    def on_selection(self, event):
        self.cb_value = self.cb.GetValue()
        try:
            hwnd = win32gui.FindWindow(None,self.cb_value)
            rect = win32gui.GetWindowRect(hwnd)
            win32gui.ShowWindow(hwnd,1)
            if (rect[0] > 0) and (rect[1] > 0):
                win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, rect[0], rect[1], (rect[2] - rect[0]) , (rect[3]-rect[1]) , 0)
        except:
            pass

    def on_unpin(self, event):
        try:
            hwnd = win32gui.FindWindow(None,self.cb_value)
            rect = win32gui.GetWindowRect(hwnd)
            if (rect[0] > 0) and (rect[1] > 0):
                win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, rect[0], rect[1], (rect[2] - rect[0]) , (rect[3]-rect[1]) , 0)
                EnumWindows(EnumWindowsProc(foreach_window), 0)
        except:
            pass

class WindowPinning(wx.Frame):
    def __init__(self, parent):
        super().__init__(None, -1,title='Window Pinning',size=(280, 150))
        panel = MainPanel(self)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, event):
        self.Hide()
        return
