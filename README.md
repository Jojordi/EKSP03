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

![image](https://user-images.githubusercontent.com/30658657/176699003-94e66531-943d-4c49-9dd1-dcdf4d5e9ad6.png)
![image](https://user-images.githubusercontent.com/30658657/176699113-02d595f2-eb39-4cb2-b326-396bebb92a85.png)
![image](https://user-images.githubusercontent.com/30658657/176699282-aae60df3-a151-4abb-9818-81b277e88e98.png)
![image](https://user-images.githubusercontent.com/30658657/176699492-2989401e-ea0f-4173-abb0-980fed635da7.png)
![image](https://user-images.githubusercontent.com/30658657/176699717-47f7426a-a342-442b-b96f-9016fc9bc242.png)


**Generar archivo instalador**

Dado que el projecto posee bastantes dependencias, el solo archivo main.exe no es suficiente para poder ejecutarlo completo con lo cual se necesitara un programa que recopile todas estas dependencias y las empaquete para el instalador, para ello se utilizó el programa **Nullsoftware Scriptable Install System** o NSIS el cual puede ser obtenido desde [sourceforge.net](https://sourceforge.net/)

Una vez instalado NSIS se debe generar un archivo zip de la carpeta contenedora del projecto

Finalmente se debera abrir NSIS y utilizar la opción

![image](https://user-images.githubusercontent.com/30658657/176700303-b0cff725-33bd-498e-a373-0aa7f8f6f45b.png)

