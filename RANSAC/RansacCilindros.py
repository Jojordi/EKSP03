# -*- coding: utf-8 -*-
"""
Created on Mon Aug 31 17:28:38 2020

@author: Erick
"""

#%% RANSAC-3D
"""Import Libraries and Local Functions"""

import open3d as o3d
import numpy as np
import random
import timeit
from numpy import mean
from numpy import cov
from numpy.linalg import eig
from scipy.spatial.transform import Rotation
from skspatial.objects import Plane
from skspatial.objects import Line


def calc_dist_to_line(point, position, orientation):
    """ Calculate the distance of a 3D point to a 3D line that passes through (xc, yc, zc) with direction
    (sx, sy, sz) """
    Xd = position[0] - point[0]
    Yd = position[1] - point[1]
    Zd = position[2] - point[2]
    D1 = Yd * orientation[2] - Zd * orientation[1]
    D2 = Xd * orientation[2] - Zd * orientation[0] 
    D3 = Xd * orientation[1] - Yd * orientation[0] 
    return (np.sqrt(D1**2 + D2**2 + D3**2))/(np.sqrt(orientation[0]**2 + orientation[1]**2 + orientation[2]**2))

#%% Data Input and Pre-Processing

## PROBLEM FOR THESE OPTIONS: Cylinder including top and bottom faces, not just mantle
# pcd = o3d.io.read_point_cloud("STLs/Cilindro1_R40_L100_X45Y45_Manto.pcd")
# pcd = o3d.io.read_point_cloud("STLs/Cilindro1Mitad_R40_L100_X45Y45Z45_Manto.pcd")
# pcd = o3d.io.read_point_cloud("STLs/Cilindro3_R30_L140.pcd")
# pcd = o3d.io.read_point_cloud("STLs/Cilindro3_R30_L140_X45Y45Z45.pcd")


# pcd = o3d.io.read_point_cloud("STLs/Cylinder_Manto.pcd") #Radius 20
# pcd = o3d.io.read_point_cloud("STLs/Mantos/cilindro-abrasion2.pcd") #Radius 2.06
# pcd = o3d.io.read_point_cloud("STLs/Mantos/cilindro-abrasion3.pcd")
# pcd = o3d.io.read_point_cloud("STLs/Mantos/cilindro-abrasion4.pcd")
# pcd = o3d.io.read_point_cloud("STLs/Mantos/cilindro-pitting1-profundo.pcd")
# pcd = o3d.io.read_point_cloud("STLs/Mantos/cilindro-pitting1-profundo2.pcd")
# pcd = o3d.io.read_point_cloud("STLs/Mantos/cilindro-pitting2.pcd")

"""Cylinder mantles scaled with respect to previous options by a 10x factor. 
Also added options not parallel to X,Y,Z axis. Radius for options here is 20.6"""
# pcd = o3d.io.read_point_cloud("STLs/Mantos/cilindro-abrasion2_10x.pcd")    
# pcd = o3d.io.read_point_cloud("STLs/Mantos/cilindro-abrasion3_10x.pcd")
# pcd = o3d.io.read_point_cloud("STLs/Mantos/cilindro-abrasion3_10x_X45Z45.pcd")
# pcd = o3d.io.read_point_cloud("STLs/Mantos/cilindro-abrasion4_10x.pcd")
# pcd = o3d.io.read_point_cloud("STLs/Mantos/cilindro-abrasion4_10x_X45Z45.pcd")
# pcd = o3d.io.read_point_cloud("STLs/Mantos/Pitting_10x_X45_Crop.pcd")
pcd = o3d.io.read_point_cloud("STLs/Mantos/cilindro-pitting2_10x.pcd")
# pcd = o3d.io.read_point_cloud("STLs/Mantos/cilindro-pitting3_segment.pcd")
# pcd = o3d.io.read_point_cloud("STLs/Mantos/cilindro-pitting2_10x_inliers.pcd")
 
