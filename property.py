
from kivy.uix.modalview import ModalView
from kivy.properties import StringProperty


class Property(ModalView):

    password = StringProperty()
    username = StringProperty()

    def __init__(self, **kwargs):
        self.username = kwargs['username']
        self.password = kwargs['password']
        ModalView.__init__(self, **kwargs)


