# -*- coding: utf-8 -*-
"""
Versión 1
FUNCIÓN: 
        Seleccionar puntos relevantes de cada linea de trayectoria

CONTENIDO:
        * Diferencia de selección entre tipos de pieza
            *Clasificación de puntos por ángulo
            *Selección de puntos por filtros
            *Adición de puntos para disminución de velocidad 
"""
#Librerias externas
import pandas as pd
import numpy as np
from shapely.ops import split, unary_union, nearest_points
from shapely.geometry import Point, MultiPoint, Polygon, LineString
#Librerias internas
from path_generation.concavity import  find_concave_vertices,find_convex_vertices


def seleccion_puntos(points, y, type_piece):
    #RECIBE:
        #points: Lista de Puntos(x,y,z) de una linea de trayectoria
        #y: variable del eje externo
    #DEBE ENTREGAR:
        #arr_puntos: Array de todos los puntos a usar en la simulación
        #amount_concaves: Cantidad de puntos concávos que me dice que movimiento será
        #pose_l: Lista de posiciones de puntos que se repiten para terminar un MOVEC y aplicar MOVEL
        #pts_curvos: Lista de puntos a los que se les debe disminuir la velocidad
    if len(points) <= 15:
        #Se usan todos los puntos 
        arr_puntos = points
        amount_concaves = 0
        pose_l = []
        pts_curvos = []    
    else:
        point_collection_z = MultiPoint(points) 
        line_original_z = LineString(point_collection_z)
        z_one = points[0, 2]    #Guardar Z
        points = points[:, 0:2] #Points 2D        
        point_collection = MultiPoint(points)
        polygon = Polygon(point_collection)  #Declaración de Poligono
        area = polygon.area #Área del poligono
        line_original = LineString(point_collection)  #Crear LS de todos los puntos originales

        if type_piece != 0:
            #Solo para cilindros y conos sse buscan más puntos? 
            #PASO 1.- SELECCIONAR FILTROS
            angle_x, angle_v, d_filter, d_filter_cv, angle_value_cx, \
                angle_value_cv, d_min, cut_d, d_separation = valores_filtros(area)
            #PASO 2.- CLASIFICAR PUNTOS 
            p_convexos, p_concavos, convex_df, concave_df = \
                clasificacion(polygon, angle_x, angle_v)            
            #PASO 3.- SELECCIONAR PUNTOS RELEVANTES DE TRAYECTORIA
            convex_filter, concav_filter, a_concav = \
                aplicacion_filtros(p_convexos, p_concavos, d_filter, angle_value_cx, \
                                   angle_value_cv, d_filter_cv, d_min,convex_df, concave_df)
            #PASO 4.- DEFINIR QUE TIPO DE MOVIMIENTO SE USARÁ
            amount_concaves, list_repeat = tipo_movimiento(polygon, a_concav, convex_filter)  
            amount_concaves = 10 #impone MOVEC
            #PASO 5.- SELECCIONAR PUNTOS PARA BAJAR VELOCIDAD
            lista_curvos, df_total_original = puntos_lentos(concav_filter, convex_filter, line_original)            
            #PASO 6.- AÑADIR PUNTOS A LA MITAD PARA ASEGURAR ROTACIÓN
            pts_extras, pose_l = añadir_medios(point_collection_z, df_total_original, line_original_z)
            #PASO 7.- GUARDAR PUNTOS 
            arr_puntos, pts_curvos = guardar_pz(point_collection_z, \
                                                        amount_concaves,pts_extras, \
                                                            lista_curvos,list_repeat,df_total_original )
            
        else:
            #PASO 1.- SELECCIONAR FILTROS
            angle_x, angle_v, d_filter, d_filter_cv, angle_value_cx, \
                angle_value_cv, d_min, cut_d, d_separation = valores_filtros(area)
            #PASO 2.- CLASIFICAR PUNTOS 
            p_convexos, p_concavos, convex_df, concave_df = \
                clasificacion(polygon, angle_x, angle_v)            
            #PASO 3.- SELECCIONAR PUNTOS RELEVANTES DE TRAYECTORIA
            convex_filter, concav_filter, a_concav = \
                aplicacion_filtros(p_convexos, p_concavos, d_filter, angle_value_cx, \
                                    angle_value_cv, d_filter_cv, d_min,convex_df, concave_df)            
            #PASO 4.- DEFINIR QUE TIPO DE MOVIMIENTO SE USARÁ
            amount_concaves, list_repeat = tipo_movimiento(polygon, a_concav, convex_filter)  
            #PASO 5.- SELECCIONAR PUNTOS PARA BAJAR VELOCIDAD
            lista_curvos, df_total_original = puntos_lentos(concav_filter, convex_filter, line_original)            
            
            #PASO 6.- ADICIONAR PUNTOS PARA RETOMAR VELOCIDAD 
            before_clean, after_clean, dic_lines_b, dic_lines_a = añadir_puntos(lista_curvos, line_original, cut_d, d_separation)            
            #PASO 7.- GUARDAR PUNTOS 
            arr_puntos, pts_curvos, pose_l = guardar_puntos(point_collection,amount_concaves, \
                                                            df_total_original, before_clean, after_clean, dic_lines_b, dic_lines_a, \
                                                                lista_curvos, list_repeat, z_one)
                
            
    return arr_puntos, amount_concaves, pose_l, pts_curvos
        
            
