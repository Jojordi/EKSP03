Repositorio destinado a la generación de programas instaladores de software EKSP03. Por el minuto solo es posible generar instaladores para computadores con sistema operativo Windows de 64 bits.

## Como utilizar

**Clonar repositorio**
 
 Al bajar el repositorio anotar el path de la carpeta de destino dado que será utilizado en el siguiente paso.
 
 **Instalar bibliotecas**
 
 Se incluye un archivo de requirements en la carpeta principal del projecto además de dos archivos .whl necesarios para la instalación de las bibliotecas GDAL y Fiona, para poder utilizar el archivo de requirements se debe reemplazar el apartado PATHTOPROJECT con el path de la carpeta contenedora del projecto este apartado se ve de la siguiente manera:
 
![image](https://user-images.githubusercontent.com/30658657/176694666-46ac64b4-475d-4c7b-99de-a4ff6b4299e0.png)

Luego de aquella edición utilizar el comando:

```
pip install -r requirements.txt
```

El cual instalara todas las dependencias del projecto.

**Editar Archivo Main de Biblioteca Geopandas**

La biblioteca **Geopandas** realiza un import de una base de datos la cual no es utilizada por el projecto y genera conflictos con la biblioteca que genera el archivo ejecutable del projecto por lo cual se debe comentar la siguiente linea de dicha biblioteca:

![image](https://user-images.githubusercontent.com/30658657/176698370-5c8b159b-7908-4b10-9627-b5c758aed775.png)


**Generar archivo ejecutable**

Para generar un archivo ejecutable del projecto, abrir una terminal en la carpeta principal de el projecto y ejecutar el comando:

```
pyinstaller main.spec
```

El cual despues de un tiempo generara un archivo main.exe el cual no requiere que el sistema operativo posea una version de python o alguna de sus bibliotecas para funcionar. 

Este archivo se encuentra en la carpeta dist generada por pyinstaller

![instruccion1](https://user-images.githubusercontent.com/30658657/177056408-22a9bf34-8489-4edf-a1b8-9528078415bf.JPG)

Este es el archivo ejecutable contenido por dist

![image](https://user-images.githubusercontent.com/30658657/176699113-02d595f2-eb39-4cb2-b326-396bebb92a85.png)

Este archivo debe ser enviado a la carpeta principal para que pueda utilizar todas las dependencias externas.Las carpetas señaladas ya no sirven y pueden ser eliminadas.

![instruccion2](https://user-images.githubusercontent.com/30658657/177056435-885e56c0-48fb-4dc5-87ba-805fea7c2291.JPG)

De hecho se recomienda borrar carpetas para reducir el espacio que ocupará el instalador ya que no serán utilizadas y ocupan bastante espacio. Las unicas carpetas requeridas son las siguientes:

![instruccion5](https://user-images.githubusercontent.com/30658657/177056519-05254ccf-148e-4fa7-8654-c8feb7fc3f00.JPG)


**Generar archivo instalador**

Dado que el projecto posee bastantes dependencias, el solo archivo main.exe no es suficiente para poder ejecutarlo completo con lo cual se necesitara un programa que recopile todas estas dependencias y las empaquete para el instalador, para ello se utilizó el programa **Nullsoftware Scriptable Install System** o NSIS el cual puede ser obtenido desde [sourceforge.net](https://sourceforge.net/)

![instruccion3](https://user-images.githubusercontent.com/30658657/177056475-167ef4ea-6f12-4509-b25c-151b502d8bd8.JPG)

![instruccion4](https://user-images.githubusercontent.com/30658657/177056492-f194e520-13dc-4a96-af43-59e653df43f6.JPG)

Una vez instalado NSIS se debe generar un archivo zip de la carpeta contenedora del projecto

![image](https://user-images.githubusercontent.com/30658657/176699717-47f7426a-a342-442b-b96f-9016fc9bc242.png)

Finalmente se debera abrir NSIS y utilizar la opción installer based on **.ZIP file**. Seleccionar el archivo zip generado en el paso anterior.

![image](https://user-images.githubusercontent.com/30658657/176700303-b0cff725-33bd-498e-a373-0aa7f8f6f45b.png)

Los parametros de default son correctos con lo cual simplemente seguir las instrucciones y darle siguiente al programa. Una vez finalizado se tendra un archivo ejecutable capaz de instalar el projecto.
