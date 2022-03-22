"""
Version 1

FUNCION:
        Generar geometría del cordón

CONTENIDO:
        *Selección de material
        *Input de variables de entrada
        *Entrega de variables de salida
"""
# Librerias externas
import numpy as np
from matplotlib import pyplot as plt
import pandas as pd
from sklearn import linear_model


def bead_generation(path, mat_name=None, diam=0.0, vel=0.0, amp=0.0):
    if not mat_name:
        print('INGRESAR NOMBRE DE MATERIAL')
        return 0, 0
    try:
        # A) Seleccionar material de aporte
        filepath = path
        df_filler = pd.read_excel(filepath)
        if not list(df_filler.columns) == ['Material', 'Diametro', 'Amperaje', 'Voltaje', 'Velocidad', 'Alto', 'Ancho']:
            print('ARCHIVO NO VÁLIDO, REVISAR COLUMNAS')
            return 0, 0
    except FileNotFoundError:
        print('ARCHIVO NO VÁLIDO, ELEGIR ARCHIVO VÁLIDO')
        return 0, 0

    # B) Filtros de usuario de material, diámetro de alambre y velocidad de soldadura
    df_speed = df_filler[(df_filler['Material'] == mat_name) & (df_filler['Diametro'] == diam) & (df_filler['Velocidad'] == vel)]
    x = df_speed.Amperaje.values
    x = x.reshape(len(x), 1)

    # C) Regresión lineal Speed vs Amperaje
    # Ancho (Width)
    y = df_speed.Ancho.values
    y = y.reshape(len(y), 1)
    regr = linear_model.LinearRegression().fit(x, y)
    wcoef_m = float(regr.coef_[0])  # Coeficiente lineal m
    wcoef_b = float(regr.intercept_)  # Coeficiente lineal b
    
    # Alto (Height)
    y = df_speed.Alto.values
    y = y.reshape(len(y), 1)
    regr = linear_model.LinearRegression().fit(x, y)
    hcoef_m = float(regr.coef_[0])  # Coeficiente lineal m
    hcoef_b = float(regr.intercept_)  # Coeficiente lineal b
    
    # D) Calcular variables de salida de geometria del cordón
    h = round(hcoef_m*amp + hcoef_b, 3)  # [mm] Alto del cordón
    w = round(wcoef_m*amp + wcoef_b, 3)  # [mm] Ancho del cordón
    p = round(0.738 * w, 2)  # [mm] Step-over
    
    # Información de la Soldadura
    # F = 4.7  # Wire Feed rate [m/min] - ejemplo 
    # filepath2 = r'.\database\InfoMaterials.xlsx'  # (Segunda base de datos)
    # data_filler = pd.read_excel(filepath2)
    # data_filler.columns = ['Material', 'Diametro', 'Peso', 'Densidad', 'Precio']
    # # Filtrar con los valores previos
    # data_density = data_filler.loc[(data_filler['Material'] == mat_name) & (data_filler['Diametro'] == d)]  # Filtrar por material)
    # # Obtener valor de Densidad
    # MD = float(data_density['Densidad'].values)  # [g/cm^3] Densidad del filamento con base en % de elementos
    
    return h, w, p


def calculo_voltaje(path, mat_name=None, amperaje=0.0):
    if not mat_name:
        print('INGRESAR NOMBRE DE MATERIAL')
        return 0

    try:
        # A) Seleccionar material de aporte
        filepath = path
        df = pd.read_excel(filepath)
        if not list(df.columns) == ['Material', 'Diametro', 'Amperaje', 'Voltaje', 'Velocidad', 'Alto', 'Ancho']:
            print('ARCHIVO NO VÁLIDO, REVISAR COLUMNAS')
            return 0
    except FileNotFoundError:
        print('ARCHIVO NO VÁLIDO, ELEGIR ARCHIVO VÁLIDO')
        return 0

    df = df[df['Material'] == mat_name]
    amp = df.Amperaje.values
    amp = amp.reshape(len(amp), 1)
    volt = df.Voltaje.values
    volt = volt.reshape(len(volt), 1)
    regr = linear_model.LinearRegression().fit(amp, volt)
    coef_m = float(regr.coef_[0])  # Coeficiente lineal m
    coef_b = float(regr.intercept_)  # Coeficiente lineal b
    voltage= coef_m * amperaje + coef_b
    return voltage


# Visualización de la geometria del cordón
def plot_cordon(h, p, w):
    # Parabola
    def f1(x):
        return ((-4*h)/(w**2))*(x**2) + h

    # Desplazamiento usando p
    def f2(x):
        return ((-4*h)/(w**2))*((x-p)**2) + h
    
    x = np.arange(-10, 15, 0.1)
    # Graficar ambas funciones.
    plt.plot(x, [f1(i) for i in x])
    plt.plot(x, [f2(i) for i in x])
    # Limitar los valores de los ejes.
    plt.xlim(-5, 10)
    plt.ylim(0, 7)
    plt.show()



if __name__ == '__main__':
    print("PASO 1.- MODELAMIENTO DEL CORDÓN")
    # Entregar variables de entrada:
    # mat_name = input("Nombre del material:")       #Nombre del material (AWS)
    # d = float(input("Diámetro del alambre[mm]:"))  #[mm] Diámetro del alambre de alimentación
    # S = float(input("Velocidad torcha[m/min]:"))   #[m/min] Welding torch speed (max de 1 m/min para no comprometer la fusión)
    # A = int(input("Amperaje [A]:"))                #[A] Amperaje
    # F = float(input("Velocidad alimentación[m/min]:"))  #Wire Feed rate [m/min]

    # Ejemplos
    material = 'ER70S-6'
    archivo = r'.\database\Materials.xls'
    d = 0.9  # Diámetro alambre mm
    S = 0.6  # Velocidad de soldadura m/min
    F = 4.7  # Wire feedrate m/min
    A = 90  # Amperaje

    height, width, p = bead_generation(archivo, mat_name=material, diam=d, vel=S, amp=A)  # Variables a usar de la Función

    o = 0.5*width  # [mm] Offset del contorno
    r = 0.5*d  # [mm]radio del cable

    print("Altura del cordón: {} mm".format(height))
    print("Ancho del cordón: {} mm".format(width))
    print("Step-over: {} mm".format(p))

    plot_cordon(height, p, width)  # plot simple de 2 cordones
