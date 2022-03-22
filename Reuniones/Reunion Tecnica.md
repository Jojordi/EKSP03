## Reunion Tecnica 19.08.2020

FC, FL, EK, AF, RF, JCZ


### Temas generales
RF preguta porque algunas curvas desaprecen
FC explica que por ahora  se deja asi, pero hay que tener encuenta como lo toma AF

JCZ Pide revisar carta Gantt
- Estamos atrasados un par de meses
- De decide que FC avance en la interfaz para desarrollar rapidamente un producto entregable

### FC
#### Avances
- WXpython, WXglade, interfaces parecidas a las de la tormach. Muestra ejemplo de tutorial

#### Siguientes pasos
- un mockup de la interfaz semifuncional hasta los cortes

### AF
#### Avances
- separacion de poligonos no funciono
- se logro detectar puntos convexidad
- se ven todas las apternativas
- manualmente se eligieron algunas separaciones
- se generaron dsitintas trayectorias para cada poligono

#### Siguientes pasos
- Se estudiara un indicador para optimizar la separacion
- Se probaran en distintos casos

### EK
#### Avances
- traspaso a python de ramnsac de linea
- ransac de deteccion de circulo
- Deteccion de 2 circulos con agrupacion

#### Siguientes pasos
- Ver ransac 2d cilindro con falla para determinar relleno
- pasar a 3d de forma bruta y de forma holistica

### FL
#### Avances
-

#### Siguientes Pasos
- Aumentar espesor de un cilindro
- Geometrias 3d estrategias

---

## Reunion Tecnica 26.08.2020

EK, FL, RF, FC, AF

### FC
#### Avances
- mockup de la interfaz
#### Siguiente pasos
- seguir trabajando mockup
- 

### AF
#### Avances
- calculo de paerametros (calculo de area) por estrategia, indicador de area listo, indicador de volumen

#### Siguientes pasos
- Se estudiara un indicador para optimizar la separacion
- Se generara mas fallas por cada tipo de falla
- se sigue trabajnado en indicador de volumen, ejemplo de zigzag

### EK
#### Avances
- Ransac de circulo con pacman funciono bien, 
- avances en reconstruccion del cilindro en 3d, por secciones transversales.

#### Siguientes pasos
- Par de vueltas por slice
- avance en ransac 3d global


### FB 
#### Avances
- Estrategias de relleno en base a ransac

#### Siguientes pasos
- Caso base para aumentar diametro
- Estrategias de relleno en casos cilindrico

---

## Reunion Tecnica 02.09.2020

FL, RF, FC, AF, EK, JCZ


### FC
#### Avances
- Maqueta interfaz y unir con lo que tenemos
- principalmente 	separacion de curvas y forma manual de como cortar las curvas
- La idea es que se trabaje en paralelo con la programa de Alejandra

#### Siguiente Pasos
- Ver intercaccion con la separacion de curvas de manera manual (output lista de punto para que AF lo separe)

### AF 
#### Avances
- parametros de volumen de llenado y STL de de daños

#### Siguientes Pasos
- Agrandar mas daños para probar mas geometrias
- Data frame para relleno

### EK
#### Avances
- no muchos avances, calculo con cuerda y distancia maxima, (no es muy util)

#### Siguientes Pasos
- Desorientar cilindro y encotrar diámetro por ransac 3d

###FL
####Avances
- Recubrimiento de los cilindros a fuerza bruta helicoidal

#### Siguientes Pasos
- Recubrimento helicoidal
- ver patrones de relleno cilindrico













 






