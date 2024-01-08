from kivy.config import Config
## Configuración de dimensiones de ventana
# Config.set('graphics', 'resizable', '0') 
Config.set('graphics', 'width', '600')
Config.set('graphics', 'height', '800')
from kivymd.app import MDApp
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.screen import Screen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivy.properties import StringProperty, BooleanProperty, NumericProperty
from kivy.properties import DictProperty, ListProperty, ObjectProperty
from kivymd.uix.card import MDCard
from kivymd.uix.list import OneLineListItem
from kivymd.uix.button import MDIconButton, MDFlatButton
from kivymd.uix.scrollview import MDScrollView
from kivy.lang import Builder
from kivy.clock import Clock
import asynckivy as ak
from kivymd.uix.dialog import MDDialog

import os
import configparser as confp
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from threading import Thread
from pprint import pprint

__version__ = "Beta"

Builder.load_file("vista.kv")
# Extracción de datos Meteorológicos ########################################
def hora_futura(fh:int, str=True):
    '''Suma una cantidad determinada de horas a la hora actual.
    ### Parámetros
        - h: horas a sumar
        - str: (`bool`) por defecto hora en string
    ### return
        - hora (24hs) en `str` o `int`
    '''
    ts = datetime.now() + timedelta(hours=fh)
    return ts.strftime('%H') if str else int(ts.strftime('%H'))

def hs_restantes() -> int:
    '''Retorna número de horas 
    restantes en el día.'''
    ahora = int(datetime.now().strftime('%H'))
    hasta_24 = range(ahora,23)

    return len(hasta_24)
def hora_loc(time, solo_h=False) -> str:
    '''
    Ajusta hora desde GMT-0 a GMT-3 y lo formatea como strting:
    `%H:%M hs. del %d/%m/%y`.
    ### Parámetros
       - time: timestamp entregado en json desde API.'''
    time = pd.to_datetime(time)
    time = time - pd.Timedelta(hours=3) # GMT-0 a GMT-3
    if solo_h:
        t_str= "%H:%M hs."
    else:
        t_str = "%H:%M hs. del %d/%m/%y"
    return time.strftime(t_str)  

class Config:
    '''Administra archivo de configuración.'''
    def __init__(self) -> None:
        DIR = os.getcwd()
        self.CFG_R = os.path.join(DIR, "config.ini")
        self.cfg = confp.ConfigParser()
        self.cfg.read(os.path.join(DIR, self.CFG_R))

    def cargar_loc(self) -> list:
        '''
        Lee del archivo de configuración nombre, latitud y longitud.

        ### return
            - Si las variables contienen "None" -> `[False, None]`  
                ("Sin conf", datos vacios)
            - Si las variables contienen datos > `[True, dict]`  
                ("Con conf", diccionario con nombre, latitud y longitud).
        '''
        url = self.cfg["endpoint"]["openmeteo"]
        loc_cfg = self.cfg["configvars"]
        nom, lat = loc_cfg["nombre"], loc_cfg["latitud"]
        long = loc_cfg["longitud"]
        
        if nom == "None" or lat == "None" or long == "None" or url == "None":
            print("\nNo se ha seleccionado localidad.\n")
            return [False, None]
        else:
            print(f"\nCiudad guardada: {nom}\n\
                Se hace pedido dedatos para esta.")
            return [True, {"nom":nom,"lat":lat,"long":long}]
    
    def meteo_url_set_coord(self, lat:str, long:str):
        '''
        Guardar URL con la latitud y longitud de la 
        localidad seleccionada.
        
        ### Parámetros
            - lat: latitud `str(float)` 
            - long: longitud `str(float)`
        '''
        url = [
            self.cfg["endpoint"]["openmeteo_set"],
            f"latitude={lat}&longitude={long}",
            self.cfg["endpoint"]["arg_curr"],
            self.cfg["endpoint"]["arg_hor"]
        ]
        
        self.cfg["endpoint"]["openmeteo"] = "".join(url)
        
        with open(self.CFG_R, "w") as cfg_ar:
            self.cfg.write(cfg_ar)

    def meteo_url(self):
        '''Obtener URL (endpoint API open-meteo) del archivo de configuración.'''
        return self.cfg["endpoint"]["openmeteo"]

    def loc_url(self):
        '''Obtener URL (endpoint geocoding-API open-meteo) del archivo de configuración.'''
        return self.cfg["endpoint"]["localidad"]
    
    def guardar_loc(self, nombre:str, lat:str, log:str, pais:str):
        '''
        Guarda coordenadas y nombre de la localidad elegida.
        
        ### Parámetros
            - nombre: nombre de la ciudad.
            - lat: latitud `str(float)`
            - log: longitud `str(float)`
            - pais: nombre del país
        '''
        
        self.cfg["configvars"] = {
            "nombre":nombre,
            "latitud":lat,
            "longitud":log,
            "pais":pais
        }
        
        with open(self.CFG_R, "w") as cfg_ar:
            self.cfg.write(cfg_ar)
            
            
