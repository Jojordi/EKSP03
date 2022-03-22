import trimesh as tm
import open3d as o3d
import numpy as np
import math
from scipy.spatial.transform import Rotation as R
import matplotlib.pyplot as plt
import copy
import freeformpathplanning as fp

#Parámetros
#Estos valores serán calculados según literatura, sin embargo para poder ir desarrollando las funciones se han dejado para manipular
w =5.2  # Ancho cordón soldadura
h= 2.4  # Alto cordón soldadura
o =0.738  # Cuociente entre distancia entre cordones y ancho de cordón de soldadura
v=0.05 #tamaño del voxel
d=w*o #Distancia entre cordones
theta= np.pi/(-2) #Ángulo del raster
vector=(np.cos(theta),np.sin(theta),0) #Vector que indica la dirección del raster
vector2=(np.cos(theta+np.pi/2),np.sin(theta+np.pi/2),0) #Vector que indica la dirección sugerida para recorrer el raster

#Apertura de archivo
pcd = o3d.io.read_point_cloud("D:\Stuff\Tareas\8-Año 8\Memoria\Archivos\Modelos fallas\eje_original.pcd") #dirección del archivo
pcd1 =pcd.voxel_down_sample(voxel_size=v)
pcd1.scale(10, (0, 0, 0)) #se escala la nube
R = pcd1.get_rotation_matrix_from_xyz((0,np.pi/2, 0))
pcd1.rotate(R)
pcd1.translate((0,0,-100))
pcd1.paint_uniform_color((0.5,0.5,1))
axis = o3d.geometry.TriangleMesh.create_coordinate_frame()  # se crea eje coordenado para referencia
axis.scale(10, (0, 0, 0)) #se escala el eje
o3d.visualization.draw_geometries([axis,pcd1])
#Offset
n=5
layers=fp.offset3d(pcd1,h,2)
layersvis=fp.addpoints(fp.pcdlistvis(layers,100,(0,-1,0))).translate((300,100,0))
layer1=fp.normtrans(pcd1,h)
layer2=fp.normtrans(pcd1,h,[0,1,0])
layer3=fp.normtrans(pcd1,h,[0,-1,0])
layer4=fp.normtrans(pcd1,h,[0,0,-1])
add=fp.addpoints([layer1,layer2,layer3,layer4]).translate((300,0,0))

layer2.translate((0,100,0))
layer3.translate((0,200,0))
layer4.translate((0,300,0))
#visualización
pcd1.translate((-300,0,0))
layers=fp.addpoints((fp.multioffset3d(pcd1,h,3,py=True,ny=True,nz=True))).translate((1000,0,0))

o3d.visualization.draw_geometries([axis,pcd1,layer1,layer2,layer3,layer4,add,layers])