from kivy.lang import Builder
from coins_app.coinsapp import CoinsApp


if __name__ == '__main__':
    Builder.load_file('coins_app/error.kv')
    Builder.load_file('coins_app/settings/password.kv')
    CoinsApp().run()
