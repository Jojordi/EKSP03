#PRUEBA PARA CASO eje
import trimesh
import open3d as o3d
import numpy as np
import math
from scipy.spatial.transform import Rotation as R
import matplotlib.pyplot as plt
import copy
import freeformpathplanning as fp

# datos soldadura
# --------------
#Estos valores serán calculados según literatura, sin embargo para poder ir desarrollando las funciones se han dejado para manipular
ampere= 100
[h,w]=fp.beamgeoemetry(100,0.2)
print(h,w)
o =0.738  # Cuociente entre distancia entre cordones y ancho de cordón de soldadura
v=0.05 #tamaño del voxel
d=w*o #Distancia entre cordones
theta= np.pi/(1) #Ángulo del raster
vector=(np.cos(theta),np.sin(theta),0) #Vector que indica la dirección del raster
vector2=(np.cos(theta+np.pi/2),np.sin(theta+np.pi/2),0) #Vector que indica la dirección sugerida para recorrer el raster
# Lectura de archivo
# --------------
originalpcd = o3d.io.read_point_cloud("D:\Stuff\Tareas\8-Año 8\Memoria\Archivos\Modelos fallas\eje_original.pcd") #dirección del archivo
defectpcd = o3d.io.read_point_cloud("D:\Stuff\Tareas\8-Año 8\Memoria\Archivos\Modelos fallas\eje_falla.pcd") #dirección del archivo


axis = o3d.geometry.TriangleMesh.create_coordinate_frame()  # se crea eje coordenado para referencia
axis.scale(10, (0, 0, 0)) #se escala el eje
# Pre procesamiento de la nube
# --------------
pcd1 = originalpcd.voxel_down_sample(voxel_size=v)
pcd2 = defectpcd.voxel_down_sample(voxel_size=v)
R = pcd1.get_rotation_matrix_from_xyz((np.pi, 0, 0))
R2 = pcd2.get_rotation_matrix_from_xyz((np.pi, 0, 0))
pcd1.rotate(R)
pcd2.rotate(R2)

pcd1.paint_uniform_color((0.5,0.5,1))
pcd2.paint_uniform_color((0.5,0.5,1))
pcd1.scale(10, (0, 0, 0))
pcd2.scale(10, (0, 0, 0))
pcd1.translate((0,0,50))
pcd2.translate((100,-6,27))
o3d.visualization.draw_geometries([axis,pcd2])
pcd2.translate((-100,0,0))

diameter = np.linalg.norm(np.asarray(pcd1.get_max_bound()) - np.asarray(pcd1.get_min_bound()))
camera = np.asarray([0,0,1]) * diameter
radius = diameter * 100
_, pt_map = pcd2.hidden_point_removal(camera, radius)
pcd2= pcd2.select_by_index(pt_map)

defect=fp.deleteintersect(pcd2,pcd1,d)
defectminz= np.min(np.asarray(defect.points)[:,2])
originalmaxz=np.max(np.asarray(pcd1.points)[:,2])
n=int(np.ceil((originalmaxz-defectminz)/h)) #Determinación del número de capas
layers=fp.color(fp.offset3d(defect,h,11))
pcd2.translate((100,0,0))
bbox = pcd1.get_axis_aligned_bounding_box()
o3d.visualization.draw_geometries([axis,pcd2,defect])
multi=fp.addpoints(fp.multioffset3d(pcd1,h,2,True,True,True,True,True,True))
multi=fp.addpoints([pcd1,multi])
allpath=[]
for i in layers:
    i=fp.deleteintersect(i,multi,d).crop(bbox)
    if i.has_points()==True:
        slice=fp.preslice01(i,d,vector,voxel_size=v)
        path=fp.completepath01(slice,vector2,w)
        allpath.append(fp.addpoints(path))
finalpath=fp.addsafepoints(allpath,h,d)
layersvis=fp.deleteintersect(fp.addpoints(layers).crop(bbox),multi,d)
pcd1.translate((-100,0,0))
multi.translate((-200,0,0))
o3d.visualization.draw_geometries([axis,pcd2,defect,layersvis,pcd1,multi])
o3d.visualization.draw_geometries([layersvis])
fp.animate(finalpath,t=100)
fp.pathvis(finalpath)
finalpath=fp.addpoints(finalpath)
finalpath.translate((1100,-100,200))
fp.dtpspoints([finalpath],name='eje2')