class MeteoDat:
    '''
    Conexión con API, extracción y formateo.
    '''
    def __init__(self, conf:Config) -> None:
        '''
        Parámetros
            - conf: Instancia de clase administradora \
                de archivo de configuración `Config`.
        '''
        self.cfgp = conf

    def descar_datos(self) -> dict:
        '''
        Hace el pedido a la API.

        return: diccionario con los datos meteorológicos.
        '''
        print("Haciendo consulta")
        url = self.cfgp.meteo_url()
        
        try:
            with requests.get(url) as req:
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
    def prob_prec(predicc:pd.DataFrame, h_prec:int) -> list:
        '''
        Obtiene la fila del Datafreme de condiciones predichas por horas,
        la correspondiente a la cantidad indicada de horas a futuro.

        ### Parámetros
            predicc: elemento 'hourly' de la respuesta de API, \
convertido a pandas.Dataframe.
            h_prec: número de horas futuras sumadas a la actual.

        ### Return
            - `list`
                - [0] `pandas.Dataframe` Valor de probablilidad de precipitaciones para las horad futura
                del mismo día.
                - [1] `str` con hora actual de referencia (hs)
                - [2] `int` n° horas futuras hoy
        '''

        # Hora futura deseada
        ts_h = hora_futura(0)
        # convertir columna a timestamp, y luego a str solo con la hora
        predicc['time'] = pd.to_datetime(predicc['time']).dt.strftime('%H')
       
        h_futuras_hoy = [hs for hs in list(predicc['time']) if hs > ts_h]
        print("\nHoras restantes: ",h_futuras_hoy)
        
        fila_predicc = predicc.loc[predicc['time'] >= ts_h]
        print(fila_predicc)
        
        # Retornar valor
        return [fila_predicc[["time","precipitation_probability"]], ts_h, len(h_futuras_hoy)]
    
    @staticmethod
    def tabla_pronost(json:dict)-> pd.DataFrame:
        '''Recibe diccionario (json clave "Hourly" en respuesta de API)
        lo pasa a pandas.DataFrame y transforam columna "time" de timestamp a
        str con horas en formato 24 hs.'''
        df = pd.DataFrame(json)
        df['time'] = pd.to_datetime(df['time']).dt.strftime('%H')
        return df
        
        
        
        