def valores_filtros(area):
    # ENTREGA VALORES DE FILTROS CON BASE EN EL ÁREA
    if area < 1100:
        angle_x = 18  
        angle_v = 6.5
        d_filter = 1.5  # 3 #distancia entre puntos a filtrar,  ¿relacionado con p ?
        d_filter_cv = d_filter
        # 12 #15 #45#60 #valor del ángulo de puntos  concavos que no se eliminan
        angle_value_cx = 12
        angle_value_cv = 0.5
        d_min = 1.1  #distancia minima, depende del detalle en la falla
        cut_d = 0.5  #Buscar punto a tal distancia
        d_separation = 10
        if area < 500:
            d_filter_cv = 0.4  # 3 #distancia entre puntos a filtrar,  ¿relacionado con p ?
            d_min = 1.5  # distancia minima, depende del detalle en la falla
            cut_d = 0.4  #Buscar punto a tal distancia
    elif area >= 1100 and area <= 3000:
        angle_x = 20  # 8.5#45# 60
        angle_v = 15
        d_filter = 2.8  # distancia entre puntos a filtrar,  ¿relacionado con p ?
        d_filter_cv = d_filter
        angle_value_cx = 12
        angle_value_cv = 0.5
        d_min = 3.2  # distancia minima, depende del detalle en la falla
        cut_d = 0.5  # 2.5 #Buscar punto a tal distancia
        d_separation = 6
    else:
        angle_x = 70  # 60
        angle_v = 60
        d_filter = 3  # 3 #distancia entre puntos a filtrar,  ¿relacionado con p ?
        d_filter_cv = d_filter
        angle_value_cx = 12  # 15 #45#60 #valor del ángulo de puntos  concavos que no se eliminan
        angle_value_cv = 8
        d_min = 4  # 3.5 #1.5 #distancia minima, depende del detalle en la falla
        cut_d = 2  # 2.5 #Buscar punto a tal distancia
        d_separation = 6
    return angle_x, angle_v, d_filter, d_filter_cv, angle_value_cx, angle_value_cv, d_min, cut_d, d_separation

def clasificacion(polygon, angle_x, angle_v):
    #ENTREGA DATAFRAME DE PUNTOS CONCAVOS Y CONVEXOS
    p_convexos = find_convex_vertices(polygon, 0, filter_type='all')
    p_concavos = find_concave_vertices(polygon, 0, filter_type='all')
    #ADICIONAL---> IDENTIFICAR PUNTOS QUE NO DEBEN FALTAR
    convex_df = p_convexos[p_convexos['angle']
                             > angle_x]  # lista de pts obligados
    convex_df = convex_df.reset_index(drop=True)
    concave_df = p_concavos[p_concavos['angle']
                              > angle_v]  # lista de pts obligados
    concave_df = concave_df.reset_index(drop=True)
    return p_convexos, p_concavos, convex_df, concave_df

