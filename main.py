from kivy.config import Config
## Configuración de dimensiones de ventana
# Config.set('graphics', 'resizable', '0') 
Config.set('graphics', 'width', '600')
Config.set('graphics', 'height', '660')
from kivymd.app import MDApp
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.screen import Screen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivy.properties import StringProperty, NumericProperty, DictProperty, ListProperty
from kivymd.uix.card import MDCard
from kivymd.uix.list import OneLineListItem
from kivymd.uix.label import MDLabel
# from kivymd.uix.dialog import MDDialog
from kivy.lang import Builder
from kivy.clock import Clock
import asynckivy as ak


import multitasking

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

    def meteo_url(self):
        return self.cfg["endpoint"]["origdata"]

    def loc_url(self):
        return self.cfg["endpoint"]["localidad"]  

class MeteoDat:
    '''Conexión con API y extracción'''
    def __init__(self, conf:Config) -> None:
        self.cfgp = conf
        self.url = self.cfgp.meteo_url()

    def descar_datos(self) -> dict:
        '''
        Hace el pedido a la API.

        return: diccionario con los datos meteorológicos.
        '''
        print("Haciendo consulta")
        try:
            with requests.get(self.url) as req:
                respuesta = req.json()
                respuesta["err"] = False
            return respuesta
        except:
            print("Error: No se obtuvo respuesta desde API")
            return {"err": True}

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


class GeoCod:
    
    '''Administra consultas a "Geocoding API"'''
    
    def __init__(self, config:Config):
        '''
        Parámetros
            config: instancia de clase de configuración.
        '''
        self.config = config
        self.endp = self.config.loc_url()
        
    
    async def consulta_api(self,input:str) -> dict:
        '''
        Confecciona URL para y los usa para consultar a
        API-Geocoding.
        
        Parámetros
            input: nombre de localidad deseada.
        '''
        input = input.replace(" ", "+")
        param = f"name={input}&count={20}&language=es&format=json"
        url = self.endp+param
        try:
            with requests.get(url) as req:
                dic_ciud = req.json()
                dic_ciud["err"] = False
                
                # crear clave por orden
                nitems = range(len(dic_ciud['results']))
                for i in nitems:
                    dic_ciud['results'][i]["id"] = str(i)
            return dic_ciud
        except:
            print("\nERROR requests")
            return {"err":True}
            #raise Exception("Error de conexión: Geocoding API")
        
    def listar_res(self, dic_ciud:dict) -> list:
        '''
        Crea lista de elementos para mostrar al usario las opciones
        derivadas de su búsqueda.
        
        Parámetros
            dic_ciud: diccionario obtenido de la API.
        '''
        
        str_res_ciud = []
        print(dic_ciud["err"],"\n",list(dic_ciud.keys()))     
        if dic_ciud["err"]:
            str_res_ciud.append(["E","...sin resultados"])
        else:
            if "results" not in dic_ciud.keys():
                str_res_ciud.append(["E","-    sin resultados    - "])
            else:
                for c, id in zip(dic_ciud['results'], 
                        range(len(dic_ciud['results']))):
                    str_res_ciud.append([
                        id,
                        [c["name"], c["country"], 
                        c["latitude"], c["longitude"]]
                    ])
        
        return str_res_ciud
    
    
