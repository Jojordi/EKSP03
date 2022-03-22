# -*- coding: utf-8 -*-
"""
Created on Wed Dec  2 01:23:51 2020

@author: Erick
"""

#%% RANSAC-3D
### Import Libraries and Local Functions

import open3d as o3d
import numpy as np
import random
import timeit
import copy
# import matplotlib.pyplot as plt
from scipy import optimize as opt
from numpy import mean
from numpy import cov
from numpy.linalg import eig
from scipy.spatial.transform import Rotation
# from scipy.linalg import norm
# from mpl_toolkits.mplot3d import Axes3D


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

def dist_pts3d(x,y):
    """ Calculate distance between two 3D points """
    return np.sqrt((x[0]-y[0])**2 + (x[1]-y[1])**2 + (x[2]-y[2])**2)

def direction_vector(x,y):
    """ Calculate direction of vector """
    return (x[0]-y[0])/dist_pts3d(x,y) , (x[1]-y[1])/dist_pts3d(x,y) , (x[2]-y[2])/dist_pts3d(x,y)

def dist_cone(cone_args,points):
    """ Calculate the total distance of multiple points to a cone """
    phi, positionX, positionY, positionZ, orientationX, orientationY, orientationZ = cone_args
    position_apex = positionX, positionY, positionZ

    orientationX = 0
    orientationY = 0
    orientationZ = 1
    orientation = orientationX, orientationY, orientationZ

    total_dist = 0
    points_T = points.T
    
    for point in points_T:
        ## Considering an ideal cone
        
        New_Point = [point[0]-positionX,point[1]-positionY,point[2]-positionZ]
        Xr = calc_dist_to_line(New_Point, [0,0,0], orientation)    
        Xh_proyected = proyect_point_to_line(New_Point, orientation)
        Xh = dist_pts3d(Xh_proyected, position_apex)
        
        calc_dist = Xr*np.cos(phi) - Xh*np.sin(phi)
        
        total_dist = total_dist + abs(calc_dist)
       
    return (total_dist)**2

def dist_cone_individual(cone_args,point):
    """ Calculate the total distance of single point to a cone """
    phi, positionX, positionY, positionZ = cone_args
    position_apex = positionX, positionY, positionZ
    orientation = orientationX, orientationY, orientationZ
   
    total_dist = 0
    point = point.T
    
    ## Considering an ideal cone
    
    New_Point = [point[0]-positionX,point[1]-positionY,point[2]-positionZ]
    Xr = calc_dist_to_line(New_Point, [0,0,0], orientation)    
    Xh_proyected = proyect_point_to_line(New_Point, orientation)
    Xh = dist_pts3d(Xh_proyected, position_apex)
    
    calc_dist = Xr*np.cos(phi) - Xh*np.sin(phi)
    
    total_dist = total_dist + calc_dist
       
    return (total_dist)**2

def proyect_point_to_line(point,orientation):
    """ Proyects a point to a line with certain orientation """
    p = point
    s = np.asarray(orientation)
    proyection = ((p[0]*s[0]+p[1]*s[1]+p[2]*s[2])/(s[0]*s[0]+s[1]*s[1]+s[2]*s[2]))*s
    return proyection

def ec_sphere(x,Samp):
    (p1,p2,p3) = Samp
    return [(p1[0]-x[0])**2 + (p1[1]-x[1])**2 + (p1[2]-x[2])**2 - (x[3])**2,
            (p2[0]-x[0])**2 + (p2[1]-x[1])**2 + (p2[2]-x[2])**2 - (x[3])**2,
            (p3[0]-x[0])**2 + (p3[1]-x[1])**2 + (p3[2]-x[2])**2 - (x[3])**2]

#%% Data Input
    
# Cones parallel to axis Z
# pcd = o3d.io.read_point_cloud("STLs/Conos/Cone.pcd")
# pcd = o3d.io.read_point_cloud("STLs/Conos/HalfCone.pcd")
# pcd = o3d.io.read_point_cloud("STLs/Conos/QuarterCone.pcd")

# pcd = o3d.io.read_point_cloud("STLs/Conos/Cone_Angle30_Outlier.pcd")
pcd = o3d.io.read_point_cloud("STLs/Conos/HalfCone_Angle30_Outlier.pcd")
# pcd = o3d.io.read_point_cloud("STLs/Conos/QuarterCone_Angle30_Outlier.pcd")


# Rotated Cones with an aperture angle of 30 degrees, rotated 45 deg w/r to axis X, then 45 deg w/r to axis Y
# pcd = o3d.io.read_point_cloud("STLs/Conos/Cone_Angle30.pcd")
# pcd = o3d.io.read_point_cloud("STLs/Conos/HalfCone_Angle30.pcd")
# pcd = o3d.io.read_point_cloud("STLs/Conos/QuarterCone_Angle30.pcd")

# pcd = o3d.io.read_point_cloud("STLs/Conos/Cone_Angle30_Outlier_Rotated.pcd")
# pcd = o3d.io.read_point_cloud("STLs/Conos/HalfCone_Angle30_Outlier_Rotated.pcd")
# pcd = o3d.io.read_point_cloud("STLs/Conos/QuarterCone_Angle30_Outlier_Rotated.pcd")