def aplicacion_filtros(p_convexos, p_concavos, d_filter, angle_value_cx,angle_value_cv, d_filter_cv, d_min,convex_df, concave_df):
    #ENTREGA DF FINAL DE PUNTOS A USAR 
    #A) DISCRIMINAR POR DISTANCIA ACUMULADA, (pero aceptan aquellos con ángulo superior a filtro)
    # CONVEXOS
    cum_d = 0  # Suma acumulativa de distancia
    index_ = []  # lista de puntos s añadir
    pts_convex = p_convexos['geometry'].to_list()  # extraer puntos
    if len(pts_convex) == 0:
        for ptc in range(1, len(pts_convex)):
            longt = pts_convex[ptc-1].distance(pts_convex[ptc])
            cum_d += longt
            if cum_d >= d_filter:
                index_.append(ptc)
                cum_d = 0
    else:
        ang_convex = p_convexos['angle'].to_list()
        pts_convex.append(pts_convex[-1])
        ang_convex.append(ang_convex[-1])
        for ptc in range(1, len(pts_convex)-1):
            longt = pts_convex[ptc-1].distance(pts_convex[ptc])
            cum_d += longt
            if cum_d >= d_filter:
                # si el que sigue es de 90 no se añade
                if ang_convex[ptc+1] >= angle_value_cx:
                    index_.append(ptc+1)
                else:
                    index_.append(ptc)
                cum_d = 0
    index_.insert(0, 0)
    # CÓNCAVOS
    index_2 = []  # lista de puntos s añadir
    cum_d = 0
    pts_concav = p_concavos['geometry'].to_list()  # extraer puntos
    if len(pts_concav) == 0:
        for ptc in range(1, len(pts_concav)):
            longt = pts_concav[ptc-1].distance(pts_concav[ptc])
            cum_d += longt
            if cum_d >= d_filter_cv:
                index_2.append(ptc)
                cum_d = 0
    else:
        ang_concav = p_concavos['angle'].to_list()
        pts_concav.append(pts_concav[-1])
        ang_concav.append(ang_concav[-1])
        for ptc in range(1, len(pts_concav)-1):
            longt = pts_concav[ptc-1].distance(pts_concav[ptc])
            cum_d += longt
            if cum_d >= d_filter_cv:
                # si el que sigue es de 90 no se añade
                if ang_concav[ptc+1] >= angle_value_cv:
                    index_2.append(ptc+1)
                else:
                    index_2.append(ptc)
            cum_d = 0

    index_2.insert(0, 0)
    # FILTER BY CUM DISTANCE
    convex_filter_1 = p_convexos[p_convexos.index.isin(index_)]
    concav_filter_1 = p_concavos[p_concavos.index.isin(index_2)]
    
    #B) VERIFICACION DE PUNTOS, ELIMINAR LOS PUNTOS CERCANOS A OTROS 
    # CONVEXOS
    distances = []  # lista para calcular valores de distancia
    pts_convex = convex_filter_1['geometry'].to_list()  # extraer puntos
    for ptc in range(0, len(pts_convex)-1):
        longt = pts_convex[ptc-1].distance(pts_convex[ptc])
        distances.append(longt)  # guardar distancia
    distances.insert(0, 100)  # valor del primero aleatorio
    convex_filter_1['distance'] = distances  # añadir columna dataframe de distancia pto anterior
    convex_filter_2 = convex_filter_1[convex_filter_1['distance'] > d_min] # filtrar
    
    # CÓNCAVOS
    distances = []  # lista para calcular valores de distancia
    pts_concav = concav_filter_1['geometry'].to_list()  # extraer puntos
    for ptc in range(0, len(pts_concav)-1):
        longt = pts_concav[ptc].distance(pts_concav[ptc+1])
        distances.append(longt)  # guardar distancia
    distances.insert(0, 100)  # valor del primero aleatorio    
    concav_filter_1['distance'] = distances # añadir columna dataframe de distancia pto anterior    
    concav_filter_2 = concav_filter_1[concav_filter_1['distance'] > d_min] # filtrar
    
    #C) FILTRAR PUNTOS CUYO ÁNGULO NO ES RELEVANTE
    #C.1 IDENTIFICAR TIPO DE GEOMETRIA POR RAZÓN ENTRE PUNTOS
    #Si es cerca de 1 es más regular
    razon = len(convex_filter_1)/len(concav_filter_2)    
    # formas concavas no conviene reducir el ángulo mucho, se pierden detalles
    if razon > 1.5:
        a_min = 1.2  #Valor del ángulo a filtrar
        a_concav = 2  # 10 #filtro de ángulos cóncavos
    else:
        a_min = 0.2        
        a_concav = 1.5
    #Filtrar
    concav_filter_3 = concav_filter_2[concav_filter_2['angle'] > a_min]
    convex_filter_3 = convex_filter_2[convex_filter_2['angle'] > a_min]
    
    #D) CORROBORAR QUE ESTEN LOS PUNTOS MÁS IMPORTANTES
    pts_set_cx = convex_df['geometry'].to_list()
    pts_0 = convex_filter_3['geometry'].to_list()
    n_ = [] #Lista de indices de puntos a añadir
    for row in range(len(pts_set_cx)):
        state = pts_set_cx[row] in pts_0
        if state == False:
            n_.append(row)  # se añade index en caso de no estar
    convex_required = convex_df[convex_df.index.isin(n_)]
    pts_set_cv = concave_df['geometry'].to_list()
    pts_c = concav_filter_3['geometry'].to_list()
    n_ = []
    for row in range(len(pts_set_cv)):
        state = pts_set_cv[row] in pts_c
        if state == False:
            n_.append(row)  # se añade index en caso de no estar
    concav_required = concave_df[concave_df.index.isin(n_)]
    #Añadir los que no esten
    concav_filter = pd.concat([concav_filter_3, concav_required]).drop_duplicates(keep=False)
    convex_filter = pd.concat([convex_filter_3, convex_required]).drop_duplicates(keep=False)
    
    return convex_filter, concav_filter, a_concav