class GeoCod:
    
    '''Administra consultas a "Geocoding API"'''
    
    def __init__(self, config:Config):
        '''
        Parámetros
            config: Instancia de clase administradora \
                de archivo de configuración `Config`.
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
                l = dic_ciud['results']
                for c, id in zip(l, 
                        range(len(l))):
                    if 'country' not in c.keys():
                        dic_ciud['results'][id]["country"] = "???"
                                  
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
    vrs = StringProperty()
    
    #    veleta 
    a_viento = NumericProperty()
    a_viento_s= StringProperty()
    
    #   tarjetas
    prob_ll = ListProperty()
    hf = StringProperty()
    
    tstamp = StringProperty()
    tstamp_f = StringProperty()
    temp= StringProperty()
    hum = StringProperty()
    lluv = StringProperty() 
    veloc = StringProperty()
    direc_s = StringProperty()      
    raf = StringProperty()
    
    actual = BooleanProperty(True)
    
    # Screen: eleg_loc
    ciud_input = StringProperty()
    lista_res = ListProperty()
    dicc_res = DictProperty()
    ciud_eleg_id = StringProperty()
    
    def __init__(self, err=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.app = MainApp.get_running_app()
        self.vrs = self.app.conf.cfg["info"]["version"]
        print("con_loc:", self.app.con_loc)
        
        self.contador_h = 1
        self.hf = hora_futura(self.contador_h)
        
        if self.app.con_loc:
            self.meteo_data = self.app.con.descar_datos()
            if self.meteo_data["err"]:
                self.endp = self.conf.meteo_url()
                self.root.current = "conex_err"
            else:
                self.app.consulta_api()
                Thread(target=Clock.schedule_interval(self.app.consulta_api,900),
                    daemon=True).start()
                
                # Barra info y 
                self.cargar_barra()
        else:
            self.current = "eleg_loc"

    def cargar_barra(self, *args):
            '''Cargar datos en Barra superior y banner. 
            Lanza hilo de actualización'''
            lat = self.app.meteo_data["latitude"]
            lon = self.app.meteo_data["longitude"]
            nom = self.app.conf.cfg["configvars"]["nombre"]
            pais = self.app.conf.cfg["configvars"]["pais"]
            
            self.localid = f'{nom}, {pais}'
            self.coord = f"Latitud: {lat}, Longitud: {lon}"       
            
            self.set_data()
            self.tstamp = hora_loc(self.cond_ahora["time"], solo_h=True)
            self.tstamp_f = hora_loc(self.cond_ahora["time"])
            self.tiempo_ahora()
            # self.recarg_tj()
            # lanzar actualización
            Clock.schedule_interval(self._rutina, 850)
            self.current = "main"

    def _rutina(self, *args):
        self.set_data()
        self.tiempo_ahora()
        self.recarg_tj()
        # self.tiempo_ahora()
    
    def set_data(self):
        self.cond_ahora = self.app.meteo_data["current"]
        
        pronost = self.app.meteo_data["hourly"]
        self.t_pronost = MeteoDat.tabla_pronost(pronost)
        
    def tiempo_ahora(self):
        '''Mostrar en tarjetas datos del momento.'''
        # señalizar que son datos del momento
        self.actual= True
        
        
        self.temp= str(self.cond_ahora["temperature_2m"])+" °C"
        self.hum= str(self.cond_ahora["relative_humidity_2m"])+" %"
        self.lluv= str(self.cond_ahora["rain"])+" mm"
        self.veloc= str(self.cond_ahora["wind_speed_10m"])+" km/h"
        direc = self.cond_ahora["wind_speed_10m"]
        self.direc_s= "   "+MeteoDat.a_cardinales(direc)
        self.raf= str(self.cond_ahora["wind_gusts_10m"])+" km/h"
        
        # esta variable solo puede ser futura... (pero la quiero mostrar igual)
        self.prob_ll = self.probab_ll(hora_futura(1))
        
        # actualizar tarjetas
        self.recarg_tj()
        
        # rosa de los vientos
        self.a_viento = direc
        
    def pronost_tiempo(self):
        '''Mostrar en tarjetas datos pronosticados.'''
        print("Pronóstico para:",self.hf)        
        # señalizar que son predicciones
        self.actual= False
        
        # Mostrar en tarjetas pronóstico para `ScMg.hf` (hora futura)
        t = self.t_pronost
        self.temp= str(t.loc[t["time"]==self.hf,"temperature_2m"].values[0])+" °C"
        self.hum= str(t.loc[t["time"]==self.hf,"relative_humidity_2m"].values[0])+" %"
        self.lluv= str(t.loc[t["time"]==self.hf,"rain"].values[0])+" mm"
        self.veloc= str(t.loc[t["time"]==self.hf,"wind_speed_10m"].values[0])+" km/h"
        direc = float(t.loc[t["time"]==self.hf,"wind_speed_10m"].values[0])
        self.direc_s= "   "+MeteoDat.a_cardinales(direc)
        self.raf= str(t.loc[t["time"]==self.hf,"wind_gusts_10m"].values[0])+" km/h"
        #  pronóstico lluvia
        self.prob_ll = self.probab_ll(self.hf)
        
        # actualizar tarjetas
        self.recarg_tj()
        
        # rosa de los vientos
        self.a_viento = direc
        
    def probab_ll(self, h) -> list:
        '''
        Obtener probabilidad de lluvia para cualquiera de 
        las horas de día.
        ### Parámetro
            - h: hora deseada (formato 24hs)
        ### Return
            - `list`
                - [0] valor de probabilidad de lluvia
                - [1] hora  de predicción (formato 24hs) correspondiente 
        '''
        pll_en1h = self.t_pronost.loc[
            self.t_pronost["time"] == h,
            "precipitation_probability"
        ].values[0]
        return [f"{pll_en1h} %", h]
        
    def recarg_tj(self):
        '''Actualizar tarjetas de condiciones meteorológicas.'''
        ## Recargar datos de tarjetas
        self.limp_tarj()
        
        # Señalizar actual o predicción
        c_solido = [
            (.91, .56, .56, 1), 
            (.56, .70, .91, 1), 
            (.56, .91, .90, 1), 
            (.60, .91, .46, 1), 
            (.70, .91, .46, 1),  
            (.56, .91, .77, 1)
        ]
        if self.actual:
            col_tarj = c_solido
        else:
            col_tarj = [(0, 0, 0, 0) for i in range(len(c_solido))]
        
        # Declaración de tarjetas en bucle
        for tit, dat, col, lin in zip(
            ["Temperatura ",
            "Humedad rel.",
            "Lluvia",
            "Velocidad \ndel viento ",
            "Viento desde ",
            "Vel. ráfagas"], 
            [self.temp, 
             self.hum, 
             self.lluv, 
             self.veloc, 
             self.direc_s,
             self.raf],
            col_tarj,
            c_solido):
            self.ids.tabla.add_widget(MetDat(tit=tit, dat=dat, 
                 col=col, line_color=lin, x_pos1=0.25, x_pos2=0.72))
        #  pronóstico lluvia por debajo
        self.ids.sep.add_widget(
            MetDat(tit=f"Precipitaciones a las [b]{self.prob_ll[1]} hs[/b]:", 
                    dat=self.prob_ll[0], col="#76C7E8", x_pos1=0.35, x_pos2=0.7)
        )
            
    def limp_tarj(self):
        '''Limpiar tarjetas.'''
        self.ids.tabla.clear_widgets()
        self.ids.sep.clear_widgets()

    def hora_futura(self):
        '''
        :Acción botón "reloj" a la derecha de pronóstico:
        
        Agrega una hora al pronóstico que se muestra
        (propiedad `ScMg.hf`).'''
        self.contador_h += 1
        if self.contador_h > hs_restantes():
            self.contador_h = 1
        
        print(f"hora_futura({self.contador_h}):\n",
            hora_futura(self.contador_h))
        self.hf = hora_futura(self.contador_h)
        self.pronost_tiempo()
            

    # Métodos Screen: eleg_loc              ######
    def lista_ciud(self, lista_res):
        '''Cargar lista de ciudades en GUI.
        
        Parámetros
            lista_res: lista a insertar en `MDlist.`
        '''
        
        self.ids.list_ciud.clear_widgets()
        for c in lista_res:
            self.ids.list_ciud.add_widget(
                CiudItem(id=str(c[0]), 
                    text=f"{c[1][0]}, {c[1][1]} ({c[1][2]}, {c[1][3]})",
                app=self.app
                )
            )

    def buscar_ciud(self):
        '''
        Consulta a API de geolocalización, y carga GUI con los resultados.
        '''
        async def cons():
            '''Lanzar consulta asincrónica, listado de resultados y envío a 
            widget `MDlist`'''
            self.dicc_res = await self.app.localid.consulta_api(self.ciud_input)            
            self.lista_res = self.app.localid.listar_res(self.dicc_res)
            self.lista_ciud(self.lista_res)
        ak.start(cons())

    def confirmar_ciud(self):
        if self.ciud_eleg_id == "E":
            print("Usuario hizo click en mensaje de error")
        else:
            loc_eleg = self.dicc_res["results"][int(self.ciud_eleg_id)]
            print(loc_eleg["name"], "es id de ciudad elegida en json/dict")
            lat = loc_eleg["latitude"]
            long = loc_eleg["longitude"]
            # Guardado de Ciudad y coord.
            self.app.conf.guardar_loc(
                loc_eleg["name"], 
                lat, 
                long,
                loc_eleg["country"]
            )
            self.app.conf.meteo_url_set_coord(
                lat=lat, long=long
            )
            # Se eligió localidad
            self.app.con_loc = True
            
            print("ejecutando self.app.consulta_api")
            self.app.consulta_api()


class MetDat(MDCard):
    '''Tarjeta de datos meteorológicos. Pensada para usarse en bucle.'''
    tit = StringProperty()
    dat = StringProperty()
    col = StringProperty()
    x_pos1 = NumericProperty()
    x_pos2 = NumericProperty()

    
    def __init__(self, tit:str, dat:str, col:str, boton=False,
                 *args, **kwargs):
        '''
        ### Parámetros
            - tit: Variable meteorológica a informar.
            - dat: Valor de la variable meteorológica.
            - col: Color de la tarjeta. (Hexadecimal)
            - boton: (defoult: `False`) activa el botón-ícono para cambiar \
                el número de horas futuras de la predicción.
        '''        
        super().__init__(*args, **kwargs)

        self.app = MainApp.get_running_app()
        self.tit = tit
        self.dat = dat
        self.md_bg_color = col
        
        # Botón para pronóstico de lluvia
        if boton:
            self.add_widget(
                MDIconButton(
                    size_hint= (None,None,),
                    pos_hint= {'top': 1, 'right':0},
                    icon= "clock",
                    on_press=self.precip_prob,
                    text=f"[b]+ {self.app.h_ll} h[/b]"
                )
            )
    
    def precip_prob(self, *args):
        '''Método invocado por el botón para sumar 
        horas al pronósitico de lluvia.'''
        self.app.h_ll += 1
        print(self.app.h_ll)
        self.app.root.probab_ll(recargar=True)
        
        
class DatTab(MDGridLayout):pass


class ScrIm(MDScrollView):pass


class CiudItem(OneLineListItem):
    '''Ciudades encontradas por 
    API de geo-posicionamiento, mostradas por GUI.'''
    id = StringProperty()
    
    def __init__(self, id:str, app, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.app = app
        self.id = id
        
    def click(self):
        self.app.root.ciud_eleg_id = self.id
        
class MainApp(MDApp):
    title= "Veleta"
    
    meteo_data = DictProperty()
    endp = StringProperty()
    conf_carg = ListProperty()
    
    # False: no se guardó localidad de referencia 
    # True: hay localidad de referencia guardada
    con_loc = BooleanProperty()
    
    # error de conexión
    conex_err = BooleanProperty()
    
    # hora futura para predicción de lluvia
    h_ll = NumericProperty(1)
    
    # info emergente
    dialog = None 
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Instanciación de objeto de configuración, verif/seteo
        self.conf = Config()
        self.conf_carg = self.conf.cargar_loc()
        
        #  localidad seteada? True/False
        print("inició. Datos:::",self.con_loc)
        self.con_loc = self.conf_carg[0]
        
        self.localid = GeoCod(self.conf)
        self.con = MeteoDat(self.conf)
        
    def build(self):
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Orange"
        
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
        
    def volver_main(self):
        if self.con_loc:
            
            self.pantalla("main")
        print(self.root.ciud_eleg_id)
    

    # Lanzar info emergente
    def vent_info(self):
        '''Lanzar información sobre App.'''
        if not self.dialog:
            self.dialog = MDDialog(
                text=f'{self.conf.cfg["info"]["app_ia"]}\n\
{self.conf.cfg["info"]["app_ib"]}\n\
Versión: {self.conf.cfg["info"]["version"]} \n\n\
{self.conf.cfg["info"]["firma"]}',
                buttons=[
                    MDFlatButton(
                        text="OK",
                        theme_text_color="Custom",
                        text_color=self.theme_cls.primary_color,
                        on_press= self.cerr_info
                    ),
                ],
            )
        # self.dialog.text = self.conf.cfg["info"]["app_i"]
        self.dialog.open()            
        
    # Cerrar info emergente
    def cerr_info(self, inst):
        '''Orden para cerrar info app. emergente.'''
        if self.dialog:
            self.dialog.dismiss(force=True) 
if __name__ == "__main__":

    MainApp().run()