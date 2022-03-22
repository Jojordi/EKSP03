# -*- coding: utf-8 -*-
import vedo
import random
import timeit
import trimesh
from vedo.mesh import Mesh
import utilidades
import shapely.ops
import numpy as np
import pandas as pd
from sklearn import linear_model
from skspatial.objects import Line
from skspatial.objects import Plane
from scipy.spatial.transform import Rotation
from path_generation import param_values
from typing import List, Sequence, Tuple, Union


class Procesador:
    """
        Implementa un conjunto de métodos utilizados para realizar los cálculos necesarios 
        para los distintos procesos de la reparación (orientar mallas, calcular cortes, calcular trayectorias, etc.). 

        Attributes
        ----------        
        df_info_soldaduras: pd.DataFrame, by default None
            pandas DataFrame para acceder a los datos de soldaduras.
            Contiene datos sobre amperajes, voltajes, velocidades, y anchos y altos de cordones de soldadura.
            Datos son usados para estimar la geometría de los cordones de soldadura a usar, según sus
            parámetros de soldadura.
            
            Datos son dados según material de alambre, por ejemplo: 
            Material: ER70S-6, con Diámetro: 0.9, a un Amperaje: 90, a un Voltaje: 16.4, con Velocidad: 0.2 
            tiene un cordon de Alto: 2.4 y Ancho: 5.2

        df_info_materiales: pd.DataFrame, by default None
            pandas DataFrame para acceder a los datos de materiales.
            Contiene datos sobre peso por rollo, densidad, y precio de alambres de soldadura.
            Datos son usados para estimar cantidad de material usado.

        Methods
        -------
        cargar_archivo_soldaduras
            Carga archivo con datos de alambres, amperajes, voltajes, velocidades, 
            y geometría de cordones de soldadura.
        
        cargar_archivo_materiales
            Carga archivo con datos de peso, densidad, y precio según alambre.
        
        calcular_cordones
            Estima geometría y step-over de los cordones de soldadura, dados los parámetros de soldadura ingresados.
            Estimación se realiza con una regresión lineal usando datos del archivo de soldadura.

        calcular_voltaje
            Estima voltaje de soldadura, dados los parámetros de soldadura ingresados.
            Estimación se realiza con una regresión lineal usando datos del archivo de soldadura.
        
        orientar_malla
            Orienta la malla ingresada usando los marcadores colocados sobre su superficie para calcular las rotaciones necesarias.
            La malla es rotada respecto a su centro.
            La estrategia de orientación utilizada depende del tipo de pieza que se quiera orientar.
        
        orientar_placa
            Orienta la malla ingresada usando los marcadores colocados sobre su superficie para calcular las rotaciones necesarias.
            La malla es rotada respecto a su centro.
            Para la orientación de placas se requieren 3 marcadores.
            Todos los marcadores deben estar en el mismo plano para obtener un buen resultado.
            Una vez rotada la malla se hace una traslación para colocar el origen de la pieza en el origen global.
        
        orientar_cilindro_manualmente
            Orienta la malla ingresada usando los marcadores colocados sobre su superficie para calcular las rotaciones necesarias.
            La malla es rotada respecto a su centro.
            Para la orientación de cilindros se requieren 4 marcadores.
            Se asume que el eje del cilindro será orientado al eje X.
            Todos los marcadores deben estar en el manto para obtener un buen resultado.
            Una vez rotada la malla se hace una traslación para centrar el cilindro, posición final debe ser [0, 0, coordZCentro]
        
        calc_dist_to_line
            Calcular la distancia de un punto (o puntos) 3D a una línea 3D que pasa a través de [xc, yc, zc] con dirección [sx, sy, sz]
        
        calc_singlepointdist_to_line
            Calcular la distancia de un punto 3D a una línea 3D que pasa a través de [xc, yc, zc] con dirección [sx, sy, sz]
        
        dist_pts3d
            Calcula la distancia entre dos puntos en 3D.
        
        direction_vector
            Calcula la dirección de un vector.
        
        dist_point_to_cone
            Calcula la distancia de un punto a un cono.
        
        dist_points_to_cone
            Calcula la suma de las distancias de un grupo de puntos a un cono.
        
        project_point_to_line
            Proyecta un punto a una línea con cierta orientación.
        
        in_sphere
            Calcula que puntos de un grupo de puntos se encuentran dentro de una esfera
            definida por su centro y radio.
        
        orientar_cono_manualmente
            Orienta la malla ingresada usando los marcadores colocados sobre su superficie para calcular las rotaciones necesarias.
            La malla es rotada respecto a su centro.
            Para la orientación de conos se requieren 4 marcadores.
            El primer marcador corresponde al origen elegido para la pieza.
            Se asume que el eje del cono será orientado al eje X.
            Para un buen resultado, el primer y segundo punto deben estar ambos en la misma generatriz del cono.
            Además, los marcadores deben estar en el manto, y el primer, tercer, y cuarto punto deben estar todos en la base de la malla.
            Finalmente, se debe dar la mayor separación posible al tercer y cuarto marcador.
            Una vez rotada la malla se hace una traslación para centrar el cono, posición final debe ser [0, 0, coordZCentro]
        
        orientar_marcadores
            Orienta los marcadores ingresados según la transformación dada.
            Utilizado para orientar los marcadores usados en la orientación manual de las mallas.
        
        calcular_rotacion
            Estima una transformación para alinear los vectores dados a los ejes ingresados.

        calcular_angulo_apertura_cono
            Estima el ángulo de apertura del cono dado en la pieza, basado en el promedio de las normales cercanas al punto entregado.
        
        calcular_cortes_malla
            Calcula cortes transversales de la malla ingresada, utilizando la geometría del cordón de soldadura para estimar las alturas de corte.
            Los cortes son hechos con planos paralelos al plano XY.
            Para los casos de cilindros y conos, los cortes son hechos en un sistema de coordenadas cilíndricas.
            Retorna una lista de listas. Cada elemento de la lista es una capa, la cual a su vez es una lista.
            Cada capa contiene los contornos encontrados, los cuales son np.ndarray.
            Se asume que cada contorno encontrado es una falla y será considerado como un contorno independiente.
        
        calcular_cortes_placa
            Calcula cortes transversales de la malla ingresada, utilizando la geometría del cordón de soldadura para estimar las alturas de corte.
            Los cortes son hechos con planos paralelos al plano XY.
            Retorna una lista de listas. Cada elemento de la lista es una capa, la cual a su vez es una lista.
            Cada capa contiene los contornos encontrados, los cuales son np.ndarray.
            Se asume que cada contorno encontrado es una falla y será considerado como un contorno independiente.
        
        calcular_cortes_cilindro
            Calcula cortes transversales de la malla ingresada, utilizando la geometría del cordón de soldadura para estimar las alturas de corte.
            Los cortes son hechos con planos paralelos al plano XY, en el caso de cilindros el eje Y representa caparados.
            Los cortes son realizados en un sistema de coordenadas cilíndrico, las coordenadas de la malla son transformadas y luego se corta como placa.
            Los cortes a su vez son transformados a un sistema de coordenadas cartesianos antes de su retorno.
            Retorna una lista de listas. Cada elemento de la lista es una capa, la cual a su vez es una lista.
            Cada capa contiene los contornos encontrados, los cuales son np.ndarray.
            Se asume que cada contorno encontrado es una falla y será considerado como un contorno independiente.
        
        calcular_cortes_cono
            Calcula cortes transversales de la malla ingresada, utilizando la geometría del cordón de soldadura para estimar las alturas de corte.
            Los cortes son hechos con planos paralelos al plano XY, en el caso de conos el eje Y representa grados.
            Los cortes son realizados en un sistema de coordenadas cilíndrico, las coordenadas de la malla son transformadas y luego se corta como placa.
            En el caso de conos es necesario realizar la transformación a coordenadas cilíndricas, y luego rotar la malla en el eje Y
            un ángulo igual al de apertura para su procesamiento, luego considerando el caso como de placa.
            Los cortes a su vez son transformados a un sistema de coordenadas cartesianos antes de su retorno.
            Retorna una lista de listas. Cada elemento de la lista es una capa, la cual a su vez es una lista.
            Cada capa contiene los contornos encontrados, los cuales son np.ndarray.
            Se asume que cada contorno encontrado es una falla y será considerado como un contorno independiente.
            
        calcular_trayectorias
            Calcula las trayectorias para los contornos contenidos en los cortes ingresados.
            En un principio, el cálculo se realiza de manera independiente por cada contorno y por cada capa.
            En caso que un contorno se repita en capas las capas siguientes a las que aparece, 
            se repite la trayectoria calculada para el primero.
            Cada trayectoria se elige entre una lista de estrategias, seleccionando la que tenga mejor desempeño,
            medido en área cubierta, cantidad de movimientos, soldadura sobrante estimada.
            Para los casos de cilindros y conos, los cortes son transformados a un sistema de coordenadas cilindricas,
            y luego se calculan las trayectorias. En ese caso, las trayectorias son transformadas a un sistema de coordenadas
            cartesianos antes de retornarlas.

        calcular_trayectorias_placa
            Calcula las trayectorias para los contornos contenidos en los cortes ingresados.
            En un principio, el cálculo se realiza de manera independiente por cada contorno y por cada capa.
            En caso que un contorno se repita en capas las capas siguientes a las que aparece, 
            se repite la trayectoria calculada para el primero.
            Cada trayectoria se elige entre una lista de estrategias, seleccionando la que tenga mejor desempeño,
            medido en área cubierta, cantidad de movimientos, y soldadura sobrante estimada.
        
        calcular_trayectorias_cilindro
            Calcula las trayectorias para los contornos contenidos en los cortes ingresados.
            En un principio, el cálculo se realiza de manera independiente por cada contorno y por cada capa.
            En caso que un contorno se repita en capas las capas siguientes a las que aparece, 
            se repite la trayectoria calculada para el primero.
            Cada trayectoria se elige entre una lista de estrategias, seleccionando la que tenga mejor desempeño,
            medido en área cubierta, cantidad de movimientos, y soldadura sobrante estimada.
            Para el caso de cilindros, los cortes son transformados a un sistema de coordenadas cilindricas,
            y luego se calculan las trayectorias, finalmente las trayectorias son transformadas a un sistema de coordenadas
            cartesianos antes de retornarlas.
        
        calcular_trayectorias_cono
            Calcula las trayectorias para los contornos contenidos en los cortes ingresados.
            En un principio, el cálculo se realiza de manera independiente por cada contorno y por cada capa.
            En caso que un contorno se repita en capas las capas siguientes a las que aparece, 
            se repite la trayectoria calculada para el primero.
            Cada trayectoria se elige entre una lista de estrategias, seleccionando la que tenga mejor desempeño,
            medido en área cubierta, cantidad de movimientos, y soldadura sobrante estimada.
            En el caso de conos es necesario realizar la transformación a coordenadas cilíndricas, y luego rotar la malla en el eje Y
            un ángulo igual al de apertura, para que puedan calcularse las trayectorias.
            Las trayectorias son transformadas a un sistema de coordenadas cartesianos antes de retornarlas.
        
        calcular_hardfacing_malla
            Calcula los contornos necesarios para realizar hardfacing/surfacing sobre una/s área/s en particular, seleccionados sobre una malla.
            Áreas separadas por una distancia mayor al radio de clustering son consideradas como áreas separadas.
            El número de contornos obtenidos es al menos la cantidad ingresada.
            Para el caso de cilindros y conos se realiza una transformación de los puntos desde un sistema cartesiano a un sistema cilíndrico,
            y luego se realiza el cálculo de contornos para hardfacing/surfacing.
            Los contornos son obtenidos triangulando los puntos del área elegida, mediante Delaunay 2D, y luego extruyendo el área.
            Esa extrusión es cortada, obteniendo sus contornos.
        
        extruir_seleccion
            Calcula la extrusión del área elegida para hardfacing/surfacing.
            El área se obtiene triangulando los puntos ingresados, mediante Delaunay 2D.
            El área es luego extruida una altura dada por la altura del cordón de soldadura
            y la cantidad de capas que se quieren utilizar para el hardfacing/surfacing.
            En caso de tener más de un área, separadas por una distancia mayor al radio de clustering, 
            cada área es extruida por separado.
        
        calcular_cortes_hardfacing_placa
            Calcula los contornos necesarios para realizar hardfacing/surfacing sobre una/s área/s en particular, seleccionados sobre una malla.
            Áreas separadas por una distancia mayor al radio de clustering son consideradas como áreas separadas.
            El número de contornos obtenidos es al menos la cantidad ingresada.
            Los contornos son obtenidos triangulando los puntos del área elegida, mediante Delaunay 2D, y luego extruyendo el área.
            Esa extrusión es cortada, obteniendo sus contornos.
        
        calcular_cortes_hardfacing_cilindro
            Calcula los contornos necesarios para realizar hardfacing/surfacing sobre una/s área/s en particular, seleccionados sobre una malla.
            Áreas separadas por una distancia mayor al radio de clustering son consideradas como áreas separadas.
            El número de contornos obtenidos es al menos la cantidad ingresada.
            Para el caso de cilindros se realiza una transformación de los puntos desde un sistema cartesiano a un sistema cilíndrico,
            y luego se realiza el cálculo de contornos para hardfacing/surfacing considerandolo como una placa.
            Los contornos son obtenidos triangulando los puntos del área elegida, mediante Delaunay 2D, y luego extruyendo el área.
            Esa extrusión es cortada, obteniendo sus contornos.
            Los contornos son transformados a un sistema de coordenadas cartesianas antes de retornarlo.

        calcular_cortes_hardfacing_cono
            Calcula los contornos necesarios para realizar hardfacing/surfacing sobre una/s área/s en particular, seleccionados sobre una malla.
            Áreas separadas por una distancia mayor al radio de clustering son consideradas como áreas separadas.
            El número de contornos obtenidos es al menos la cantidad ingresada.
            En el caso de conos es necesario realizar la transformación a coordenadas cilíndricas, y luego rotar la malla en el eje Y
            un ángulo igual al de apertura, luego se realiza el cálculo de contornos para hardfacing/surfacing considerandolo como una placa.
            Los contornos son obtenidos triangulando los puntos del área elegida, mediante Delaunay 2D, y luego extruyendo el área.
            Esa extrusión es cortada, obteniendo sus contornos.
            Los contornos son transformados a un sistema de coordenadas cartesianas antes de retornarlo.
    """

    def __init__(self) -> None:
        """
            Constructor para la clase Procesador.
        """

        self.df_info_soldaduras = None
        self.df_info_materiales = None

    def cargar_archivo_soldaduras(self, path_soldaduras: str) -> str:
        """
            Carga archivo con datos de alambres, amperajes, voltajes, velocidades, 
            y geometría de cordones de soldadura.
            Necesario para realizar los cálculos de trayectorias.
            Verifica existencia y formato de archivo.
            Retorna el resultado de la operación.

            Parameters
            ----------
            path_soldaduras : str
                path al archivo que contiene los datos de las soldaduras.
                Archivo debe ser de tipo Excel.

            Returns
            -------
            str
                mensaje de resultado de la operación.
        """
        
        try:
            self.df_info_soldaduras = pd.read_excel(path_soldaduras)
        except FileNotFoundError:
            msge = f'ARCHIVO DE DATOS {path_soldaduras} NO ENCONTRADO\n'
            return msge
        
        columnas = ['Material', 'Diametro', 'Amperaje', 'Voltaje', 'Velocidad', 'Alto', 'Ancho']
        if not list(self.df_info_soldaduras.columns) == columnas:
            msge = f'REVISAR FORMATO DE ARCHIVO {path_soldaduras}, COLUMNAS DEBEN SER:\n'
            msge += "'Material', 'Diametro', 'Amperaje', 'Voltaje', 'Velocidad', 'Alto', 'Ancho'\n"
            msge += f"{', '.join(columnas)}\n"
            return msge
        else:
            msge = f'ARCHIVO {path_soldaduras} CARGADO!\n'
            return msge
    
    def cargar_archivo_materiales(self, path_materiales: str) -> str:
        """
            Carga archivo con datos de peso, densidad, y precio según alambre.
            Necesario para realizar los cálculos de trayectorias.
            Verifica existencia y formato de archivo.
            Retorna el resultado de la operación.

            Parameters
            ----------
            path_materiales : str
                path al archivo que contiene los datos de los materiales.
                Archivo debe ser de tipo Excel.

            Returns
            -------
            str
                mensaje de resultado de la operación.
        """

        try:
            self.df_info_materiales = pd.read_excel(path_materiales)
        except FileNotFoundError:
            msge = f'ARCHIVO DE DATOS {path_materiales} NO ENCONTRADO\n'
            return msge
        
        columnas = ['Material', 'Diametro', 'Peso', 'Densidad', 'Precio']
        if not list(self.df_info_materiales.columns) == columnas:
            msge = f'REVISAR FORMATO DE ARCHIVO {path_materiales}, COLUMNAS DEBEN SER:\n'
            msge += f"{', '.join(columnas)}\n"
            return msge
        else:
            msge = f'ARCHIVO {path_materiales} CARGADO!\n'
            return msge

    def calcular_cordones(self, material: str, diametro: float, velocidad: float, amperaje: float) -> Tuple[float, float, float]:
        """
            Estima geometría y step-over de los cordones de soldadura, dados los parámetros de soldadura ingresados.
            Estimación se realiza con una regresión lineal usando datos del archivo de soldadura.
            Parámetros de material, diámetro, y velocidad deben estar presentes en el archivo de datos de soldadura.

            Parameters
            ----------
            material : str
                alambre de soldadura usado

            diametro : float
                diámetro del alambre de soldadura a usar

            velocidad : float
                velocidad de soldadura a usar

            amperaje : float
                amperaje a usar en la soldadura

            Returns
            -------
            Tuple[float, float, float]
                lista con alto y ancho del cordón, y el step-over de los cordones
        """

        # Filtros de usuario de material, diámetro de alambre y velocidad de soldadura
        df_speed = self.df_info_soldaduras[(self.df_info_soldaduras['Material'] == material) & 
                                            (self.df_info_soldaduras['Diametro'] == diametro) & 
                                            (self.df_info_soldaduras['Velocidad'] == velocidad)]
        x = df_speed.Amperaje.values
        x = x.reshape(len(x), 1)

        # Regresión lineal Speed vs Amperaje
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

        # Calcular variables de salida de geometria del cordón
        h = round(hcoef_m*amperaje + hcoef_b, 3)  # [mm] Alto del cordón
        w = round(wcoef_m*amperaje + wcoef_b, 3)  # [mm] Ancho del cordón
        p = round(0.738 * w, 2)  # [mm] Step-over

        return h, w, p

    def calcular_voltaje(self, material: str, amperaje: float) -> float:
        """
            Estima voltaje de soldadura, dados los parámetros de soldadura ingresados.
            Estimación se realiza con una regresión lineal usando datos del archivo de soldadura.
            Parámetro de material debe estar presente en el archivo de datos de soldadura.
            
            Parameters
            ----------
            material : str
                alambre de soldadura usado
            
            amperaje : float
                amperaje a usar en la soldadura
            
            Returns
            -------
            float
                voltaje estimado para la soldadura
        """

        df = self.df_info_soldaduras[self.df_info_soldaduras['Material'] == material]
        amp = df.Amperaje.values
        amp = amp.reshape(len(amp), 1)
        volt = df.Voltaje.values
        volt = volt.reshape(len(volt), 1)
        regr = linear_model.LinearRegression().fit(amp, volt)
        coef_m = float(regr.coef_[0])  # Coeficiente lineal m
        coef_b = float(regr.intercept_)  # Coeficiente lineal b
        voltage = coef_m * amperaje + coef_b

        return voltage

    def orientar_malla(self, mesh: vedo.Mesh, 
                        lista_marcadores: List[vedo.shapes.Cross3D], 
                        rotaciones: List, tipo_pieza: int=0, tipo_orientacion: int=0) -> Tuple[List[Rotation], vedo.Mesh, List[vedo.shapes.Cross3D]]:
        """
            Orienta la malla ingresada usando los marcadores colocados sobre su superficie para calcular las rotaciones necesarias.
            La malla es rotada respecto a su centro.
            La estrategia de orientación utilizada depende del tipo de pieza que se quiera orientar.
            Para la orientación de placas se requieren 3 marcadores, para cilindros y conos se requieren 4.
            En todos los casos el primer marcador colocado corresponde al origen de la pieza, una vez rotada la malla
            se hace una traslación para colocar ese origen en el origen global.

            Parameters
            ----------
            mesh : vedo.Mesh
                malla a orientar, visualizada en VedoPanel

            lista_marcadores : List[vedo.shapes.Cross3D]
                lista de marcadores colocados sobre la pieza para guiar la orientación de la malla.
                La utilidad de los marcadores es solo la posición en la que se encuentran, una vez orientados 
                ya no son útiles, solo son orientados y visualizados por consistencia.

            rotaciones : List
                lista vacía para guardar las rotaciones aplicadas a la malla en la orientación actual.
                Usado para poder resetear la última orientación guardada.

            tipo_pieza : int, optional
                indicador de tipo de pieza.
                0=placa, 1=cilindro, 2=cono, by default 0

            Returns
            -------
            List[Rotation], vedo.Mesh, List[vedo.shapes.Cross3D]
                lista de rotaciones usadas, malla orientada, lista con marcadores orientados
        """

        # CASO DE PLACAS
        if tipo_pieza == 0:
            rotaciones, mesh, lista_marcadores = self.orientar_placa(mesh, lista_marcadores, rotaciones)
        
        # CASO CILINDROS
        if tipo_pieza == 1:
            if tipo_orientacion == 1:
                mesh = self.orientar_cilindro_automaticamente(mesh)
            elif tipo_orientacion == 0:
                rotaciones, mesh, lista_marcadores = self.orientar_cilindro_manualmente(mesh, lista_marcadores, rotaciones)

        # CASO CONOS
        if tipo_pieza == 2:
            if tipo_orientacion == 1:
                mesh = self.orientar_cono_automaticamente(mesh)
            elif tipo_orientacion == 0:
                rotaciones, mesh, lista_marcadores = self.orientar_cono_manualmente(mesh, lista_marcadores, rotaciones)
        
        return rotaciones, mesh, lista_marcadores
    
    def orientar_placa(self, mesh: vedo.Mesh, lista_marcadores: List[vedo.shapes.Cross3D], rotaciones: List) -> Tuple[List[Rotation], vedo.Mesh, List[vedo.shapes.Cross3D]]:
        """
            Orienta la malla ingresada usando los marcadores colocados sobre su superficie para calcular las rotaciones necesarias.
            La malla es rotada respecto a su centro.
            Para la orientación de placas se requieren 3 marcadores.
            El primer marcador corresponde al origen elegido para la pieza.
            El segundo marcador es usado para crear un vector entre el primer y segundo marcador, 
            indicando la dirección del eje X.
            El tercer marcador es usado para crear un vector entre el primer y tercer marcador, 
            este vector es usado para calcular el eje Z mediante un producto cruz con el vector del eje X elegido.
            Todos los marcadores deben estar en el mismo plano para obtener un buen resultado.
            Una vez rotada la malla se hace una traslación para colocar el origen de la pieza en el origen global.

            Parameters
            ----------
            mesh : vedo.Mesh
                malla a orientar, visualizada en VedoPanel
            
            lista_marcadores : List[vedo.shapes.Cross3D]
                lista de marcadores colocados sobre la pieza para guiar la orientación de la malla.
                La utilidad de los marcadores es solo la posición en la que se encuentran, una vez orientados 
                ya no son útiles, solo son orientados y visualizados por consistencia.
            
            rotaciones : List
                lista vacía para guardar las rotaciones aplicadas a la malla en la orientación actual.
                Usado para poder resetear la última orientación guardada.
            
            Returns
            -------
            List[Rotation], vedo.Mesh, List[vedo.shapes.Cross3D]
                lista de rotaciones usadas, malla orientada, lista con marcadores orientados
        """

        if len(lista_marcadores) == 3:
            punto_origen = np.asarray(lista_marcadores[0].GetPosition())
            punto_eje_x = np.asarray(lista_marcadores[1].GetPosition())
            punto_eje_y = np.asarray(lista_marcadores[2].GetPosition())
            # VECTORES MAGNITUD Y DIRECCIÓN DE LOS EJES DE COORDENADAS
            vector_x = punto_eje_x - punto_origen
            vector_x = vector_x/np.linalg.norm(vector_x)
            
            vector_y = punto_eje_y - punto_origen
            vector_y = vector_y/np.linalg.norm(vector_y)
            
            vector_z = np.cross(vector_x, vector_y)
            vector_z = vector_z/np.linalg.norm(vector_z)

            ejes_alineacion = [[1, 0, 0], [0, 0, 1]]
            vectores_elegidos = [vector_x, vector_z]
            rotacion_transform = self.calcular_rotacion(ejes_alineacion, vectores_elegidos)
            mesh.applyTransform(rotacion_transform.as_matrix(), reset=True)
            lista_marcadores = self.orientar_marcadores(lista_marcadores, rotacion_transform.as_matrix())
            rotaciones.append(rotacion_transform)

            # SE MUEVE ESCENA AL ORIGEN DESPUÉS DE ROTAR
            punto_origen = np.asarray(lista_marcadores[0].getTransform().GetPosition())
            mesh.shift(-punto_origen)
            for i, marcador in enumerate(lista_marcadores):
                lista_marcadores[i] = marcador.shift(-punto_origen)

            return rotaciones, mesh, lista_marcadores
        else:
            return rotaciones, mesh, lista_marcadores
        
    def orientar_cilindro_automaticamente(self, mesh):
        """
            Orienta la malla de manera automática a partir de ajustar malla a un modelo obtenido mediante propiedades geométricas y RANSAC.
            Proceso de manera iterativa toma puntos aleatoriamente para ajustar un modelo que defina los parámetros de la malla usada.
            Mediante ajuste se detecta eje central del cilindro y radio del mismo.
            Obtenidos los parámetros que mejor ajustan a la malla, se usan para rotar desde orientación arbitraria a una de utilidad.
            Una vez rotada la malla la orientación final debe ser [1, 0, 0]

            Parameters
            ----------
            mesh : vedo.Mesh
                malla a orientar, visualizada en VedoPanel

                
            Returns
            -------
            vedo.Mesh
                malla orientada
        """
        
        start_time = timeit.default_timer()
        checkpoint = 0
        veces = 0
        while checkpoint == 0:
            """Carga de vertices del mesh como un array."""
            if type(mesh) != trimesh.base.Trimesh:
                malla_trimsh = vedo.utils.vedo2trimesh(mesh)
            vertices_full = malla_trimsh.vertices
            normales = malla_trimsh.vertex_normals
            axis_1 = max(vertices_full[:,0])-min(vertices_full[:,0])
            axis_2 = max(vertices_full[:,1])-min(vertices_full[:,1])
            axis_3 = max(vertices_full[:,2])-min(vertices_full[:,2])
            max_axis = axis_1, axis_2, axis_3
            max_dim = max(max_axis)
            
            """Selección de los puntos con sus respectivas normales"""
            Points_With_Normals = vertices_full[:,0],vertices_full[:,1],vertices_full[:,2],normales[:,0],normales[:,1],normales[:,2]
        
            Points_With_Normals = np.array(Points_With_Normals).T
            List_PointsWithNormals_FullSize = list(Points_With_Normals)
            if len(List_PointsWithNormals_FullSize) > 500000:
                List_PointsWithNormals = random.sample(List_PointsWithNormals_FullSize,500000)
                PointsWithNormals = np.asarray(List_PointsWithNormals)
                vertices = PointsWithNormals[:,0], PointsWithNormals[:,1], PointsWithNormals[:,2]
                vertices = np.asarray(vertices)
                vertices = vertices.T   
            else:
                List_PointsWithNormals = List_PointsWithNormals_FullSize
                vertices = vertices_full  
                
            NumIter = 500
            Thresh = 0.01 # Percentage, use with radius
            Score = 0
            Best_Sample = [0, 0, 0, 0, 0, 0, 0, 0]
            Best_Sample_Position = 0
            Data_Iterations = list(range(NumIter))
            Max_Possible_Score = len(vertices)
            
            for iteration in range(NumIter):  
                """Se eligen 3 puntos al azar, se extraen sus posiciones XYZ y sus normales"""
                points = np.asarray(random.sample(List_PointsWithNormals,3))
                # points = np.asarray(random.sample(list(self.in_sphere(len(vertices)*0.01,Points_With_Normals[random.randint(0,len(vertices)-1)],Points_With_Normals)),3))
                
                Point1 = np.array([points[0][0],points[0][1],points[0][2]])
                Point2 = np.array([points[1][0],points[1][1],points[1][2]])
                Point3 = np.array([points[2][0],points[2][1],points[2][2]])
                
                N1 = np.array([points[0][3],points[0][4],points[0][5]])
                N2 = np.array([points[1][3],points[1][4],points[1][5]])
                N3 = np.array([points[2][3],points[2][4],points[2][5]])
                
                """Se calcula el producto cruz de cada par y se promedian entre si"""
                Orientation = (np.cross(N1,N2)+np.cross(N1,N3)+np.cross(N2,N3))/3
                
                """Producto cruz entre la normal calculada anteriormente y las 3 normales iniciales"""
                N4 = np.cross(N1,Orientation)
                N5 = np.cross(N2,Orientation)
                N6 = np.cross(N3,Orientation)
                
                try:
                    """Generacion de planos que pasan por los puntos elegidos con la normal calculada"""
                    Plane1 = Plane(point=Point1, normal=N4)
                    Plane2 = Plane(point=Point2, normal=N5)
                    Plane3 = Plane(point=Point3, normal=N6)
                    
                    """A partir de los planos, se intersectan de a pares para generar 3 intersecciones"""
                    Line1 = Plane1.intersect_plane(Plane2)
                    Line2 = Plane1.intersect_plane(Plane3)
                    Line3 = Plane2.intersect_plane(Plane3)
                    
                    """Linea que define al eje del cilindro"""
                    Pnt = (Line1.point + Line2.point + Line3.point)/3
                    Direction = (Line1.direction + Line2.direction + Line3.direction)/3
                    line = Line(point=Pnt, direction=Direction)
                    
                    """Cálculo del radio"""
                    R1 = self.calc_singlepointdist_to_line(Point1,line.point,line.direction)
                    R2 = self.calc_singlepointdist_to_line(Point2,line.point,line.direction)
                    R3 = self.calc_singlepointdist_to_line(Point3,line.point,line.direction)
                    R = np.asarray([R1, R2, R3])
                    maxR = max(R)
                    R = R/maxR
                    for i in range(len(R)):
                        if R[i] < 0.75:
                            R[i] = max(R)
                    R = R*maxR
                    R = R.mean()
        
                    """Se descartan soluciones que generen un radio más grande que toda la PCD"""
                    if R > max_dim*0.5:
                        continue
        
                    radius = R
                    position_optimized = line.point
                    orientation_optimized = line.direction
                        
                    """Threshold for comparison"""
                    UmDist = radius*Thresh
                    lowerRadius = radius-UmDist
                    upperRadius = radius+UmDist
                    comp_R = self.calc_dist_to_line(vertices,position_optimized, orientation_optimized)
                    comparison = (comp_R > lowerRadius) & (comp_R < upperRadius)
                    Local_Score = comparison.sum()
                    RANSAC_Score = Local_Score
                    Data_Iterations[iteration] = [radius,line.point,line.direction], RANSAC_Score
                    
                    if RANSAC_Score > Score and RANSAC_Score < Max_Possible_Score:
                        Score = RANSAC_Score
                        Best_Sample = radius, position_optimized[0], position_optimized[1], position_optimized[2], orientation_optimized[0], orientation_optimized[1], orientation_optimized[2]
                        Best_Sample_Position = iteration+1
                        print("Iteration: {}".format(iteration+1+veces*NumIter))
                        print("Current Radius:", Best_Sample[0])
                        print("Current Position: X: {}, Y:{}, Z:{}".format(Best_Sample[1],Best_Sample[2],Best_Sample[3]))
                        print("Current Orientation: X: {}, Y:{}, Z:{}".format(Best_Sample[4],Best_Sample[5],Best_Sample[6]))
                        # print("Current Length:", Best_Sample[7])
                        print("RANSAC Score: {}, Score: {} (Found in Iteration {})".format(RANSAC_Score,Score,Best_Sample_Position))
                        print("----------")
                    else:
                        print("Iteration: {}".format(iteration+1+veces*NumIter))
                        print("Current Radius:", Best_Sample[0])
                        print("RANSAC Score: {}, Score: {} (Found in Iteration {})".format(RANSAC_Score,Score,Best_Sample_Position))
                        print("----------")
                except:
                    continue
                
            """Parametros para la generacion de la primitiva del cilindro"""
            Cylinder_Radius = Best_Sample[0]
            
            """Matrices de rotacion"""
            Vector_Orientacion = [Best_Sample[4],Best_Sample[5],Best_Sample[6]]
            normalizado_orientacion = max(abs(np.asarray(Vector_Orientacion)))
            Vector_Orientacion = Vector_Orientacion/normalizado_orientacion
            Rotate = Rotation.align_vectors([Vector_Orientacion], [[0,0,1]]) # Para rotar primitiva a orientacion de pcd
            mesh.applyTransform(Rotate[0].as_matrix(), reset=True)
            New_Orientation = Rotate[0].apply(Vector_Orientacion)
            normalizado_nuevo = max(abs(np.asarray(New_Orientation)))
            New_Orientation = New_Orientation/normalizado_nuevo
    
            if (New_Orientation[0] <= 0.001) and (abs(New_Orientation[1]) <= 0.001) and (abs(New_Orientation[2]) == 1):
                break

        matrixZtoX = np.asarray([[0., 0., 1.],[0., 1., 0.],[-1., 0., 0.]])
        mesh.applyTransform(matrixZtoX, reset=True)
        stop_time = timeit.default_timer()
        
        # new_vertices = Rotate[0].apply(vertices)
        # axis_1 = max(new_vertices[:,0])-min(new_vertices[:,0])
        # axis_2 = max(new_vertices[:,1])-min(new_vertices[:,1])
        # axis_3 = max(new_vertices[:,2])-min(new_vertices[:,2])
        # max_axis = axis_1, axis_2, axis_3
        # max_dim = max(max_axis)
        # radio = max_dim/2
        print("Original Orientation: X: {:.5f}, Y:{:.5f}, Z:{:.5f}".format(Vector_Orientacion[0],Vector_Orientacion[1],Vector_Orientacion[2]))
        print("New Orientation: X: {:.5f}, Y:{:.5f}, Z:{:.5f}".format(New_Orientation[0],New_Orientation[1],New_Orientation[2]))
        print("Radio: {:.5f}".format(Cylinder_Radius))
        print('Time: {:.5} seconds'.format(stop_time - start_time))  
        return mesh

    def orientar_cilindro_manualmente(self, mesh: vedo.Mesh, lista_marcadores: List[vedo.shapes.Cross3D], rotaciones: List) -> Tuple[List[Rotation], vedo.Mesh, List[vedo.shapes.Cross3D]]:
        """
            Orienta la malla ingresada usando los marcadores colocados sobre su superficie para calcular las rotaciones necesarias.
            La malla es rotada respecto a su centro.
            Para la orientación de cilindros se requieren 4 marcadores.
            El primer marcador corresponde al origen elegido para la pieza.
            El segundo marcador es usado para crear un vector entre el primer y segundo marcador, indicando la dirección general del eje X.
            Se asume que el eje del cilindro será orientado al eje X.
            Los últimos dos marcadores son usados para estimar el centro y radio de cilindro.
            Todos los marcadores deben estar en el manto para obtener un buen resultado.
            Una vez rotada la malla se hace una primera traslación para centrar el cilindro, 
            y una segunda traslación coloca el origen de la pieza en la posición 0 del eje X global.
            Con esto posición final debe ser [0, 0, coordZCentro]

            Parameters
            ----------
            mesh : vedo.Mesh
                malla a orientar, visualizada en VedoPanel
            
            lista_marcadores : List[vedo.shapes.Cross3D]
                lista de marcadores colocados sobre la pieza para guiar la orientación de la malla.
                La utilidad de los marcadores es solo la posición en la que se encuentran, una vez orientados 
                ya no son útiles, solo son orientados y visualizados por consistencia.
            
            rotaciones : List
                lista vacía para guardar las rotaciones aplicadas a la malla en la orientación actual.
                Usado para poder resetear la última orientación guardada.
            
            Returns
            -------
            List[Rotation], vedo.Mesh, List[vedo.shapes.Cross3D]
                lista de rotaciones usadas, malla orientada, lista con marcadores orientados
        """

        if len(lista_marcadores) == 4:
            # TODO: REVISAR PORQUE SCIPY DA USERWARNING SOBRE ROTACIONES
            # DICE QUE NO SON ÓPTIMAS O ESTÁN BIEN DEFINIDAS
            punto_origen = np.asarray(lista_marcadores[0].pos())
            punto_eje_x = np.asarray(lista_marcadores[1].pos())
            
            # Primera rotación para alinear con eje X
            vector_x = punto_eje_x - punto_origen
            vector_x = vector_x/np.linalg.norm(vector_x)
            
            ejes_alineacion = [[1, 0, 0]]
            vectores_elegidos = [vector_x]
            rotacion_transform = self.calcular_rotacion(ejes_alineacion, vectores_elegidos)
            mesh.applyTransform(rotacion_transform.as_matrix(), reset=True)
            lista_marcadores = self.orientar_marcadores(lista_marcadores, rotacion_transform.as_matrix())
            rotaciones.append(rotacion_transform)

            # Orientación usando OBB, 'ordena' el cilindro después de alinearlo
            # Importante porque vector X hecho por usuario no necesariamente es necesariamente colinear a eje de cilindro
            # Esto hace que sea un poco más robusto con respecto a la elección de los puntos
            # Funciona porque cilindros son regulares
            malla_trimsh = vedo.utils.vedo2trimesh(mesh)
            half = malla_trimsh.bounding_box_oriented.primitive.extents / 2

            puntos_esquinas_transformados = trimesh.transform_points(trimesh.bounds.corners([-half, half]), 
                                                                    malla_trimsh.bounding_box_oriented.primitive.transform)

            vector_alineacion_x = puntos_esquinas_transformados[4] - puntos_esquinas_transformados[0]
            vector_alineacion_x = vector_alineacion_x/np.linalg.norm(vector_alineacion_x)
            
            vector_alineacion_z = puntos_esquinas_transformados[1] - puntos_esquinas_transformados[0]
            vector_alineacion_z = vector_alineacion_z/np.linalg.norm(vector_alineacion_z)

            if puntos_esquinas_transformados[1, 2] < puntos_esquinas_transformados[0, 2]:
                # Alinea vector a Z positivo en caso de estár apuntando a Z negativo
                vector_alineacion_z = puntos_esquinas_transformados[0] - puntos_esquinas_transformados[1]
            if puntos_esquinas_transformados[4, 0] < puntos_esquinas_transformados[0, 0]:
                # Alinea vector a X positivo en caso de estár al revés
                vector_alineacion_x = puntos_esquinas_transformados[0] - puntos_esquinas_transformados[4]

            ejes_alineacion = [[1, 0, 0], [0, 0, 1]]
            vectores_elegidos = [vector_alineacion_x, vector_alineacion_z]
            rotacion_transform = self.calcular_rotacion(ejes_alineacion, vectores_elegidos)
            mesh.applyTransform(rotacion_transform.as_matrix(), reset=True)
            lista_marcadores = self.orientar_marcadores(lista_marcadores, rotacion_transform.as_matrix())
            rotaciones.append(rotacion_transform)
            
            # Orientación deja punto origen en Z positivo
            punto_origen = np.asarray(lista_marcadores[0].getTransform().GetPosition())
            punto_y_positivo = np.asarray(lista_marcadores[2].getTransform().GetPosition())
            punto_final_circulo = np.asarray(lista_marcadores[3].getTransform().GetPosition())
            
            centro, _ = utilidades.calcular_cilindro([punto_origen, punto_y_positivo, punto_final_circulo])
            punto_centro = [punto_origen[0], centro[0], centro[1]]
            vector_z = punto_origen - punto_centro
            vector_z = vector_z/np.linalg.norm(vector_z)

            ejes_alineacion = [[0, 0, 1]]
            vectores_elegidos = [vector_z]
            rotacion_transform = self.calcular_rotacion(ejes_alineacion, vectores_elegidos)
            mesh.applyTransform(rotacion_transform.as_matrix(), reset=True)
            lista_marcadores = self.orientar_marcadores(lista_marcadores, rotacion_transform.as_matrix())
            rotaciones.append(rotacion_transform)
            
            # Cálculo de centro de cilindro y traslación
            punto_origen = np.asarray(lista_marcadores[0].getTransform().GetPosition())
            punto_y_positivo = np.asarray(lista_marcadores[2].getTransform().GetPosition())
            punto_final_circulo = np.asarray(lista_marcadores[3].getTransform().GetPosition())
            
            centro, _ = utilidades.calcular_cilindro([punto_origen, punto_y_positivo, punto_final_circulo])
            punto_centro = np.asarray([punto_origen[0], centro[0], centro[1]])

            mesh.shift(-punto_centro)
            for i, marcador in enumerate(lista_marcadores):
                lista_marcadores[i] = marcador.shift(-punto_centro)
            
            return rotaciones, mesh, lista_marcadores
        else:
            return rotaciones, mesh, lista_marcadores

    def calc_dist_to_line(self, point: Sequence, position: Sequence, orientation: Sequence) -> float:
        #TODO: CHECK DOSCSTRING
        """
            Calcular la distancia de un punto (o puntos) 3D a una línea 3D que pasa a través de [xc, yc, zc] con dirección [sx, sy, sz]

            Parameters
            ----------
            point : Sequence
                punto (o puntos) al cual se le quiere calcular la distancia a una línea.

            position : Sequence
                punto en la línea a la cual se quiere calcular la distancia desde un punto (o puntos).

            orientation : Sequence
                orientación de la línea a la cual se quiere calcular la distancia desde el punto.

            Returns
            -------
            float
                distancia normalizada desde el punto (o puntos) a la línea.
        """

        point = np.asarray(point)
        position = np.asarray(position)
        orientation = np.asarray(orientation)
        dist = position - point
        d = np.cross(dist,orientation)
        
        if len(np.shape(point)) == 1:
            return (np.linalg.norm(d))/(np.linalg.norm(orientation))
        else:
            return (np.linalg.norm(d, axis=1))/(np.linalg.norm(orientation))
    
    def calc_singlepointdist_to_line(self, point: Sequence, position: Sequence, orientation: Sequence) -> float:
        #TODO: CHECK DOSCSTRING
        """
            Calcular la distancia de un punto 3D a una línea 3D que pasa a través de [xc, yc, zc] con dirección [sx, sy, sz]

            Parameters
            ----------
            point : Sequence
                punto al cual se le quiere calcular la distancia a una línea.
            
            position : Sequence
                punto en la línea a la cual se quiere calcular la distancia desde un punto (o puntos).

            orientation : Sequence
                orientación de la línea a la cual se quiere calcular la distancia desde el punto.

            Returns
            -------
            float
                distancia normalizada a la línea desde el punto.
        """

        point = np.asarray(point)
        position = np.asarray(position)
        orientation = np.asarray(orientation)
        dist = position - point
        d = np.cross(dist, orientation)
        
        return (np.linalg.norm(d))/(np.linalg.norm(orientation))
    
    def dist_pts3d(self, x: Sequence, y: Sequence) -> np.ndarray:
        #TODO: CHECK DOCSTRING
        """
            Calcula la distancia entre dos puntos en 3D.

            Parameters
            ----------
            x : Sequence
                punto al cual se le quiere calcular la distancia con otro

            y : Sequence
                punto al cual se le quiere calcular la distancia con otro

            Returns
            -------
            np.ndarray
                distancia entre los puntos.
        """

        x = np.asarray(x)
        x = x.T
        return np.sqrt((x[0]-y[0])**2 + (x[1]-y[1])**2 + (x[2]-y[2])**2)
    
    def direction_vector(self, x: Sequence, y: Sequence) -> Sequence:
        #TODO: CHECK DOCSTRING
        """
            Calcula la dirección de un vector.
        """
        return (x[0]-y[0])/self.dist_pts3d(x, y), (x[1]-y[1])/self.dist_pts3d(x, y), (x[2]-y[2])/self.dist_pts3d(x, y)
    
    def dist_point_to_cone(self, cone_args: Sequence, point: Sequence) -> float:
        """
            Calcula la distancia de un punto a un cono.
            
            Parameters
            ----------
            cone_args : Sequence
                parámetros de posición, origen, y ángulo del cono.
            
            point : Sequence
                punto al cual se le quiere calcular la distancia a un cono.

            Returns
            -------
            float
                distancia desde el punto a un cono.
        """

        phi, posX, posY, posZ, oriX, oriY, oriZ = cone_args
        position = [posX, posY, posZ]
        orientation = [oriX, oriY, oriZ]
        
        xr = self.calc_dist_to_line(point, position, orientation)
        # xh_0 = list(project_point_to_line(point, orientation))
        xh = np.sqrt((self.dist_pts3d(point, position))**2-xr**2)
        
        dist = xr*np.cos(phi) - (xh)*np.sin(phi)

        return abs(dist)
    
    def dist_points_to_cone(self, cone_args: Sequence, points: Sequence) -> float:
        #TODO: CHECK DOCSTRING
        """
            Calcula la suma de las distancias de un grupo de puntos a un cono.

            Parameters
            ----------
            cone_args : Sequence
                parámetros de posición, origen, y ángulo del cono.
            
            points : Sequence
                grupo de puntos a los cuales se les quiere calcular la distancia a un cono.

            Returns
            -------
            float
                suma de distancias del grupo de puntos a un cono.
        """

        distancias = self.dist_point_to_cone(cone_args, points)
        return sum(distancias)**2
    
    def project_point_to_line(self, point: Sequence, orientation: Sequence) -> Sequence:
        #TODO: CHECK DOCSTRING
        """
            Proyecta un punto a una línea con cierta orientación.

            Parameters
            ----------
            point : Sequence
                punto que se quiere proyectar a una línea.
            
            orientation : Sequence
                orientación de la línea en la cual se quiere proyectar el punto

            Returns
            -------
            Sequence
                punto proyectado en la línea
        """

        p = np.asarray(point)
        p = np.reshape(p, (-1, 3))

        s = np.asarray(orientation)
        s = np.reshape(s, (-1, 3))
        s = s.T
        
        projection = p@s/np.linalg.norm(s)*s.T
        
        return projection
    
    def in_sphere(self, radio: float, center: Sequence, points: np.ndarray) -> np.ndarray:
        """
            Calcula que puntos de un grupo de puntos se encuentran dentro de una esfera
            definida por su centro y radio.

            Parameters
            ----------
            radio : float
                radio de la esfera a usar para la evaluación.
            
            center : Sequence
                centro de la esfera a usar para la evaluación.
            
            points : np.ndarray
                grupo de puntos a evaluar.
            
            Returns
            -------
            np.ndarray
                puntos del grupo de puntos contenidos en la esfera definida por el radio.
        """

        radios = self.dist_pts3d(points, center)
        posiciones = radios < radio
        contenidos = points[np.where(posiciones == 1)[0]]

        return contenidos

    def orientar_cono_automaticamente(self, mesh):
        """
            Orienta la malla de manera automática a partir de ajustar malla a un modelo obtenido mediante propiedades geométricas y RANSAC.
            Proceso de manera iterativa toma puntos aleatoriamente para ajustar un modelo que defina los parámetros de la malla usada.
            Mediante ajuste se detecta posición del apex del cono (indistinto si el cono tiene un apex físico o solo imaginario),
            radio, ángulo de apertura y orientación en el espacio.
            Obtenidos los parámetros que mejor ajustan a la malla, se usan para rotar desde orientación arbitraria a una de utilidad.
            Una vez rotada la malla la orientación final debe ser [1, 0, 0]

            Parameters
            ----------
            mesh : vedo.Mesh
                malla a orientar, visualizada en VedoPanel

                
            Returns
            -------
            vedo.Mesh
                malla orientada
        """
        
        # TODO: AGREGAR ROTACIONES USADAS A RETURN PARA PODER RESETEAR ORIENTACIÓN
        start_time = timeit.default_timer()
        checkpoint = 0
        veces = 0
        while checkpoint == 0:
            """Carga de vertices del mesh como un array."""
            malla_trimesh = vedo.utils.vedo2trimesh(mesh)
            vertices_full = malla_trimesh.vertices
            normales = malla_trimesh.vertex_normals
            axis_1 = max(vertices_full[:,0])-min(vertices_full[:,0])
            axis_2 = max(vertices_full[:,1])-min(vertices_full[:,1])
            axis_3 = max(vertices_full[:,2])-min(vertices_full[:,2])
            max_axis = axis_1, axis_2, axis_3
            max_dim = max(max_axis)
            
            """Selección de los puntos con sus respectivas normales"""
            Points_With_Normals = vertices_full[:,0],vertices_full[:,1],vertices_full[:,2],normales[:,0],normales[:,1],normales[:,2]
        
            Points_With_Normals = np.array(Points_With_Normals).T
            List_PointsWithNormals_FullSize = list(Points_With_Normals)
            if len(List_PointsWithNormals_FullSize) > 500000:
                List_PointsWithNormals = random.sample(List_PointsWithNormals_FullSize,500000)
                PointsWithNormals = np.asarray(List_PointsWithNormals)
                vertices = PointsWithNormals[:,0], PointsWithNormals[:,1], PointsWithNormals[:,2]
                vertices = np.asarray(vertices)
                vertices = vertices.T   
            else:
                List_PointsWithNormals = List_PointsWithNormals_FullSize
                vertices = vertices_full
                
            NumIter = 1000
            Thresh = 0.001*max_dim
            Score = 0
            Best_Sample = [0, 0, 0, 0, 0, 0, 0]
            Best_Sample_Position = 0
            Data_Iterations = list(range(NumIter))
            
    
            for iteration in range(NumIter):    
                try:
                    Local_Score = 0
                    # points = np.asarray(random.sample(List_PointsWithNormals,3))
                    points = np.asarray(random.sample(list(self.in_sphere(len(vertices)*0.01,Points_With_Normals[random.randint(0,len(vertices)-1)],Points_With_Normals)),3))
                    
                    Point1 = np.array([points[0][0],points[0][1],points[0][2]])
                    Point2 = np.array([points[1][0],points[1][1],points[1][2]])
                    Point3 = np.array([points[2][0],points[2][1],points[2][2]])
                    N1 = np.array([points[0][3],points[0][4],points[0][5]])
                    N2 = np.array([points[1][3],points[1][4],points[1][5]])
                    N3 = np.array([points[2][3],points[2][4],points[2][5]])
    
                    a = np.array([list(N1),list(N2),list(N3)])
                    b = np.array([np.dot(Point1,N1),np.dot(Point2,N2),np.dot(Point3,N3)])
                    x1 = np.linalg.solve(a,b)
                    q = (N1[0]*(Point1[1]-Point2[1])+N1[1]*(Point2[0]-Point1[0]))/(N1[0]*N2[1]-N1[1]*N2[0])
                    x2 = np.array([Point2[0]+q*N2[0], Point2[1]+q*N2[1], Point2[2]+q*N2[2]]) 
                    x = self.direction_vector(x1,x2)
                    Angles = np.array([np.arcsin(self.calc_singlepointdist_to_line(Point1,x1,x)/self.dist_pts3d(x1,Point1)),np.arcsin(self.calc_singlepointdist_to_line(Point2,x1,x)/self.dist_pts3d(x1,Point2)),np.arcsin(self.calc_singlepointdist_to_line(Point3,x1,x)/self.dist_pts3d(x1,Point3))])
                    Apex = x1
                    Angle = Angles.mean()
                    if Angle < np.radians(5) or Angle > np.radians(90):
                        continue
                    Direction = x
                    cone_args = [Angle, Apex[0], Apex[1], Apex[2], Direction[0], Direction[1], Direction[2]]
                    
                    """Comparison and scoring of points"""
                    comparison = self.dist_point_to_cone(cone_args,vertices) < Thresh
                    Local_Score = comparison.sum()
                    RANSAC_Score = Local_Score
                    Data_Iterations[iteration] = RANSAC_Score, cone_args
                    
                    if RANSAC_Score > Score:
                        Score = RANSAC_Score
                        Best_Sample = cone_args
                        Best_Sample_Position = iteration+1
                            
                        print("Iteration: {}".format(iteration+1+veces*NumIter))
                        print("Current Aperture Angle (in degrees):", abs((Best_Sample[0]*180/np.pi)%180))
                        print("Current Apex Position: X: {}, Y:{}, Z:{}".format(Best_Sample[1],Best_Sample[2],Best_Sample[3]))
                        print("Current Orientation: X: {}, Y:{}, Z:{}".format(Best_Sample[4],Best_Sample[5],Best_Sample[6]))
                        print("RANSAC Score: {}, Score: {} (Found in Iteration {})".format(RANSAC_Score,Score,Best_Sample_Position))
                        print("----------")
                        
                    # else:
                    #     print("Iteration: {}".format(iteration+1))
                    #     print("Current Aperture Angle (in degrees):", abs((Best_Sample[0]*180/np.pi)%180))
                    #     print("RANSAC Score: {}, Score: {} (Found in Iteration {})".format(RANSAC_Score,Score,Best_Sample_Position))
                    #     print("----------")
                except:
                    continue
            
            """Parametros para la generación de la primitiva del cono desde PCD"""
            Apex_Position = [Best_Sample[1],Best_Sample[2],Best_Sample[3]]
            Max_Generatriz = max(self.dist_pts3d(Apex_Position,vertices.T))
            Cone_Radius = abs(np.sin(Best_Sample[0])*Max_Generatriz)
                
            """Matrices de rotacion"""
            Vector_Orientacion = [Best_Sample[4],Best_Sample[5],Best_Sample[6]]
            normalizado_orientacion = max(abs(np.asarray(Vector_Orientacion)))
            Vector_Orientacion = Vector_Orientacion/normalizado_orientacion
            Rotate = Rotation.align_vectors([Vector_Orientacion], [[0,0,1]]) # Para rotar primitiva a orientacion de pcd
            mesh.applyTransform(Rotate[0].as_matrix(), reset=True)
            New_Orientation = Rotate[0].apply(Vector_Orientacion)
            normalizado_nuevo = max(abs(np.asarray(New_Orientation)))
            New_Orientation = New_Orientation/normalizado_nuevo
            Apex_Position = [Best_Sample[1],Best_Sample[2],Best_Sample[3]]
            Apex_Position = Rotate[0].apply(Apex_Position)
            
            new_vertices = Rotate[0].apply(vertices)
            stop_time = timeit.default_timer()
            axis_1 = max(new_vertices[:,0])-min(new_vertices[:,0])
            axis_2 = max(new_vertices[:,1])-min(new_vertices[:,1])
            axis_3 = max(new_vertices[:,2])-min(new_vertices[:,2])
            radio = (axis_1/2 + axis_2/2)/2
            
            if (New_Orientation[0] <= 0.001) and (abs(New_Orientation[1]) <= 0.001) and (abs(New_Orientation[2]) == 1):
                break
            
        matrixZtoX = np.asarray([[0., 0., 1.],[0., 1., 0.],[-1., 0., 0.]])
        mesh.applyTransform(matrixZtoX, reset=True)
        # New_Orientation = matrixZtoX.apply(New_Orientation)
        # normalizado_nuevo = max(abs(np.asarray(New_Orientation)))
        # New_Orientation = New_Orientation/normalizado_nuevo
        stop_time = timeit.default_timer()
        print("Aperture Angle (in degrees):", abs((Best_Sample[0]*180/np.pi)%180))
        # print("Original Orientation: X: {:.5f}, Y:{:.5f}, Z:{:.5f}".format(Vector_Orientacion[0],Vector_Orientacion[1],Vector_Orientacion[2]))
        # print("New Orientation: X: {:.5f}, Y:{:.5f}, Z:{:.5f}".format(New_Orientation[0],New_Orientation[1],New_Orientation[2]))
        print("Radius: {:.5f}".format(radio))
        print("Matriz de rotacion:")
        # print(matriz)
        print('Time: {:.5} seconds'.format(stop_time - start_time))
        return mesh

    def orientar_cono_manualmente(self, mesh: vedo.Mesh, lista_marcadores: List[vedo.shapes.Cross3D], rotaciones: List) -> Tuple[List[Rotation], vedo.Mesh, List[vedo.shapes.Cross3D]]:
        """
            Orienta la malla ingresada usando los marcadores colocados sobre su superficie para calcular las rotaciones necesarias.
            La malla es rotada respecto a su centro.
            Para la orientación de conos se requieren 4 marcadores.
            El primer marcador corresponde al origen elegido para la pieza.
            El segundo marcador es usado para crear un vector entre el primer y segundo marcador, indicando la dirección general del eje X.
            Se asume que el eje del cono será orientado al eje X.
            Los últimos dos marcadores son usados para estimar el centro y radio de la base del cono.
            Para un buen resultado, el primer y segundo punto deben estar ambos en la misma generatriz del cono.
            Además, los marcadores deben estar en el manto, y el primer, tercer, y cuarto punto deben estar todos en la base de la malla.
            Finalmente, se debe dar la mayor separación posible al tercer y cuarto marcador.
            Una vez rotada la malla se hace una primera traslación para centrar el cono, 
            y una segunda traslación coloca el origen de la pieza en la posición 0 del eje X global.
            Con esto posición final debe ser [0, 0, coordZCentro]

            Parameters
            ----------
            mesh : vedo.Mesh
                malla a orientar, visualizada en VedoPanel
            
            lista_marcadores : List[vedo.shapes.Cross3D]
                lista de marcadores colocados sobre la pieza para guiar la orientación de la malla.
                La utilidad de los marcadores es solo la posición en la que se encuentran, una vez orientados 
                ya no son útiles, solo son orientados y visualizados por consistencia.
            
            rotaciones : List
                lista vacía para guardar las rotaciones aplicadas a la malla en la orientación actual.
                Usado para poder resetear la última orientación guardada.
            
            Returns
            -------
            List[Rotation], vedo.Mesh, List[vedo.shapes.Cross3D]
                lista de rotaciones usadas, malla orientada, lista con marcadores orientados
        """

        if len(lista_marcadores) == 4:
            punto_origen = np.asarray(lista_marcadores[0].pos())
            punto_eje_x = np.asarray(lista_marcadores[1].pos())
            
            # Alinear con eje X
            vector_x = punto_eje_x - punto_origen
            vector_x = vector_x/np.linalg.norm(vector_x)
            
            ejes_alineacion = [[1, 0, 0]]
            vectores_elegidos = [vector_x]
            rotacion_transform = self.calcular_rotacion(ejes_alineacion, vectores_elegidos)
            mesh.applyTransform(rotacion_transform.as_matrix(), reset=True)
            lista_marcadores = self.orientar_marcadores(lista_marcadores, rotacion_transform.as_matrix())
            rotaciones.append(rotacion_transform)

            # Rotación alinea con eje Z
            # Así obtenemos nuevas posiciones sacadas de la matriz de transformación interna
            # Matriz da la posición actual del objeto (Orientación y Posición)
            # Podría usarse GetCenter() también
            punto_origen = np.asarray(lista_marcadores[0].getTransform().GetPosition())
            punto_y_positivo = np.asarray(lista_marcadores[2].getTransform().GetPosition())
            punto_final_circulo = np.asarray(lista_marcadores[3].getTransform().GetPosition())
            
            centro, _ = utilidades.calcular_cilindro([punto_origen, punto_y_positivo, punto_final_circulo])

            punto_centro = [punto_origen[0], centro[0], centro[1]]
            vector_z = punto_origen - punto_centro            
            vector_z = vector_z/np.linalg.norm(vector_z)

            ejes_alineacion = [[0, 0, 1]]
            vectores_elegidos = [vector_z]
            rotacion_transform = self.calcular_rotacion(ejes_alineacion, vectores_elegidos)
            mesh.applyTransform(rotacion_transform.as_matrix(), reset=True)
            lista_marcadores = self.orientar_marcadores(lista_marcadores, rotacion_transform.as_matrix())
            rotaciones.append(rotacion_transform)
            
            # Orientación más precisa de plano de la base del cono
            # Alineación fina con eje X
            punto_origen = np.asarray(lista_marcadores[0].getTransform().GetPosition())
            punto_y_positivo = np.asarray(lista_marcadores[2].getTransform().GetPosition())
            punto_final_circulo = np.asarray(lista_marcadores[3].getTransform().GetPosition())

            normal_plano_base = utilidades.encontrar_plano_cono([punto_origen, punto_y_positivo, punto_final_circulo])
            angulo_respecto_x = utilidades.angulo_entre_vectores([1, 0, 0], normal_plano_base)
            
            # Necesario agregar las siguientes 2 transformaciones a mano
            # Esto debido a que no siguen el mismo patrón que las transformaciones anteriores
            rotacion_transform = Rotation.from_euler('y', angulo_respecto_x, degrees=True)
            mesh.applyTransform(rotacion_transform.as_matrix(), reset=True)
            lista_marcadores = self.orientar_marcadores(lista_marcadores, rotacion_transform.as_matrix())                      
            rotaciones.append(rotacion_transform)
            
            # Alineación fina con eje Y
            normal_plano_base = utilidades.encontrar_plano_cono([punto_origen, punto_y_positivo, punto_final_circulo])
            angulo_respecto_y = 90 - utilidades.angulo_entre_vectores([0, 1, 0], normal_plano_base)
            
            rotacion_transform = Rotation.from_euler('z', angulo_respecto_y, degrees=True)
            mesh.applyTransform(rotacion_transform.as_matrix(), reset=True)
            lista_marcadores = self.orientar_marcadores(lista_marcadores, rotacion_transform.as_matrix())
            rotaciones.append(rotacion_transform)

            # Cálculo de centro de la base del cono
            # Traslación a origen elegido
            punto_origen = np.asarray(lista_marcadores[0].getTransform().GetPosition())
            punto_y_positivo = np.asarray(lista_marcadores[2].getTransform().GetPosition())
            punto_final_circulo = np.asarray(lista_marcadores[3].getTransform().GetPosition())
            
            centro, _ = utilidades.calcular_cilindro([punto_origen, punto_y_positivo, punto_final_circulo])
            punto_centro = np.asarray([punto_origen[0], centro[0], centro[1]])

            mesh.shift(-punto_centro)
            for i, marcador in enumerate(lista_marcadores):
                lista_marcadores[i] = marcador.shift(-punto_centro)
            
            return rotaciones, mesh, lista_marcadores
        else:
            return rotaciones, mesh, lista_marcadores

    def orientar_marcadores(self, lista_marcadores: List[vedo.shapes.Cross3D], transform: np.ndarray) -> List[vedo.shapes.Cross3D]:
        """
            Orienta los marcadores ingresados según la transformación dada.
            Utilizado para orientar los marcadores usados en la orientación manual de las mallas.

            Parameters
            ----------
            lista_marcadores : List[vedo.shapes.Cross3D]
                lista de marcadores colocados en la malla para realizar la orientación.
            
            transform : np.ndarray
                transformación a aplicar a los marcadores.
                Con forma (3, 3).

            Returns
            -------
            List[vedo.shapes.Cross3D]
                lista de marcadores transformados.
        """

        # POR AHORA NECESARIO HACER LO DEL INVERT Y RESET=TRUE
        # NO SE PORQUE NO SE POSICIONAN CORRECTAMENTE SI SIMPLEMENTE LOS TRANSFORMO SUCESIVAMENTE
        for i, marcador in enumerate(lista_marcadores):
            # Transformar los puntos
            lista_marcadores[i] = marcador.applyTransform(transform, reset=False)
            # Rescatar nuevas posiciones
            new_pos = lista_marcadores[i].getTransform().GetPosition()
            # Invertir transformación y dejar transformación interna en Identidad
            trnsfm = lista_marcadores[i].getTransform(invert=True)
            lista_marcadores[i].applyTransform(trnsfm, reset=True)
            # Aplica nueva posición
            lista_marcadores[i].pos(new_pos)
        return lista_marcadores

    def calcular_rotacion(self, ejes_alineacion: Union[np.ndarray, Sequence], vectores_por_alinear: Union[np.ndarray, Sequence]) -> Rotation:
        """
            Estima una transformación para alinear los vectores dados a los ejes ingresados.

            Parameters
            ----------
            ejes_alineacion : np.ndarray o Sequence, con forma (N, 3)
                ejes a los cuales se quiere alinear los vectores.
            
            vectores_por_alinear : np.ndarray o Sequence, con forma (N, 3)
                vectores que se desean alinear con los ejes ingresados.

            Returns
            -------
            Rotation
                rotación estimada para alinear vectores.
        """

        # SE DEBERÍA USAR UN USER EVENT MEJOR
        # PERO NUNCA ENTENDÍ COMO HACERLO
        # POR AHORA SE USA ESTA FUNCIÓN
        # PUESTA EN LAS ALINEACIONES DE CADA GEOMETRÍA
        rotacion_transform = Rotation.align_vectors(ejes_alineacion, vectores_por_alinear)
        return rotacion_transform[0]

    def calcular_angulo_apertura_cono(self, pieza: trimesh.Trimesh, origen: Sequence) -> float:
        """
            Estima el ángulo de apertura del cono dado en la pieza, 
            basado en el promedio de las normales cercanas al punto entregado.
            Se calcula esta normal y se gira 90 grados para calcular el ángulo entre 
            la línea generada por la normal girada y el eje X.

            Parameters
            ----------
            pieza : trimesh.Trimesh
                malla de Trimesh de un cono al cual se le quiere calcular el ángulo de apertura.
            
            origen : Sequence
                punto utilizado para calcular ángulo de apertura.
                En la orientación de conos se utiliza el origen elegido.
            
            Returns
            -------
            float
                ángulo de apertura estimado, entregado en grados
        """

        indxs = trimesh.proximity.nearby_faces(pieza, [origen])[0]
        normal = [0, 0, 0]
        for indice in indxs:
            normal += pieza.face_normals[indice]
        normal = normal / len(indxs)
        normal_punto_origen = (normal / np.linalg.norm(normal))

        r = Rotation.from_euler('y', 90, degrees=True)
        normal_rotada = r.apply(normal_punto_origen)
        segundo_punto = 10 * normal_rotada
        angulo_apertura = utilidades.angulo_entre_vectores([1,0,0], segundo_punto)

        return angulo_apertura

    def calcular_cortes_malla(self, pieza: trimesh.Trimesh, ancho_cordon: float, alto_cordon: float, step_over: float, 
                            tipo_pieza: int=0, descriptor_pieza: Tuple[float, float]=[1, 0]) -> List[List[np.ndarray]]:
        """
            Calcula cortes transversales de la malla ingresada, utilizando la geometría del cordón de soldadura para estimar las alturas de corte.
            En los casos de cilindros y conos además se hace uso del descriptor de pieza.
            Los cortes son hechos con planos paralelos al plano XY.
            Para los casos de cilindros y conos, los cortes son hechos en un sistema de coordenadas cilíndricas.
            Se usa el indicador de tipo de pieza para elegir la estrategia de corte, tipo_pieza=0 indica placas, 
            tipo_pieza=1 indica cilindros, y tipo_pieza=2 indica conos.
            Retorna una lista de listas. Cada elemento de la lista es una capa, la cual a su vez es una lista.
            Cada capa contiene los contornos encontrados, los cuales son np.ndarray.
            Se asume que cada contorno encontrado es una falla y será considerado como un contorno independiente.

            Parameters
            ----------
            pieza : trimesh.Trimesh
                pieza a la cual se le quiere detectar daños mediante el cálculo de cortes transversales.
            
            ancho_cordon : float
                ancho de cordón de soldadura.
            
            alto_cordon : float
                altura de cordón de soldadura.
            
            step_over : float
                step-over entre cordones de soldadura.
            
            tipo_pieza : int, optional
                indicador de tipo de pieza.
                0=placa, 1=cilindro, 2=cono, by default 0
            
            descriptor_pieza : Tuple[float, float], optional
                lista de descriptores usada en los casos de cilindro y cono, correspondientes a [radio base, ángulo apertura], by default [1, 0]
            
            Returns
            -------
            List[List[np.ndarray]]
                lista donde cada elemento es una capa, y cada capa es una lista que contiene los contornos encontrados en forma de arrays.
        """

        # CASO PLACA
        if tipo_pieza == 0:
            cortes = self.calcular_cortes_placa(pieza, ancho_cordon, alto_cordon, step_over)
            return cortes
        # CASO CILINDROS
        if tipo_pieza == 1:
            cortes = self.calcular_cortes_cilindro(pieza, ancho_cordon, alto_cordon, step_over, descriptor_pieza)
            return cortes
        # CASO CONOS
        if tipo_pieza == 2:
            cortes = self.calcular_cortes_cono(pieza, ancho_cordon, alto_cordon, step_over, descriptor_pieza)
            return cortes

    def calcular_cortes_placa(self, pieza: trimesh.Trimesh, ancho_cordon: float, alto_cordon: float, step_over: float) -> List[List[np.ndarray]]:
        """
            Calcula cortes transversales de la malla ingresada, utilizando la geometría del cordón de soldadura para estimar las alturas de corte.
            Los cortes son hechos con planos paralelos al plano XY.
            Retorna una lista de listas. Cada elemento de la lista es una capa, la cual a su vez es una lista.
            Cada capa contiene los contornos encontrados, los cuales son np.ndarray.
            Se asume que cada contorno encontrado es una falla y será considerado como un contorno independiente.

            Parameters
            ----------
            pieza : trimesh.Trimesh
                pieza a la cual se le quiere detectar daños mediante el cálculo de cortes transversales.
            
            ancho_cordon : float
                ancho de cordón de soldadura.
            
            alto_cordon : float
                altura de cordón de soldadura.
            
            step_over : float
                step-over entre cordones de soldadura.
            
            Returns
            -------
            List[List[np.ndarray]]
                lista donde cada elemento es una capa, y cada capa es una lista que contiene los contornos encontrados en forma de arrays.

        """

        alturas_cortes, _ = utilidades.select_layer(pieza, height_cordon=alto_cordon, width_cordon=ancho_cordon, step_over=step_over)
        
        sections_dmg = pieza.section_multiplane(plane_origin=[0, 0, 0],
                                                plane_normal=[0, 0, 1],
                                                heights=alturas_cortes)
        sections_dmg = [section for section in sections_dmg if section is not None]
        geoms_dmg = [section.polygons_full for section in sections_dmg if section is not None]  # Array por capas con poly
        geoms_dmg_multi = [shapely.geometry.MultiPolygon(list(dmg)) for dmg in geoms_dmg]
        geoms_dmg_multi = [geoms_dmg.buffer(-ancho_cordon*0.08).buffer(ancho_cordon*0.08) for geoms_dmg in geoms_dmg_multi]
        
        for i, dmg in enumerate(geoms_dmg_multi):
            matrix = sections_dmg[i].metadata["to_3D"]
            geoms_dmg_multi[i] = shapely.ops.transform(lambda x, y, z=matrix[2][3]: (x, y, z), dmg)
        
        geoms_dmg_multi = utilidades.filtrar_cortes(geoms_dmg_multi, ancho_cordon)
        curvas_por_capa = [utilidades.extraer_coords(capa) for capa in geoms_dmg_multi if capa]
        
        return curvas_por_capa
    
    def calcular_cortes_cilindro(self, pieza: trimesh.Trimesh, ancho_cordon: float, alto_cordon: float, step_over: float, descriptor_pieza: Tuple[float, float]) -> List[List[np.ndarray]]:
        """
            Calcula cortes transversales de la malla ingresada, utilizando la geometría del cordón de soldadura para estimar las alturas de corte.
            Los cortes son hechos con planos paralelos al plano XY, en el caso de cilindros el eje Y representa grados.
            Los cortes son realizados en un sistema de coordenadas cilíndrico, las coordenadas de la malla son transformadas y luego se corta como placa.
            Los cortes a su vez son transformados a un sistema de coordenadas cartesianos antes de su retorno.
            Retorna una lista de listas. Cada elemento de la lista es una capa, la cual a su vez es una lista.
            Cada capa contiene los contornos encontrados, los cuales son np.ndarray.
            Se asume que cada contorno encontrado es una falla y será considerado como un contorno independiente.

            Parameters
            ----------
            pieza : trimesh.Trimesh
                pieza a la cual se le quiere detectar daños mediante el cálculo de cortes transversales.
            
            ancho_cordon : float
                ancho de cordón de soldadura.
            
            alto_cordon : float
                altura de cordón de soldadura.
            
            step_over : float
                step-over entre cordones de soldadura.
            
            descriptor_pieza : Tuple[float, float], optional
                lista de descriptores usada en los casos de cilindro y cono, correspondientes a [radio base, ángulo apertura].
                Los cilindros no poseen un ángulo de apertura, pero el radio es usado en las transformaciones de sistemas de coordenadas.
            
            Returns
            -------
            List[List[np.ndarray]]
                lista donde cada elemento es una capa, y cada capa es una lista que contiene los contornos encontrados en forma de arrays.
        """

        pieza = utilidades.transform_cilindrical_pieza(pieza=pieza, inv=False, radio=descriptor_pieza[0])
        curvas_por_capa = self.calcular_cortes_placa(pieza, ancho_cordon, alto_cordon, step_over)
        curvas_por_capa = utilidades.transform_cilindrical_cortes(cortes=curvas_por_capa, inv=True, radio=descriptor_pieza[0])
        return curvas_por_capa
    
    def calcular_cortes_cono(self, pieza: trimesh.Trimesh, ancho_cordon: float, alto_cordon: float, step_over: float, descriptor_pieza: Tuple[float, float]) -> List[List[np.ndarray]]:
        """
            Calcula cortes transversales de la malla ingresada, utilizando la geometría del cordón de soldadura para estimar las alturas de corte.
            Los cortes son hechos con planos paralelos al plano XY, en el caso de conos el eje Y representa grados.
            Los cortes son realizados en un sistema de coordenadas cilíndrico, las coordenadas de la malla son transformadas y luego se corta como placa.
            En el caso de conos es necesario realizar la transformación a coordenadas cilíndricas, y luego rotar la malla en el eje Y
            un ángulo igual al de apertura para su procesamiento, luego considerando el caso como de placa.
            Los cortes a su vez son transformados a un sistema de coordenadas cartesianos antes de su retorno.
            Retorna una lista de listas. Cada elemento de la lista es una capa, la cual a su vez es una lista.
            Cada capa contiene los contornos encontrados, los cuales son np.ndarray.
            Se asume que cada contorno encontrado es una falla y será considerado como un contorno independiente.

            Parameters
            ----------
            pieza : trimesh.Trimesh
                pieza a la cual se le quiere detectar daños mediante el cálculo de cortes transversales.
            
            ancho_cordon : float
                ancho de cordón de soldadura.
            
            alto_cordon : float
                altura de cordón de soldadura.
            
            step_over : float
                step-over entre cordones de soldadura.
            
            descriptor_pieza : Tuple[float, float], optional
                lista de descriptores usada en los casos de cilindro y cono, correspondientes a [radio base, ángulo apertura].
                Tanto el radio base como el ángulo de apertura son utilizados en la transformación de sistema de coordendas de conos.
            
            Returns
            -------
            List[List[np.ndarray]]
                lista donde cada elemento es una capa, y cada capa es una lista que contiene los contornos encontrados en forma de arrays.
        """

        # En el caso de conos el radio es variable
        # Radio depende de la posición en el eje del cono y el ángulo de apertura
        radio_cono = -1*(np.tan(np.deg2rad(descriptor_pieza[1]))*pieza.vertices[:, 0] - descriptor_pieza[0])
        pieza = utilidades.transform_cilindrical_pieza(pieza=pieza, inv=False, radio=radio_cono)
        # Se necesita transformar a cilindricas antes de rotar el cono, para calcular el cambio de radios
        r = Rotation.from_euler('y', -descriptor_pieza[1], degrees=True)
        pieza.vertices = r.apply(pieza.vertices)

        curvas_por_capa = self.calcular_cortes_placa(pieza, ancho_cordon, alto_cordon, step_over)

        # Se rota para revertir la transformación hecha antes
        r = Rotation.from_euler('y', descriptor_pieza[1], degrees=True)
        for i, capa in enumerate(curvas_por_capa):
            for j, curva in enumerate(capa):
                curvas_por_capa[i][j] = r.apply(curva)
        curvas_por_capa = utilidades.transform_cilindrical_cortes_conos(cortes=curvas_por_capa, inv=True, descriptor=descriptor_pieza)
        return curvas_por_capa
    
    def calcular_trayectorias(self, cortes: List[List[np.ndarray]], ancho_cordon: float, alto_cordon: float, offset: float, step_over: float, 
                            velocidad: float, material: str, tipo_pieza: int=0, descriptor_pieza: Tuple[float, float]=[1, 0]) -> List[List[List[np.ndarray]]]:
        #TODO: CHECK DOCSTRING
        """
            Calcula las trayectorias para los contornos contenidos en los cortes ingresados.
            En un principio, el cálculo se realiza de manera independiente por cada contorno y por cada capa.
            En caso que un contorno se repita en capas las capas siguientes a las que aparece, 
            se repite la trayectoria calculada para el primero.
            Cada trayectoria se elige entre una lista de estrategias, seleccionando la que tenga mejor desempeño,
            medido en área cubierta, cantidad de movimientos, y soldadura sobrante estimada.
            Para los casos de cilindros y conos, los cortes son transformados a un sistema de coordenadas cilindricas,
            y luego se calculan las trayectorias. En ese caso, las trayectorias son transformadas a un sistema de coordenadas
            cartesianos antes de retornarlas.

            Parameters
            ----------
            cortes : List[List[np.ndarray]]
                contornos obtenidos del corte de mallas.
                Representan las fallas presentes en la malla.
            
            ancho_cordon : float
                ancho del cordón de soldadura.
            
            alto_cordon : float
                alto del cordón de soldadura.
            
            offset : float
                offset de los cordones de soldadura con respecto a las paredes/bordes de contornos de los cortes.
            
            step_over : float
                step-over entre cordones de soldadura.
            
            velocidad : float
                velocidad de soldadura a utilizar.
            
            material : str
                material del alambre de soldadura a utilizar.

            tipo_pieza : int, optional
                indicador de tipo de pieza.
                0=placa, 1=cilindro, 2=cono, by default 0
            
            descriptor_pieza : Tuple[float, float], optional
                lista de descriptores usada en los casos de cilindro y cono, correspondientes a [radio base, ángulo apertura], by default [1, 0]
            
            Returns
            -------
            List[List[List[np.ndarray]]]
                trayectorias calculadas para cada contorno entregado en la variable cortes.
        """

        densidad_material = self.df_info_materiales[self.df_info_materiales['Material'] == material].Densidad[0]
        # CASO PLACA
        if tipo_pieza == 0:
            trayectorias = self.calcular_trayectorias_placa(cortes, ancho_cordon, alto_cordon, offset, step_over, velocidad, densidad_material)
            return trayectorias
        # CASO CILINDROS
        if tipo_pieza == 1:
            trayectorias = self.calcular_trayectorias_cilindro(cortes, ancho_cordon, alto_cordon, offset, step_over, velocidad, densidad_material, descriptor_pieza)
            return trayectorias
        # CASO CONOS
        if tipo_pieza == 2:
            trayectorias = self.calcular_trayectorias_cono(cortes, ancho_cordon, alto_cordon, offset, step_over, velocidad, densidad_material, descriptor_pieza)
            return trayectorias

    def calcular_trayectorias_placa(self, cortes: List[List[np.ndarray]], ancho_cordon: float, alto_cordon: float, offset: float, step_over: float, 
                                velocidad: float, densidad_material: float) -> List[List[List[np.ndarray]]]:
        """
            Calcula las trayectorias para los contornos contenidos en los cortes ingresados.
            En un principio, el cálculo se realiza de manera independiente por cada contorno y por cada capa.
            En caso que un contorno se repita en capas las capas siguientes a las que aparece, 
            se repite la trayectoria calculada para el primero.
            Cada trayectoria se elige entre una lista de estrategias, seleccionando la que tenga mejor desempeño,
            medido en área cubierta, cantidad de movimientos, y soldadura sobrante estimada.

            Parameters
            ----------
            cortes : List[List[np.ndarray]]
                contornos obtenidos del corte de mallas.
                Representan las fallas presentes en la malla.
            
            ancho_cordon : float
                ancho del cordón de soldadura.
            
            alto_cordon : float
                alto del cordón de soldadura.
            
            offset : float
                offset de los cordones de soldadura con respecto a las paredes/bordes de contornos de los cortes.
            
            step_over : float
                step-over entre cordones de soldadura.
            
            velocidad : float
                velocidad de soldadura a utilizar.
            
            densidad_material : float
                densidad del material del alambre de soldadura a utilizar.
            
            Returns
            -------
            List[List[List[np.ndarray]]]
                trayectorias calculadas para cada contorno entregado en la variable cortes.
        """

        anglevalues, data, nameoption, dividelist, areacompare, areadivision = param_values.testing(cortes, offset, step_over, ancho_cordon, alto_cordon, velocidad, densidad_material)
        _, capas = param_values.generation_paths(anglevalues, data, nameoption, dividelist, areacompare, areadivision, offset, step_over, ancho_cordon, alto_cordon, velocidad, densidad_material)
        return capas[0]

    def calcular_trayectorias_cilindro(self, cortes: List[List[np.ndarray]], ancho_cordon: float, alto_cordon: float, offset: float, step_over: float, 
                                    velocidad: float, densidad_material: float, descriptor_pieza: Tuple[float, float]) -> List[List[List[np.ndarray]]]:
        """
            Calcula las trayectorias para los contornos contenidos en los cortes ingresados.
            En un principio, el cálculo se realiza de manera independiente por cada contorno y por cada capa.
            En caso que un contorno se repita en capas las capas siguientes a las que aparece, 
            se repite la trayectoria calculada para el primero.
            Cada trayectoria se elige entre una lista de estrategias, seleccionando la que tenga mejor desempeño,
            medido en área cubierta, cantidad de movimientos, y soldadura sobrante estimada.
            Para el caso de cilindros, los cortes son transformados a un sistema de coordenadas cilindricas,
            y luego se calculan las trayectorias, finalmente las trayectorias son transformadas a un sistema de coordenadas
            cartesianos antes de retornarlas.

            Parameters
            ----------
            cortes : List[List[np.ndarray]]
                contornos obtenidos del corte de mallas.
                Representan las fallas presentes en la malla.
            
            ancho_cordon : float
                ancho del cordón de soldadura.
            
            alto_cordon : float
                alto del cordón de soldadura.
            
            offset : float
                offset de los cordones de soldadura con respecto a las paredes/bordes de contornos de los cortes.
            
            step_over : float
                step-over entre cordones de soldadura.
            
            velocidad : float
                velocidad de soldadura a utilizar.
            
            densidad_material : float
                densidad del material del alambre de soldadura a utilizar.
            
            descriptor_pieza : Tuple[float, float], optional
                lista de descriptores usada en los casos de cilindro y cono, correspondientes a [radio base, ángulo apertura], by default [1, 0]
            
            Returns
            -------
            List[List[List[np.ndarray]]]
                trayectorias calculadas para cada contorno entregado en la variable cortes.
        """

        # Transformar pieza a sistema de coordenadas cilíndricos y luego tratar como placa
        cortes = utilidades.transform_cilindrical_cortes(cortes=cortes, radio=descriptor_pieza[0], inv=False)
        capas = self.calcular_trayectorias_placa(cortes, ancho_cordon, alto_cordon, offset, step_over, velocidad, densidad_material)
        # Devolver a sistema cartesiano para usos futuros y visualización
        for i, capa in enumerate(capas):
            capas[i] = utilidades.transform_cilindrical_cortes(cortes=capa, radio=descriptor_pieza[0], inv=True)
        return capas

    def calcular_trayectorias_cono(self, cortes: List[List[np.ndarray]], ancho_cordon: float, alto_cordon: float, offset: float, step_over: float, 
                                velocidad: float, densidad_material: float, descriptor_pieza: Tuple[float, float]) -> List[List[List[np.ndarray]]]:
        """
            Calcula las trayectorias para los contornos contenidos en los cortes ingresados.
            En un principio, el cálculo se realiza de manera independiente por cada contorno y por cada capa.
            En caso que un contorno se repita en capas las capas siguientes a las que aparece, 
            se repite la trayectoria calculada para el primero.
            Cada trayectoria se elige entre una lista de estrategias, seleccionando la que tenga mejor desempeño,
            medido en área cubierta, cantidad de movimientos, y soldadura sobrante estimada.
            En el caso de conos es necesario realizar la transformación a coordenadas cilíndricas, y luego rotar la malla en el eje Y
            un ángulo igual al de apertura, para que puedan calcularse las trayectorias.
            Las trayectorias son transformadas a un sistema de coordenadas cartesianos antes de retornarlas.

            Parameters
            ----------
            cortes : List[List[np.ndarray]]
                contornos obtenidos del corte de mallas.
                Representan las fallas presentes en la malla.
            
            ancho_cordon : float
                ancho del cordón de soldadura.
            
            alto_cordon : float
                alto del cordón de soldadura.
            
            offset : float
                offset de los cordones de soldadura con respecto a las paredes/bordes de contornos de los cortes.
            
            step_over : float
                step-over entre cordones de soldadura.
            
            velocidad : float
                velocidad de soldadura a utilizar.
            
            densidad_material : float
                densidad del material del alambre de soldadura a utilizar.
            
            descriptor_pieza : Tuple[float, float], optional
                lista de descriptores usada en los casos de cilindro y cono, correspondientes a [radio base, ángulo apertura], by default [1, 0]
            
            Returns
            -------
            List[List[List[np.ndarray]]]
                trayectorias calculadas para cada contorno entregado en la variable cortes.
        """

        cortes = utilidades.transform_cilindrical_cortes_conos(cortes=cortes, inv=False, descriptor=descriptor_pieza)
        r = Rotation.from_euler('y', -descriptor_pieza[1], degrees=True)
        for i, capa in enumerate(cortes):
            for j, curva in enumerate(capa):
                cortes[i][j] = r.apply(curva)
        
        capas = self.calcular_trayectorias_placa(cortes, ancho_cordon, alto_cordon, offset, step_over, velocidad, densidad_material)

        r = Rotation.from_euler('y', descriptor_pieza[1], degrees=True)
        for i, capa in enumerate(capas):
            for j, curva in enumerate(capa):
                for k, linea in enumerate(curva):
                    capas[i][j][k] = r.apply(linea)
        for i, capa in enumerate(capas):
            capas[i] = utilidades.transform_cilindrical_cortes_conos(cortes=capa, descriptor=descriptor_pieza, inv=True)
        return capas

    def calcular_hardfacing_malla(self, area_elegida: np.ndarray, ancho_cordon: float=0, alto_cordon: float=0, 
                            cant_capas: int=1, tipo_pieza: int=0, descriptor_pieza: Tuple[float, float]=[1, 0], radio_clustering: float=0) -> List[List[np.ndarray]]:
        """
            Calcula los contornos necesarios para realizar hardfacing/surfacing sobre una/s área/s en particular, seleccionados sobre una malla.
            Áreas separadas por una distancia mayor al radio de clustering son consideradas como áreas separadas.
            El número de contornos obtenidos es al menos la cantidad ingresada.
            Para el caso de cilindros y conos se realiza una transformación de los puntos desde un sistema cartesiano a un sistema cilíndrico,
            y luego se realiza el cálculo de contornos para hardfacing/surfacing.
            Los contornos son obtenidos triangulando los puntos del área elegida, mediante Delaunay 2D, y luego extruyendo el área.
            Esa extrusión es cortada, obteniendo sus contornos.

            Parameters
            ----------
            area_elegida : np.ndarray
                área elegida para realizar hardfacing sobre una malla.
                Representada por un array de puntos, correspondientes a los vértices encontrados 
                en el área seleccionada de la malla.
            
            ancho_cordon : float, optional
                ancho del cordón de soldadura, by default 0
            
            alto_cordon : float, optional
                alto del cordón de soldadura, by default 0
            
            cant_capas : int, optional
                cantidad de capas que se quieren utilizar para el hardfacing, by default 1
            
            tipo_pieza : int, optional
                indicador de tipo de pieza.
                0=placa, 1=cilindro, 2=cono, by default 0
            
            descriptor_pieza : Tuple[float, float], optional
                lista de descriptores usada en los casos de cilindro y cono, correspondientes a [radio base, ángulo apertura], by default [1, 0]
            
            radio_clustering : float, optional
                radio utilizado para separar las distintas áreas elegidas según la distancia entre puntos, by default 0

            Returns
            -------
            List[List[np.ndarray]]
                lista donde cada elemento es una capa, y cada capa es una lista que contiene los contornos encontrados en forma de arrays.
        """

        # Hardfacing es muy similar a cortes de mallas, pero son distintos
        # Se usa STEPOVER=0 para forzar a usar el número de capas pedido
        # Si no, se calcularían las capas como en caso "normal" de cortes
        step_over = 0
        # CASO PLACA
        if tipo_pieza == 0:
            cortes = self.calcular_cortes_hardfacing_placa(area_elegida, ancho_cordon, alto_cordon, cant_capas, step_over, radio_clustering)
            return cortes
        # CASO CILINDROS
        if tipo_pieza == 1:
            cortes = self.calcular_cortes_hardfacing_cilindro(area_elegida, ancho_cordon, alto_cordon, cant_capas, step_over, descriptor_pieza, radio_clustering)
            return cortes
        # CASO CONOS
        if tipo_pieza == 2:
            cortes = self.calcular_cortes_hardfacing_cono(area_elegida, ancho_cordon, alto_cordon, cant_capas, step_over, descriptor_pieza, radio_clustering)
            return cortes

    def extruir_seleccion(self, puntos: np.ndarray, alto_cordon: float, cant_capas: int, radio_clustering: float) -> vedo.Mesh:
        """
            Calcula la extrusión del área elegida para hardfacing/surfacing.
            El área se obtiene triangulando los puntos ingresados, mediante Delaunay 2D.
            El área es luego extruida una altura dada por la altura del cordón de soldadura
            y la cantidad de capas que se quieren utilizar para el hardfacing/surfacing.
            En caso de tener más de un área, separadas por una distancia mayor al radio de clustering, 
            cada área es extruida por separado.

            Parameters
            ----------
            puntos : np.ndarray
                array de puntos que representa el área elegida para hacer hardfacing/surfacing, puntos corresponden 
                a los vértices encontrados en el área seleccionada de la malla.
            
            alto_cordon : float
                alto del cordón de soldadura.
            
            cant_capas : int
                cantidad de capas que se quieren utilizar para el hardfacing.
            
            radio_clustering : float
                radio utilizado para separar las distintas áreas elegidas según la distancia entre puntos.

            Returns
            -------
            vedo.Mesh
                la extrusión del área obtenida mediante tringulación de Delaunay 2D, representada mediante un Mesh de vedo.
        """

        areas = []
        puntos_elegidos = vedo.mesh.Mesh(vedo.Points(puntos))
        clstr = vedo.pointcloud.connectedPoints(puntos_elegidos, radio_clustering, 
                                                mode=0, regions=(), vrange=(0, 1), seeds=(), angle=0)
        
        for region in np.unique(clstr.pointdata["RegionLabels"]):
            area = clstr.clone().threshold("RegionLabels", above=region, below=region)
            area = vedo.pointcloud.delaunay2D(area,  mode='xy')
            area = area.extrude(alto_cordon*cant_capas)
            area.scale(s=0.99, absolute=False)
            areas.append(area)
        areas = vedo.mesh.merge(areas)
        return areas
    
    def calcular_cortes_hardfacing_placa(self, area_elegida: np.ndarray, ancho_cordon: float, alto_cordon: float, 
                                    cant_capas: int, step_over: float, radio_clustering: float) -> List[List[np.ndarray]]:
        """
            Calcula los contornos necesarios para realizar hardfacing/surfacing sobre una/s área/s en particular, seleccionados sobre una malla.
            Áreas separadas por una distancia mayor al radio de clustering son consideradas como áreas separadas.
            El número de contornos obtenidos es al menos la cantidad ingresada.
            Los contornos son obtenidos triangulando los puntos del área elegida, mediante Delaunay 2D, y luego extruyendo el área.
            Esa extrusión es cortada, obteniendo sus contornos.

            Parameters
            ----------
            area_elegida : np.ndarray
                área elegida para realizar hardfacing sobre una malla.
                Representada por un array de puntos, correspondientes a los vértices encontrados 
                en el área seleccionada de la malla.
            
            ancho_cordon : float
                ancho del cordón de soldadura.
            
            alto_cordon : float
                alto del cordón de soldadura.
            
            cant_capas : int
                cantidad de capas que se quieren utilizar para el hardfacing.
            
            step_over : float
                step-over entre cordones de soldadura.
            
            radio_clustering : float
                radio utilizado para separar las distintas áreas elegidas según la distancia entre puntos.

            Returns
            -------
            List[List[np.ndarray]]
                lista donde cada elemento es una capa, y cada capa es una lista que contiene los contornos encontrados en forma de arrays.
        """

        caja_hardfacing = self.extruir_seleccion(area_elegida, alto_cordon, cant_capas, radio_clustering)
        cortes = self.calcular_cortes_placa(caja_hardfacing.to_trimesh(), ancho_cordon, alto_cordon, step_over)
        return cortes

    def calcular_cortes_hardfacing_cilindro(self, area_elegida: np.ndarray, ancho_cordon: float, alto_cordon: float, 
                                        cant_capas: int, step_over: float, descriptor_pieza: Tuple[float, float], radio_clustering: float) -> List[List[np.ndarray]]:
        """
            Calcula los contornos necesarios para realizar hardfacing/surfacing sobre una/s área/s en particular, seleccionados sobre una malla.
            Áreas separadas por una distancia mayor al radio de clustering son consideradas como áreas separadas.
            El número de contornos obtenidos es al menos la cantidad ingresada.
            Para el caso de cilindros se realiza una transformación de los puntos desde un sistema cartesiano a un sistema cilíndrico,
            y luego se realiza el cálculo de contornos para hardfacing/surfacing considerandolo como una placa.
            Los contornos son obtenidos triangulando los puntos del área elegida, mediante Delaunay 2D, y luego extruyendo el área.
            Esa extrusión es cortada, obteniendo sus contornos.
            Los contornos son transformados a un sistema de coordenadas cartesianas antes de retornarlo.

            Parameters
            ----------
            area_elegida : np.ndarray
                área elegida para realizar hardfacing sobre una malla.
                Representada por un array de puntos, correspondientes a los vértices encontrados 
                en el área seleccionada de la malla.
            
            ancho_cordon : float
                ancho del cordón de soldadura.
            
            alto_cordon : float
                alto del cordón de soldadura.
            
            cant_capas : int
                cantidad de capas que se quieren utilizar para el hardfacing.
            
            descriptor_pieza : Tuple[float, float]
                lista de descriptores usada en los casos de cilindro y cono, correspondientes a [radio base, ángulo apertura].
                En el caso de cilindro solo es usado el radio.
            
            radio_clustering : float
                radio utilizado para separar las distintas áreas elegidas según la distancia entre puntos.

            Returns
            -------
            List[List[np.ndarray]]
                lista donde cada elemento es una capa, y cada capa es una lista que contiene los contornos encontrados en forma de arrays.
        """

        area_elegida_cilin = utilidades.transform_cilindrical(points=area_elegida, inv=False, radio=descriptor_pieza[0])
        cortes = self.calcular_cortes_hardfacing_placa(area_elegida_cilin, ancho_cordon, alto_cordon, cant_capas, step_over, radio_clustering)
        cortes = utilidades.transform_cilindrical_cortes(cortes=cortes, inv=True, radio=descriptor_pieza[0])
        return cortes

    def calcular_cortes_hardfacing_cono(self, area_elegida: np.ndarray, ancho_cordon: float, alto_cordon: float, 
                                    cant_capas: int, step_over: float, descriptor_pieza: Tuple[float, float], radio_clustering: float) -> List[List[np.ndarray]]:
        """
            Calcula los contornos necesarios para realizar hardfacing/surfacing sobre una/s área/s en particular, seleccionados sobre una malla.
            Áreas separadas por una distancia mayor al radio de clustering son consideradas como áreas separadas.
            El número de contornos obtenidos es al menos la cantidad ingresada.
            En el caso de conos es necesario realizar la transformación a coordenadas cilíndricas, y luego rotar la malla en el eje Y
            un ángulo igual al de apertura, luego se realiza el cálculo de contornos para hardfacing/surfacing considerandolo como una placa.
            Los contornos son obtenidos triangulando los puntos del área elegida, mediante Delaunay 2D, y luego extruyendo el área.
            Esa extrusión es cortada, obteniendo sus contornos.
            Los contornos son transformados a un sistema de coordenadas cartesianas antes de retornarlo.

            Parameters
            ----------
            area_elegida : np.ndarray
                área elegida para realizar hardfacing sobre una malla.
                Representada por un array de puntos, correspondientes a los vértices encontrados 
                en el área seleccionada de la malla.
            
            ancho_cordon : float
                ancho del cordón de soldadura.
            
            alto_cordon : float
                alto del cordón de soldadura.
            
            cant_capas : int
                cantidad de capas que se quieren utilizar para el hardfacing.
            
            descriptor_pieza : Tuple[float, float]
                lista de descriptores usada en los casos de cilindro y cono, correspondientes a [radio base, ángulo apertura].
                En el caso de cono tanto el radio como el ángulo de apertura son utilizados.
            
            radio_clustering : float
                radio utilizado para separar las distintas áreas elegidas según la distancia entre puntos.

            Returns
            -------
            List[List[np.ndarray]]
                lista donde cada elemento es una capa, y cada capa es una lista que contiene los contornos encontrados en forma de arrays.
        """

        # Radio depende del ángulo de apertura y posición en el eje del cono
        radio_cono = -1*(np.tan(np.deg2rad(descriptor_pieza[1]))*area_elegida[:, 0] - descriptor_pieza[0])
        area_elegida_cilin = utilidades.transform_cilindrical(points=area_elegida, inv=False, radio=radio_cono)
        # Necesario transformar a cilíndricas antes de rotación, por como se calcula cambio de radio
        r = Rotation.from_euler('y', -descriptor_pieza[1], degrees=True)
        area_elegida_cilin = r.apply(area_elegida_cilin)

        cortes = self.calcular_cortes_hardfacing_placa(area_elegida_cilin, ancho_cordon, alto_cordon, cant_capas, step_over, radio_clustering)

        # Se rota primera para revertir transformación
        r = Rotation.from_euler('y', descriptor_pieza[1], degrees=True)
        for i, capa in enumerate(cortes):
            for j, curva in enumerate(capa):
                cortes[i][j] = r.apply(curva)
        cortes = utilidades.transform_cilindrical_cortes_conos(cortes=cortes, inv=True, descriptor=descriptor_pieza)
        return cortes