#%% Pre-Processing of Data Input
    
# downpcd = pcd.voxel_down_sample(voxel_size=0.05)
# downpcd.estimate_normals(search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=0.1, max_nn=30))

# #Visualization of pcd (full pcd) and downpcd (pcd with less points and option of showing normals) with O3D visualization. 
# o3d.visualization.draw_geometries([downpcd], point_show_normal=True) #Change point_show_normal to True in order to view normals in o3d window
# o3d.visualization.draw_geometries([pcd])

start_time = timeit.default_timer()

pcd2 = copy.deepcopy(pcd)
pcd_array = np.asarray(pcd.points)
# pcd_array = np.load('pcd_array.npy')
pcd_list  = list(pcd_array)
axis_1 = max(pcd_array[:,0])-min(pcd_array[:,0])
axis_2 = max(pcd_array[:,1])-min(pcd_array[:,1])
axis_3 = max(pcd_array[:,2])-min(pcd_array[:,2])
max_axis = axis_1, axis_2, axis_3
values, vectors = eig(cov((pcd_array - mean(pcd_array.T, axis=1)).T))

# f=open('data_quarter_cylinder.txt','w')


#%% Section for iteration of RANSAC

Big_Iterations = 1

for j in range(Big_Iterations):
    NumIter = 100
    Thresh = 0.1 # Percentage, use with radius
    Sample_Points_RANSAC = max(int(len(pcd_list)*0.00005),10) #Ver cono con 5 puntos
    Percentage_Reduction = 1 #Percentage for reducing the size of points, use values between 0 and 1.
    Score = 0
    Best_Sample = [0, 0, 0, 0, 0, 0, 0]
    # Best_Sample = [np.pi/6, 0, 0, 75, 0, 0, 1]
    Best_Sample_Position = 0
    Data_Iterations = list(range(NumIter))
    Best_Comparison = 0
    
    # A sample of a % of the total points is used for comparison of inliers in order to reduce computing time
    Big_Sample = random.sample(pcd_list,int(len(pcd_list)*Percentage_Reduction)) 
    Big_Sample = np.asarray(Big_Sample)
    Big_Sample = Big_Sample.T
    
    Big_Sample_Score = len(Big_Sample.T)
    
    for iteration in range(NumIter):    
        Local_Score = 0
        points = np.asarray(random.sample(pcd_list,Sample_Points_RANSAC))
        
    # if iteration == 0:        
        # Initial coordinates for cone apex
        position_0 = points[:,0].mean(), points[:,1].mean(), points[:,2].mean()
        positionX_0 = position_0[0]
        positionY_0 = position_0[1]
        positionZ_0 = position_0[2]
        if max(points[:,0]) > max(points[:,1]) and max(points[:,0]) > max(points[:,2]):
            positionX_0 = max(points[:,0])
        elif max(points[:,1]) > max(points[:,0]) and max(points[:,1]) > max(points[:,2]):
            positionY_0 = max(points[:,1])
        else:
            positionZ_0 = max(points[:,2])
        
        # First aproximation of cylinder orientation
        orientation_0 = vectors[0] #Ver en base a la iteracion anterior, posible mejora en velocidad
        orientationX_0 = orientation_0[0]
        orientationY_0 = orientation_0[1]
        orientationZ_0 = orientation_0[2]
        
        # First aproximation of aperture of cone 
        phi_0 = np.pi/4
    # else:
    #     phi_0 = Best_Sample[0]
    #     positionX_0 = Best_Sample[1]
    #     positionY_0 = Best_Sample[2]
    #     positionZ_0 = Best_Sample[3]      
    #     orientationX_0 = Best_Sample[4]
    #     orientationY_0 = Best_Sample[5]
    #     orientationZ_0 = Best_Sample[6]
    
    # try:
        # First Cone parameters for fitting
        x0 = [phi_0, positionX_0, positionY_0, positionZ_0, orientationX_0, orientationY_0, orientationZ_0]
        
        # params = opt.minimize(dist_cone,x0,args=(points.T,))
        params = opt.least_squares(dist_cone,x0,args=(points.T,))
        
        # Optimized parameters
        # if iteration == 0:
        #     phi_optimized, posXtop, posYtop, posZtop = [np.pi/6, 0, 0, 75]
        # else:
        phi_optimized, positionX_optimized, positionY_optimized, positionZ_optimized, orientationX_optimized, orientationY_optimized, orientationZ_optimized = params.x
        # phi_optimized = np.pi/6
        # phi_optimized = phi_optimized % 2*np.pi
        position_apex_optimized = positionX_optimized, positionY_optimized, positionZ_optimized
        orientation_optimized = orientationX_optimized, orientationY_optimized, orientationZ_optimized
        # orientation_optimized = 0,0,1
        
        #Comparison and scoring of points        
        real_radius = np.sin(phi_optimized)*dist_pts3d(position_apex_optimized, Big_Sample) #REVISAR
        phi_minus = phi_optimized*(1-Thresh)
        phi_plus = phi_optimized*(1+Thresh)
        lowerRadius = np.sin(phi_minus)*dist_pts3d(position_apex_optimized, Big_Sample)
        upperRadius = np.sin(phi_plus)*dist_pts3d(position_apex_optimized, Big_Sample)
        comp_R = calc_dist_to_line(Big_Sample,position_apex_optimized, orientation_optimized)
        comparison = (comp_R > lowerRadius) & (comp_R < upperRadius)
       
        ## TESTING
        # comparison = []
        # for point in range(len(Big_Sample.T)):
        #     Comp = dist_cone_individual(params.x,Big_Sample.T[point]) == 0
        #     comparison.append(Comp)
        # comparison = np.asarray(comparison)
        
        Local_Score = comparison.sum()
    
        RANSAC_Score = Local_Score
        
        Data_Iterations[iteration] = params.x, RANSAC_Score
        
        if RANSAC_Score > Score and RANSAC_Score < Big_Sample_Score:
            Score = RANSAC_Score
            Best_Sample = params.x
            Best_Sample_Position = iteration+1
            Best_Comparison = comparison
                
            print("Iteration: {} (Run {} of {})".format(iteration+1,j+1,Big_Iterations))
            print("Current Aperture Angle (in degrees):", abs((Best_Sample[0]*180/np.pi)%360))
            print("Current Apex Position: X: {}, Y:{}, Z:{}".format(Best_Sample[1],Best_Sample[2],Best_Sample[3]))
            print("Current Orientation: X: {}, Y:{}, Z:{}".format(Best_Sample[4],Best_Sample[5],Best_Sample[6]))
            print("RANSAC Score: {}, Score: {} (Found in Iteration {})".format(RANSAC_Score,Score,Best_Sample_Position))
            print("----------")
            
        else:
            print("Iteration: {} (Run {} of {})".format(iteration+1,j+1,Big_Iterations))
            print("Current Aperture Angle (in degrees):", abs((Best_Sample[0]*180/np.pi)%180))
            print("RANSAC Score: {}, Score: {} (Found in Iteration {})".format(RANSAC_Score,Score,Best_Sample_Position))
            print("----------")
    # except:
    #     continue
            
    stop_time = timeit.default_timer()
    
    print('Time: ', stop_time - start_time)  
    print('Aperture Angle (in degrees): ', abs((Best_Sample[0]*180/np.pi)%360))
    print("Apex Position: X: {}, Y:{}, Z:{}".format(Best_Sample[1],Best_Sample[2],Best_Sample[3]))
    print("Orientation: X: {}, Y:{}, Z:{}".format(Best_Sample[4],Best_Sample[5],Best_Sample[6]))
    Apex_Position = [Best_Sample[1],Best_Sample[2],Best_Sample[3]]
    Apex_Position = [0,0,75]
    Cone_Height = dist_pts3d(Apex_Position,[0,0,0]) #No esta centrado en origen necesariamente
    Cone_Radius = abs(np.tan(Best_Sample[0])*Cone_Height)
    
    # f.write(str(Best_Sample[0])+','+str(Best_Sample[4])+','+str(Best_Sample[5])+','+str(Best_Sample[6])+','+str(Best_Sample_Position)+'\n')