def tipo_movimiento(polygon, a_concav, convex_filter):
    #DEFINE EL TIPO DE MOVIMIENTO Y LISTA DE PUNTOS EN CASO DE MOVEC
    #A) Encontrar cóncavos suavizando ángulo
    concave_move = find_concave_vertices(polygon, 0, filter_type='peak', convolve=True)    
    concave_move = concave_move[concave_move['angle'] > a_concav] # filtrar
    amount_concaves = len(concave_move)
    # PASO 2b.-  Filtrar ángulo, identificar relevantes
    a_move = 10
    list_repeat = [] #Lista de puntos para repetir y evitar problemas con MOVEC
    convex_move = convex_filter[convex_filter['angle'] > a_move]  # filtrar
    convex_perfect = convex_filter.query('angle > 89.9')  # puntos forzosos con MOVEL
    if len(convex_perfect) > 4:
        # es MOVEL
        amount_concaves = 0  # Se entiende que tiene varios ángulos rectos
    if amount_concaves >= 6:
        # es MOVEC
        # Repetir estos puntos para evitar arcos
        convex_df3 = convex_move.query('angle > 12')
        list_repeat = convex_df3.iloc[:, 0].to_numpy().tolist()
    return amount_concaves, list_repeat

def puntos_lentos(concav_filter, convex_filter, line_original):
    #SELECCIONAR LOS PUNTOS QUE TENDRAN VELOCIDAD MÁS BAJA
    #A) UNIR PUNTOS
    df_total_original = pd.concat([concav_filter, convex_filter], ignore_index=True)  #DF de todos los puntos
    df_total = pd.concat([concav_filter, convex_filter],ignore_index=True)  # union
    lista_total = df_total['geometry'].to_list() #Lista de puntos total
    #B) ORDENAR LISTA DE PUNTOS
    # Calcular lista de distancias de cada punto  
    longitudes_cero = [] #Lista de longitudes del primer punto al punto seleccionado
    between = []  #lista de distancias entre dos puntos consecutivos
    if len(lista_total) < 500:
        for i in range(0, len(lista_total)):
            split_line = split(line_original, lista_total[i])
            if len(split_line) == 2:
                split_line = split_line[1]
            else:
                split_line = split_line[0]
            long_split = split_line.length  # line_original.length - split_line.length
            longitudes_cero.append(long_split)
        df_total['beyond'] = longitudes_cero  # añadir columna dataframe
        # ordenar de acuerdo a distancia del pto inicial de LS
        df_total = df_total.sort_values('beyond')
        longitudes_cero = df_total['beyond'].to_list()  # valores coordenados
        #CALCULAR LA DISTANCIA ENTRE PUNTOS Y AQUI ELIMINAR A LOS QUE ESTEN MUY JUNTOS
        for i in range(0, len(longitudes_cero)-1):
            # Distancia entre el punto actual y el siguiente
            between_ = longitudes_cero[i+1] - longitudes_cero[i]
            between.append(between_)        
        between.append(100) # Se inserta  un valor impuesto de 100 en el ultimo  valor
        df_total['between'] = between  # añadir valores de distancia
        df_total = df_total.reset_index(drop=True)  # reset index values        
        angle_curves =15
    else:
        #OPCIÓN ALTERNA: ENTRE MÁS PUNTOS SE VUELVE LENTO EL CÁLCULO DE IF 
        point_cero = Point(list(line_original.coords[0])) # Primer punto de linea original
        for pto in lista_total:
            distance_1 = point_cero.hausdorff_distance(pto)
            longitudes_cero.append(distance_1)
        df_total['beyond'] = longitudes_cero  # añadir columna dataframe
        # ordenar de acuerdo a distancia del pto inicial de LS
        df_total = df_total.sort_values('beyond')
        longitudes_cero = df_total['beyond'].to_list()  # valores coordenados
        # EXTRA CALCULAR LA DISTANCIA ENTRE PUNTOS Y AQUI ELIMINAR A LOS QUE ESTEN MUY JUNTOS Y NO
        for i in range(0, len(longitudes_cero)-1):
            # Distancia entre el punto actual y el siguiente
            between_ = longitudes_cero[i+1] - longitudes_cero[i]
            between.append(between_)
        # Se inserta  un valor impuesto de 100 en el ultimo  valor
        between.append(100)
        df_total['between'] = between  # añadir valores de distancia
        df_total = df_total.reset_index(drop=True)  # reset index values
        angle_curves = 80        
        
    # B) FILTRAR PUNTOS 
    filtered_values = np.where((df_total['between'] <= 2) & (df_total['angle'] < 15)) #Filtro
    df_total_1 = df_total.drop(df_total.index[filtered_values]) 
    df_final = df_total_1.query('angle >'+str(angle_curves))  # filtro por ángulo 
    lista_curvos = df_final['geometry'].to_list()# lista de puntos
    
    del(df_total_original['distance'])
    return lista_curvos, df_total_original

