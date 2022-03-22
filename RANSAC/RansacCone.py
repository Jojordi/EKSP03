# -*- coding: utf-8 -*-
"""
Created on Wed Dec  2 01:23:51 2020

@author: Erick
"""

#%% RANSAC-3D
"""Import Libraries and Local Functions"""

import open3d as o3d
import numpy as np
import random
import timeit
from scipy.spatial.transform import Rotation


def calc_dist_to_line(point, position, orientation):
    """ Calculate the distance of a 3D point to a 3D line that passes through (xc, yc, zc) with direction
    (sx, sy, sz) """
    point = np.asarray(point)
    position = np.asarray(position)
    orientation = np.asarray(orientation)
    Dist = position - point
    D = np.cross(Dist,orientation)
    return (np.linalg.norm(D, axis=1))/(np.linalg.norm(orientation))

def calc_singlepointdist_to_line(point, position, orientation):
    """ Calculate the distance of a 3D point to a 3D line that passes through (xc, yc, zc) with direction
    (sx, sy, sz) """
    point = np.asarray(point)
    position = np.asarray(position)
    orientation = np.asarray(orientation)
    Dist = position - point
    D = np.cross(Dist,orientation)
    return (np.linalg.norm(D))/(np.linalg.norm(orientation))

def dist_pts3d(x,y):
    """ Calculate distance between two 3D points """
    x = np.asarray(x)
    x = x.T
    return np.sqrt((x[0]-y[0])**2 + (x[1]-y[1])**2 + (x[2]-y[2])**2)

def direction_vector(x,y):
    """ Calculate direction of vector """
    return (x[0]-y[0])/dist_pts3d(x,y) , (x[1]-y[1])/dist_pts3d(x,y) , (x[2]-y[2])/dist_pts3d(x,y)

def dist_point_to_cone(cone_args,point):
    """ Calculate the distance of single point to a cone """
    phi, posX, posY, posZ, oriX, oriY, oriZ = cone_args
    position = [posX, posY, posZ]
    orientation = [oriX, oriY, oriZ]
    
    Xr = calc_dist_to_line(point,position,orientation)
    # Xh_0 = list(project_point_to_line(point,orientation))
    Xh = np.sqrt((dist_pts3d(point,position))**2-Xr**2)
    
    dist = Xr*np.cos(phi) - (Xh)*np.sin(phi)   
    return abs(dist)

def dist_points_to_cone(cone_args,points):
    """ Calculate the sum of distance of multiple points to a cone """
    Distancias = dist_point_to_cone(cone_args,points)
    return sum(Distancias)**2

def project_point_to_line(point,orientation):
    """ Projects a point to a line with certain orientation """
    p = np.asarray(point)
    p = np.reshape(p,(-1,3))
    s = np.asarray(orientation)
    s = np.reshape(s,(-1,3))
    s = s.T
    projection = p@s/np.linalg.norm(s)*s.T
    return projection

def pick_points(pcd):
    print("")
    print(
        "1) Please pick at least three correspondences using [shift + left click]"
    )
    print("   Press [shift + right click] to undo point picking")
    print("2) After picking points, press 'Q' to close the window")
    vis = o3d.visualization.VisualizerWithEditing()
    vis.create_window()
    vis.add_geometry(pcd)
    vis.run()  # user picks points
    vis.destroy_window()
    print("")
    return vis.get_picked_points()

