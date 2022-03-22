# -*- coding: utf-8 -*-
"""
Versión 11

FUNCIÓN: 
        Generación de trayectorias de reparación
-Opciones: 
        *Raster: separadas, continua y zigzag
            -Rotatorio: ángulo de 0° a 180°
        *Offset: Caso "Cerrado" 
                 Caso "Continuo"

Notas:
Cada estrategia devuelve información relevante para su evaluación
Rotatorio se hace con función "rotate" de Shapely, basadandose en el centro del polígono.
Offset se crea sobre el poligono anterior 
Se entregan LineString Z, es decir, lineas con coordenadas x,y,z. 
    En el caso de Raster se hace una aproximación, y en las de contorno se fija un valor z.
    

"""
#LIBRERIAS EXTERNAS
import matplotlib.pyplot as plt
import numpy as np
from shapely import affinity
from shapely.geometry import Point, Polygon, LineString, MultiLineString, MultiPoint, LinearRing
from shapely.ops import unary_union, linemerge, nearest_points, polygonize, split
import math 

# =============================================================================
#                               LÍNEAS
# =============================================================================
# FUNCIONES A LLAMAR
def rot_raster(points,angle,polygon, s_poly,o,p,w):
    #a-Obtener puntos    
    points_points, amount =  opt_rotar(points,angle, polygon,s_poly,o,p)
    #b-Generar uniones
    total_lines = union_raster(points_points, amount)
    subp_lines = [] #Variable vacia util para utilizar una sola función para calcular parametros
    return total_lines,subp_lines,points_points

def rot_zigzag(points,angle,polygon, s_poly ,o,p,w):
    #a-Obtener puntos
    points_points, amount = opt_rotar(points,angle, polygon,s_poly,o,p)
    #b-Generar uniones
    total_lines, unionls = union_zigzag(points_points, amount)
    subp_lines = []
    return total_lines, subp_lines, points_points, unionls

def rot_continuos(points,angle,polygon, s_poly,o,p,w):
    #a-Obtener puntos
    points_points, amount = opt_rotar(points,angle, polygon,s_poly,o,p)
    #b-Generar uniones
    # print("amount cc", amount)
    total_lines,points_order, unionls = union_continuo(points_points, amount)
    subp_lines = []
    return total_lines,subp_lines, points_order, unionls

#Funciona dentro de 0 a 180, de 180 a 360 se asume que asemejan el primer rango
def opt_rotar(points,angle, polygon,s_poly,o,p):
    # Clasificación del ángulo
    if angle == 0:
        points_points = points_rasterh(points, polygon,s_poly,o,p)
    elif angle>0 and angle <=180:
        points_points = points_raster(points,angle, polygon,s_poly,o,p)
    else:
        print("Valor erróneo: ángulo debe ser menor a 180°")         
    return points_points

def intersection_2D3D(points, polygon):
    #Función para  obtener el valor Z de cada punto
    multip = MultiPoint(list(polygon.coords))
    lista_p= []
    for p in points:
        #buscar en lista de puntos originales el mas cercano 
        distance = 10000 #valor inicial de distancia
        for mp in multip:
            d = mp.distance(p)
            #si es menor que la guardada se redefinen variables
            if d < distance:
                distance = d
                z_use = list(mp.coords)[0][2] #extraer valor de Z
        p_z = Point(p.x, p.y, z_use)
        lista_p.append(p_z)
    intp3d = MultiPoint(lista_p) #Multipoint con un z adecuado
    return intp3d

def points_rasterh(points, polygon,s_poly,o,p): 
    # REVISAR SI ES NECESARIO AJUSTAR P, solo para poligonos casi convexos
    area_original = Polygon(points).area #Área original CAMBIO POLYGON
    area_convex = MultiPoint(points).convex_hull.area #Área del poligono convexo
    index_convex = round(area_original/area_convex,2) #referencia de convexidad 
    #Si index >0.9 se modifica valor p
    if index_convex > 0.9:
        minx, miny, maxx, maxy = polygon.bounds
        p_min = (p/0.738) * (2/3) # valor minimo de p a usar, 2/3 de w
        ancho = maxy-miny-(2*o) #Buscar ancho del poligono
        width_final = 0 #variable de ancho inicial 
        steps = np.arange(p_min,p,0.01).tolist() #Rango de valores de step over
        steps = steps[::-1] #Invertir, empezar del ideal al menor
        # Para un rango de step over, buscar donde se cubre el mayor ancho 
        for pi in steps:
            n = int(ancho/pi) #Buscar división de lineas
            width_cover = pi*n
            #Definir el valor optimo de step over
            if width_cover > width_final:
                width_final = width_cover
                p = pi #Se redefine valor 
        
    #Crear malla de raster
    rectangle = polygon.envelope
    xx,yy= mallah(rectangle,o,p) #Malla raster horizontal
    points_order=[]
    new_lines = []
    for i in range(0,len(yy), 1):
        line = LineString([(xx[i][0],yy[i][0]),(xx[i][1],yy[i][1])]) #linea original raster
        intp = polygon.intersection(line) #MultiPoint        
        if type(intp) == LineString:
            #Se descompone en puntos en caso de ser LineString
            intp = MultiPoint(list(intp.coords))
        elif type(intp) == MultiLineString:
            cp =[] # lista para guardar puntos
            for ls in intp:
                for ps in ls.coords:
                    cp.append(ps)
            intp = MultiPoint(cp)
        intp = intersection_2D3D(intp, s_poly) #obtener el z de cada punto
        #Crear lineas entre todos los puntos
        for j in range(0,len(intp)-1,1):
            partline = LineString([(intp[j].x+o,(intp[j].y), intp[j].z),(intp[j+1].x-o,(intp[j+1].y), intp[j+1].z)]) #LineString 3D
            #Verificar que este dentro del poligono
            if polygon.contains(partline)==True:
                #Añadir 3 pto
                p_centroid = partline.centroid
                z_mean= (intp[j].z + intp[j+1].z)/2 #z promedio entre dos extremos
                p_centroid = Point(p_centroid.x, p_centroid.y,z_mean)
                partline = LineString([list(partline.coords)[0], p_centroid ,list(partline.coords)[1]]) #nueva linea con pto adicional
                new_lines.append(partline) #guarda linea
    splitlines = MultiLineString(new_lines)
    amount =  len(list(partline.coords)) #Cantidad de puntos por linea

    # GUARDAR PUNTOS INDIVIDUALES 
    for l in range(len(splitlines)):
        for pl in range(len(splitlines[l].coords)):
            ps = (list(splitlines[l].coords[pl]))
            points_order.append(ps)
    points_points = MultiPoint(points_order) #MultiPoint Z
    return points_points, amount

