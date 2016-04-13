# -*- coding: utf-8 -*-

import json
from functools import partial

import kivy
import requests
from bs4 import BeautifulSoup
from kivy.app import App
from kivy.clock import Clock
from kivy.loader import Loader
from kivy.properties import StringProperty, BooleanProperty, NumericProperty, ListProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.settings import Settings
from kivy.uix.image import AsyncImage
from kivy.resources import resource_find

from urlparse import urlparse

from error import ErrorPopup
from settings.password import SettingPassword

import os.path

Loader.num_workers = 5

kivy.require('1.8.0')


class CoinScroll(ScrollView):
    def __init__(self, **kwargs):
        self.register_event_type('on_scroll_down_event')
        super(CoinScroll, self).__init__(**kwargs)

    def on_scroll_stop(self, *args, **kwargs):
        result = super(CoinScroll, self).on_scroll_stop(*args, **kwargs)
        #print self.scroll_y
        #if self.scroll_y <= 0:
        self.dispatch('on_scroll_down_event')

        return result

    def on_scroll_down_event(self, *args):
        pass


class AsyncImageProxy(AsyncImage):
    def __init__(self, **kwargs):
        super(AsyncImageProxy, self).__init__(**kwargs)

    def _load_source(self, *args):
        source = self.source

        file_name = '.' + urlparse(self.source).path
        if os.path.isfile(file_name):
            source = file_name

        if not source:
            if self._coreimage is not None:
                self._coreimage.unbind(on_texture=self._on_tex_change)
            self.texture = None
            self._coreimage = None
        else:
            if not self.is_uri(source):
                source = resource_find(source)
            self._coreimage = image = Loader.image(source,
                nocache=self.nocache, mipmap=self.mipmap,
                anim_delay=self.anim_delay)

            image.bind(on_load=self._on_source_load)
            image.bind(on_texture=self._on_tex_change)
            self.texture = image.texture

        #super(AsyncImageProxy, self)._load_source(*args)

    def _on_source_load(self, value):
        super(AsyncImageProxy, self)._on_source_load(value)
        # сохраним на диск
        file_name = '.' + urlparse(self.source).path
        #super(AsyncImageProxy, self).save(file_name)
        if not os.path.isfile(file_name):
            self.texture.save(file_name)


class RequestButton(Button):
    have = NumericProperty()
    all = NumericProperty()
    name = StringProperty()
    color = ListProperty()
    text_request_button = StringProperty()

    def __init__(self, **kwargs):
        coin = kwargs['coin']
        self.name = coin['name']
        self.all = coin['all_coins']
        self.have = coin['have_coins']
        self.set_color_active()
        self.text_request_button = self.get_text_request_button()

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

    def change_have_coins(self, have):
        self.have += 1 if have else -1
        self.text_request_button = self.get_text_request_button()


class RequestButtonCountry(RequestButton):
    img = StringProperty()

    def __init__(self, **kwargs):
        ip_address = App.get_running_app().config.get('connection', 'ip_address')
        coin = kwargs['coin']
        self.img = ip_address + coin['img'] if coin['img'] else ""
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
        ip_address = App.get_running_app().config.get('connection', 'ip_address')

        coin = kwargs['coin']
        self.key = coin['key']
        self.have = coin['have']
        self.country = coin['country']
        self.flag = ip_address + coin['flag']
        self.img = ip_address + coin['img']
        self.year = coin['year']
        self.description = coin['description']

        BoxLayout.__init__(self, **kwargs)

        self.rect = None
        self.points = None

    def ownership_change(self, have):
        readonly = App.get_running_app().config.get('connection', 'readonly') == '1'
        if readonly:
            return
        post_data = {'id': self.key, 'have': have}
        r = App.get_running_app().send_http_post("/euro/save", post_data)
        if 'result' in r:
            if r['result'] == 'ok':
                self.have = have
                App.get_running_app().change_coin_count(have, self.year, self.country)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            touch.grab(self)
            self.points = touch.pos

        return super(BoxLayout, self).on_touch_down(touch)

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            d = (self.points[0] - touch.pos[0], self.points[1] - touch.pos[1])
            if abs(d[1] < 20):
                if d[0] < -30:
                    if not self.have:
                        self.ownership_change(True)
                if d[0] > 30:
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
    pass


class CoinViewYear(CoinView):
    pass


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


