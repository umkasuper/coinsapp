# -*- coding: utf-8 -*-

import kivy
from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty, BooleanProperty, NumericProperty, ListProperty
from kivy.clock import Clock
from kivy.uix.popup import Popup

from bs4 import BeautifulSoup

from error import ErrorPopup
from property import Property

from functools import partial

import requests
import json

from kivy.loader import Loader

Loader.num_workers = 5

kivy.require('1.0.8')

# SERVER_PATH = 'http://127.0.0.1:8080/'
#SERVER_PATH = 'http://127.0.0.1:8081'
SERVER_PATH = 'http://192.168.1.166'
SERVER_API_PATH = SERVER_PATH + '/api/v1'


class CoinScroll(ScrollView):
    def __init__(self, **kwargs):
        self.register_event_type('on_scroll_down_event')
        super(CoinScroll, self).__init__(**kwargs)

    def on_scroll_stop(self, *args, **kwargs):
        result = super(CoinScroll, self).on_scroll_stop(*args, **kwargs)

        if self.scroll_y <= 0:
            self.dispatch('on_scroll_down_event')

        return result

    def on_scroll_down_event(self, *args):
        pass


class RequestButton(Button):
    have = NumericProperty()
    all = NumericProperty()
    name = StringProperty()
    color = ListProperty()

    def __init__(self, **kwargs):
        coin = kwargs['coin']
        self.name = coin['name']
        self.all = coin['all_coins']
        self.have = coin['have_coins']
        self.set_color_active()

        super(RequestButton, self).__init__(**kwargs)

    def get_text_request_button(self):
        return ""

    @staticmethod
    def gettype():
        return ''

    @staticmethod
    def get_authorization():
        return App.get_running_app().authorization

    def is_selected(self):
        return App.get_running_app().current_button_request == self

    def set_color_active(self):
        self.color = [1, 0.3, 0.3, 1]

    def set_color_passive(self):
        self.color = [0.2, 0.1, 0.1, 1]


class RequestButtonCountry(RequestButton):
    img = StringProperty()

    def __init__(self, **kwargs):
        coin = kwargs['coin']
        self.img = SERVER_PATH + coin['img'] if coin['img'] else ""
        super(RequestButtonCountry, self).__init__(**kwargs)

    def get_text_request_button(self):
        return "%s (%s%s%s)" % \
               (u"Все страны" if self.name == 'all' else self.name,
                self.have if self.get_authorization() else "",
                "/" if self.get_authorization() else "",
                self.all)

    @staticmethod
    def gettype():
        return 'country'


class RequestButtonYear(RequestButton):
    def __init__(self, **kwargs):
        self.type = 'year'
        super(RequestButtonYear, self).__init__(**kwargs)

    def get_text_request_button(self):
        return "%s (%s%s%s)" % (self.name,
                                self.have if self.get_authorization() else "",
                                "/" if self.get_authorization() else "", self.all)

    @staticmethod
    def gettype():
        return 'year'


class CoinView(BoxLayout):
    have = BooleanProperty(False)
    img = StringProperty()
    country = StringProperty()
    flag = StringProperty()
    year = StringProperty()
    description = StringProperty()

    def __init__(self, **kwargs):
        coin = kwargs['coin']
        self.key = coin['key']
        self.have = coin['have']
        self.country = coin['country']
        self.flag = SERVER_PATH + coin['flag']
        self.img = SERVER_PATH + coin['img']
        self.year = coin['year']
        self.description = coin['description']

        BoxLayout.__init__(self, **kwargs)

        self.rect = None
        self.points = None

    def ownership_change(self, have):
        post_data = {'id': self.key, 'have': have}
        r = CoinsApp.send_http_post("/euro/save", post_data)
        if r['result']:
            self.have = have

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            touch.grab(self)
            self.points = touch.pos

        return super(BoxLayout, self).on_touch_down(touch)

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            d = (self.points[0] - touch.pos[0], self.points[1] - touch.pos[1])
            if abs(d[1] < 10):
                if d[0] < -20:
                    if not self.have:
                        self.ownership_change(True)
                if d[0] > 20:
                    if self.have:
                        self.ownership_change(False)
            return True
        return super(BoxLayout, self).on_touch_move(touch)

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            return True
        return super(BoxLayout, self).on_touch_up(touch)


class CoinViewCountry(CoinView):
    def __init__(self, **kwargs):
        CoinView.__init__(self, **kwargs)


class CoinViewYear(CoinView):
    def __init__(self, **kwargs):
        CoinView.__init__(self, **kwargs)


class CoinViewFactory:
    def __init__(self):
        pass

    @staticmethod
    def factory(**kwargs):
        instance = kwargs['instance']
        if instance.gettype() == 'country':
            return CoinViewCountry(**kwargs)
        if instance.gettype() == 'year':
            return CoinViewYear(**kwargs)
        return CoinView(**kwargs)