def points_raster(points,angle, polygon,s_poly,o,p):
    #Incrementar de tamaño la malla
    minx, miny, maxx, maxy = polygon.bounds
    dif_y = maxy - miny
    dif_x = maxx - minx
    max_ =max(dif_x,dif_y)
    extra = max_/2.5 #valor extra para hacer malla raster
    # REVISAR SI ES NECESARIO AJUSTAR P, solo para poligonos casi convexos
    area_original = Polygon(points).area #Área original CAMBIO POLYGON
    area_convex = MultiPoint(points).convex_hull.area #Área del poligono convexo
    index_convex = round(area_original/area_convex,2) #referencia de convexidad 
    #Si cumple condiciones se modifica valor p
    if index_convex >0.95 and angle == 90:        
        p_min = (p/0.738) * (2/3) # valor minimo de p a usar, 2/3 de w
        ancho = maxx-minx
        width_final = 0 #variable de ancho inicial 
        steps = np.arange(p_min,p,0.01).tolist() #Rango de valores de step over
        steps = steps[::-1] #Invertir, empezar del ideal al menor
        # Para un rango de step over, buscar donde se cubre el mayor ancho 
        for pi in steps:
            n = int(ancho/pi) #Buscar división de lineas
            width_cover = pi*n
            #Definir el valor optimo de step over
            if width_cover > width_final:
                width_final = width_cover
                p = pi
    
    centro= polygon.centroid #centro del poligono, referencia de rotación
    l_bigger = s_poly.buffer(extra, resolution=16, join_style=1, mitre_limit=5).exterior #LinearRing externo
    rectangle = l_bigger.envelope
    xx,yy= malla(rectangle,p) #Malla raster en x
    if s_poly.is_ccw == False:
        side =  'right'
    else:
        side = 'left'
    l_small = s_poly.buffer(o, resolution=16, join_style=1, mitre_limit=5).interiors #LinearRing interior de offset
    if len(l_small) == 0:
        l_small = s_poly.parallel_offset(o, side, join_style=1)
    else:
        l_small = s_poly.buffer(o, resolution=16, join_style=1, mitre_limit=5).interiors[0] #LinearRing interior de offset
    l_small = Polygon(l_small) #Se define como pol para calcular área
    percent_error = l_small.area*100/area_original
    if percent_error < 80:
        #En algunos casos no toma el poligono correcto o este se descompone en mas partes, 
        #se usa parallel offset
        l_small = s_poly.parallel_offset(o, side, join_style=1)
    #Buscar lineas de interseccion, coordenadas X y Y
    coords = []
    for i in range(0,len(yy), 1):
        # print("\n Line G", i)
        line = LineString([(xx[i][0],yy[i][0]),(xx[i][1],yy[i][1])]) #linea original raster
        l_rotated = affinity.rotate(line, angle, origin=centro) #Se genera linea rotada girando respecto al centro del poligono 
        intp = l_small.intersection(l_rotated) #MultiPoint (intersección entre poligono con offset hacia adentro)   
        #Descomponer en puntos si no es multipunto
        if type(intp) == LineString:
            intp = MultiPoint(list(intp.coords))
        elif type(intp) == MultiLineString:
            cp =[] # lista para guardar puntos
            for ls in intp:
                for ps in ls.coords:
                    cp.append(ps)
            intp = MultiPoint(cp)
        if type(intp) == MultiPoint:
            #Si al crear una linea, esta se encuentra adentro solo se toman los extremos
            if len(intp) > 2:
                line_test = LineString(intp) #corroborar si puede ser solo un elemento
                if polygon.contains(line_test) == True:
                    intp = MultiPoint([list(line_test.coords)[0], list(line_test.coords)[-1]]) #solo pts extremos
            #CREAR LINEAS EN FORMAS CONCAVAS, SE CORROBORA INTERSECCIÓN
            #Crear lineas entre todos los puntos
            for j in range(0,len(intp)-1,1):                
                partline = LineString([(intp[j].x,(intp[j].y)),(intp[j+1].x,(intp[j+1].y))]) #LineString                 
                #Verificar que este dentro del poligono
                if polygon.contains(partline)==True:
                    p_centroid = partline.centroid
                    partline = LineString([list(partline.coords)[0], p_centroid ,list(partline.coords)[1]]) #nueva linea con pto adicional
                    coords.append(list(partline.coords)) #Guardar coordenadas
        else:
            pass  
    #OPCION PARA BUSCAR VALOR Z : buscar intersección de cada punto con la superficie de un poligono
    amount = len(list(partline.coords)) #Cantidad de puntos por linea
    coords3d = []
    #Crear malla a 0 grados
    step = p/6 # valor de step pequeño para crear una malla de raster fina
    points_cero, amount0 = points_rasterh(points, polygon,s_poly,step,step)
    lines_cero = union_raster(points_cero, amount0)
    for i in range(0,len(coords)):        
        for c in range (0,len(coords[i])):
            p_c = Point(coords[i][c])            
            d_start = 50
            #Llamar cada linea de la malla 
            for lc in range(len(lines_cero)):
                z_c = nearest_points(p_c, lines_cero[lc]) #Tuple of Points (x,y), se toma el segundo 
                distance_c = z_c[1].distance(p_c)
                #Buscar el punto más cercano 
                if distance_c < d_start:
                    d_start = distance_c
                    index_l = lc
            
            z_use =list(lines_cero[index_l].coords[0])[2] #Sacar z
            p_c = coords[i][c] +( z_use,) #Añadir z
            coords3d.append(p_c)
    points_points = MultiPoint(coords3d) #MultiPoint Z
    return points_points, amount

