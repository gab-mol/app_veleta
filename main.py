# from kivy.config import Config
# ## Configuración de dimensiones de ventana
# Config.set('graphics', 'resizable', '0') 
# Config.set('graphics', 'width', '1000')
# Config.set('graphics', 'height', '500')
from kivymd.app import MDApp
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.screen import Screen
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.properties import StringProperty
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivy.lang import Builder

import os
import configparser as confp
import requests
import pandas as pd

from pprint import pprint
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
        pprint(json["current"])
        print("\nPor horas:\n")
        prediciones = pd.DataFrame(json["hourly"])
        actual = pd.DataFrame(json["current"])

        #return {"actual":actual,"prediciones":prediciones}
        return actual, prediciones



# KivyMD ####################################################################
class ScMg(MDBoxLayout):pass

class Veleta(Screen):pass

class MainApp(MDApp):
    title= "Veleta"

    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Red"

        return ScMg()


if __name__ == "__main__":

    MainApp().run()