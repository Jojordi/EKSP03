# -*- coding: utf-8 -*-
"""
Versión 4

FUNCIÓN: 
        Obtener subpoligonos 

CONTENIDO:
        * Localizar puntos cóncavos
        * Construir lista de lineas 
        * Realizar corte y generar subpoligonos
        * Identificar puntos principales para generación de código .csr


"""
#Librerias externas
import pandas as pd
import geopandas as gpd 
from shapely.ops import linemerge, unary_union, polygonize
from shapely.geometry import Point,LinearRing, MultiPoint, Polygon, LineString, MultiLineString
import numpy as np 
import itertools
import warnings
warnings.filterwarnings("ignore")
#Librerias internas
from path_generation.concavity import  find_concave_vertices
from path_generation.concavity.utils import gaussian_smooth_geom_1

#PASO 1 OBTENER PUNTOS CONCAVOS
def points_concaves(points):    
    points = points[:, 0:2]
    point_collection = MultiPoint(list(points)) #envelope is a Polygon of shapely            
    poly = Polygon(point_collection) #Declaración de Poligono
    #Entrega puntos concavos
    # concave_df = find_concave_vertices(poly,0, filter_type ='all')#Opción de suavizar el poligono
    ch = gaussian_smooth_geom_1(poly, sigma = 2) 
    #Opción de suavizar ángulo 
    concave_df = find_concave_vertices(ch,0, filter_type ='peak', convolve=True)
    #Limitar ángulos a entregar
    concave_new = concave_df.query('angle > 6') #MAyor valor a mayor cantidad de puntos
    #Seleccionar puntos
    psfinal= concave_new.iloc[:,0] 
    arrp = psfinal.to_numpy() #array de "Puntos" 
    #Obtener coordenadas de "Puntos" 
    xs = [point.x for point in arrp]
    ys = [point.y for point in arrp]
    arrc = np.column_stack((xs, ys))
    if len(arrc) <= 0:
        print("ERROR: {}pts, se utilizará eje de división".format(len(arrc)))
        centroid = poly.centroid
        envelope = poly.envelope #vertices del rectangulo 
        x_min, y_min, x_max, y_max = envelope.bounds #puntos de extremos
        axis = LineString([(centroid.x,y_min),(centroid.x,y_max)])
        axis_h = LineString([(x_min, centroid.y),(x_max, centroid.y)]) #eje horizontal
        intersection_v = poly.intersection(axis) #instersection of line with polygon 
        intersection_h = poly.intersection(axis_h) #instersection of line with polygon    
        ls_ = list(intersection_v.coords)
        ls_h = list(intersection_h.coords)
        xs = [point[0] for point in ls_]
        ys = [point[1] for point in ls_]
        xs2 = [point[0] for point in ls_h]
        ys2 = [point[1] for point in ls_h]
        xs = xs+xs2
        ys = ys + ys2 
        arrc = np.column_stack((xs, ys))
    return arrc


#PASO 2 FILTRAR LINEAS 
def filter_lines(arraypts,polygon):        
    #Lista de combinaciones posibles
    iterationopt =list(zip(*itertools.chain.from_iterable(itertools.combinations(arraypts, 2))))
    s_poly = LinearRing(list(polygon.exterior.coords)) 
    if s_poly.is_ccw == False:
        side = 'left'
    else:
        side = 'right'
    polygon_2 = s_poly.parallel_offset(.95, side, join_style=1) #polygon con pequeño offset hacia afuera
    polygon2 = Polygon(polygon_2) #Poligono para verificar que lo contenga
    #Filtrar lineas internas
    list_test = []
    for i in range(len(iterationopt[0])-1):
        pa =Point((iterationopt[0][i]),(iterationopt[1][i]))
        pb =Point((iterationopt[0][i+1]),(iterationopt[1][i+1]))
        linecut = LineString([pa,pb])
        testcontain = polygon2.contains(linecut)      
        if testcontain is True:
            #Si esta adentro se guarda
            long = linecut.length
            coord_inside = (((iterationopt[0][i]),(iterationopt[1][i])),((iterationopt[0][i+1]),(iterationopt[1][i+1])))
            list_test.append(coord_inside)
        
    list_final=[] #lista para ploteo 
    list_dffinal = [] #df final

    if len(list_test) > 1:
        list_test.append(list_test[0]) #repito primer elemento
        for ls in range(0,len(list_test)-1):
            lf = LineString(list_test[ls])
            lf_2 = LineString(list_test[ls+1])
            testsame = (lf).equals(lf_2) 
            #Si no se repite se guarda
            if testsame is False:
                # print("No se repite")
                list_final.append(lf_2) #queda como conjunto de LS
                long = lf_2.length
                new_row = ((list_test[ls+1][0]),(list_test[ls+1][1]), long) 
                list_dffinal.append(new_row) #lista para crear df
    else:
        lf_2 = LineString(list_test[0])
        list_final.append(lf_2) #queda como conjunto de LS
        long = lf_2.length
        new_row = ((list_test[0][0]),(list_test[0][1]), long) 
        list_dffinal.append(new_row) #lista para crear df
    #dataframe de lineas
    df_lines = pd.DataFrame(list_dffinal, columns=['Pa','Pb','Longitud'])
    #opción para plotear lineas
    multils = MultiLineString(list_final) #se plotea como MLS
    return multils, df_lines