# f.close()


Best_Comparison_Positions = np.asarray(np.where(Best_Comparison == True)[0])
pcd2.paint_uniform_color([1,0,0])

Vector_Orientacion = [Best_Sample[4],Best_Sample[5],Best_Sample[6]]
Rotate = Rotation.align_vectors([Vector_Orientacion], [[0,0,1]])
Inv_Rotate = Rotation.align_vectors([[0,0,1]],[Vector_Orientacion])

ABC = list(range(Best_Comparison.sum()))
np.asarray(pcd2.colors)[ABC] = [0.5,0.5,0.5]

coord_frame = o3d.geometry.TriangleMesh.create_coordinate_frame(size=100, origin=[0, 0, 0])

RANSAC_Cone = o3d.geometry.TriangleMesh.create_cone(radius=Cone_Radius,height=Cone_Height,resolution=100)
RANSAC_Cone.paint_uniform_color((0.75,0.75,0.75))
# RANSAC_Cone = RANSAC_Cylinder.translate((0,0,0), relative=False)

## Rotation of primitive and alignment with PCD
RANSAC_Cone_Vertex = np.asarray(RANSAC_Cone.vertices)
RANSAC_Cone_Vertex = Rotate[0].apply(RANSAC_Cone_Vertex)
RANSAC_Cone.vertices = o3d.utility.Vector3dVector(RANSAC_Cone_Vertex)
o3d.visualization.draw_geometries([coord_frame, RANSAC_Cone, pcd2])

## For rotation of pcd and alignment with Z axis
# pcd2_points = np.asarray(pcd2.points)
# pcd2_points = Inv_Rotate[0].apply(pcd2_points)
# pcd2.points = o3d.utility.Vector3dVector(pcd2_points)
# o3d.visualization.draw_geometries([coord_frame, pcd2])


# stop_time = timeit.default_timer()

# print('Time: ', stop_time - start_time)  