class CoinsApp(App):
    client = None  # клиент для авторизации
    authorization = False
    coins = None
    current_button_request = None

    """
    конструктор
    """

    def __init__(self, **kwargs):
        super(CoinsApp, self).__init__(**kwargs)

    def on_start(self):
        """
        Выполняется при старте приложения
        :return: None
        """
        #Property(auto_dismiss=False, username="maksim", password="maksim").open()

        self.authorization = self.login()

        coins_group_layout = self.root.ids.coins_group_layout

        # создаем страны
        countries = self.request_all_countries()
        # добавляем в него кнопки со странами
        for country in countries:
            btn = RequestButtonCountry(coin=country)
            coins_group_layout.add_widget(btn)

        # создаем года
        years = self.request_all_years()
        # добавляемв него кнопки со странами
        for year in years:
            btn = RequestButtonYear(coin=year)
            coins_group_layout.add_widget(btn)

        if coins_group_layout.children:
            self.on_pressed_request_button(coins_group_layout.children[0])

    def login(self):
        """
        логиниться на сайт
        :return:
        """
        url = SERVER_PATH + '/login/'
        self.client = requests.session()
        try:
            self.client.get(url)
        except requests.ConnectionError:
            ErrorPopup(title=u'Ошибка', info=u'Ошибка подключения').open()
            return False
        csrftoken = self.client.cookies['csrftoken']
        payload = {'username': 'maksim', 'password': 'maksim', 'csrfmiddlewaretoken': csrftoken, 'next': '/'}
        try:
            r = self.client.post(url, data=payload, headers=dict(Referer=url))

            if r.status_code == 200:
                root_xml = BeautifulSoup(r.text, 'html.parser')
                loginerror = root_xml.findAll("ul", {"class": "errorlist"})
                if len(loginerror) != 0:
                    ErrorPopup(title=u'Ошибка', info=u'Ошибка авторизации').open()
                    return False
                return True

        except requests.ConnectionError:
            return False

    def send_http_post(self, url, post_data):
        """
        метод вызывающий http post
        :param post_data: данные для передачи
        :param url: адрес сайта
        :return:
        """
        try:
            headers = {'Content-type': 'application/json'}
            r = self.client.post(SERVER_API_PATH + url, data=json.dumps(post_data), headers=headers)
            return json.loads(r.content)
        except requests.ConnectionError:
            return None

    def request_all_countries(self):
        """
        запрашивает все страны члены евро
        :return:
        """
        r = self.send_http_post('/euro/list_countries', None)
        return r if r else ()

    def request_all_years(self):
        """
        запрашивает все года
        :return:
        """
        r = self.send_http_post('/euro/list_years', None)
        return r if r else ()

    def on_scroll_down_callback(self):
        """
        сообщание от ScrollView где отображены монеты
        :return:
        """
        if self.coins is not None:
            coins_layout = self.root.ids.coins_layout
            while self.root.ids.coins_scroll_view.scroll_y <= 0:
                if self.coins:
                    # view_coin = CoinView(coin=self.coins.pop(0))
                    view_coin = CoinViewFactory.factory(instance=self.current_button_request, coin=self.coins.pop(0))
                    coins_layout.add_widget(view_coin)

                    percent = (100.0 * view_coin.height) / float(coins_layout.height + 1)
                    self.root.ids.coins_scroll_view.scroll_y += percent / 100.0
                else:
                    break

    def request_coins(self, instance, *tmp):
        """
        формирует зпрос по http монет
        :param instance:
        :param largs:
        :return:
        """
        coins_layout = self.root.ids.coins_layout
        coins_scroll_view = self.root.ids.coins_scroll_view
        post_data = {'what': instance.name, 'type': instance.gettype()}
        self.coins = self.send_http_post('/euro/what', post_data)
        if self.coins is not None:
            coins_layout.clear_widgets()
            coins_scroll_view.scroll_y = 1

            main_box_layout = self.root
            height = 0
            while self.coins:
                # view_coin = CoinView(coin=self.coins.pop(0))
                view_coin = CoinViewFactory.factory(instance=instance, coin=self.coins.pop(0))
                coins_layout.add_widget(view_coin)

                height += view_coin.height
                if main_box_layout.height + view_coin.height < height:
                    break

    def on_pressed_request_button(self, instance):
        """
        нажатие на кпопку семейсва Request
        :param instance:
        """
        # кэшируем последний запрос
        if self.current_button_request == instance:
            return

        if self.current_button_request:
            self.current_button_request.set_color_active()
        self.current_button_request = instance
        self.current_button_request.set_color_passive()

        Clock.schedule_once(partial(self.request_coins, instance), 0.1)

    def on_property_dismiss(self, prop, button):
        if prop.ok:
            pass
        button.state = 'normal'

    def on_press_property(self, instance):
        if instance.state == 'down':
            prop = Property(username="maksim", password="maksim")
            prop.bind(on_dismiss=lambda x: self.on_property_dismiss(prop, instance))
            prop.open()

        #if instance.state == 'normal':
        #    self.root.ids.sm.current = 'screen1'