#MALLAS PARA GENERAR LINEAS DE INTERSECCION 
def mallah(envelope,o,p):
    #Malla caso sin rotación, horizontal = 0 grados
    x_min, y_min, x_max, y_max = envelope.bounds #puntos de extremos
    xvalues = np.array([x_min, x_max]) 
    yvalues = np.arange((y_min+o), (y_max-o), p)
    xx, yy = np.meshgrid(xvalues, yvalues)
    return xx,yy

def malla(envelope,p):
    x_min, y_min, x_max, y_max = envelope.bounds #puntos de extremos
    xvalues = np.array([x_min, x_max]) 
    yvalues = np.arange((y_min), (y_max), p) #solo lineas espaciadas en p
    xx, yy = np.meshgrid(xvalues, yvalues)
    return xx,yy

#FUNCIONES DE UNIONES ENTRE PUNTOS
def union_raster(points_points, amount):
    """TIPO RASTER"""
    #Orden: 0-1,2-3,4-5,6-7 |||||||
    new_line = [] #array de elementos    
    #Crear N elementos = N linea con m/2 PTOS
    for i in range(0, len(points_points), amount):
        line00 = LineString(points_points[i:i+amount])
        new_line.append(line00)
        total_lines = MultiLineString(new_line) #lineas raster    
    return total_lines

def union_zigzag(points_points, amount):
    """TIPO ZIGZAG"""
    #Orden: 0-1-2-3-4-5-6-7 |\|\|\
    #para ploteo se crearan n linestrings para visualizar solapamiento 
    new_line = [] #array de elementos
    #Crear N elementos = N linea con m/2 PTOS
    for i in range(0, len(points_points)-2, amount):
        line00 = LineString(points_points[i:i+amount])
        new_line.append(line00)
        if i < len(points_points)-amount:
            line01 = LineString([points_points[i+amount-1], points_points[i+amount] ])#unión entre lineas
            new_line.append(line01)
    total_lines = MultiLineString(new_line) #lineas raster
    unionls = linemerge(total_lines)
    unionls = MultiLineString([unionls])
    return total_lines, unionls

def union_continuo(points_points, amount):
    """TIPO CONTINUO"""
    # Orden: 0-1-3-2-4-5-7-6 -_-_-_
    #Crear array con todos lo puntos en el orden deseado
    new_line = [] #array de elementos
    m = len(points_points)          #Cantidad puntos x,y
    order = np.arange(m)            #Vector de orden 1:m     
    j=0                             #Definición del contador  
    for i in range(m):              #For para cantidad de m puntos
        order[i]=i                  #Asigna mismo valor 
        if j==3:                    #En posición 2 y 3 cambia
            order[i]=i+2      
        if j==5:
            order[i]=i-2
        j=j+1                       #Contador de serie
        if j==6:
            j=0                     #Reinicia cada 4ta posición 
    points_order = [points_points[i] for i in order] #Reordena con nuevo orden de indices
        
    #Crear N elementos para visualizacion de solapamiento
    new_line = [] #array de elementos
    for i in range(0, len(points_order)-2, amount):
        line00 = LineString(points_order[i:i+amount])
        new_line.append(line00)
        if i < len(points_order)-amount:
            line01 = LineString([points_order[i+amount-1], points_order[i+amount] ])#unión entre lineas
            new_line.append(line01)
    total_lines = MultiLineString(new_line) #lineas raster
    unionls = linemerge(total_lines)
    unionls = MultiLineString([unionls])
    return total_lines, points_order, unionls


#%%
# =============================================================================
#                                  OFFSET
# =============================================================================
def sort_list(list1, list2): 
    #Reordernar lista
    zipped_pairs = zip(list2, list1) 
    z = [x for _, x in sorted(zipped_pairs)]     
    return z

