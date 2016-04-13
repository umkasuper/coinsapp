from kivy.lang import Builder
from coins_app.coinsapp import CoinsApp

__version__ = '1.0.0'

# import sys
# from os import environ
# from os.path import join, dirname, realpath
#
#
# def prep_win_standalone():
#     class DummyStream():
#         def __init__(self):
#             pass
#
#         def write(self, data):
#             pass
#
#         def read(self, data):
#             pass
#
#         def flush(self):
#             pass
#
#         def close(self):
#             pass
#
#     sys.stdin = DummyStream()
#     sys.stdout = DummyStream()
#     sys.stderr = DummyStream()
#     sys.__stdin__ = DummyStream()
#     sys.__stdout__ = DummyStream()
#     sys.__stderr__ = DummyStream()
#
#     exec_dir = dirname(realpath(sys.argv[0]))
#     environ['KIVY_DATA_DIR'] = join(exec_dir, 'data')
#
# prep_win_standalone()

if __name__ == '__main__':
    Builder.load_file('coins_app/error.kv')
    Builder.load_file('coins_app/settings/password.kv')
    CoinsApp().run()
