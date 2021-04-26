import wx
import keyboard
import pickle
import mouse
########################################################################
class MacroRecorder(wx.Frame):

    #----------------------------------------------------------------------
    def __init__(self):
        wx.Frame.__init__(self, None, -1, "Macro Manager",size=(270, 110))
        panel = wx.Panel(self, wx.ID_ANY)
        gbBtnNoBmp = wx.Button(panel, label="Record Mouse Macro")
        gbBtn_s = wx.Button(panel, label="Run Mouse Macro")
        gbBtnNoBmp.Bind(wx.EVT_BUTTON, self.onPressMe)
        gbBtn_s.Bind(wx.EVT_BUTTON, self.onPressMe2)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(gbBtnNoBmp, 0, wx.CENTER|wx.ALL, 5)
        sizer.Add(gbBtn_s, 0, wx.CENTER|wx.ALL, 5)
        panel.SetSizer(sizer)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    #----------------------------------------------------------------------
    def onPressMe(self, event):
        """"""
        mouse_events = []
        mouse.hook(mouse_events.append)
        mouse.wait(button='middle', target_types=('up', 'down', 'double'))
        mouse.unhook(mouse_events.append)
        try:
            with wx.FileDialog(self, "Save to file:", ".", "",wildcard = "Tama Macro (*.macrot)|*.macrot", style = wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as dlg:
                if (dlg.ShowModal() == wx.ID_OK):
                    path = dlg.GetPath()
                    with open(path, 'wb') as f:
                        pickle.dump(mouse_events, f)
                        f.close()
                        dlg.Destroy()
        except:
            pass

    def onPressMe2(self, event):
        try:
            with wx.FileDialog(self, "Open File:", ".", "", wildcard = "Tama Macro (*.macrot)|*.macrot", style = wx.FD_OPEN |wx.FD_FILE_MUST_EXIST) as dlg:
                if (dlg.ShowModal() == wx.ID_OK):
                    path = dlg.GetPath()
                    with open(path,'rb') as f:
                        mouse_events2 = pickle.load(f)
                        f.close()
                        dlg.Destroy()
                    mouse.play(mouse_events2)
        except:
            pass

    def OnClose(self, event):
        self.Hide()
        return
