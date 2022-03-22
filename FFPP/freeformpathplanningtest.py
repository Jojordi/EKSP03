import open3d as o3d
import numpy as np
import math
from scipy.spatial.transform import Rotation as R
import matplotlib.pyplot as plt
import copy
import freeformpathplanning as fp

# Parámetros iniciales--------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------

ampere= 100 #Valor del ampearaje a utilizar
s=0.2 #Valor de la velocidad de la herramienta
[h,w]=fp.beamgeoemetry(ampere,s) #Calcula la geometría del cordón
c =0.738  # Cuociente entre distancia entre cordones y ancho de cordón de soldadura
v=0.05 #tamaño del voxel
d=w*c #Distancia entre cordones
theta= np.pi/(2) #Ángulo de la dirección del ráster
vector=(np.cos(theta),np.sin(theta),0) #Vector que indica la dirección del raster
vector2=(np.cos(theta+np.pi/2),np.sin(theta+np.pi/2),0) #Vector que indica la dirección sugerida para recorrer con zigzag
clockwise=False #Indica si se desea el recorrido espiral en sentido horario o antihorario

# Lectura de archivo----------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------------
#En esta sección se cargan los archivos, puede o no contener el archivo original
defectpcd = o3d.io.read_point_cloud("escribir dirección aquí") #dirección del archivo PCD que contiene el defecto
#originalpcd = o3d.io.read_point_cloud("dirección aquí") #dirección del archivo PCD original

axis = o3d.geometry.TriangleMesh.create_coordinate_frame()  # se crea eje coordenado para referencia
axis.scale(15, (0, 0, 0)) #se escala el eje para archivos creados en CloudCompare

# Pre procesamiento de la nube------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------
pcd1 = defectpcd.voxel_down_sample(voxel_size=v) #Reducción de puntos para la nube del defecto
#pcd2 = originalpcd.voxel_down_sample(voxel_size=v) #Reducción de puntos para la nube original
#R = originalpcd.get_rotation_matrix_from_xyz((np.pi/2, 0, 0)) #Matriz de rotación para orientar la nube de puntos en caso de ser necesario
#pcd1.rotate(R) #Rotación
#pcd2.rotate(R) #Rotación
pcd1.scale(10, (0, 0, 0)) #Escalamiento para nubes creadas en CloudCompare
#pcd2.scale(10, (0, 0, 0)) #Escalamiento para nubes creadas en CloudCompare
pcd1.translate((0,0,50)) #Traslación para ubicar la nube en el lugar deseado
#pcd2.translate((0,0,50)) #Traslación para ubicar la nube en el lugar deseado

#Aislación de la falla caso con PCD original y cálculo de n número de capas
#-------------------------------------------
# defect=fp.deleteintersect(pcd2,pcd1,2) #Resta entre las nubes
# defectminz= np.min(np.asarray(pcd1.points)[:,2]) #Obtención del punto mínimo en Z
# originalmaxz=np.max(np.asarray(pcd2.points)[:,2]) #Obtención del punto máximo en Z
# n=int(np.ceil((originalmaxz-defectminz)/h)  #Determinación del número de capas

#Aislación de la falla caso sin PCD original y cálculo de n número de capas
#-------------------------------------------
defectminz= np.min(np.asarray(pcd1.points)[:,2]) #Obtención del punto mínimo en Z
originalmaxz=np.max(np.asarray(pcd1.points)[:,2]) #Obtención del punto máximo en Z
n=int(np.ceil((originalmaxz-defectminz)/h)) #Determinación del número de capas
pl = fp.plane((0,0, originalmaxz), 150, 1) #Generación de plano alineado con la capa superior
defect = fp.deleteintersect(pcd1, pl, 2) #Eliminación e puntos intersecados con el plano generado

#Generación de capas----------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------------------
layers=fp.offset3d(defect,h,n) #Generación de capas
layersvis=fp.addpoints(layers) #Unión d ecapas para permitir su visualización
bbox = defect.get_axis_aligned_bounding_box() #Bounding box que encierra el defecto
croplayer=layersvis.crop(bbox) #Corte de capas según la bounding del defecto

#Visualización de capas y defecto---------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------------
o3d.visualization.draw_geometries([axis,defect]) #Visualización del defecto aislado
# o3d.visualization.draw_geometries([axis,croplayer]) #Visualización de las capas generadas

#Generación de trayectorias---------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------------
#En esta sección se debe elegir el tipo de recorrido
allpath=[]

#Generación de trayectoria para caso zigzag
#------------------------------------------
for i in layers:
    i=i.crop(bbox) #Elimina los puntos excedentes de la capa
    if i.has_points()==True:
        slice=fp.preslice01(i,d,vector,voxel_size=v) #Genera la subdivisión de nubes para facilitar el recorrido
        if slice!=[]:
            path=fp.completepath01(slice,vector2,w) #Genera el recorrido de las subnubes
            allpath.append(fp.addpoints(fp.addsafepoints(path,h,d))) #Une los caminos y añade puntos de levantamiento de herramienta para las subnubes y el código de color
finalpath=fp.addpoints(fp.addsafepoints(allpath,h,d))  #Une los caminos y añade puntos de levantamiento de herramienta para las capas y el código de color


#Generación de trayectoria para caso espiral
#-------------------------------------------
# for i in layers:
#     i=i.crop(bbox) #Elimina los puntos excedentes de la capa
#     if i.has_points()==True:
#         slice=fp.preslice02(i,d,voxel_size=v,clockwise=clockwise) #Genera la subdivisión de nubes para facilitar el recorrido
#         if slice!=[]:
#             path=fp.completepath02(slice,w,clockwise=clockwise) #Genera el recorrido de las subnubes
#             allpath.append(fp.addpoints(fp.addsafepoints(path,h,d))) #Une los caminos y añade puntos de levantamiento de herramienta para las subnubes y el código de color
# finalpath=fp.addpoints(fp.addsafepoints(allpath,h,d)) #Une los caminos y añade puntos de levantamiento de herramienta para las capas y el código de color


#Visualización y generación de código-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------------
o3d.visualization.draw_geometries([axis,finalpath]) #Visualización en Open3D
fp.animate([finalpath],t=100) #Animación con matplotlib
fp.pathvis([finalpath]) #Gráfico en matplotlib
finalpath.translate((250,900,250)) #Traslación hasta el punto de trabajo en DTPS
fp.dtpspoints([finalpath],name='nombre',s=s,ampere=ampere) #Generación de archivo CSR