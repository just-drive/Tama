import wx

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

class TamaMoodEvent(wx.PyCommandEvent):
    """description of class"""
    def __init__(self, evt_type, id, current_mood = None):
        wx.PyCommandEvent.__init__(self, evt_type, id)
        self.current_mood = current_mood
        return

    def set_current_mood(self, val):
        self.current_mood = val
        return

    def get_current_mood(self):
        return self.current_mood

    def get_conditions(self):
        return self.current_mood.get('Condition')

    def get_happiness_condition(self):
        return self.current_mood.get('Condition').get('Happiness')

    def get_satiation_condition(self):
        return self.current_mood.get('Condition').get('Satiation')

    def get_energy_condition(self):
        return self.current_mood.get('Condition').get('Energy')

    def get_health_condition(self):
        return self.current_mood.get('Condition').get('Health')

    def get_stats(self):
        return self.current_mood.get('Stats')

    def get_happiness_value(self):
        return self.current_mood.get('Stats').get('Happiness')

    def get_satiation_value(self):
        return self.current_mood.get('Stats').get('Satiation')

    def get_energy_value(self):
        return self.current_mood.get('Stats').get('Energy')

    def get_health_value(self):
        return self.current_mood.get('Stats').get('Health')

    def get_happiness_max(self):
        return self.current_mood.get('Max').get('Happiness')

    def get_maxes(self):
        return self.current_mood.get('Max')

    def get_satiation_max(self):
        return self.current_mood.get('Max').get('Satiation')

    def get_energy_max(self):
        return self.current_mood.get('Max').get('Energy')

    def get_health_max(self):
        return self.current_mood.get('Max').get('Health')

    def get_modifiers(self):
        return self.current_mood.get('Modifiers')