def añadir_puntos(lista_curvos, line_original, cut_d, d_separation):
    #AÑADE LOS PUNTOS NECESARIOS PARA RETOMAR VELOCIDAD ANTES Y DESPUÉS
    #A) CREAR DATAFRAMES para revisar distancia entre puntos
    dic_lines_b = {}  # Diccionario punto real : punto a añadir -BEFORE
    dic_lines_a = {}  # Diccionario punto real : punto a añadir -AFTER
    df_before = pd.DataFrame(columns=['geometry', 'before', 'separation', 'beyond'])
    df_before['geometry'] = lista_curvos
    df_after = pd.DataFrame(columns=['geometry', 'after', 'separation2', 'beyond'])
    df_after['geometry'] = lista_curvos
    
    #B) BUSCAR PUNTOS
    for i in range(len(lista_curvos)):        
        tuple_c = (lista_curvos[i].x, lista_curvos[i].y) # Guardar valor como tuple
        # 1.- Cortar linea en punto p, el punto cero de split_line debe ser el mismo de tuple_c        
        split_line = split(line_original, lista_curvos[i]) #split line a certain point, [1] es LS del punto
        if len(split_line) == 2:
            split_line = split_line[1]
        else:
            split_line = split_line[0]

        # 2.-Buscar punto a una distancia "cut_d", ANTES de cada arr_cuve[i]
        # Longitud de la linea original- long a punto - cut_d
        long_split = line_original.length - split_line.length - cut_d
        if long_split > 0:
            # Si la longitud es 0 o menos se omite añadir punto
            # Genera nueva LS, cortando a distancia long_split
            line_cutted_2 = cut_piece(line_original, 0.00001, long_split)
            p_extra2 = Point(list(line_cutted_2.coords)[-1]) #Obtener último punto            
            dic_lines_b[tuple_c] = p_extra2                  #Guardar valores como diccionario            
            df_before.iloc[i, 1] = p_extra2                  #Dataframe de puntos anteriores            
            df_before.iloc[i, 2] = split_line.length - cut_d #Valor aproximado de ubicación en linea
            
        # 3.- Buscar punto a una distancia "cut_d", DESPUÉS de cada arr_cuve[i]
        # Genera nueva LS, cortando a distancia cut_d
        line_cutted = cut_piece(split_line, 0.00001, cut_d)        
        p_extra = Point(list(line_cutted.coords)[-1])   #Obtener último punto
        dic_lines_a[tuple_c] = p_extra                  #Guardar valores como diccionario
        df_after.iloc[i, 1] = p_extra                   #Dataframe de puntos posteriores
        df_after.iloc[i, 2] = split_line.length + cut_d #Valor aproximado de ubicación en linea

    #C) ELIMINAR AQUELLOS PUNTOS QUE NO ESTEN TAN DISTANCIADOS
    #C.1 Calcular distancia entre punto ANTERIOR a añadir y el punto anterior
    # Sacar elementos a usar
    list_poriginal = df_before['geometry'].to_list()
    list_pbefore = df_before['before'].to_list()
    list_separation = []  # Guardar valores de distancia
    for pb in range(1, len(list_poriginal)):
        if type(list_pbefore[pb]) == Point:
            separation_ = list_pbefore[pb].distance(list_poriginal[pb-1])
        else:
            separation_ = 100  # si no hay punto se añade 100, para no eliminarlo
        list_separation.append(separation_)
    # Se inserta  un valor impuesto de 100 en el primer valor
    list_separation.insert(0, 100)
    df_before['separation'] = list_separation  # Añadir a dataframe
    
    #C.2 Filtrar valores
    before_clean = df_before[df_before['separation'] > d_separation]
    # Quitar filas con valores nulos
    before_clean = before_clean[before_clean['before'].notnull()]    
    #Crear diccionario, Tuple pto original: <Point> de punto añadir
    d = {}  # diccionario nuevo
    for i, j in zip(before_clean.geometry, before_clean.before):
        tuple_c = (i.x, i.y)  # Guardar valor como tuple
        d[tuple_c] = j
    dic_lines_b = d

    #C.3 Calcular distancia entre puntos de lista list_pcurve
    list_distancias = []  # Lista de distancias entre puntos a añadir
    lista2 = []
    list_pafter = df_after['after'].to_list()
    for pb in range(0, len(lista_curvos)-1):
        distancia_ = lista_curvos[pb].distance(lista_curvos[pb+1])
        list_distancias.append(distancia_)
    for pb in range(0, len(lista_curvos)-1):
        distancia_ = lista_curvos[pb].distance(list_pafter[pb+1])
        lista2.append(distancia_)
    # Se inserta  un valor impuesto de 100 en el primer valor
    list_distancias.insert(0, 100)
    lista2.insert(0, 100)
    df_after['separation2'] = list_distancias  # Añadir a dataframe

    #C.4 Filtrar valores
    after_clean = df_after[df_after['separation2'] > d_separation]
    # Quitar filas con valores nulos
    after_clean = after_clean[after_clean['after'].notnull()]
    #Crear diccionario, Tuple pto original: <Point> de punto añadir
    d = {}  # diccionario nuevo
    for i, j in zip(after_clean.geometry, after_clean.after):
        tuple_c = (i.x, i.y)  # Guardar valor como tuple
        d[tuple_c] = j
    dic_lines_a = d
    return before_clean, after_clean, dic_lines_b, dic_lines_a