"""Cylinders sections with radius >> L, under evaluation""" 
# pcd = o3d.io.read_point_cloud("STLs/Mantos/cilindro_1m_abrasion v1_cut1_X45Y45.pcd")
# pcd = o3d.io.read_point_cloud("STLs/Mantos/cilindro_1m_abrasion v1_cut1_X45Y45_onlyinlier.pcd")
# pcd = o3d.io.read_point_cloud("STLs/Mantos/cilindro_1m_abrasion v1_cut1_X45Y45_onlybottomoutlier.pcd")
# pcd = o3d.io.read_point_cloud("STLs/Mantos/cilindro_1m_abrasion v1_cut1_X45Y45_onlyoutlier.pcd")
# pcd = o3d.io.read_point_cloud("STLs/Mantos/cilindro_1m_abrasion3 v1_cut1.pcd")
# pcd = o3d.io.read_point_cloud("STLs/Mantos/cilindro_1m_abrasion3 v1_cut1_X45.pcd")
    
# pcd = o3d.io.read_point_cloud("STLs/Mantos/cilindro_1m_abrasion v1_halfmantle.pcd")
# pcd = o3d.io.read_point_cloud("STLs/Mantos/cilindro_1m_abrasion v1_halfmantle_X45Y45.pcd")
# pcd = o3d.io.read_point_cloud("STLs/Mantos/cilindro_1m_abrasion v1_quarter.pcd")
# pcd = o3d.io.read_point_cloud("STLs/Mantos/cilindro_1m_abrasion v1_quarter_X45Y45.pcd")

pcd = pcd.translate((0,0,0), relative=False)

start_time = timeit.default_timer()
pcd_array = np.asarray(pcd.points)
# pcd_array = np.load('pcd_array.npy')
pcd_list = list(pcd_array)
axis_1 = max(pcd_array[:,0])-min(pcd_array[:,0])
axis_2 = max(pcd_array[:,1])-min(pcd_array[:,1])
axis_3 = max(pcd_array[:,2])-min(pcd_array[:,2])
max_axis = axis_1, axis_2, axis_3
max_dim = max(max_axis)
values, vectors = eig(cov((pcd_array - mean(pcd_array.T, axis=1)).T))

"""Selección de los puntos con sus respectivas normales"""
Points_With_Normals = np.array(pcd.points)[:,0],np.array(pcd.points)[:,1],np.array(pcd.points)[:,2],np.array(pcd.normals)[:,0],np.array(pcd.normals)[:,1],np.array(pcd.normals)[:,2]
Points_With_Normals = np.array(Points_With_Normals).T
List_PointsWithNormals = list(Points_With_Normals)

# f=open('data_quarter_cylinder.txt','w')

#%% Section for iteration of RANSAC

Big_Iterations = 1

for j in range(Big_Iterations):
    NumIter = 250
    Thresh = 0.01 # Percentage, use with radius
    Sample_Points_RANSAC = max(int(len(pcd_list)*0.00005),10)
    Score = 0
    Best_Sample = [0, 0, 0, 0, 0, 0, 0, 0]
    Best_Sample_Position = 0
    Data_Iterations = list(range(NumIter))
    Best_Comparison = 0
    
    """A sample of a % of the total points is used for comparison of inliers in order to 
    reduce computing time"""
    Big_Sample = pcd_array
    Big_Sample = Big_Sample.T
    
    Big_Sample_Score = len(Big_Sample.T)
    
    for iteration in range(NumIter):  
        """Se eligen 3 puntos al azar, se extraen sus posiciones XYZ y sus normales"""
        points = np.asarray(random.sample(List_PointsWithNormals,3))
        
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
            R1 = calc_dist_to_line(Point1,line.point,line.direction)
            R2 = calc_dist_to_line(Point2,line.point,line.direction)
            R3 = calc_dist_to_line(Point3,line.point,line.direction)
            R = (R1+R2+R3)/3

            """Se descartan soluciones que generen un radio más grande que toda la PCD"""
            if R > max_dim:
                continue

            radius = R
            position_optimized = line.point
            orientation_optimized = line.direction
                
            """Threshold for comparison"""
            UmDist = radius*Thresh
            lowerRadius = radius-UmDist
            upperRadius = radius+UmDist
            comp_R = calc_dist_to_line(Big_Sample,position_optimized, orientation_optimized)
            comparison = (comp_R > lowerRadius) & (comp_R < upperRadius)
            Local_Score = comparison.sum()
            RANSAC_Score = Local_Score
            Data_Iterations[iteration] = [radius,line.point,line.direction], RANSAC_Score
            
            if RANSAC_Score > Score and RANSAC_Score < Big_Sample_Score:
                Score = RANSAC_Score
                Best_Sample = radius, position_optimized[0], position_optimized[1], position_optimized[2], orientation_optimized[0], orientation_optimized[1], orientation_optimized[2]
                Best_Sample_Position = iteration+1
                Best_Comparison = comparison
                print("Iteration: {} (Run {} of {})".format(iteration+1,j+1,Big_Iterations))
                print("Current Radius:", Best_Sample[0])
                print("Current Position: X: {}, Y:{}, Z:{}".format(Best_Sample[1],Best_Sample[2],Best_Sample[3]))
                print("Current Orientation: X: {}, Y:{}, Z:{}".format(Best_Sample[4],Best_Sample[5],Best_Sample[6]))
                # print("Current Length:", Best_Sample[7])
                print("RANSAC Score: {}, Score: {} (Found in Iteration {})".format(RANSAC_Score,Score,Best_Sample_Position))
                print("----------")
            else:
                print("Iteration: {} (Run {} of {})".format(iteration+1,j+1,Big_Iterations))
                print("Current Radius:", Best_Sample[0])
                print("RANSAC Score: {}, Score: {} (Found in Iteration {})".format(RANSAC_Score,Score,Best_Sample_Position))
                print("----------")
        except:
            continue
    
    # f.write(str(Best_Sample[0])+','+str(Best_Sample[4])+','+str(Best_Sample[5])+','+str(Best_Sample[6])+','+str(Best_Sample_Position)+'\n')

