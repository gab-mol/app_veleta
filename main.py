from kivy.config import Config
## Configuración de dimensiones de ventana
#Config.set('graphics', 'resizable', '0') 
Config.set('graphics', 'width', '800')
Config.set('graphics', 'height', '950')
from kivymd.app import MDApp
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.screen import Screen
from kivymd.uix.label import MDLabel
from kivymd.uix.gridlayout import MDGridLayout
from kivy.properties import StringProperty, NumericProperty
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivy.lang import Builder

import os
import configparser as confp
import requests
import pandas as pd
import datetime
from pprint import pprint

Builder.load_file("vista.kv")
# Extracción de datos Meteorológicos ########################################
class Config:
    '''Cargar archivo de configuración.'''
    def __init__(self) -> None:
        DIR = os.getcwd()
        self.cfg = confp.ConfigParser()
        self.cfg.read(os.path.join(DIR, "config.ini"))

    def endpoint_url(self):
        return self.cfg["endpoint"]["origdata"]
    

class MeteoDat:
    '''Conexión con API y extracción,'''
    def __init__(self) -> None:
        self.cfgp = Config()
        self.url = self.cfgp.endpoint_url()

    def descar_datos(self) -> dict:
        '''
        Hace el pedido a la API.

        return: diccionario con los datos meteorológicos.
        '''
        try:
            respuesta = requests.get(self.url)
            return respuesta.json()
        except:
            raise Exception("No se obtuvo respuesta desde API")

    def datos_ord(self):
        '''Entrega todos los datos ordenadas en pandas.Dataframe 
        para su uso en app.'''
        json = self.descar_datos()
        pprint(list(json.keys()))
        pprint(json["current"])
        print("\nPor horas:\n")
        predicciones = pd.DataFrame(json["hourly"])
        actual = pd.DataFrame(json["current"])

        #return {"actual":actual,"prediciones":prediciones}
        return actual, predicciones



# KivyMD ####################################################################
class ScMg(MDScreenManager):
    reloj = StringProperty()
    a_viento = NumericProperty()
    a_viento_s= StringProperty()
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.app = MainApp.get_running_app()
        
        # Descarga desde API
        self.data = MeteoDat().descar_datos()

        # Datos para barra info
        time = pd.to_datetime(self.data["current"]["time"])
        time = time - pd.Timedelta(hours=3) # GMT-0 a GMT-3
        lat = self.data["latitude"]
        lon = self.data["longitude"]
        self.a_viento = self.data["current"]["wind_direction_10m"]
        self.a_viento_s = str(self.a_viento)
        # print(type(time), time)
        self.reloj = time.strftime(f"Condiciones a las %H:%M hs del %d/%m/%y \
|| lat: {lat}, long: {lon}")

        # datos para grilla de info
        self.cargar_dat(
            str(self.data["current"]["rain"]),
            str(self.data["current"]["wind_speed_10m"]),
            str(self.data["current"]["wind_direction_10m"]),
            str( self.data["current"]["temperature_2m"])
        )
        
    def cargar_dat(self, prec, veloc, direc, temp):
        print(prec, veloc, direc, temp)
        for tit, dat, col in zip(["precip","veloc_v","direc_v","temp"],
                                [prec, veloc, direc, temp],
                                ["#76C7E8", "#99E876", "#99E876", "#E89090"]):
            self.ids.tabla.add_widget(MetDat(tit=tit, dat=dat, col=col))
            
            
class Veleta(Screen):pass


class MetDat(MDCard):
    tit = StringProperty()
    dat = StringProperty()
    col = StringProperty()
    
    def __init__(self, tit:str, dat:str, col:str,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tit = tit
        self.dat = dat
        self.md_bg_color = col


class DatTab(MDGridLayout):
    pass
    # tit = StringProperty()
    # veloc = StringProperty()
    # direc = StringProperty()
    # otro  = StringProperty()
    
    # def __init__(self, lista:list, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.add_widget(MetDat(tit="prob_precip", dat=lista[0], col="#76C7E8"))
    #     self.add_widget(MetDat(tit="veloc_v", dat=lista[1], col="#99E876"))
    #     self.add_widget(MetDat(tit="direc_v", dat=lista[2], col="#99E876"))
    #     self.add_widget(MetDat(tit="otro", dat=lista[3], col="#E6E6E6"))


class MainApp(MDApp):
    title= "Veleta"
    # Builder.load_file("vista.kv")
    def build(self):
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Red"

        return ScMg()

    # def cargar_dat(self, prob, veloc, direc, otro):
    #     print(prob, veloc, direc, otro)
    #     for tit, dat, col in zip(["prob_precip","veloc_v","direc_v","otro"],
    #                             [prob, veloc, direc, otro],
    #                             ["#76C7E8", "#99E876", "#99E876", "#E6E6E6"]):
    #         self.root.ids.tabla.add_widget(MetDat(tit=tit, dat=dat, col=col))
    
    def on_start(self):pass
        # self.cargar_dat()


if __name__ == "__main__":

    MainApp().run()