def cut(line, distance):
    #FunciÃ³n para cortar una linea a una distancia deseada desde el punto 0
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

def guardar_puntos(point_collection,amount_concaves, df_total_original, before_clean, after_clean,dic_lines_b, dic_lines_a, lista_curvos, list_repeat, z_one):
    #GUARDAR PUNTOS EN ORDEN Y CON VALOR Z
    #A) UNIR TODOS LOS PUNTOS 
    list_points = df_total_original['geometry'].to_list()
    list_before = before_clean['before'].to_list()
    list_after = after_clean['after'].to_list()
    #Lista de pts concavos +convexos +adicioneles(antes, después)
    l_union = list_points + list_before + list_after
    
    #B) ORDENAR PUNTOS, con base en la lista original 
    l_puntos = []  #Lista p/añadir puntos en orden de aparición
    pose_l = []    #Lista p/guardar posiciones con MOVEL
    foundp = 0     #Contador de c/3 puntos
    preal = 0
    # GUARDAR puntos a usar, porque hasta el momento no estan en orden
    for pto in range(len(point_collection)):
        if point_collection[pto] in l_union:
            # AÑADIR puntos antes del actual
            if point_collection[pto] in lista_curvos:
                tuple_pto = (point_collection[pto].x, point_collection[pto].y)
                for key, value in dic_lines_b.items():
                    if tuple_pto == key:
                        l_puntos.append(value) #añade punto anterior de velocidad
            l_puntos.append(point_collection[pto])  # Añadir punto actual
            # AÑADIR puntos después del actual
            if point_collection[pto] in lista_curvos:
                #Si la ubicación del punto es de las ultimas ya no se agrega
                if pto < len(point_collection)-3:
                    # si hay punto curvo se añade su key de diccionario
                    tuple_pto = (point_collection[pto].x, point_collection[pto].y)
                    for key, value in dic_lines_a.items():
                        if tuple_pto == key:
                            l_puntos.append(value)
            foundp += 1
            preal += 1
            # Si es MOVEC repetir angle
            if amount_concaves >= 6 and len(list_repeat) >= 1:
                if point_collection[pto] in list_repeat:
                    pose_l.append(preal-1)
                    pose_l.append(preal)
            if amount_concaves >= 6 and foundp % 3 == 0:
                # Tercer punto de un elemento concavo se repite
                l_puntos.append(point_collection[pto])
                preal += 1
                
    #C) AÑADIR Z 
    xs = [point.x for point in l_puntos]
    ys = [point.y for point in l_puntos]
    zs = [z_one]*len(xs)
    arr_puntos = np.column_stack((xs, ys, zs))
    
    xp = [point.x for point in lista_curvos]
    yp = [point.y for point in lista_curvos]
    zp = [z_one]*len(xp)
    pts_curvos = np.column_stack((xp, yp, zp))
    pts_curvos = pts_curvos.tolist()    
    return arr_puntos, pts_curvos, pose_l