# KivyMD ####################################################################
class ScMg(MDScreenManager):
    
    # Screen: main
    localid = StringProperty()
    reloj = StringProperty()
    coord = StringProperty()
    a_viento = NumericProperty()
    a_viento_s= StringProperty()
    
    # Screen: eleg_loc
    ciud_input = StringProperty()
    lista_res = ListProperty()
    dicc_res = DictProperty()
    ciud_eleg = StringProperty()
    
    def __init__(self, err=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.app = MainApp.get_running_app()

        
        if err:
        # Si ocurre error de conexión    
            self.current = "conex_err" 
        else:  
            # Bucle de actualización de GUI
            self.cargar_dat()
            Clock.schedule_interval(self.cargar_dat,850)

        # PROVISORIO: BORRAR ESTAS LÍNEAS AL FINAL
        self.current = "eleg_loc"
        # self.lista_ciud()

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
        
        self.localid = "<proximamente>"
        self.a_viento = direc
        self.a_viento_s = str(direc)              
        self.reloj = time.strftime(f"%H:%M hs. del %d/%m/%y")
        self.coord = f"Latitud: {lat}, Longitud: {lon}"
        # Tarjetas   
        prob_ll = "   "+str(MeteoDat.prob_prec(
            pd.DataFrame(cond_pred), 
            h_prec= 1))+" %"
        veloc = str(cond_ahora["wind_speed_10m"])+" km/h"
        direc_s  = "   "+MeteoDat.a_cardinales(direc)
        temp = str(cond_ahora["temperature_2m"])+" °C"

        ## Recargar datos de tarjetas
        self.limp_tarj()
        for tit, dat, col in zip(["Precipitaciones en 1 h ","Velocidad del viento ",
                                  "Viento desde ","Temperatura "],
                                [prob_ll, veloc, direc_s, temp],
                                ["#76C7E8", "#99E876", "#B3E876", "#E89090"]):
            self.ids.tabla.add_widget(MetDat(tit=tit, dat=dat, col=col))
            
    def limp_tarj(self):
        '''Limpiar tarjetas'''
        self.ids.tabla.clear_widgets()

    def lista_ciud(self, lista_res):
        '''Cargar lista de ciudades en GUI.
        
        Parámetros
            lista_res: lista a insertar en `MDlist.`
        '''
        # print(lista_res)
        
        self.ids.list_ciud.clear_widgets()
        for c in lista_res:
            self.ids.list_ciud.add_widget(
                CiudItem(id=str(c[0]), text=str(c[1]),
                app=self.app
                )
            )

    def buscar_ciud(self):
        '''
        Consulta a API de geolocalización, y carga GUI con los resultados
        '''
        async def cons():
            '''Lanzar consulta asincrónica, listado de resultados y envío a 
            widget `MDlist`'''
            self.dicc_res = await self.app.localid.consulta_api(self.ciud_input)            
            self.lista_res = self.app.localid.listar_res(self.dicc_res)
            print(self.lista_res)
            self.lista_ciud(self.lista_res)
        ak.start(cons())

    def confirmar_ciud(self):
        if self.ciud_eleg == "E":
            print("Usuario hizo click en mensaje de error")
        else:
            print(self.ciud_eleg, "es id de ciudad elegida en json/dict")
            
        # En progreso...

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


class CiudItem(OneLineListItem):
    '''Ciudades encontradas por 
    API de geo-posicionamiento, mostradas por GUI.'''
    id = StringProperty()
    
    def __init__(self, id:str, app, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.app = app
        self.id = id
        
    def click(self):
        
        # print(self.id, "CiudItem.click")
        
        self.app.root.ciud_eleg = self.id
        # return super().on_touch_down(touch)
        
class MainApp(MDApp):
    title= "Veleta"
    
    meteo_data = DictProperty()
    endp = StringProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.conf = Config()
        self.con = MeteoDat(self.conf)
        self.localid = GeoCod(self.conf)
    def build(self):
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Orange"
        
        # Descargar datos y lanzar hilo de actualización cada 900s
        self.meteo_data = self.con.descar_datos()
        ## Avisar de error de conexión al usuario
        if self.meteo_data["err"]:
            self.endp = self.conf.meteo_url()
            return ScMg(err=True)
        else:
            Thread(target=Clock.schedule_interval(self.consulta_api,900),
                daemon=True).start()
            
            return ScMg()
    
    def consulta_api(self, *args):
        '''
        Actualizar información si la aplicación 
        se deja abierta más de 15 minutos.
        '''
        print("\n\nEjecutando: consulta_api\n\n")
        try:
            self.meteo_data = self.con.descar_datos()
        except:
            raise Exception("Error en consulta a API. \n\
No se pueden actualizar los datos.")
        
    def pantalla(self,pantalla):
        self.root.current = pantalla
        
        
if __name__ == "__main__":

    MainApp().run()