#OBTENER LINEAS PARA OFFSET
def offset_closed(points,polygon, s_poly, envelope,o,p,w, endpoint):
    def plot_offset(ax, ob, color='#999999'):
        parts = hasattr(ob, 'geoms') and ob or [ob]
        for part in parts:
            x, y = part.xy

    z_one = points[0][2] #valor de z  único para todas las líneas generadas
    new_line=[] #variable para lineas offset del pol original
    list_ueps = [] #lista, ultimo en entrar primero en salir 
    sub_line= [] #variable para offset de subpoligonos  
    sub_ueps = [] #lista, ultimo en entrar primero en salir 
    poly_o = s_poly #primer linestring del poligono original
    ax = plt.gca() #necesario para crear subp
    
    #CICLO LINEAS CERRADO
    x_min, y_min, x_max, y_max = envelope.bounds #puntos de extremos
    centroy= (s_poly.centroid.y)
    restay= y_max-centroy
    limit =  int(restay)+1 # Distancia limite para realizar contornos
    t =  np.arange(o, limit, p) #offset se repetira len(t) veces
    offset = [p]*len(t) #Lista de distancia uniforme etre offsets de p
    offset.insert(0,o) #crear primer offset a distancia o
    side = ['left']*len(t) #declara el lado en que se crea el offset 
    #Obtener la dirección del primer offset (se evita en caso de saber el sentido de c/curva)
    condition = (s_poly.is_ccw) #Returns True if coordinates are in counter-clockwise order
    if condition is False:
        side.insert(0,"right")
    big_lines = 0 #Caso cuando los offset externos no se guardan como tal
    try:
        # realizar offset por n times 
        for ko in range (len(t)):
            #En algunos casos por razóm desconocida buffer no se realiza por lo que se da de opción parallel
            try:
                line_rings = poly_o.buffer(offset[ko], resolution=16, join_style=1, mitre_limit=5).interiors #interior rings
                line_ptos = [line_rings[i] for i in range(len(line_rings))] #convertir en lista 
                if len(line_rings) >1:
                    for l in reversed(range(0,len(line_rings))):
                        long = line_ptos[l].length
                        if long <= 1:
                            del line_ptos[l]     
            except:
                line_rings = s_poly.parallel_offset(offset[ko], side[ko], resolution=16, join_style=1, mitre_limit=5.0)
                if type(line_rings) == MultiLineString:
                    line_ptos = []
                    for lst in range(line_rings):
                        line_ptos.append(line_rings[lst])
                else:
                    line_ptos  = [line_rings]       
            #Si hay 2 o + elementos, entonces, se crean subpoligonos
            if len(line_ptos) > 1: 
                npol=(len(line_ptos)) #Cantidad de subpoligonos
                #Buscar el subpoligono mas cercano al punto final 
                p_last = Point(list(poly_o.coords[-1])) #Punto final de el contorno externo
                distancia_list = [] #lista para guardar distancia
                for l in range(0,npol):
                    p_first = Point(list(line_ptos[l].coords[0])) #Primer pto de la linea
                    d_top = p_last.distance(p_first)
                    distancia_list.append(d_top) 
                l_index = np.argsort(distancia_list) #Reordenar índices por distancia
                line_ptos = sort_list(line_ptos,l_index)
                #Generar contornos dentro de cada subpoligono
                for l in range(0,npol):
                    #Creación de subpoligonos  
                    sub_pol = [] #variable para interiores
                    sub_pol_ueps = [] #variable para interiores-orden inverso 
                    poly_s = LineString(line_ptos[l]) #define nuevo LineString
                    line_ring = line_ptos[l] #LinearRing
                    length_p = poly_s.length
                    if length_p < w/4:
                        pass
                    else:
                        #Contornos dentros de los subpoligonos
                        while length_p >= w/4:
                            #Añadir Z
                            puntos_curva = np.asarray(list(poly_s.coords))
                            forma_alturas = (puntos_curva.shape[0], 1)
                            altura_curva = np.full(forma_alturas, z_one)
                            puntos_curva = np.append(puntos_curva, altura_curva, axis=1)
                            poly_s = LineString(puntos_curva)
                            sub_pol.append(poly_s) #Guarda ls del pol anterior                        
                            sub_pol_ueps.insert(0,poly_s) #Guarda ls del pol anterior, en sentido inverso                        
                            line_sub = line_ring.buffer(p, resolution=16, join_style=1, mitre_limit=5).interiors 
                            if len(line_sub) ==0:
                                break
                            else:
                                line_sub = line_sub[0]
                                poly_s = LineString(line_sub) #nuevo contorno generado
                                line_ring = LinearRing(line_sub)
                                length_p = poly_s.length
                                try:
                                    plot_offset(ax, poly_s, color='purple') 
                                except AttributeError:
                                    #Si no se puede plotear tambien es señal de que no 
                                    #se pueden obtener mas offset
                                    break
                        small_pol = MultiLineString(sub_pol) #crea mls de todos los pol
                        small_pol_ueps = MultiLineString(sub_pol_ueps) #crea mls de todos los pol
                        sub_line.append(small_pol) #Guarda por elemento de subpoligono
                        sub_ueps.insert(0,small_pol_ueps)
                break
            else:
                if len(line_ptos)==0:
                    #Caso de elementos vacios
                    pass
                else:
                    #Nueva linea offset
                    line_ptos = line_ptos[0] #interior 0, Linear Ring                    
                    #Si la linea es el primer offset generado
                    if ko == 0:  
                        p_end = Point(list(line_ptos.coords[-1]))
                        #Corroborar ubicación del ultima linea 
                        tuple_end = (int(p_end.x), int(p_end.y))
                        # si son iguales se crea otro punto de partida 
                        if tuple_end == endpoint:
                            line_point = cut_piece(line_ptos,0.0001, w) #Mover el punto de inicio
                            distance = line_point.length # distancia de pto cero a punto final 
                            line_first = cut_piece(line_ptos,distance,line_ptos.length-distance)
                            line_1 = list(line_first.coords)
                            line_2 = list(line_point.coords)
                            line_3 = line_1 + line_2
                            line_ptos = LinearRing(line_3) 
                    #Añadir Z 
                    puntos_curva = np.asarray(list(line_ptos.coords))
                    forma_alturas = (puntos_curva.shape[0], 1)
                    altura_curva = np.full(forma_alturas, z_one)
                    puntos_curva = np.append(puntos_curva, altura_curva, axis=1)
                    poly_o = LineString(puntos_curva)
                    new_line.append(poly_o) #Lista de offsets
                    list_ueps.insert(0,poly_o) #Lista de offsets-sentido inverso
                big_lines = MultiLineString(new_line)  
                biggest_lines = MultiLineString(list_ueps)  
    except:
        pass
    
    #UNIÓN DE DATOS PARA ENTREGA A TRADUCTOR
    if type(big_lines) == MultiLineString:
        #Caso normal, se guardó como MLS 
        if len(sub_line) == 0:
            # print("NO HAY SUBPOLIGONOS")
            unionls = MultiLineString(new_line)
        else:            
            for pl in range(len(sub_line)):
                #Entra a cada subpoligono
                for ip in range(len(sub_line[pl])):
                    #Entra a cada subelemento
                    linet= sub_line[pl][ip] #LineString de subpoligono 
                    new_line.insert(0,linet) #Añadir en la inversa
            #Variable de unión, en caso de subpoligonos
            unionls = MultiLineString(new_line)
    else:
        #Caso extraño de generar subpoligono que deberian ser poligonos externos
        #redefinir big_lines y subline
        for pl in range(len(sub_line)):
            for ip in range(len(sub_line[pl])):
                linet= sub_line[pl][ip] #LineString de subpoligono 
                new_line.append(linet)
            biggest_lines = MultiLineString(new_line)
            unionls = MultiLineString(new_line) #variable en caso de existir subpoligonos
            sub_line= [] #se vacia porque los valores estan en big_lines
    return biggest_lines, sub_ueps, unionls


