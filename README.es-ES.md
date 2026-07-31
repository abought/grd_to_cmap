

## Herramienta de conversión de degradados de Photoshop a Matplotlib
### Propósito
Se han creado muchos mapas de color (tablas de consulta) útiles y de uso especial para 
Adobe Photoshop. Esta herramienta está diseñada para extraer información de estos archivos 
y hacer que estos mapas de color estén disponibles en matplotlib para su uso como parte de una 
cadena de herramientas gratuita y de código abierto. 

La herramienta de conversión actualmente admite colores especificados en RGB, HSV y CMYK, 
y convertirá automáticamente al formato RGB para uso interno en matplotlib.

### Uso
Esta herramienta ha sido probada con python 2.7. 
Las dependencias requeridas pueden instalarse mediante el siguiente comando:

`pip install -r requirements.txt`

El lector básico puede invocarse desde otros programas, o ejecutarse directamente para generar 
una representación textual de los datos del archivo de degradado:

`python grd_reader.py input_filename.grd`

Para analizar el archivo y generar un mapa de color en formato matplotlib importable en Python 
(con extensión .py):

`python matplotlib_converter.py input_filename.grd` 

Y para analizar el archivo y generar una lista de paradas de color 
(adecuada para usar con degradados de canvas HTML5) en un nuevo archivo 
(con extensión .js):

`python jsgradient_converter.py`

En el futuro, estos scripts se consolidarán en una sola herramienta.

### Limitaciones conocidas
Esta herramienta fue diseñada originalmente para un propósito específico (extracción de las 
[tablas de consulta "Advanced forensic actions" de ORI](http://ori.hhs.gov/advanced-forensic-actions) para su uso con matplotlib).

Como tal, está fuertemente orientada hacia la creación de mapas de color segmentados lineales 
con colores equidistantes. Los degradados discontinuos, la opacidad y el 
esquema de color LAB son características que actualmente no se admiten. 
Los reportes de problemas y los pull requests son bienvenidos.

### Agradecimientos 
Valek Filippov y el equipo de RE-lab decodificaron el formato de archivo .grd y proporcionaron 
una [implementación inicial del analizador](https://gitorious.org/re-lab/graphics/source/781a65604d405f29c2da487820f64de8ddb0724d:photoshop/grd) 
en la que esta herramienta depende en gran medida.