#PASO 3 CALCULAR COEFICIENTE DE CONVEXIDAD 
def cut_coeficient(polygon, lines,df_lines, point_collection, slices):
    #Función de corte
    area_list = [] #lista para guardar áreas
    area_listc = [] #lista de areas convexas
    area_extras = []
    area_extras2 = []
    for ls in range(len(lines)):
        merged = linemerge([polygon.boundary, lines[ls]]) #add seccond line
        borders = unary_union(merged)
        polygons = list(polygonize(borders))
        area_cut = [] #lista para encontrar el mínimo
        area_cch =[]
        for pc in range(len(polygons)):
            area_p= (polygons[pc].area)
            points_p = MultiPoint(list(polygons[pc].exterior.coords))
            area_convex = points_p.convex_hull.area
            area_cch.append(area_convex)
            area_cut.append(area_p) #guardar áreas
        areal= (min(area_cut)) #valor del mín
        area_list.append(areal) #lista de todos los mínimos
        area_extras.append(max(area_cut))
        area_listc.append(min(area_cch))
        area_extras2.append(max(area_cch))
    #Calcular coeficientes de convexidad
    df_lines['Área'] = area_list #Añadir valores área 
    df_lines['Área2'] = area_extras #Añadir valores área 
    df_lines['ÁreaC'] = area_listc #Añadir valores área 
    df_lines['ÁreaC2'] = area_extras2 #Añadir valores área 
    #CONVEX HULL DE SET DE PUNTOS 
    point_collection.envelope
    convex_hull_polygon = point_collection.convex_hull
    A_r = (convex_hull_polygon.area) #Área de Convex Hull
    
    #Área Convex de c/elemento
    n= len(df_lines)
    H_list = list(itertools.repeat(A_r, n))
    df_lines['H_i'] = H_list
    
    #Coeficiente P de c/elemento
    df_lines['Ci'] = (df_lines['Área']*df_lines['Área'])/(df_lines['ÁreaC']*df_lines['H_i'])
    df_lines['Ci2'] = (df_lines['Área2']*df_lines['Área2'])/(df_lines['ÁreaC2']*df_lines['H_i'])
    df_lines['Prom'] = round((df_lines['Ci']+df_lines['Ci2'] )/2,2)    
    
    #Seleccionar los de Ci mas alto 
    #Ordenar por Ci de mayor a menor
    df_lines=df_lines.sort_values(by=['Prom'], ascending=0)
    #Redondeando a dos decimales, se identifica si solo existe un promedio igual, caso de ejes
    values = df_lines.Prom.unique()
    if len(values) == 1:
        df_lines=df_lines.sort_values(by=['Ci'], ascending=0)
    df_five = df_lines.iloc[0:slices]   # el primero
    #Añadir Z
    z_one =list(polygon.exterior.coords)[0][2]
    z_one = (z_one,)    
    # Crear LS de df
    lines_select = [] #Lista para LS
    for ll in range(len(df_five)):
        p1 = df_five.iloc[ll].loc['Pa'] 
        p1 = p1+z_one
        p2 = df_five.iloc[ll].loc['Pb']
        p2 = p2 + z_one
        lselect = LineString([p1,p2])
        lines_select.append(lselect)
        
    return  lines_select


#PASO 4 GENERAR SUBPOLIGONOS
def gen_subplot(line_split_collection, polygon):
    line_split_collection.append(polygon.boundary) 
    merged_lines = linemerge(line_split_collection)
    border_lines = unary_union(merged_lines)
    decomposition = polygonize(border_lines)
    result = list(decomposition)
    def plot(shapely_objects, figure_path='fig.png'):
        boundary = gpd.GeoSeries(shapely_objects)
        boundary.plot(color=['mistyrose','bisque', 'lavender', 'lightsteelblue', 'lemonchiffon', 'pink', 
                              'lightgrey', 'thistle', 'ivory', 'honeydew','silver','slateblue', 'rosybrown'])
    #Se corrobora que el poligono generado este dentro 
    nresult = []
    for part in range(len(result)):
        pointc = result[part].centroid
        testinside =  (pointc.within(polygon))
        if testinside is True:
            nresult.append(result[part])
    return nresult