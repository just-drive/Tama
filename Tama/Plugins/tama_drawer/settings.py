import wx
import webbrowser

class CSMSettings(wx.Dialog):
    def __init__(self, settings, *args, **kwargs):
        wx.Dialog.__init__(self, None, -1, "Child Safety Settings",size=(320, 80))
        self.settings = settings

        self.panel = wx.Panel(self)
        self.button_ok = wx.Button(self.panel, label="OK")
        self.button_cancel = wx.Button(self.panel, label="Cancel")
        self.button_ok.Bind(wx.EVT_BUTTON, self.onOk)
        self.button_cancel.Bind(wx.EVT_BUTTON, self.onCancel)

        self.checkboxes = []
        for i in range(1):
            checkbox = wx.CheckBox(self.panel, label="Child Safety Mode")
            checkbox.SetValue(self.settings[i])
            self.checkboxes.append(checkbox)

        self.sizer = wx.BoxSizer()
        for checkbox in self.checkboxes:
            self.sizer.Add(checkbox)
        self.sizer.Add(self.button_ok)
        self.sizer.Add(self.button_cancel)

        self.panel.SetSizerAndFit(self.sizer)

    def onCancel(self, e):
        self.EndModal(wx.ID_CANCEL)

    def onOk(self, e):
        for i in range(1):
            self.settings[i] = self.checkboxes[i].GetValue()
        self.EndModal(wx.ID_OK)

    def GetSettings(self):
        print(self.settings)
        return self.settings



class Settings(wx.Frame):
    def __init__(self, *args, **kwargs):
        wx.Frame.__init__(self, None, -1, "Settings",size=(230, 170))

        self.panel = wx.Panel(self)
        self.button = wx.Button(self.panel, label="Child Safety Mode")
        self.button.Bind(wx.EVT_BUTTON, self.onSettings)
        self.button2 = wx.Button(self.panel, label="Update")
        self.button3 = wx.Button(self.panel, label="About")
        self.button4 = wx.Button(self.panel, label="Developer Info")
        self.button2.Bind(wx.EVT_BUTTON, self.onUpdate)
        self.button3.Bind(wx.EVT_BUTTON, self.onAbout)
        self.button4.Bind(wx.EVT_BUTTON, self.onDeveloper)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.button,0, wx.CENTER|wx.ALL, 5)
        self.sizer.Add(self.button2,0, wx.CENTER|wx.ALL, 5)
        self.sizer.Add(self.button3,0, wx.CENTER|wx.ALL, 5)
        self.sizer.Add(self.button4,0, wx.CENTER|wx.ALL, 5)
        self.panel.SetSizerAndFit(self.sizer)  
        self.Show()

        self.settings = [False]

    def onSettings(self, e):
        settings_dialog = CSMSettings(self.settings, self)
        res = settings_dialog.ShowModal()
        if res == wx.ID_OK:
            self.settings = settings_dialog.GetSettings()
        settings_dialog.Destroy()
    
    def onAbout(self,e):
         aboutBox = wx.MessageDialog(None, "Tama v1.0" + "\n" + 
                                     "Uses the BSD-3 License by the Open Source Inititive"+'\n'
                                     +'Developed by William Anderson, Dorsey Roten, and Meron Solomon','About Tama', wx.OK)
         answer=aboutBox.ShowModal()
         aboutBox.Destroy()


    def onDeveloper(self,e):
        webbrowser.open_new_tab('https://github.com/just-drive/Tama')

    def onUpdate(self,e):
         try:
            with wx.FileDialog(self, "Open File", ".", "", wildcard = "Tama Update (*.tupdate)|*.update", style = wx.FD_OPEN |wx.FD_FILE_MUST_EXIST) as dlg:
                if (dlg.ShowModal() == wx.ID_OK):
                    path = dlg.GetPath()
                    dlg.Destroy()
         except:
            pass


app = wx.App(False)
win = Settings(None)
app.MainLoop()