def añadir_medios(pointsz, df_total_original, line_original):
    #SE AÑADEN PUNTOS ADICIONALES PARA CASO DE CONOS/CILINDROS PARA INFORMACIÓN DE CURVAS
    minx, miny, maxx, maxy = pointsz.bounds
    #Revisar cantidad de divisiones necesarias 
    cuts_y = 7
    cuts_x = 7
   
    #AÑADIR PUNTOS DE INTERSECCIONES EQUIDISTANTES
    separaciones_x = np.linspace(minx, maxx, cuts_x)[1:cuts_x-1]
    separaciones_y = np.linspace(miny, maxy, cuts_y)[1:cuts_y-1]
    
    #HACER BUSQUEDA CON SEPARACIONES Y
    cross_pointsy =[] #lista de multipoints= ?
    for ly in range(len(separaciones_y)):
        linex = LineString([(minx, separaciones_y[ly]), (maxx, separaciones_y[ly] )])
        c_points = line_original.intersection(linex) 
        cross_pointsy.append(c_points)
    cross_pointsy = unary_union(cross_pointsy)

    #Crear interseccioncon cada linea
    cross_pointsx =[] #lista de multipoints
    for lx in range(len(separaciones_x)):
        linex = LineString([(separaciones_x[lx], miny), (separaciones_x[lx], maxy)])
        c_points = line_original.intersection(linex) 
        cross_pointsx.append(c_points)    
                                                   
    cross_pointsx = unary_union(cross_pointsx)
    union_points = unary_union([cross_pointsx, cross_pointsy])
    pts_extras,arrpose = obtener_puntos(pointsz, union_points,df_total_original, line_original) #en desordenn, puntos finales no se pueden ordenar    
    return pts_extras, arrpose

def obtener_puntos(pointsz, cpoints, df_total_original, line_original):
    #ORDENAR PUNTOS CON BASE EN LONGITUD 
    l_points_2d = df_total_original['geometry'].to_list()
    list_points = find_z(pointsz, l_points_2d) #AÑADIR Z, existen en lista 
    pts_ordenados = []
    #1 ORDENAR
    for i in range(len(pointsz)): 
        if pointsz[i] in list_points:
            pts_ordenados.append(pointsz[i])
    arrpose = []  # lista p/guardar posiciones con MOVEL
    preal = -1
    #2 BUSCAR LA UBICACIÓN DE CADA PUNTO
    pts_finales = [] #lisra de todos los puntos a usar
    for p in range(len(pts_ordenados)-1):
        split_line = split(line_original, pts_ordenados[p])[-1]#la ultima corresponde al punto deseado al final
        #SEGUNDA DIVISION CON EL SIGUIENTE PUNTO         
        split_second = split(split_line, pts_ordenados[p+1])[0] #LS 2D la primera es entre primer punto y segundo 
        split_second_buffer = split_second.buffer(0.2) #polygon
        pts_finales.append(pts_ordenados[p])
        preal += 1
        arrpose.append(preal)
        #obtener primer y ultimo punto para saber como es la diferencia
        p_inicio = Point(list(split_second.coords)[0])
        p_final = Point(list(split_second.coords)[-1])
        dif_x = p_inicio.x- p_final.x
        dif_y = p_inicio.y - p_final.y   
        #BUSCAR SI EN ESA LINEA TOCA ALGUN PUNTO DE MPOINTS
        list_pts = [] #lista de puntos que tocan, sin ordenar
        for n in range(len(cpoints)):
            if split_second_buffer.contains(cpoints[n]):
                pointspp = MultiPoint(list(split_second.coords))
                near_p = nearest_points(cpoints[n], pointspp)
                pto_z = [near_p[-1]]
                pto_z = find_z(pointsz, pto_z)
                z_value = pto_z[0].z
                #añadir el valor de Z  que corresponda
                pextra_z= Point(near_p[-1].x,near_p[-1].y,z_value)
                list_pts.append(np.array(pextra_z))
        if len(list_pts) > 1:
            #Solo si existieron puntos se realiza lo sig.
            if abs(dif_x) < 5:
                if dif_y > 0:
                    #y decrece, va de más a menos
                    list_pts = sorted(list_pts, key=lambda x: -x[1])
                else:
                    #y aumenta, va de menos a más
                    list_pts = sorted(list_pts, key=lambda x: x[1])
            else:
                #x es el que cambia
                if dif_x > 0:
                    list_pts = sorted(list_pts, key=lambda x: -x[0])
                else:
                    #x aumenta, va de menos a mas
                    list_pts = sorted(list_pts, key=lambda x: x[0])
            for arr in range(len(list_pts)):            
                pto_p = Point(list_pts[arr]) #Transformar a punto
                pts_finales.append(pto_p) #añadir
                preal += 1
    return pts_finales, arrpose

   
def find_z(points, pts):
    #para puntos que si existen originalmente
    coords3d = [] #lista de puntos c/coordenada Z
    for p in range(len(pts)):
        d_start = 100
        for o in range(len(points)):
            distance_c = points[o].distance(pts[p])
            #Buscar el punto más cercano 
            if distance_c < d_start:
                d_start = distance_c
                index_l = o
        z_use = points[index_l].z #Sacar z
        p_c = Point(pts[p].x,pts[p].y, z_use) #Añadir z
        coords3d.append(p_c)
    return coords3d