# =============================================================================
#                                  ESPIRAL
# =============================================================================
def cut(line, distance):
    #Función para cortar una linea a una distancia deseada desde el punto 0
    if distance <= 0.0 or distance >= line.length:
        return [LineString(line)]
    coords = list(line.coords)
    for i, p in enumerate(coords):
        pd = line.project(Point(p))
        if pd == distance:
            return [
                LineString(coords[:i+1]),
                LineString(coords[i:])]
        if pd > distance:
            cp = line.interpolate(distance)
            return [
                LineString(coords[:i] + [(cp.x, cp.y)]),
                LineString([(cp.x, cp.y)] + coords[i:])]

def cut_piece(line,distance, lgth):
    """ From a linestring, this cuts a piece of length lgth at distance.
    Needs cut(line,distance) func from above"""
    precut = cut(line,distance)[1]
    result = cut(precut,lgth)[0]
    return result
def addpoint_toline(cut_p, p_end, p_nearest, line):
    if len(list(p_end.coords)[0]) == 3:
        #Caso de POINT Z
        p_end = Point(p_end.x, p_end.y)
    #Función para añadir punto en linea y poner como primer punto
    bite = LineString([p_end,p_nearest]) #Convertir punto en linea
    bite =bite.buffer(cut_p, cap_style=3)#PROBAR CREAR POLIGONO DE BITE
    bitering = LinearRing(list(bite.exterior.coords))
    union1 = line.union(bitering) #PROBAR unir
    result = [geom for geom in polygonize(union1)] #Añade elemento a linea
    max_value = result[0].length
    for parte in range(1,len(result)):
        value = result[parte].length #verificar que use la parte más grande
        if value > max_value: 
            ix = parte
        else:
            ix = 0
    points_l =  list(result[ix].exterior.coords) #Puntos de la geometria resultante
    l_next2 = LineString(points_l) #Linea con el punto necesario
    l_nexto = LinearRing(l_next2) #LineRing con el punto necesario
    #Revisar si es necesario reordenar
    if l_nexto.is_ccw  == True:
        l_next2.coords = list(l_next2.coords)[::-1] #debe ser False 
    return l_next2

def add_zvalue(linea,z):
    #Añadir Z
    puntos_curva = np.asarray(list(linea.coords))
    forma_alturas = (puntos_curva.shape[0], 1)
    altura_curva = np.full(forma_alturas, z)
    puntos_curva = np.append(puntos_curva, altura_curva, axis=1)
    line_cut = LineString(puntos_curva) #LineString Z
    return line_cut

def line_minimal(line_c,p_zero):
    #Obtener linea de dos puntos para simplificar linea pequeña
    #Crear una linea del punto inicial al extremo del rectangulo minimo 
    p_end = Point(list(line_c.coords[-1]))
    min_rectangle = MultiPoint(list(line_c.coords)).minimum_rotated_rectangle
    minxr, minyr, maxxr, maxyr = min_rectangle.bounds
    #para cada punto del rectangulo cual es la LS más larga
    min_rect = Point(minxr, (maxyr+minyr)/2)
    max_rect = Point(maxxr, (maxyr+minyr)/2)
    min_recty = Point((maxxr+minxr)/2, minyr)
    max_recty = Point((maxxr+minxr)/2, maxyr)
    list_options = [min_rect, max_rect, min_recty, max_recty]
    long_ =0 #variable inicial para comparar
    for pt in list_options:
        long_pt = p_end.distance(pt)
        if long_pt > long_:
            pt_extremo = pt
            long_ = long_pt
    pt_extremo = Point(pt_extremo.x,pt_extremo.y,p_end.z)
    line1 = LineString([pt_extremo, p_end,p_zero]) #LS Z final de pts relevantes  
    return line1

def point_minimal(line_c,p_zero):
    #Obtener linea de dos puntos para simplificar linea pequeña
    #Crear una linea del punto inicial al extremo del rectangulo minimo 
    p_end = Point(list(line_c.coords[-1]))
    min_rectangle = MultiPoint(list(line_c.coords)).minimum_rotated_rectangle
    minxr, minyr, maxxr, maxyr = min_rectangle.bounds
    #para cada punto del rectangulo cual es la LS más larga
    min_rect = Point(minxr, (maxyr+minyr)/2)
    max_rect = Point(maxxr, (maxyr+minyr)/2)
    min_recty = Point((maxxr+minxr)/2, minyr)
    max_recty = Point((maxxr+minxr)/2, maxyr)
    list_options = [min_rect, max_rect, min_recty, max_recty]
    long_ =0 #variable inicial para comparar
    for pt in list_options:
        long_pt = p_end.distance(pt)
        if long_pt > long_:
            pt_extremo = pt
            long_ = long_pt
    mp_point = MultiPoint([pt_extremo, p_end,p_zero])
    return mp_point

