# Veleta de escritorio

### Concepto
> Aplicación minimalista para visualizar la dirección y velocidad del viento actual, T°, y predicciones para precipitaciones en horas siguientes.  
> (Practicar uso de KivyMD y extracción de datos de API)

## Desarrollo | Actualmente: _1.0_

### Historia
- Fecha de inicio de desarrollo: 6/12/2023
- Fecha lanz. Alfa. 4/1/2024
- Fecha lanz. Beta.1 6/1/2024
- Fecha lanz. Beta.2 8/1/2024
- Fecha lanz. pre-1.0 10/1/2024
- Fecha lanz. 1.0 11/1/2024

## Información general
### Datos (endpoints gratuitos de **open-meteo.com**)
#### Variables meteorológicas
Se extraen los datos meteorolócos desde [Weather Forecast API](https://open-meteo.com/en/docs).
#### Coordenadas para las localidades
Información de geolocalización (para funcionalidad de selección de localidad por nombre) desde [Geocoding API](https://open-meteo.com/en/docs/geocoding-api).
### Imagen de fondo para rosa de los vientos (pixabay.com)
Se emplea para marcar los grados de la rosa de los vientos [esta](https://pixabay.com/es/vectors/marcar-grado-br%C3%BAjula-m%C3%ADnima-5726232/) imagen, obtenida de **pixabay.com**.  
Para que funcione es necesario descargarla, nombrarla `dial.png` y ubicarla en una carpeta llamada `recursos` en el directorio de trabajo de git del repositorio.
Agradecimientos al usuario [5663591](https://pixabay.com/es/users/5663591-5663591/).
### Zona horaria
La API meteorológica entrega las marcas de tiempo en GMT. Por defecto la aplicación las pasa a GMT-3. Para ajustar a otra banda horaria es necesario especificar el número de horas a sumar o sustraer en en la variable de configuración `zona_hor` dentro de la sección `[hora]` del archivo de configuración _config.ini_.
### Python, Framework
#### Python
- Versión: **Python 3.10.6**  
#### GUI desarrollada en:
- Kivy               2.2.1
- Kivy-Garden        0.1.5
- kivymd             1.1.1