#%% Data Input and Pre-Processing
start_time = timeit.default_timer()
Check = 0
while Check == 0:    
    """Cones parallel to axis Z"""
    # pcd = o3d.io.read_point_cloud("STLs/Conos/Cone.pcd")
    # pcd = o3d.io.read_point_cloud("STLs/Conos/HalfCone.pcd")
    # pcd = o3d.io.read_point_cloud("STLs/Conos/QuarterCone.pcd")
    # pcd = o3d.io.read_point_cloud("STLs/Conos/Cone_Angle30_Outlier.pcd")
    # pcd = o3d.io.read_point_cloud("STLs/Conos/HalfCone_Angle30_Outlier.pcd")
    # pcd = o3d.io.read_point_cloud("STLs/Conos/QuarterCone_Angle30_Outlier.pcd")
    
    """Rotated Cones with an aperture angle of 30 degrees, rotated 45 deg w/r to axis X, then 45 deg w/r to axis Y"""
    # pcd = o3d.io.read_point_cloud("STLs/Conos/Cone_Angle30.pcd")
    # pcd = o3d.io.read_point_cloud("STLs/Conos/HalfCone_Angle30.pcd")
    # pcd = o3d.io.read_point_cloud("STLs/Conos/QuarterCone_Angle30.pcd")
    # pcd = o3d.io.read_point_cloud("STLs/Conos/Cone_Angle30_Outlier_Rotated.pcd")
    # pcd = o3d.io.read_point_cloud("STLs/Conos/Cone_Angle30_Outlier_Rotated_NoRecto.pcd")
    # pcd = o3d.io.read_point_cloud("STLs/Conos/HalfCone_Angle30_Outlier_Rotated.pcd")
    pcd = o3d.io.read_point_cloud("STLs/Conos/QuarterCone_Angle30_Outlier_Rotated.pcd")
    
    """Centrado de PCD en origen"""
    pcd = pcd.translate((0,0,0), relative=False)
    
    """Carga de puntos de la pcd como un array."""
    pcd_array = np.asarray(pcd.points)
    pcd_normals = np.asarray(pcd.normals)
    # pcd_array = np.load('pcd_array.npy')
    axis_1 = max(pcd_array[:,0])-min(pcd_array[:,0])
    axis_2 = max(pcd_array[:,1])-min(pcd_array[:,1])
    axis_3 = max(pcd_array[:,2])-min(pcd_array[:,2])
    max_axis = axis_1, axis_2, axis_3
    max_dim = max(max_axis)
    
    """Selección de los puntos con sus respectivas normales"""
    Points_With_Normals = np.array(pcd.points)[:,0],np.array(pcd.points)[:,1],np.array(pcd.points)[:,2],np.array(pcd.normals)[:,0],np.array(pcd.normals)[:,1],np.array(pcd.normals)[:,2]
    Points_With_Normals = np.array(Points_With_Normals).T
    List_PointsWithNormals = list(Points_With_Normals)
    
    """Verificar nube de puntos cargada, mantener comentado para uso automatico"""
    # coord_frame = o3d.geometry.TriangleMesh.create_coordinate_frame(size=60, origin=[0, 0, 0])
    # o3d.visualization.draw_geometries([coord_frame, pcd])
           
    # f=open('data_quarter_cylinder.txt','w')
    
    #%% Section for iteration of RANSAC
    
    Big_Iterations = 1
    for j in range(Big_Iterations):
        NumIter = 50
        Thresh = 0.004*max_dim
        Score = 0
        Best_Sample = [0, 0, 0, 0, 0, 0, 0]
        Best_Sample_Position = 0
        Data_Iterations = list(range(NumIter))
        Best_Comparison = 0
        
        for iteration in range(NumIter):    
            Local_Score = 0
            points = np.asarray(random.sample(List_PointsWithNormals,3))
            
            Point1 = np.array([points[0][0],points[0][1],points[0][2]])
            Point2 = np.array([points[1][0],points[1][1],points[1][2]])
            Point3 = np.array([points[2][0],points[2][1],points[2][2]])
            N1 = np.array([points[0][3],points[0][4],points[0][5]])
            N2 = np.array([points[1][3],points[1][4],points[1][5]])
            N3 = np.array([points[2][3],points[2][4],points[2][5]])
         
            try:
    
                a = np.array([list(N1),list(N2),list(N3)])
                b = np.array([np.dot(Point1,N1),np.dot(Point2,N2),np.dot(Point3,N3)])
                x1 = np.linalg.solve(a,b)
                q = (N1[0]*(Point1[1]-Point2[1])+N1[1]*(Point2[0]-Point1[0]))/(N1[0]*N2[1]-N1[1]*N2[0])
                x2 = np.array([Point2[0]+q*N2[0], Point2[1]+q*N2[1], Point2[2]+q*N2[2]]) 
                x = direction_vector(x1,x2)
                Angles = np.array([np.arcsin(calc_singlepointdist_to_line(Point1,x1,x)/dist_pts3d(x1,Point1)),np.arcsin(calc_singlepointdist_to_line(Point2,x1,x)/dist_pts3d(x1,Point2)),np.arcsin(calc_singlepointdist_to_line(Point3,x1,x)/dist_pts3d(x1,Point3))])
                Apex = x1
                Angle = Angles.mean()
                Direction = x
                cone_args = [Angle, Apex[0], Apex[1], Apex[2], Direction[0], Direction[1], Direction[2]]
                
                """Comparison and scoring of points"""
                comparison = dist_point_to_cone(cone_args,pcd_array) < Thresh
                Local_Score = comparison.sum()
                RANSAC_Score = Local_Score
                Data_Iterations[iteration] = RANSAC_Score, cone_args
                
                if RANSAC_Score > Score:
                    Score = RANSAC_Score
                    Best_Sample = cone_args
                    Best_Sample_Position = iteration+1
                    Best_Comparison = comparison
                        
                    print("Iteration: {} (Run {} of {})".format(iteration+1,j+1,Big_Iterations))
                    print("Current Aperture Angle (in degrees):", abs((Best_Sample[0]*180/np.pi)%180))
                    print("Current Apex Position: X: {}, Y:{}, Z:{}".format(Best_Sample[1],Best_Sample[2],Best_Sample[3]))
                    print("Current Orientation: X: {}, Y:{}, Z:{}".format(Best_Sample[4],Best_Sample[5],Best_Sample[6]))
                    print("RANSAC Score: {}, Score: {} (Found in Iteration {})".format(RANSAC_Score,Score,Best_Sample_Position))
                    print("----------")
                    
                else:
                    print("Iteration: {} (Run {} of {})".format(iteration+1,j+1,Big_Iterations))
                    print("Current Aperture Angle (in degrees):", abs((Best_Sample[0]*180/np.pi)%180))
                    print("RANSAC Score: {}, Score: {} (Found in Iteration {})".format(RANSAC_Score,Score,Best_Sample_Position))
                    print("----------")
            except:
                continue
                
        print('Aperture Angle (in degrees): ', abs((Best_Sample[0]*180/np.pi)%180))
        print("Apex Position: X: {}, Y:{}, Z:{}".format(Best_Sample[1],Best_Sample[2],Best_Sample[3]))
        print("Orientation: X: {}, Y:{}, Z:{}".format(Best_Sample[4],Best_Sample[5],Best_Sample[6]))
    
        
        # f.write(str(Best_Sample[0])+','+str(Best_Sample[4])+','+str(Best_Sample[5])+','+str(Best_Sample[6])+','+str(Best_Sample_Position)+'\n')
    
    # f.close()
        if (Score/len(Best_Comparison)) > 0.5:
            Check = 1
    
