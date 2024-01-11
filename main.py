from kivy.config import Config
## Configuración de dimensiones de ventana
Config.set('graphics', 'resizable', '0')
Config.set('graphics', 'width', '600')
Config.set('graphics', 'height', '800')
from kivymd.app import MDApp
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.screen import Screen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivy.properties import StringProperty, BooleanProperty, NumericProperty
from kivy.properties import DictProperty, ListProperty
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
from datetime import datetime, timedelta
from threading import Thread

__version__ = "1.0"

Builder.load_file("vista.kv")


# Funciones relacionadas al manejo de las horas
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


# Extracción de datos Meteorológicos ########################################
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
                # print(respuesta["hourly"]["time"])
            return respuesta
        except:
            print("Error: No se obtuvo respuesta desde API")
            return {"err": True}

    @staticmethod
    def a_cardinales(grados:int):
        
        '''Transforma dirección del viento (°) a 
        puntos cardinales.
        
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
    def tabla_pronost(json:dict)-> pd.DataFrame:
        '''Recibe diccionario (json clave "Hourly" en respuesta de API)
        lo pasa a pandas.DataFrame y transforam columna "time" de timestamp a
        str con horas en formato 24 hs.'''
        df = pd.DataFrame(json)
        df['time_h'] = pd.to_datetime(df['time']).dt.strftime('%H')
        df['time_d'] = pd.to_datetime(df['time']).dt.strftime('%d/%m')
        # df.to_csv("/home/gabrielmolina/Escritorio/Proyectos/app_veleta_env/ver.csv")
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
    col_cir = StringProperty()
    #   tarjetas
    prob_ll = StringProperty()
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
        
        self.contador_h = hora_futura(1,str=False)
        print("seteo en init de contador_h =",self.contador_h)
        if self.app.con_loc:
            self.meteo_data = self.app.con.descar_datos()
            if self.meteo_data["err"]:
                self.endp = self.conf.meteo_url()
                self.root.current = "conex_err"
            else:
                print("ejecución else en init")
                self.app.consulta_api()
                Thread(target=Clock.schedule_interval(self.app.consulta_api,900),
                    daemon=True).start()
                
                # Barra info y 
                self.cargar_barra()
        else:
            self.current = "eleg_loc"

    def cargar_barra(self, *args):
            '''
            Carga datos en Barra superior y banner. 
            Lanza reloj (`kivy.clock.Clock`) de actualización.
            '''
            lat = self.app.meteo_data["latitude"]
            lon = self.app.meteo_data["longitude"]
            nom = self.app.conf.cfg["configvars"]["nombre"]
            pais = self.app.conf.cfg["configvars"]["pais"]
            
            self.localid = f'{nom}, {pais}'
            self.coord = f"Latitud: {lat}, Longitud: {lon}"       
            
            self.set_data()
            self.tstamp = self.app.hora_loc(self.cond_ahora["time"], solo_h=True)
            self.tstamp_f = self.app.hora_loc(self.cond_ahora["time"])
            self.tiempo_ahora()

            # lanzar actualización
            Clock.schedule_interval(self._rutina, 850)
            self.current = "main"

    def reiniciar_hf(self):
        '''Hora/día 1 h al futuro'''
        print("se ejecuta reiniciar_hf()")
        self.hf =f'{self.t_pronost.iloc[self.contador_h]["time_h"]} \
hs. {self.t_pronost.iloc[self.contador_h]["time_d"]}'

    def _rutina(self, *args):
        '''
        Bloque objetivo de rutina de actualización de datos 
        mostrados en GUI (`kivy.clock.Clock`).
        
        Las consultas a las APIs las realiza paralelamente
        un hilo (`threading.Thread`) (ver `ScMg.__init__`).
        '''
        
        self.set_data()
        self.tiempo_ahora()
        self.recarg_tj()
    
    def set_data(self):
        '''
        - Toma datos de las respuestas de las APIs (desde instancia de
        clase `App`) y declara propiedades de esta instancia de
        clase `MDScreenManager`.
        
        - Castea respuesta de API open-meteo desde `dict` (viene de json) a 
        `pandas.Dataframe`.
        
        - Setea propiedad `ScMg.hf` (hora/dia de pronóstico) a 1 h en 
        el futuro. (`ScMg.reiniciar_hf`)
        '''
        self.cond_ahora = self.app.meteo_data["current"]
        
        pronost = self.app.meteo_data["hourly"]
        self.t_pronost = MeteoDat.tabla_pronost(pronost)
        self.reiniciar_hf()
    
    def tiempo_ahora(self):
        '''Mostrar en tarjetas datos del momento.'''
        # señalizar que son datos del momento
        self.actual= True
        self.col_cir = "ff9800"
        
        # reinicia contador para 1 h al futuro al precionar
        self.contador_h = hora_futura(1,str=False)
        self.reiniciar_hf()
        
        self.temp= str(self.cond_ahora["temperature_2m"])+" °C"
        self.hum= str(self.cond_ahora["relative_humidity_2m"])+" %"
        self.lluv= str(self.cond_ahora["rain"])+" mm"
        self.veloc= str(self.cond_ahora["wind_speed_10m"])+" km/h"
        direc = self.cond_ahora["wind_direction_10m"]
        self.direc_s= "   "+MeteoDat.a_cardinales(direc)
        self.raf= str(self.cond_ahora["wind_gusts_10m"])+" km/h"
        
        # esta variable solo puede ser futura... (pero la quiero mostrar igual)
        self.prob_ll = self.probab_ll(hora_futura(0,str=False))
        
        # actualizar tarjetas
        self.recarg_tj()
        
        # rosa de los vientos
        self.a_viento = direc
            
    def pronost_tiempo(self):
        '''
        Muestra en tarjetas y veleta de la GUI, los valores pronosticados
        para el índice que indique `ScMg.contador_h` (1 fila por cada una 
        de las 48 hs que se obtienen de API open-meteo).
        '''
        # señalizar que son predicciones
        self.actual= False
        self.col_cir = "e9e9e9"
        
        # Mostrar en tarjetas pronóstico
        t = self.t_pronost
        self.hf =f'{t.iloc[self.contador_h]["time_h"]} \
hs. {t.iloc[self.contador_h]["time_d"]}'
        self.temp= str(t.iloc[self.contador_h]["temperature_2m"])+" °C"
        self.hum= str(t.iloc[self.contador_h]["relative_humidity_2m"])+" %"
        self.lluv= str(t.iloc[self.contador_h]["rain"])+" mm"
        self.veloc= str(t.iloc[self.contador_h]["wind_speed_10m"])+" km/h"
        direc = float(t.iloc[self.contador_h]["wind_direction_10m"])        
        self.direc_s= "   "+MeteoDat.a_cardinales(direc)
        self.raf= str(t.iloc[self.contador_h]["wind_gusts_10m"])+" km/h"
        #  pronóstico lluvia
        self.prob_ll = self.probab_ll(self.contador_h)        
        # actualizar tarjetas
        self.recarg_tj()
        
        # rosa de los vientos
        self.a_viento = direc    
        
    def hora_pronostico(self):
        '''
        :Acción botón "reloj" a la derecha de pronóstico:
        
        Agrega una hora al pronóstico que se muestra
        (propiedad `ScMg.hf`).'''
        
        # Pronóstico: Se pueden mostrar hasta 24 hs a futuro
        ahora = hora_futura(0,str=False)
        hs_restantes = ahora+24
        # hs_restantes = len(range(ahora, mas24h))
        
        print("ahora:",ahora)
        print("mas24h:",hs_restantes)
        self.contador_h += 1
        if self.contador_h > hs_restantes:
            self.contador_h = ahora
        self.pronost_tiempo()

    def probab_ll(self, indice:int) -> str:
        '''
        Obtener probabilidad de lluvia para cualquiera de las 48 filas 
        correspondientes a las 48 hs de predicciones obtendidas de 
        API open-meteo.
        ### Parámetro
            - indice: índice de fila (se usa en `pandas.Dataframe.iloc`)
        ### Return
            - `str`+" %"  (valor de probabilidad de lluvia).
        '''
        t = self.t_pronost
        prob_ll = str(t.iloc[indice]["precipitation_probability"])
        
        return f"{prob_ll} %"
    
    #  Métodos de gestión tarjetas
    def recarg_tj(self):
        '''
        Declara las tarjetas de condiciones meteorológicas.
        '''
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
        c_solidohex = [
            "#FA3D01",
            "#87F0B1",
            "#49FEDE", 
            "#69A7C0", 
            "#19E269", 
            "#49FEDE", 
            "#87F09A"
        ]
        c_tema = ['#ff9800' for i in range(6)]
        
        if self.actual:
            col_tarj = c_tema
        else:
            col_tarj = [(0, 0, 0, 0) for i in range(len(c_tema))]
        
        # Declaración de tarjetas en bucle
        for tit, dat, col, tex in zip(
            ["Temperatura ",
            "Viento desde ",             
            "Lluvia",
            "Velocidad \ndel viento ",
            "Humedad rel.",            
            "Vel. ráfagas"], 
            [self.temp,
             self.direc_s,             
             self.lluv, 
             self.veloc,
             self.hum,
             self.raf],
            col_tarj,
            c_solidohex):
            self.ids.tabla.add_widget(MetDat(tit=f"[b]{tit}[/b]", dat=dat, 
                col=col, line_color=tex, f_color=tex, x_pos1=0.25, x_pos2=0.72))
        #  pronóstico lluvia por debajo
        self.ids.sep.add_widget(
            MetDat(tit=f"Precipitaciones a las [b]{self.hf}[/b]", 
                    dat=self.prob_ll, col="#76C7E8", f_color="#000000", x_pos1=0.35, x_pos2=0.8)
        )
            
    def limp_tarj(self):
        '''Limpiar tarjetas.'''
        self.ids.tabla.clear_widgets()
        self.ids.sep.clear_widgets()

    # Métodos Screen: eleg_loc              ######
    def lista_ciud(self, lista_res):
        '''
        Cargar lista de ciudades en GUI.
        
        Parámetros
            lista_res: lista a insertar en `MDlist`.
        '''
        
        self.ids.list_ciud.clear_widgets()
        print("dentro",lista_res[0])
        if lista_res[0][0]=='E':
            print("entró en error")
            self.ids.list_ciud.add_widget(
                CiudItem(id=str(lista_res[0][0]), 
                    text=f"{lista_res[0][1]}",
                app=self.app
                )
            )
        else:
            for c in lista_res:
                print(c)
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
            print("self.lista_res:", self.lista_res)
            self.lista_ciud(self.lista_res)
        ak.start(cons())

    def confirmar_ciud(self):
        if self.ciud_eleg_id == 'E':
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
            self.cargar_barra()
            self.app.volver_main()


class MetDat(MDCard):
    '''Tarjeta de datos meteorológicos. Pensada para usarse en bucle.'''
    tit = StringProperty()
    dat = StringProperty()
    col = StringProperty()
    x_pos1 = NumericProperty()
    x_pos2 = NumericProperty()
    f_color = StringProperty()
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
        self.app.root.confirmar_ciud()
        
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
            print(self.meteo_data)
        except:
            raise Exception("Error en consulta a API. \n\
No se pueden actualizar los datos.")
            
    def hora_loc(self, time, solo_h=False) -> str:
        '''
        Ajusta hora desde GMT+0, el número de horas guardado en el 
        archivo de configuración y lo formatea como strting:
        `%H:%M hs. del %d/%m/%y`.
        ### Parámetros
        - time: timestamp entregado en json desde API.
        - solo_h: `True` = hora y fecha | `False` = solo hora.
        '''
        time = pd.to_datetime(time)
        
        # API: GMT-0. Leer corrección desde config.ini
        h = int(self.conf.cfg["hora"]["zona_hor"])
        time = time + pd.Timedelta(hours=h)
        if solo_h:
            t_str= "%H:%M hs."
        else:
            t_str = "%H:%M hs. del %d/%m/%y"
        return time.strftime(t_str) 
    
    def pantalla(self,pantalla):
        self.root.current = pantalla
        
    def volver_main(self):
        '''Retornar a pantalla principal.'''
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
        self.dialog.open()            
        
    # Cerrar info emergente
    def cerr_info(self, inst):
        '''Orden para cerrar info app. emergente.'''
        if self.dialog:
            self.dialog.dismiss(force=True) 
if __name__ == "__main__":

    MainApp().run()