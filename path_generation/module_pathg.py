# -*- coding: utf-8 -*-
"""
Versión 2

FUNCIÓN: 
        MODULO DE GENERACIÓN DE TRAYECTORIAS

Contenido:
        *Llamar librerias locales

"""
#Librerias externas
import numpy as np
#Librerias locales
from bead_profile import bead_generation, calculo_voltaje
from param_values import testing, generation_paths, results_ 


print("PASO 1.- MODELAMIENTO DEL CORDÓN")
# Ejemplos
material = 'ER70S-6'
archivo = r'.\database\Materials.xls'
d = 0.9  # Diámetro alambre mm
F = 4.7  # Wire feedrate m/min
MD = 5.06 #Densidad del material [g/cm^3] 
# S = 0.6    # Velocidad de soldadura m/min
# A = 100 # Amperaje
S = 0.4  # Velocidad de soldadura m/min
A = 200 # Amperaje

h, w, p = bead_generation(archivo, mat_name=material, diam=d, vel=S, amp=A)  # Variables a usar de la Función
voltage = calculo_voltaje(archivo, mat_name=material, amperaje=A)

o = 0.3*w  # [mm] Offset del contorno
r = 0.5*d  # [mm]radio del cable
print("Altura del cordón: {} mm".format(h))
print("Ancho del cordón: {} mm".format(w))
print("Step-over: {} mm".format(p))

print("\nPASO 2.- DIVISIÓN DE LA NUBE DE PUNTOS")

loaded_arr = np.loadtxt(".\points\geekfile2.txt") #geekfile2 bolsillo2 cline ccircle
arr = np.random.rand(5, 4, 3)
datap = loaded_arr.reshape(
    loaded_arr.shape[0], loaded_arr.shape[1] // arr.shape[2], arr.shape[2])
datap = [[loaded_arr]]


data_new =  datap #  #  bolsillo # bolsillo #datap #  datap # pitting #       

def traslacion3d(puntos, vector_traslacion=(0,0,0)):
    return puntos + vector_traslacion

vector_traslacion = np.array([640, 680, 270]) #vecotr para cline
# vector_traslacion = np.array([119.87, 0, 75.91]) #vecotr para cline
# vector_traslacion = np.array([282.548, 0, 75.86]) #vector para ccurve
for altura in range(len(data_new)):
            for curva in range(len(data_new[altura])):
                data_new[altura][curva] = traslacion3d(data_new[altura][curva], vector_traslacion)

# print("\nPASO 4.- ENCONTRAR MEJOR ESTRATEGIA")
# Busca el ángulo óptimo-> realiza testeo de trayectorias -> encuentra la mejor opción 
anglevalues, data, nameoption, dividelist,areacompare, areadivision = testing(data_new,o,p,w,h,S,MD)
# # GENERACIÓN DE TRAYECTORIAS
# # Entrega lista con opción -> en caso de no haberla realiza división 
df_final, capas = generation_paths(anglevalues, data,nameoption,dividelist,areacompare,areadivision, o, p, w, h, S, MD)
# # print("\nPASO 6.- CALCULO DE PARÁMETROS")
# # results_(df_final)


print("\nPASO 7.- TRADUCCIÓN A CÓDIGO DEL ROBOT ")
from generatorcsr import write_code
radio_min = 25
write_code(capas, S,A, voltage, radio_min)

# from generatorcsr import timer
# end_ = time.time()
# et = timer(start_, end_)
# print("Tiempo total: {}".format(et))