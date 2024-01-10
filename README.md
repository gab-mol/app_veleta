# Veleta de escritorio

### Concepto
> Aplicación minimalista para visualizar la dirección y velocidad del viento actual, T°, y predicciones para precipitaciones en horas siguientes.  
> (Practicar uso de KivyMD y extracción de datos de API)

## Desarrollo | Actualmente: _Beta_

### Historia
- Fecha de inicio de desarrollo: 6/12/2023
- Fecha lanz. Alfa. 4/1/2024
- Fecha lanz. Beta.1 6/1/2024
- Fecha lanz. Beta.2 8/1/2024
- Fecha lanz. 1.0 10/1/2024
## Información general
### Datos meteorológicos (endpoints gratuitos)
Se extraen de [Weather Forecast API](https://open-meteo.com/en/docs)   
Información de geolocalización de [Geocoding API](https://open-meteo.com/en/docs/geocoding-api)
### Imagen de fondo para rosa de los vientos (pixabay.com)
Actualmente se emplea [esta](https://pixabay.com/es/vectors/marcar-grado-br%C3%BAjula-m%C3%ADnima-5726232/) imagen de **pixabay.com** para mostrar los grados de la rosa de los vientos.  
Para que funcione es necesario descargarla, nombrarla `dial.png` y ubicarla en una carpeta llamada `recursos` en el directorio de trabajo de git del repositorio.
Agradecimientos al usuario [5663591](https://pixabay.com/es/users/5663591-5663591/).

### Framework
GUI desarrollada en **Kivy v.: 2.0.0**
### Python
Versión: Python 3.10.6