# f.close()

stop_time = timeit.default_timer()

print('Time: ', stop_time - start_time)  
print('Radius: ', Best_Sample[0])
print("Orientation: X: {}, Y:{}, Z:{}".format(Best_Sample[4],Best_Sample[5],Best_Sample[6]))

"""Parámetros para construcción de primitiva de cilindro"""
Cylinder_Height = Best_Sample[0]/10
Cylinder_Radius = Best_Sample[0]
Centroid = [Best_Sample[1],Best_Sample[2],Best_Sample[3]]

"""Pintado de todos los puntos como rojos, y posterior pintado de los inliers como plomos"""
Best_Comparison_Positions = np.asarray(np.where(Best_Comparison == True)[0])
pcd.paint_uniform_color([1,0,0])
Inliers = list(Best_Comparison_Positions)
np.asarray(pcd.colors)[Inliers] = [0.5,0.5,0.5]

"""Traslación de la PCD y generación de matrices de rotación"""
pcd = pcd.translate((-Best_Sample[1],-Best_Sample[2],-Best_Sample[3]), relative=False)

Vector_Orientacion = [Best_Sample[4],Best_Sample[5],Best_Sample[6]]
Rotate = Rotation.align_vectors([Vector_Orientacion], [[0,0,1]])
Inv_Rotate = Rotation.align_vectors([[0,0,1]],[Vector_Orientacion])

coord_frame = o3d.geometry.TriangleMesh.create_coordinate_frame(size=3, origin=[0, 0, 0])

"""For rotation of pcd and alignment with Z axis for calculation of whole PCD size"""
pcd_points = np.asarray(pcd.points)
pcd_points = Inv_Rotate[0].apply(pcd_points)
Centroid = Inv_Rotate[0].apply(Centroid)
Cylinder_Height = max(pcd_points[:,2])-min(pcd_points[:,2])
pcd = pcd.translate((0,0,-Centroid[2]), relative=False)
pcd_points = Rotate[0].apply(pcd_points)
pcd.points = o3d.utility.Vector3dVector(pcd_points)

RANSAC_Cylinder = o3d.geometry.TriangleMesh.create_cylinder(radius=Cylinder_Radius,height=Cylinder_Height,resolution=100)
RANSAC_Cylinder.paint_uniform_color((0.75,0.75,0.75))

"""Rotation of primitive and alignment with PCD"""
RANSAC_Cylinder_Vertex = np.asarray(RANSAC_Cylinder.vertices)
RANSAC_Cylinder_Vertex = Rotate[0].apply(RANSAC_Cylinder_Vertex)
RANSAC_Cylinder.vertices = o3d.utility.Vector3dVector(RANSAC_Cylinder_Vertex)
WireFrame = o3d.geometry.LineSet.create_from_triangle_mesh(RANSAC_Cylinder)
o3d.visualization.draw_geometries([coord_frame, WireFrame, pcd])