Best_Comparison_Positions = np.asarray(np.where(Best_Comparison == True)[0])
pcd.paint_uniform_color([1,0,0])
Inliers = list(Best_Comparison_Positions)
np.asarray(pcd.colors)[Inliers] = [0.5,0.5,0.5]

coord_frame = o3d.geometry.TriangleMesh.create_coordinate_frame(size=60, origin=[0, 0, 0])

"""Matrices de rotacion"""
Vector_Orientacion = [Best_Sample[4],Best_Sample[5],Best_Sample[6]]
Rotate = Rotation.align_vectors([Vector_Orientacion], [[0,0,1]]) # Para rotar primitiva a orientacion de pcd
Inv_Rotate = Rotation.align_vectors([[0,0,1]],[Vector_Orientacion]) # Para rotar pcd a orientación [0,0,1]

"""Parametros para la generación de la primitiva del cono"""
Apex_Position = [Best_Sample[1],Best_Sample[2],Best_Sample[3]]
Max_Generatriz = max(dist_pts3d(Apex_Position,pcd_array.T))
Cone_Height = Max_Generatriz*np.cos(Best_Sample[0])
Cone_Radius = abs(np.sin(Best_Sample[0])*Max_Generatriz)
RANSAC_Cone = RANSAC_Cone = o3d.geometry.TriangleMesh.create_cone(radius=Cone_Radius,height=Cone_Height,resolution=100)
RANSAC_Cone.paint_uniform_color((0.75,0.75,0.75))

PrimitiveCone_Apex = [0,0,Cone_Height]
PrimitiveCone_Apex = Rotate[0].apply(PrimitiveCone_Apex)

"""Rotation of primitive and alignment with PCD"""
pcd_array = Inv_Rotate[0].apply(pcd_array) #PCD alineada con [0,0,1]
Desfase_Altura = abs(min(pcd_array[:,2])) 
pcd_array[:,2] = pcd_array[:,2]+Desfase_Altura #Se corrige de manera que PCD tenga su base en plano XY
pcd.points = o3d.utility.Vector3dVector(pcd_array)

"""Traslation of PCD for alignment with Primitive figure"""
Apex_Position = np.asarray(Apex_Position)
Apex_Position = Inv_Rotate[0].apply(Apex_Position)
pcd_center = pcd.get_center()
pcd = pcd.translate((-Apex_Position[0],-Apex_Position[1],pcd_center[2]),relative=False)

# RANSAC_Cone_Vertex = np.asarray(RANSAC_Cone.vertices)
# RANSAC_Cone_Vertex = Rotate[0].apply(RANSAC_Cone_Vertex) #Se orienta primitiva a dirección original PCD
# RANSAC_Cone.vertices = o3d.utility.Vector3dVector(RANSAC_Cone_Vertex)
# pcd_array = Rotate[0].apply(pcd_array) #Se devuelve PCD a su orientación original
# pcd.points = o3d.utility.Vector3dVector(pcd_array)

stop_time = timeit.default_timer()

WireFrame = o3d.geometry.LineSet.create_from_triangle_mesh(RANSAC_Cone)
o3d.visualization.draw_geometries([coord_frame, pcd])
o3d.visualization.draw_geometries([coord_frame, WireFrame, pcd])



print('Cone Height: {}'.format(Cone_Height))


print('Time: ', stop_time - start_time)  