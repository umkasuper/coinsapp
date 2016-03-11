
from kivy.lang import Builder
from coinsapp import CoinsApp

if __name__ == '__main__':
    Builder.load_file('error.kv')
    Builder.load_file('property.kv')
    CoinsApp().run()
