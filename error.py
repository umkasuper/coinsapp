# -*- coding: utf-8 -*-

from kivy.uix.popup import Popup
from kivy.properties import StringProperty


class ErrorPopup(Popup):

    info = StringProperty()

    def __init__(self, **kwargs):
        self.info = kwargs['info']
        Popup.__init__(self, **kwargs)