def guardar_puntos_z(point_collection_z, amount_concaves, df_total_original,list_points_extra, lista_curvos,list_repeat):
    #PREPARAR PUNTOS
    l_points_2d = df_total_original['geometry'].to_list()
    list_points = find_z(point_collection_z, l_points_2d) #AÑADIR Z, existen en lista 
    # print("1er curvo", lista_curvos[0])
    lista_curvos = find_z(point_collection_z, lista_curvos) #AÑADIR Z, existen en lista 
    # print("Despues curvo", lista_curvos[0])
    if len(list_repeat) > 1:
        list_repeat = find_z(point_collection_z, list_repeat) #AÑADIR Z, existen en lista 
        # print("1er repeat", (list_repeat[0]))
    # Lista de pts concavos +adicionales
    arr_union = list_points +list_points_extra# + list_before + list_after 
    # print("len union", len(arr_union))              
    arrp = []  # Lista p/añadir puntos en orden de aparición
    arrpose = []  # lista p/guardar posiciones con MOVEL
    # Para order se busca con la lista original de pts
    foundp = 0  # Contandor de c/3 numeros
    preal = 0
    # p_after = 0
    # p_before = 0
    # GUARDAR puntos a usar, porque hasta el momento no estan en orden
    for pto in range(len(point_collection_z)):
        if point_collection_z[pto] in arr_union:
            # AÑADIR puntos antes del actual
            # if point_collection[pto] in arr_curve:
            #     # print("ubicación", pto)
            #     tuple_pto = (
            #         point_collection[pto].x, point_collection[pto].y)
                # for key, value in dic_lines_b.items():
                #     if tuple_pto == key:
                #         # print("SE ENCONTRO ",value)
                #         arrp.append(value)
                #         p_before += 1
            arrp.append(point_collection_z[pto])  # Añadir punto
            # print("+",point_collection_z[pto]) #Casi es de mayor a menor en beyond,exceptuando el primero q es ultimo
            # AÑADIR puntos después del actual
            # if point_collection[pto] in arr_curve:
                # print("ubicación", pto)
                # si la ubicación del punto es de las ultimas ya no se agrega
                # if pto < len(point_collection)-3:
                    # si hay punto curvo se añade su key de diccionario
                    # tuple_pto = (
                    #     point_collection[pto].x, point_collection[pto].y)
                    # for key, value in dic_lines_a.items():
                    #     if tuple_pto == key:
                    #         # print("SE ENCONTRO ",value)
                    #         arrp.append(value)
                    #         p_after += 1
            foundp += 1
            # preal += 1
            # Si es MOVEC repetir angle /
            # AQUI SE REPITEN CADA 3R PTO, SI EL SIG VARIA EN Y OBLIGATORIAMENTE SE REPITE Y REINICIA
            if amount_concaves >= 6 and len(list_repeat) >= 1:
                if point_collection_z[pto] in list_repeat:
                    # print("encontro repeat")
                    arrpose.append(preal-1)
                    arrpose.append(preal)
            if amount_concaves >= 6 and foundp % 3 == 0:
                # print("Tercer punto de un elemento concavo")
                arrp.append(point_collection_z[pto])
                preal += 1
    # print("Z", z_one)
    # print("Found:",foundp)
    
    xs = [point.x for point in arrp]
    ys = [point.y for point in arrp]
    zs = [point.z for point in arrp] #[z_one]*len(xs) #
    arr_puntos = np.column_stack((xs, ys, zs))
    # print("l1",len(arrc))
    # Añadir valor de Z a array de puntos con curva
    xp = [point.x for point in lista_curvos]
    yp = [point.y for point in lista_curvos]
    zp = [point.z for point in lista_curvos] #[z_one]*len(xp) #
    p_curve = np.column_stack((xp, yp, zp))
    p_curve = p_curve.tolist()
    #B)
    return arr_puntos, p_curve, arrpose

def guardar_pz(point_collection_z, amount_concaves,list_points, lista_curvos,list_repeat, df_total_original):
    #PREPARAR PUNTOS    
    lista_curvos = find_z(point_collection_z, lista_curvos) #AÑADIR Z, existen en lista 
    if len(list_repeat) > 1:
        list_repeat = find_z(point_collection_z, list_repeat) #AÑADIR Z, existen en lista 
    arr_union = list_points 
    xs = [point.x for point in arr_union]
    ys = [point.y for point in arr_union]
    zs = [point.z for point in arr_union] #[z_one]*len(xs) #
    arr_puntos = np.column_stack((xs, ys, zs))
    # Añadir valor de Z a array de puntos con curva
    xp = [point.x for point in lista_curvos]
    yp = [point.y for point in lista_curvos]
    zp = [point.z for point in lista_curvos] #[z_one]*len(xp) #
    p_curve = np.column_stack((xp, yp, zp))
    p_curve = p_curve.tolist()
    return arr_puntos, p_curve