json_settings = '''
[
        {
            "type": "string",
            "title": "Имя пользователя",
            "desc": "Имя пользователя",
            "section": "connection",
            "key": "username"
        },
        {
            "type": "password",
            "title": "Пароль",
            "desc": "Пароль пользователя",
            "section": "connection",
            "key": "password"
        },
        {
            "type": "bool",
            "title": "Режим",
            "desc": "Режим работы только чтение",
            "section": "connection",
            "key": "readonly",
            "true": "auto"
        },
        {
            "type": "string",
            "title": "Адрес сервера",
            "desc": "Адрес сервера",
            "section": "connection",
            "key": "ip_address"
        }
    ]
'''


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

        self.settings_cls = Settings

        self.use_kivy_settings = False

        self.title = "2euro memorable"

    def on_pause(self):
        # Here you can save data if needed
        return True

    def on_resume(self):
        # Here you can check if any data needs replacing (usually nothing)
        pass

    """
    значение параметров конфигурации по умолчинию
    """
    def build_config(self, config):
        """
        Задает значение конфигурации по умолчанию
        """
        config.setdefaults('connection',
                           {
                               'username': 'guest',
                               'password': 'guest',
                               'readonly': True,
                               'ip_address': 'http://192.168.5.106:8081'
                           }
                           )

    """
    построитель конфигурации
    """
    def build_settings(self, settings):
        """
        """

        settings.register_type('password', SettingPassword)
        settings.add_json_panel('Подключение', self.config, data=json_settings)

    """
    измнение параметров конфигурации
    """
    def on_config_change(self, config, section, key, value):
        """
        """
        pass

    """
    закрытие окна с настройкаим
    """
    def close_settings(self, settings):
        """
        """
        self.root.ids.property_button.state = 'normal'
        super(CoinsApp, self).close_settings(settings)

        self.current_button_request = None
        self.on_start()

    def on_start(self):
        """
        Выполняется при старте приложения
        :return: None
        """
        # Property(auto_dismiss=False, username="maksim", password="maksim").open()

        self.authorization = self.login()

        coins_group_layout = self.root.ids.coins_group_layout

        # очищаем все кнопки если они есть
        coins_group_layout.clear_widgets()

        # создаем страны
        countries = self.request_all_countries()
        # добавляем в него кнопки со странами
        for country in countries:
            btn = RequestButtonCountry(coin=country)
            coins_group_layout.add_widget(btn)

        # создаем года
        years = self.request_all_years()
        # добавляем в него кнопки со странами
        for year in years:
            btn = RequestButtonYear(coin=year)
            coins_group_layout.add_widget(btn)

        # позиционируемся на последюю запись
        if coins_group_layout.children:
            self.root.ids.coins_group_scroll_view.scroll_to(coins_group_layout.children[0])
            self.on_pressed_request_button(coins_group_layout.children[0])

    def login(self):
        """
        логиниться на сайт
        :return:
        """

        username = self.config.get('connection', 'username')
        password = self.config.get('connection', 'password')
        ip_address = self.config.get('connection', 'ip_address')

        url = ip_address + '/login/'

        self.client = requests.session()
        try:
            self.client.get(url)
        except requests.ConnectionError:
            ErrorPopup(title=u'Ошибка', info=u'Ошибка подключения').open()
            return False
        csrftoken = self.client.cookies['csrftoken']

        payload = {'username': username, 'password': password, 'csrfmiddlewaretoken': csrftoken, 'next': '/'}
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
        ip_address = self.config.get('connection', 'ip_address') + '/api/v1'

        try:
            headers = {'Content-type': 'application/json'}
            r = self.client.post(ip_address + url, data=json.dumps(post_data), headers=headers)
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

    """
    вставка монеток
    """
    def insert_coins(self, *tmp):
        """
        вставляет монетки во view
        :param largs:
        :return:
        """
        if not self.coins:  # нечего вставлять вышли
            return

        coins_layout = self.root.ids.coins_layout

        coin_height = coins_layout.children[0].height   # высота одной монеты
        coins_scroll_count = round(self.root.ids.coins_scroll_view.height / coin_height)   # сколько всего видно монет
        coins_lost_count = round(self.root.ids.coins_scroll_view.viewport_size[1]*self.root.ids.coins_scroll_view.scroll_y / coin_height)   # сколько осталось до конца монет

        if coins_lost_count > coins_scroll_count:  # еще не нужно вставлять
            return

        # вставляем одну монеты и запускаемся по новой
        view_coin = CoinViewFactory.factory(instance=self.current_button_request, coin=self.coins.pop(0))
        coins_layout.add_widget(view_coin)

        percent = (100.0 * view_coin.height) / float(coins_layout.height)
        self.root.ids.coins_scroll_view.scroll_y += percent / 100.0

        Clock.schedule_once(partial(self.insert_coins), 0.1)

    """
    сообщение от скроллера
    """
    def on_scroll_down_callback(self):
        """
        сообщание от ScrollView где отображены монеты
        :return:
        """
        if self.coins is not None:
            coins_layout = self.root.ids.coins_layout
            if not coins_layout.children:
                return

            if not self.coins:
                return

            Clock.schedule_once(partial(self.insert_coins), 0.1)
            return


    """
    запрос монеток по нажатию кнопки
    """
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
            if Loader.pool is not None:     # если что то было в овчерди на загрузку,отключаем
                Loader.stop()
            coins_layout.clear_widgets()    # удаляем все что было вставлено
            coins_scroll_view.scroll_y = 1  # скроллер на начало

            coins_scroll_view.height = self.root.height

            height = 0
            while self.coins:
                view_coin = CoinViewFactory.factory(instance=instance, coin=self.coins.pop(0))
                coins_layout.add_widget(view_coin)
                height += view_coin.height
                if coins_scroll_view.height + 2*view_coin.height < height:
                    break

    """
    нажатие на кнопку запроса монеток
    """
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

        # взводим таймер на реальный запрос
        Clock.schedule_once(partial(self.request_coins, instance), 0.1)

    """
    нажатие на кнопку настроек
    """
    def on_press_property(self, instance):
        if instance.state == 'down':
            self.open_settings()

    """
    отыскивает группу монет по имени
    """
    def get_coins_group_by_name(self, name):
        coins_group_layout = self.root.ids.coins_group_layout

        for children in coins_group_layout.children:
            if children.name == name:
                return children
        return None

    """
    изменение количества монет во владении
    """
    def change_coin_count(self, have, year, country):
        for name in [u"all", year, country]:
            group = self.get_coins_group_by_name(name)
            if group:
                group.change_have_coins(have)


