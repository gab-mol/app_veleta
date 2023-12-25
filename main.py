from kivy.config import Config
## Configuración de dimensiones de ventana
Config.set('graphics', 'resizable', '0') 
Config.set('graphics', 'width', '600')
Config.set('graphics', 'height', '650')
from kivymd.app import MDApp
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.screen import Screen
# from kivymd.uix.label import MDLabel
from kivymd.uix.gridlayout import MDGridLayout
from kivy.properties import StringProperty, NumericProperty, DictProperty
from kivymd.uix.card import MDCard
# from kivymd.uix.button import MDFlatButton
# from kivymd.uix.dialog import MDDialog
from kivy.lang import Builder
from kivy.clock import Clock

import os
import configparser as confp
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from threading import Thread
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
    '''Conexión con API y extracción'''
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

    @staticmethod
    def a_cardinales(grados:int):
        
        '''Transforma dirección del viento en grados (°) a 
        puntos cardinales (Eng).
        
        Parametros
            grados: valor en grados a transformar.'''
        
        if grados >= 355 or grados <= 5:
            return "N"
        elif grados > 5 and grados <= 30:
            return "NNE"
        elif grados > 30 and grados <= 60:
            return "NE"
        elif grados > 60 and grados < 85:
            return "ENE"
        elif grados >= 85 and grados <= 95:
            return "E"
        elif grados > 95 and grados <= 120:
            return "ESE"
        elif grados > 120 and grados <= 150:
            return "SE"
        elif grados > 150 and grados < 175:
            return "SSE"
        elif grados >= 175 and grados <= 185:
            return "S"
        elif grados > 185 and grados <= 210:
            return "SSO"
        elif grados > 210 and grados <= 240:
            return "SO"
        elif grados > 240 and grados <= 265:
            return "OSO"
        elif grados >= 265 and grados <= 275:
            return "O"
        elif grados > 275 and grados <= 300:
            return "ONO"
        elif grados > 300 and grados <= 330:
            return "NO"
        elif grados > 330 and grados <= 355:
            return "NNO"

    @staticmethod
    def prob_prec(predicc:pd.DataFrame, h_prec:int) -> np.int64:
        '''
        Obtiene la fila del Datafreme de condiciones predichas por horas,
        la correspondiente a la cantidad indicada de horas a futuro.

        ## Parametros
            predicc: elemento 'hourly' de la respuesta de API, \
convertido a pandas.Dataframe.
            h_prec: número de horas futuras sumadas a la actual.

        ## Return
            Valor de probablilidad de precipitaciones para hora futura.
        '''

        # Hora futura deseada
        ts = datetime.now() + timedelta(hours=h_prec)
        ts_h = ts.strftime('%H')
        
        # convertir columna a timestamp, y luego a str solo con la hora
        predicc['time'] = pd.to_datetime(predicc['time']).dt.strftime('%H')
        fila_predicc = predicc.loc[predicc['time'] == ts_h]

        # Retornar valor
        return fila_predicc["precipitation_probability"].iloc[0]


# KivyMD ####################################################################
class ScMg(MDScreenManager):
    reloj = StringProperty()
    a_viento = NumericProperty()
    a_viento_s= StringProperty()
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.app = MainApp.get_running_app()
        
        # Bucle de actualización de GUI
        self.cargar_dat()
        Clock.schedule_interval(self.cargar_dat,850)

    def cargar_dat(self, *args):
        '''Toma datos de la propiedad `meteo_data` de la instancia de `MainApp`, 
        y actualiza la GUI.
        Pensada para ejecutarse regularmente con `kivy.clock.Clock`.
        '''
        print("\Cargando GUI con datos...\n")
        
        # Recuperar datos desde app
        cond_ahora = self.app.meteo_data["current"]
        cond_pred = self.app.meteo_data["hourly"]
        
        direc = cond_ahora["wind_direction_10m"]
        
        # Barra info
        time = pd.to_datetime(cond_ahora["time"])
        time = time - pd.Timedelta(hours=3) # GMT-0 a GMT-3
        lat = self.app.meteo_data["latitude"]
        lon = self.app.meteo_data["longitude"]
        
        self.a_viento = direc
        self.a_viento_s = str(direc)              
        self.reloj = time.strftime(f"Condiciones a las %H:%M hs del %d/%m/%y \
|| lat: {lat}, long: {lon}")

        # Tarjetas   
        prob_ll = str(MeteoDat.prob_prec(
            pd.DataFrame(cond_pred), 
            h_prec= 1))
        veloc = str(cond_ahora["wind_speed_10m"])+" km/h"
        direc_s  = MeteoDat.a_cardinales(direc)
        temp = str(cond_ahora["temperature_2m"])+" °C"

        ## Recargar datos de tarjetas
        self.limp_tarj()
        for tit, dat, col in zip(["Precipitaciones en 1 h","Velocidad del viento",
                                  "Viento desde","Temperatura"],
                                [prob_ll, veloc, direc_s, temp],
                                ["#76C7E8", "#99E876", "#B3E876", "#E89090"]):
            self.ids.tabla.add_widget(MetDat(tit=tit, dat=dat, col=col))
            
    def limp_tarj(self):
        '''Limpiar tarjetas'''
        self.ids.tabla.clear_widgets()


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
    

class DatTab(MDGridLayout):pass


class MainApp(MDApp):
    title= "Veleta"
    
    meteo_data = DictProperty()
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.con = MeteoDat()
        
    def build(self):
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Red"
        
        # Descargar datos y lanzar hilo de actualización cada 900s
        self.meteo_data = self.con.descar_datos()
        Thread(target=Clock.schedule_interval(self.consulta_api,900),
               daemon=True).start()
        
        return ScMg()
    
    def consulta_api(self, *args):
        '''
        Actualizar información si la aplicación 
        se deja abierta más de 15 minutos.
        '''
        print("\n\nEjecundo: consulta_api\n\n")
        try:
            self.meteo_data = self.con.descar_datos()
        except:
            raise Exception("Error en consulta a API. \n\
No se pueden actualizar los datos.")
        
        
if __name__ == "__main__":

    MainApp().run()