#OFFSET CONTINUO-FORMA DE ESPIRAL
def offset_spiral(points,polygon, s_poly, envelope,o,p,w, endpoint):
    big_lines,sub_line,unionls = offset_closed(points,polygon, s_poly, envelope,o,p,w, endpoint) #Llamar función offset
    area_weld =  math.pi* ((w/2)**2) #Área minima de soldadura
    
    #LINEAS EXTERNAS
    #Entrada:Lista de Linestrings
    #Salida: LineString   
    #Paso 1. Cortarlas (Input: Lista de LS)
    cut_lines = [] #lista de lineas cortadas
    if (len(big_lines))== 1 and (len(sub_line)) < 1:
        #Si solo hay una linea y no hay subpoligonos no se corta
        union_lines = big_lines
    #Para todos los demas caso se corta
    else:
        cut_value = w/3 #valor de corte para cada linea
        cut_p = p/6        
        for ls in range(len(big_lines)):            
            lineo0 = big_lines[ls] #LineString
            #Separar z y añadir al final
            l_2d = np.asarray(list(lineo0.coords))
            z_one = l_2d[0, 2]
            l_2d = l_2d[:, 0:2] #puntos coordenadas x, y
            lineo0 = LineString(l_2d)      
            o_length = lineo0.length #Longitud original de la linea 
            if o_length >= p: 
                #Los cortes son validos para lineas mas largas que p
                if ls == 0:
                    #Entra a line 0 para valor de referencia
                    line_cutted =  cut_piece(lineo0,0.0001, (o_length - cut_value)) 
                    p_end = Point(list(line_cutted.coords[-1])) #ultimo punto de la linea cortada 
                    #Corroborar ubicación del ultima linea 
                    tuple_end = (int(p_end.x), int(p_end.y))
                    #si son iguales se crea otro punto de partida 
                    if tuple_end == endpoint:
                        line_point = cut_piece(lineo0,0.0001, w) #Mover el punto de inicio
                        distance = line_point.length # distancia de pto cero a punto final 
                        line_first = cut_piece(lineo0,distance,lineo0.length-distance)
                        line_1 = list(line_first.coords)
                        line_2 = list(line_point.coords)
                        line_3 = line_1 + line_2
                        line_new = LineString(line_3) 
                        line_cut =  cut_piece(line_new,0.001, (o_length - cut_value))  
                    else:
                        line_cut = line_cutted
                    p_end = Point(list(line_cut.coords[-1])) #ultimo punto de la linea cortada 
                    line_cut = add_zvalue(line_cut,z_one) #Añadir Z
                    cut_lines.append(line_cut) #guardar en lista                      
                else:
                    #Valores de corte para ultima linea
                    if ls == len(big_lines)-1:
                        cut_value = w/8
                        cut_p = p/14
                    p_zero = nearest_points(p_end, lineo0)[1] #Pto más cercano de la siguiente linea
                    #Recortar linea
                    l_next2 = addpoint_toline(cut_p, p_end, p_zero, lineo0)    
                    line_sliced = cut_piece(l_next2,0.0001, (o_length - cut_value)) 
                    p_end = Point(list(line_sliced.coords[-1])) #ultimo punto de la linea cortada 
                    line_cut = add_zvalue(line_sliced,z_one) #Añadir Z
                    cut_lines.append(line_cut) #guardar en lista
            else:
                c_min = w/10 #CORTAR UN POCO P/EVITAR MULTIPLES ELEMENTOS
                line_cutted =  cut_piece(lineo0,0.001, (o_length - c_min))  
                line_cut = add_zvalue(line_cutted,z_one) #Añadir Z
                cut_lines.append(line_cut)
                #Caso de primera linea- sentido inverso 
                if ls == 0:
                    p_end = Point(list(lineo0.coords[-1]))
        #Paso 2. CREAR UNION ENTRE LINEAS 
        list_wunions = [] #lista de LS = LS+LS de union        #Se recibe lista de LS(+cortas) para crear una linea continua
        #Se añade punto final de la linea actual al punto inicial de la siguiente
        for lt in range(0,len(cut_lines)-1):
            line_c = cut_lines[lt] #linea actual
            line_next = cut_lines[lt+1] #linea siguiente
            p_zero = Point(list(line_next.coords[0]))
            if len(list(line_c.coords))>=3:
                convex_p= MultiPoint(list(line_c.coords)).convex_hull #Usar la del convexo por tema de figuras largas c/protuberancias
            else: 
                #menos de dos puntos no pueden formar un poligono
                convex_p = Polygon(line_c.buffer(w/2).exterior)#buffer de la linea, es un poco mayor que hacer pol
            # si es linea menor que P, lo mejor es modifcarla a una linea diagonal o aun punto en el centro
            if convex_p.area < area_weld:
                #Crear una linea del punto inicial al extremo del rectangulo minimo 
                line_line = line_minimal(line_c,p_zero) #linea + linea de union 
            else:            
                p_end = Point(list(line_c.coords[-1]))
                line_union = LineString([p_end, p_zero])
                #obtener ptos de linea o crear linestring de pto inicio y final de
                #LA MAYORIA DE ERRORES SE GENERAN ACA PORQUE NO SE PUEDE CREAR UNA LS
                try:
                    line_line = linemerge([line_c,line_union]) #LineString 
                except:
                    line_line = unary_union([line_c,line_union]) #LineString 
            list_wunions.append(line_line) #List of LineStrings
        #Paso 3. UNIR ELEMENTOS
        if len(list_wunions) >= 1:
            #SI list_wunions no tiene mas de 1 elemento,  no hay necesidad de formar MLS
            megamerge = MultiLineString(list_wunions) #ERROR porque no todos los elementos son MLS  
            if type(cut_lines[-1]) != LineString:
                last_line = cut_lines[-1][-1]
            else:
                last_line = cut_lines[-1]
            last_one = MultiLineString([last_line]) #Falta ultima curva
            union_lines = unary_union([megamerge,last_one]) #MLS de n LS
        else:
            union_lines = cut_lines[0]
            
    #VARIABLES A ENTREGAR: 1 MULTILINESTRING
    lines_polext = unary_union(union_lines) #MultiLineString de elementos exteriores
    #Variable para datos de DTPS
    if len(cut_lines) ==1:
        l_grande = unary_union(union_lines) #debe ser LS
    else:
        l_grande = linemerge(union_lines) #LineString unida de todas las externas
    
    #LINEAS INTERNAS : SUBPOLIGONOS
    #Entrada:Lista de MultiLinestrings
    #Salida: MultiLineString (n Linestrings de c/suboffset)  
    #Paso 1. CORTAR cada linea de subpoligono
    list_subpc = [] #Lista de listas con LS cortadas
    for sp in range(len(sub_line)):
        list_subls = [] #lista de n LS de c/subpoligono
        if sp == 0 and len(sub_line) == 1:
            #si solo es una linea y la primera no se corta
            line2= sub_line[sp][0] 
            list_subls.append(line2)
        if sp == 0 and len(sub_line[0]) == 1:
            #Si es primera linea y solo tiene un elemento tampoco se corta 
            line2= sub_line[sp][0] 
            list_subls.append(line2)
        else:
            #Entra a cada linea
            for ls in range(len(sub_line[sp])-1,-1,-1):
                sline0 = sub_line[sp][ls] #LineString
                #Separar z y añadir al final
                l_2d = np.asarray(list(sline0.coords))
                z_one = l_2d[0, 2]
                l_2d = l_2d[:, 0:2]
                sline0 = LineString(l_2d) 
                if (sline0.length) >= 3*p: 
                    cut_p = p/14
                    len_cut = sline0.length - (p/1.75) #longitud original-long de corte
                    if sp == (len(sub_line)-1):
                        #Se separa porque se busca mejor union con el elemento externo
                        if ls == len(sub_line[sp])-1:
                            #Primer elemento del subpoligono a unir
                            p_bigend = Point(list(l_grande.coords)[-1]) #punto final de la linea externa 
                            p_nearest = nearest_points(p_bigend, sline0)[1] #Buscar el punto más cercano en linea
                            l_next2 = addpoint_toline(cut_p, p_bigend, p_nearest, sline0)
                            line_cut = cut_piece(l_next2,0.0001, len_cut) 
                            p_previo = Point(list(line_cut.coords)[-1]) #ultimo punto de la linea cortada
                        else:
                            p_nearest = nearest_points(p_previo, sline0)[1] #Buscar el punto más cercano en linea
                            l_next2 = addpoint_toline(cut_p, p_previo, p_nearest, sline0)
                            line_cut = cut_piece(l_next2,0.0001, len_cut) 
                            p_previo = Point(list(line_cut.coords)[-1]) #ultimo punto de la linea cortada
                    else:
                        line_cut = cut_piece(sline0,0.0001, len_cut) 
                    if type(line_cut) == MultiLineString:
                        line_cut = line_cut[0]
                    line_cut = add_zvalue(line_cut,z_one) #Añadir Z
                    list_subls.insert(0,line_cut)#Si se recorre en sentido inverso, se guarda con insert
                else:
                    line_original = add_zvalue(sline0,z_one) #Añadir Z
                    list_subls.insert(0,line_original)#Si se recorre en sentido inverso, se guarda con insert
        list_subpc.append(list_subls) #lista de n subpoligonos con n LS
    # Paso 2. UNIR LS
    list_subl = [] #lista de n LS (lineas unida por c/subp)
    lista_allsubp = [] #lista de n MLS (TODOS los elementos de subpoligonos c/union para PLOT)
    list_firstp = [] #lista de puntos Inicio de cada elemento
    for lsp in range(len(list_subpc)):
        list_wunions_ueps = [] #lista de LS con union al siguiente
        #entra a cada subpoligono
        if len(list_subpc[lsp])>1:
            #Añadir punto inicial de la linea actual al punto final de la siguiente (Por recorrerse en orden inverso)
            for lt in range(0,len(list_subpc[lsp])-1):
                line_subp = list_subpc[lsp][lt] #linea actual
                line_next = list_subpc[lsp][lt+1] #linea siguiente
                if len(list(line_subp.coords))>=3:
                    pol_linea = Polygon(list(line_subp.coords))  #Convertir en polygono para sacar área
                    convex_p = MultiPoint(list(line_subp.coords)).convex_hull
                else: 
                    #menos de dos puntos no pueden formar un poligono
                    convex_p = Polygon(line_subp.buffer(w/2).exterior)#buffer de la linea, es un poco mayor que hacer pol
                if convex_p.area < area_weld:
                    pto_centro = pol_linea.centroid
                    p_zero = Point(list(line_next.coords[-1])) #pto final de la siguiente linea 
                    #solo es linea entre la siguiente y el punto centro 
                    line1 = LineString([pto_centro, p_zero]) 
                else:
                    p_nuevo = Point(list(line_subp.coords[0])) #Pto inicial de la linea actual
                    p_cero = Point(list(line_next.coords[-1])) #pto final de la siguiente linea
                    line_union = LineString([p_nuevo,p_cero ])    
                    #obtener ptos de linea o crear linestring de pto inicio y final de 
                    line1 = linemerge([line_subp,line_union]) #LineString
                if line1.crosses(line_next) == True: #Checar si la linea intersecta con la linea de union 
                    #SI CRUZA NO SE AÑADE
                    pass
                else:
                    list_wunions_ueps.append(line1) #Guardar variable, en orden normal    
            list_firstp.append(Point(list(list_subpc[lsp][-1].coords[0]))) #Guardar punto INICIAL de la ultima linea 
            last_one = list_subpc[lsp][-1] #Falta ultima curva
            list_wunions_ueps.append(last_one)
            megamerge = MultiLineString(list_wunions_ueps) #MLS de n LS, opción inversa            
            union_slines = linemerge(megamerge) #deberia ser LS para dtps 
            list_subl.append(union_slines)
        else:
            #solo 1 elemento
            p_end = Point(list(list_subpc[lsp][0].coords[0])) #Pto INICIAL de la linea actual  
            list_firstp.append(p_end) #guardar punto FINAL de cada linea
            union_slines = list_subpc[lsp][0] #LS unica
            list_wunions_ueps.append(union_slines)
            megamerge = MultiLineString(list_wunions_ueps) #se transforma a MLS
            list_subl.append(union_slines) #Añadir MLS
        lista_allsubp.append(megamerge) #lista de n MLS 
    #Paso 3. En caso de haber subpoligonos: CREAR UNIÓN de la ultima linea externa y la primera de un subpoligono más cercano
    if len(list_firstp) >=1:
        #A) Obtener punto de la primer linea (Adentro hacia afuera) de poligono externo
        if type(l_grande) == MultiLineString:
            first_exterior = Point(list(l_grande[0].coords[0])) #En caso de MLS-probar PRIMERO
        else:            
            first_exterior = Point(list(l_grande.coords[0]))
        #Buscar el punto más cercano de los subp
        for pte in range(len(list_firstp)):
            min_d = first_exterior.distance(list_firstp[pte]) #INVERSO UEPS
            if pte == 0:
                d_use = min_d
                p_use = list_firstp[pte]
                ix = 0
            else:
                if min_d < d_use:
                    d_use = min_d
                    p_use = list_firstp[pte]
                    ix = pte
        px = ix
        #B) Revisar a que elemento corresponde y eliminarlo de lista
        for ls1 in range(len(list_subl)): #lista de n LS            
            # for ls2 in range(len(list_subl[ls1])): #LS
            if list_subl[ls1].contains(p_use):
                px = ls1
            else:
                pass
        union_final=list_subl[px] #LS del poligono a unir
        del list_subl[px] #se elimina porque se unira con externo
        #C) Revisar tamaño de union final 
        if type(union_final) == LineString:
            spol = Polygon(list(union_final.coords))
            spol_area = spol.area
        else: 
            spol_area = area_weld
        if spol_area <area_weld:
            #Si es menor se seleccionan puntos relevantes para unión
            part_union = line_minimal(union_final,first_exterior)
            union_points = linemerge([part_union, l_grande])
            if type(union_points) != LineString:
                #ERROR (A veces no devuelve LS al unir con l_grande)
                mp_union = point_minimal(union_final,first_exterior) 
                mp_gde = MultiPoint(list(l_grande.coords))
                union_points = unary_union([mp_union, mp_gde]) #MultiPoint
                union_points = LineString(union_points)     
            union_s = union_points #LS de externo c/interno
            #Se actualiza lista p/PLOT
            del lista_allsubp[px] #Se elimina el ultimo elemento 
            if type(lista_allsubp) == LineString:               
                lista_allsubp = [lista_allsubp]                
        else:
            part_union = LineString([p_use,first_exterior]) #unión entre contorno interno a externo
            # si la linea intersecta se corta un pedazo
            if union_final.crosses(part_union) == True: 
                #Checar si la linea intersecta con la linea de union 
                try:
                    intersect_ = union_final.intersection(part_union)[1] #Checar si la linea intersecta con la linea de union 
                    extra_cut = Point(list(union_final.coords)[0]).distance(intersect_) #distancia de pto final a intersección
                    union_final2D = np.asarray(list(union_final.coords))
                    z_one = union_final2D[0, 2]
                    l_2d = union_final2D[:, 0:2]
                    union_final = LineString(l_2d)
                    d_cut = extra_cut+ 0.5  #Definir distancia a cortar, aproximado distancia
                    len_cut = union_final.length - d_cut #longitud original-long de corte
                    line_cut = cut_piece(union_final,d_cut, len_cut)
                    union_final = add_zvalue(line_cut, z_one)
                except:
                    pass            
            mp_final = MultiPoint(list(union_final.coords))
            if mp_final[0] == p_use:
                union_final = LineString(list(union_final.coords)[::-1])
            arr_final = np.array(union_final)
            arr_union = np.array(part_union)
            arr_grande = np.array(l_grande)
            union_np = np.concatenate([arr_final, arr_union, arr_grande])
            union_s = LineString(union_np)
        lista_allsubp.append(part_union) #añadir elemento de unión p/PLOTEO
        list_subl.append(union_s) #si se añade al final empieza la soldadura de adentro hacia afuera
    else:
        #Solo elemento externo
        if type(l_grande) == LineString:
            list_subl = [l_grande]
        else:
            list_subl=l_grande
            
    #Paso 4. Variables a entregar
    unionls = list_subl
    if type(unionls) != MultiLineString:
        unionls = MultiLineString(unionls) #Crea MLS para traductor
    if type(lines_polext) == LineString:
        lines_polext = MultiLineString([lines_polext]) #Crea MLS para traductor
    return lines_polext, lista_allsubp, unionls