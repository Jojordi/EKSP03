# -*- coding: utf-8 -*-
"""
Versión 8

FUNCIÓN: 
        Cálculo de parámetros para cada curva de cada capa a rellenar

CONTENIDO:
        *Funciones de cálculos 
        *Funciones para plotear
        *Generación de dataframe de estrategias para cada caso
        *Generación de trayectorias para cada curva con base en la mejor opcion
        *Generación de dataframe de 1 estrategia por curva 
         (Clasificación por centroide de c/curva)

NOTAS:
    Incluye Pausa entre capas
"""
# Librerias externas
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Point, MultiPoint,MultiLineString, MultiPolygon, Polygon, LineString, LinearRing
from shapely.ops import unary_union
from descartes import PolygonPatch
import pandas as pd
import time
import copy
import matplotlib.gridspec as gridspec
from statistics import mean
from sklearn.neighbors import KDTree

# Librerias locales
from path_generation.path_strategies import rot_raster, rot_continuos, rot_zigzag, offset_closed, offset_spiral
from path_generation.partition import points_concaves, filter_lines, cut_coeficient, gen_subplot
from path_generation.concavity.utils import gaussian_smooth_3d, gaussian_smooth_3d1
from path_generation.generatorcsr import printProgressBar


# %%
# =============================================================================
#                       CÁLCULO DE PARÁMETROS
# =============================================================================
# Funcion para calcular párametros de relleno a evaluar dentro de cada estrategia
def parameters_gral(lineas, sublineas, poligono, opcion, h, w, p, MD, S):
    # lineas: lineas de trayectoria generadas, MLS de n LS
    # sublineas: lineas de subpoligonos (en caso de contornos closed/spiral)
    # poligono: geometria del desgaste original
    d_z = h
    new_cord = []  # array de cordones
    new_cord2 = []  # cordones de subpoligonos
    longt_sub = 0  # Longitud acumulada de sub lineas
    sub_elements = 0  # Contador de elementos

    for ls in range(len(lineas)):
        dilated_l = lineas[ls].buffer(w / 2, cap_style=1)
        new_cord.append(dilated_l)
        sub_elements += 1
    total_cord = MultiPolygon(new_cord)  # Poligono de cordones
    # sub_elements= len(lineas) # cantidad de elementos 
    dilated_ext = unary_union(total_cord)  # pol de cordones
    if len(sublineas) == 0:
        # print("NO HAY SUBPOLIGONOS")
        dilated = unary_union(dilated_ext)  # unión de pol
    else:
        # en caso de que existan subp sumar individuales
        for pl in range(len(sublineas)):
            # Entra a cada subpoligono
            if type(sublineas[pl]) == LineString:
                # print("no hay subp")
                length_sub = sublineas[pl].length
                longt_sub += length_sub
                linet = sublineas[pl]  # LineString de subpoligono
                dilated2 = linet.buffer(w / 2, cap_style=1)
                new_cord2.insert(0, dilated2)  # Añadir en la inversa
            else:
                sub_elements += len(sublineas[pl])
                for ip in range(len(sublineas[pl])):
                    # Entra a cada subelemento
                    length_sub = sublineas[pl][ip].length
                    longt_sub += length_sub
                    linet = sublineas[pl][ip]  # LineString de subpoligono
                    dilated2 = linet.buffer(w / 2, cap_style=1)
                    new_cord2.insert(0, dilated2)  # Añadir en la inversa
        total_cord2 = MultiPolygon(new_cord2)
        dilated2 = unary_union(total_cord2)  # pol de cordones interiores
        dilatedsum = [dilated_ext, dilated2]  # conj de poligonos
        dilated = unary_union(dilatedsum)  # unión de pol

    # SOLDADURA
    elements = sub_elements  # No. de elementos total    
    longt = (lineas.length) + longt_sub  # [mm] longitud de las trayectorias
    lengthinside = (lineas.intersection(poligono)).length  # [mm] long linea dentro del pol
    # ÁREA DE SOLDADURA [mm^2]
    area_capa = poligono.area  # área a cubrir
    arealines = (dilated.area)  # área de cordones total
    out = ((dilated.difference(poligono)).area)  # soldadura por fuera del daño
    areacordon = arealines - out  # area de cordones dentro del poligono
    area_p = (2 / 3) * (h * w)  # Área parabola   
    # VOLUMEN DE SOLDADURA [mm^3] 
    vol_capa = area_capa * d_z  # vol. del polígono
    vol_cor = area_p * longt  # vol de los cordones

    # Estos cálculos varian por el tipo de trayectorias,
    # uno de tipo contorno deja vacio con la pared
    if opcion == 'raster' or opcion == 'raster_c':
        weld_area = 0
        for l in lineas:
            d_val = ((l.buffer(w / 2, cap_style=1)).intersection(poligono)).area
            weld_area += d_val
        vol_weld = weld_area * d_z  # [mm^3]vol de soldadura dentro del poligono
        vol_cover = areacordon * d_z  # Vol cubierto=area*alto de capa
        if opcion == 'raster_c':
            elements = 1  # En Zig-zag y continuo es solo un elemento
    else:
        area_c = (d_z * w)  # Área de rectangulo p/aproximación de exceso
        area_noncover = area_capa - areacordon
        vol_weld = area_c * lengthinside  # vol de los cordones dentro del poligono
        av_borde = 0 #(d_z * w) / 6  # área vacia entre cordon y borde
        vol_voids = av_borde * (poligono.length) + (area_noncover * d_z)  # vol sin cubrir
        vol_cover = vol_capa - vol_voids  # restando el vol s/cubrir
        if len(lineas) ==1 and len(sublineas)== 0:
            vol_weld = vol_cover
        if opcion == 'continuo':
            if len(sublineas) > 1:
                elements = len(sublineas)-1
            elif len(sublineas) == 0:
                #no hay subelementos
                elements = 1

    # PORCENTAJES
    percent_areac = round((areacordon * 100) / area_capa, 1)  # porcentaje de área cubierta
    percent_vnc = round((vol_capa - vol_cover) / vol_capa * 100, 1)  # porcentaje de volumen no cubierto
    percent_out = round((out * d_z) / vol_capa * 100, 1)  # porcentaje de material depositado afuera
    percent_excs = round((vol_weld - vol_cover) / vol_cover * 100, 1)  # Porcentaje de solapamiento,el exceso que hay adentro
    # -->valor aproximado de solapamiento
    if percent_excs >= 0:
        percent_excs = percent_excs
    else:
        percent_excs = 0
    # WELDING COSTS
    W_filler = ((vol_cor * 1E-3) * MD) / 1000  # [kg] Weight weld metal
    time_pc = ((longt / 1000) / S)  # [min]

    return elements, area_capa, vol_capa, areacordon, vol_cover, percent_areac, percent_vnc, time_pc, W_filler, percent_out, percent_excs


# %%
# =============================================================================
#                       FUNCIONES PARA GRAFICAR
# =============================================================================

alfa = 0.2  # intensidad de transparencia del cordon
alfap = 0.9  # intensidad de transparencia del poligono
colorp = 'dimgray'  # color del poligono (curva original)
colors = '#6699cc'  # color del cordón de soldadura
colorl = '#999999'  # color de lineas de trayectorias
color3d = 'dimgray' #color de lineas 3D
def plot_line3(ax, ob):
    #plotear lineas 3D
    for line in ob:
        zs = (list(line.coords[0])[2], list(line.coords[1])[2])
        xs, ys = zip(*list((p.x, p.y) for p in line.boundary)) 
        zline = zs
        xline = xs
        yline = ys
        ax.plot3D(xline, yline, zline, 'gray')# Data for three-dimensional scattered points

def plot_line(ax, ob, w):
    x, y = ob.xy
    ax.plot(x, y, color=colorl, linewidth=1, solid_capstyle='round', zorder=1)
    dilated = ob.buffer(w / 2, cap_style=1)
    patch1 = PolygonPatch(dilated, fc=colors, ec=colors, alpha=alfa, zorder=2)
    ax.add_patch(patch1)

def plot_lines(ax, ob, w):
    for line in ob:
        plot_line(ax, line, w)

# Funcion general para plotear n linestrings
def plot_only(lines, w):
    ax = plt.gca()
    # ax.axis('equal')
    plot_lines(ax, lines, w)  # plotea una única linea en el orden entregado: zigzag-continuo

def plot_contours(pol_lines, subp_lines, w):
    ax = plt.gca()
    # ax.axis('equal')
    try:
        plot_lines(ax, pol_lines, w)  # MLS
    except:
        plot_line(ax, pol_lines, w)
    # Para lista de subcontornos
    try:
        for i in range(len(subp_lines)):
            plot_lines(ax, subp_lines[i], w)
    # En caso de que solo se genere un subofsset
    except:
        plot_lines(ax, subp_lines, w)
def plot_contours_union(pol_lines, subp_lines, w):
    ax = plt.gca()
    if type(pol_lines) == MultiLineString:
    # try:
        plot_lines(ax, pol_lines, w)  # MLS
    elif type(pol_lines) == LineString:
    # except:
        plot_line(ax, pol_lines, w)
    # Para lista de subcontornos
    if type(subp_lines) == list:
        # print("Es lista PLOT")
        for sub in subp_lines:
            if type(sub)== LineString:
                plot_line(ax, sub, w)
            else:
                plot_lines(ax, sub, w)
    else:
        try:
            for i in range(len(subp_lines)):
                plot_lines(ax, subp_lines[i], w)
        # En caso de que solo se genere un subofsset
        except:
            plot_lines(ax, subp_lines, w)
# Ploteo de lineas de división
def plot_lsimple(ax, ob):
    for line in ob:
        x, y = line.xy
        ax.plot(x, y, linewidth=2, solid_capstyle='round', zorder=1)


# Ploteo de lineas en 3D
def plot_line_3Z(ax, ob, layer):
    # Ploteo de LineString
    pp = list(ob.coords)
    x = [cx[0] for cx in pp]
    y = [cx[1] for cx in pp]
    z = [cx[2] for cx in pp]
    ax.plot(x, y,z, color=color3d, alpha=0.7, linewidth=3, solid_capstyle='round', zorder=2)      

def plot_lines_3DZ(ax,ob,layer):
    for line in ob:
        plot_line_3Z(ax, line,layer)
# %%
# =============================================================================
#                     FUNCIONES DE VALIDACIÓN
# =============================================================================

def shapely_elements(curva, p):
    # FUNCION DE ELEMENTOS NECESARIOS PARA ESTRATEGIAS
    point_collection = MultiPoint(list(curva))  # envelope is a Polygon of shapely
    envelope = point_collection.envelope  # rectangulo que lo contiene
    poligono = Polygon(point_collection)  # Declaración de Poligono
    kdt = (KDTree(curva, leaf_size=2).query_radius(curva[:1], r=p, count_only=True))
    # Pocos puntos no se hace suavizamiento
    if kdt <= 3:
        p_test = poligono
    else:
        if kdt < 14:
            p_smooth = gaussian_smooth_3d1(poligono, sigma=0.2)  # smooth geometry
            p_test= Polygon(p_smooth)
        elif kdt < 60:
            p_smooth = gaussian_smooth_3d1(poligono, sigma=1) #Np Array de x,y,z
            p_test= Polygon(p_smooth)
        else:
            p_smooth = gaussian_smooth_3d(poligono, sigma=2)
            p_test= Polygon(p_smooth)
    if len(point_collection) > 1500:
        # Realizar simplificación adicional para archivos de escaneo
        tolerance = 0.3
        p_test = p_test.simplify(tolerance, preserve_topology=False)
    s_poly = LinearRing(list(p_test.exterior.coords))  # Frontera del polígono, como una linea# Filtro para identificar -> por centros
    c_centro = poligono.centroid  # centroide
    buffer_centro = c_centro.buffer(3)
    c_centrox = int(round(c_centro.x))    
    c_centroy = int(round(c_centro.y))
    c_centro = (c_centrox, c_centroy)
    return envelope, poligono, s_poly, c_centro, buffer_centro


# FUNCIÓN PARA FILTRAR CURVAS POR ÁREA
def pass_curve(data, ancho_cordon):
    filtered_data = []  # CAPAS DE CURVAS VÁLIDAS
    min_areacover = ancho_cordon**2  # [mm^2]
    for i, capa in enumerate(data):
        filtered_capa = []  # CURVAS QUE CUMPLEN CONDICIONES
        for j, curva in enumerate(capa):
            if len(curva) > 3:  # MÍNIMO PARA CREAR POLYGON
                poligono = Polygon(list(curva))
                # MÍNIMO PARA PODER GENERAR RASTER
                if poligono.area <= min_areacover:
                    print("ÁREA INSUFICIENTE: ", i, j, poligono.area)
                    # filtered_capa.append(curva)
                else:
                    # ANCHO/ALTO INSUFICIENTE
                    percent_pe = (poligono.area / poligono.envelope.area) * 100
                    x_min, y_min, x_max, y_max = poligono.envelope.bounds
                    ancho = x_max - x_min
                    alto = y_max - y_min
                    if ancho < ancho_cordon or alto < ancho_cordon:
                        print("ANCHO/ALTO INSUFICIENTE: ", i, j, ancho, alto, poligono.area)  # CASO POLYGON REGULAR
                        # filtered_capa.append(curva)
                    elif percent_pe > 40:  # ACÁ SE ELIMINAN LAS PARTES QUE QUEREMOS TENER
                        # FILTRO DE CURVAS QUE CUMPLEN ÁREA PERO TIENEN FORMAS EXTRAÑAS
                        # VER CASOS CON CORTES DE ESCANEOS (SE DA POR RUIDO EN ESCANEO)
                        filtered_capa.append(curva)
        filtered_data.append(filtered_capa)

    return filtered_data


def obtain_angle(data_o, o, p, w, h, S, MD):
    # SE FILTRAN LAS CAPAS QUE NO TENGAN EL ÁREA MINIMA
    data = pass_curve(data_o, w)

    # INICIA PRUEBAS CON ANGULOS
    print("Buscando mejor ángulo...")
    # Imprimir 0% progreso
    printProgressBar(0, len(data), prefix='Progress:', suffix='Complete', length=50)
    angles = np.arange(0, 180, 10)  # Valores de ángulos a testear
    list_df = []  # lista para crear dataframe de comparacion de ángulos
    list_circles =[] #lista de circulos del centro
    tipo = 0  # Tipo para diferenciar entre curvas

    for capa in range(len(data)):
        for subc in range(len(data[capa])):
            curva = data[capa][subc]
            # Función para obtener elementos de shapely
            envelope, poligono, s_poly, c_centro, buffer_centro = shapely_elements(curva,p)  # Datos generales para trayectorias
            centro = Point(c_centro)
            if len(list_circles) == 0:
                predicate = False
            else: 
                for circle in list_circles:
                    contiene =  circle.contains(centro) 
                    if contiene == True:
                        predicate = True
                        break
                    else:
                        predicate = False
            if predicate == False:
                centro_df =list(buffer_centro.centroid.coords)[0] #centro a guardar en dataframe será el 
                list_circles.append(buffer_centro) # Se añade el poligono donde se verifica que contenga el pto
                for ang in angles:
                    # Existen angulos que al rotar no queda alguna linea dentro del poligono
                    # debido a que el espacio entre las dos lineas es mas grande que el ancho de la figura
                    try:
                        name = 'raster'
                        lineas, subp_lines, points_final = rot_raster(curva, ang, poligono, s_poly, o, p, w)
                        elements, area_capa, vol_capa, areacordon, vol_cover, percent_areac, percent_vvoids, time_pc, W_filler, percent_out, percent_excs = parameters_gral(
                            lineas, subp_lines, poligono,name, h, w, p, MD, S)
                        new_row = (tipo, name, ang, centro_df, elements, percent_areac, percent_vvoids)
                        list_df.append(new_row)
                        # print("Para curva {}, SI aplica {}°".format(tipo,ang))
                    except:
                        # print("Para curva {}, no aplica {}°".format(tipo,ang))
                        pass
                tipo += 1  # actualización del tipo de curva
            else:
                # print("Done") #Se evita el testeo
                pass
        time.sleep(0.1)
        printProgressBar(capa + 1, len(data), prefix='Progress:', suffix='Complete', length=50)

    df_angles = pd.DataFrame(list_df,
                             columns=['Curva', 'Estrategia', 'Grados', 'Centro', 'Elementos', '% Área C', '% Vol NC'])
    n_curves = df_angles['Curva'].unique().tolist()
    dict_angle = {}  # diccionario de angulos con centro
    for nc in n_curves:
        curve_n = df_angles[df_angles['Curva'] == nc] 
        curve_n = curve_n.sort_values(by=['% Área C', 'Elementos'], ascending=[False, True])
        angleoption_ = (curve_n['Grados'].values[0])        
        centro_n = (curve_n['Centro'].values[0])
        dict_angle[centro_n] = angleoption_
    return dict_angle, data


# %%
# =============================================================================
#                     SELECCIONAR ESTRATEGIA
# =============================================================================

# PASO 1. Realizar testeo para cada curva diferente que aparezca en todas las capas
def testing(data_new, o, p, w, h, S, MD):
    data_copia = copy.deepcopy(data_new)
   # BUSCAR EL ÁNGULO ÓPTIMO
    anglevalues, data = obtain_angle(data_copia, o, p, w, h, S, MD)  # Entrega lista de n angulos para n curvas

    print("\nRealizando pruebas con todas las estrategias...")
    l = len(data)
    printProgressBar(0, l, prefix='Progress:', suffix='Complete', length=50)  # Imprimir 0% progreso

    list_circles =[] #lista de circulos del centro
    list_df = []  # lista para dataframe de resultados
    tipo = 0
    endpoint = (None,None) #variable inicial para punto final de capa
    for capa in range(len(data)):       
        for subc in range(len(data[capa])):
            curva = data[capa][subc]
            envelope, poligono, s_poly, c_centro, buffer_centro = shapely_elements(curva,p)
            centro = Point(c_centro)
            if len(list_circles) == 0:
                predicate = False
            else: 
                for circle in list_circles:
                    contiene =  circle.contains(centro) 
                    if contiene == True:
                        predicate = True
                        break
                    else:
                        predicate = False
            if predicate == False:
                list_circles.append(buffer_centro)
                centro_df =list(buffer_centro.centroid.coords)[0] #centro a guardar en dataframe será el 
                grados = None #valor default grados
                Fig, ax = plt.subplots(figsize=[15, 10], constrained_layout=True, sharex=True, sharey=True)
                spec = gridspec.GridSpec(ncols=3, nrows=2, figure=Fig)
                Fig.suptitle('Curva {}'.format(tipo), fontsize=20)
                # Se busca el ángulo encontrado para ese caso
                grados = None
                for key, value in anglevalues.items():
                    if centro_df == key:
                        grados = value
                        break
                # ESTRATEGIAS
                if grados != None:
                    #En algunos caso no hay ángulo   
                    # 1 Raster al angulo óptimo:
                    name = 'Raster Discrete'
                    opcion= 'raster'
                    # print("{} to {}°".format(name,grados))
                    ax1 = Fig.add_subplot(spec[0, 0])
                    ax1.set_title("{}".format(name), fontsize=15)
                    lineas, subp_lines, points_final = rot_raster(curva, grados, poligono, s_poly, o, p, w)
                    elements, area_capa, vol_capa, areacordon, vol_cover, percent_areac, percent_vvoids, time_pc, W_filler, percent_out, percent_excs = parameters_gral(
                        lineas, subp_lines, poligono,opcion, h, w, p, MD, S)
                    new_row = (capa, tipo, centro_df, name, elements, area_capa, percent_areac, percent_vvoids, percent_out, percent_excs)
                    list_df.append(new_row)
                    variables1 = ("Covered area " + str(percent_areac) +
                                  "%  Exs.Overlap " + str(percent_excs) +
                                  "%  Outside " + str(percent_out) + "%")  # Variables a mostrar                
                    ax1.set_title("{}".format(name), fontsize=15)
                    ax1.plot(curva[:, 0], curva[:, 1], color=colorp, alpha=alfap,
                              linewidth=3, solid_capstyle='round', zorder=2, label=variables1)  # ploteo de la curva
                    plot_only(lineas, w)
                    ax1.autoscale()
                    ax1.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05), facecolor='gainsboro')  # , labelcolor='w'
                    # 2 Raster continuo al ángulo óptimo
                    name = 'Raster Continuos'
                    opcion='raster_c'
                    # # print("{} to {}°".format(name,grados))
                    ax2 = Fig.add_subplot(spec[0, 1])
                    ax2.set_title("{}".format(name), fontsize=15)
                    lineas, subp_lines, points_final, unionls = rot_continuos(curva, grados, poligono, s_poly, o, p, w)
                    elements, area_capa, vol_capa, areacordon, vol_cover, percent_areac, percent_vvoids, time_pc, W_filler, percent_out, percent_excs = parameters_gral(
                        lineas, subp_lines, poligono,opcion, h, w, p, MD, S)
                    new_row = (capa, tipo, centro_df, name, elements, area_capa, percent_areac, percent_vvoids, percent_out, percent_excs)
                    list_df.append(new_row)
                    variables2 = ("Covered area " + str(percent_areac) +
                                  "%  Exs.Overlap " + str(percent_excs) +
                                  "%  Outside " + str(percent_out) + "%")  # Variables a mostrar
                    ax2.plot(curva[:, 0], curva[:, 1], color=colorp, alpha=alfap,
                              linewidth=3, solid_capstyle='round', zorder=2, label=variables2)  # ploteo de la curva
                    ax2.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05), facecolor='gainsboro')
                    plot_only(lineas, w)
                    ax2.autoscale()
                    # 3 Raster zig zag  al ángulo óptimo
                    # print("Raster rotatorio zig zag a {}°".format(grados))
                    name = 'Rotatorio Zigzag'
                    ax3 = Fig.add_subplot(spec[0, 2])
                    ax3.set_title("{}".format(name), fontsize=15)
                    lineas, subp_lines, points_final, unionls = rot_zigzag(curva, grados, poligono, s_poly, o, p, w)
                    elements, area_capa, vol_capa, areacordon, vol_cover, percent_areac, percent_vvoids, time_pc, W_filler, percent_out, percent_excs = parameters_gral(
                        lineas, subp_lines, poligono,opcion, h, w, p, MD, S)
                    new_row = (capa, tipo, centro_df, name, elements, area_capa, percent_areac, percent_vvoids, percent_out, percent_excs)
                    list_df.append(new_row)
                    variables3 = ("Covered area " + str(percent_areac) +
                                  "%  Exs.Overlap " + str(percent_excs) +
                                  "%  Outside " + str(percent_out) + "%")  # Variables a mostrar
                    ax3.plot(curva[:, 0], curva[:, 1], color=colorp, alpha=alfap,
                              linewidth=3, solid_capstyle='round', zorder=2, label=variables3)  # ploteo de la curva
                    ax3.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05), facecolor='gainsboro')
                    plot_only(lineas, w)
                    ax3.autoscale()
                else:
                    # print("\n NO SE APLICA RASTER")
                    pass
                try:    
                    #Estas estrategias generan error si hay partes muy estrechas que se cierran
                    # # o partes concavas muy pronunciadas, tal vez pueda solucionarse con division de poligonos
                    name = 'Contour Discrete'
                    opcion= 'contorno'
                    # # print("{}".format(name))
                    ax4 = Fig.add_subplot(spec[1, 0])
                    pol_lines, subp_lines, unionls = offset_closed(curva, poligono, s_poly, envelope, o, p, w, endpoint)
                    elements, area_capa, vol_capa, areacordon, vol_cover, percent_areac, percent_vvoids, time_pc, W_filler, percent_out, percent_excs = parameters_gral(
                        pol_lines, subp_lines, poligono,opcion, h, w, p, MD, S)
                    new_row = (capa, tipo, centro_df, name, elements, area_capa, percent_areac, percent_vvoids, percent_out,
                                percent_excs)
                    list_df.append(new_row)
                    ax4.set_title("{}".format(name), fontsize=15)
                    variables4 = ("Covered area " + str(percent_areac) +
                                  "%  Exs.Overlap " + str(percent_excs) +
                                  "%  Outside " + str(percent_out) + "%")  # Variables a mostrar
                    ax4.plot(curva[:, 0], curva[:, 1], color=colorp, alpha=alfap,
                              linewidth=3, solid_capstyle='round', zorder=2, label=variables4)  # ploteo de la curva
                    ax4.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05), facecolor='gainsboro')
                    plot_contours(pol_lines, subp_lines, w)
                    ax4.autoscale()
                    # 4
                    name = 'Contour Continuos'
                    opcion= 'continuo'
                    # print("{}".format(name))
                    ax5 = Fig.add_subplot(spec[1, 1])
                    pol_lines, subp_lines, unionls = offset_spiral(curva, poligono, s_poly, envelope, o, p, w, endpoint)
                    # list_empty = [], unionls, list_empty #PENDIENTE CASO DE ELEMENTOS
                    elements, area_capa, vol_capa, areacordon, vol_cover, percent_areac, percent_vvoids, time_pc, W_filler, percent_out, percent_excs = parameters_gral(
                        pol_lines, subp_lines, poligono,opcion, h, w, p, MD, S)
                    new_row = (capa, tipo, centro_df, name, elements, area_capa, percent_areac, percent_vvoids, percent_out,
                                percent_excs)
                    list_df.append(new_row)
                    ax5.set_title("{}".format(name), fontsize=15)
                    variables5 = ("Covered area " + str(percent_areac) +
                                  "%  Exs.Overlap " + str(percent_excs) +
                                  "%  Outside " + str(percent_out) + "%")  # Variables a mostrar
                    ax5.plot(curva[:, 0], curva[:, 1], color=colorp, alpha=alfap,
                              linewidth=3, solid_capstyle='round', zorder=2, label=variables5)  # ploteo de la curva
                    ax5.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05), facecolor='gainsboro')                    
                    plot_contours_union(pol_lines, subp_lines, w)
                    ax5.autoscale()
                except:
                    # Topology exception:
                    ax4.text(0.5, 0.5, 'Concave parts or insufficient space',
                              verticalalignment='center', horizontalalignment='center',
                              transform=ax4.transAxes, color='black', fontsize=12)
                    pass 
                tipo += 1  # actualización del tipo de curva
                ax.set_axis_off()
                plt.show()
        time.sleep(0.1)
        # Actualizar barra de progresion
        printProgressBar(capa + 1, l, prefix='Progress:', suffix='Complete', length=50)
    # Dataframe de todas las estrategias
    df_results = pd.DataFrame(list_df,
                              columns=['Capa', 'Curva', 'Centro', 'Estrategia', 'Elementos', 'Área', '% Área C', '% Vol NC',
                                       'Fuera de', 'Exceso'])
    # Seleccionar mejor estrategia para cada curva
    nameoption, dividelist, areacompare, areadivision = select_option(df_results)
    # En caso de que las alturas se manejen de manera separada
    data_3d = []
    data_3d.append(data)
    return anglevalues, data_3d, nameoption, dividelist, areacompare, areadivision


# FUNCIÓN PARA SELECCIONAR ESTRATEGIA DE RELLENO
def select_option(df_results):
    # Se utilizan promedios ponderados para seleccionar opción
    print("\nEncontrar mejor opción...")
    damages = df_results['Curva'].unique()
    ndamage = len(damages)  # Cantidad de curvas
    list_todivide = []  # Lista de curvas para dividir
    areacompare = []  # Lista de valores de %AC de curva original, usado p/division
    areadivision = []  # Se guardan los valor de área pero solo se ocupan cuando se divide
    min_area = 92  # Se maneja ese porcentaje temporalmente para evitar division #% Porcentaje minimo para no optar por
    # división de poligono
    weight_a = 0.98 #Peso del área cubierta
    weight_b = 0.35 #Peso de los elementos
    weight_c = 0.12 #Peso de material por fuera
    weight_d = 0.09 #Peso de solapammiento de material
    sum_weight = weight_a+weight_b+weight_c+weight_d #Suma de pesos
    
    #SELECCIONAR OPCIÓN PARA CADA ESTRATEGIA 
    list_option=[]#lista de opcion para cada curva
    
    for nc in range(ndamage):
        #Para cada curva tener una opción:
        print("\n Curva {}".format(damages[nc]),end="    ")
        curve_n = df_results.loc[df_results['Curva'] == damages[nc]]
        curve_n['PP'] = (curve_n['% Área C']*weight_a - curve_n['Elementos']*weight_b - 
                         curve_n['Fuera de']*weight_c - curve_n['Exceso']*weight_d) / sum_weight
        curve_n=curve_n.sort_values(by=['PP'],ascending=[False])
        areacover = (curve_n['% Área C'].values[0])
        centro_n = (curve_n['Centro'].values[0])
        nameoption_ = (curve_n['Estrategia'].values[0])
        if areacover < min_area:
            print("Área: {}% ".format(areacover), end= " ")
            print("Se realizará división")
            #Guardar para dividir
            try:
                values_c = (nameoption_ ,eval(centro_n))
            except:
                values_c = (nameoption_,centro_n)
            list_todivide.append(values_c)
            areacompare.append(areacover)
            areadivision.append(areacover)
        else:
            # print("No se realizará división")
            print("Área: {}% ".format(areacover), end= " ")              
            print("Opción: %s " %nameoption_)
            #guarda centros con nombre de estrategia
            values_c =(nameoption_,centro_n)
            list_option.append(values_c)
            areadivision.append(areacover)
    
    list_todivide = np.array(list_todivide)
    return list_option, list_todivide, areacompare, areadivision
# %%%
# =============================================================================
#                           DIVISIÓN 
# =============================================================================

# Generar subpoligonos de la curva seleccionada
def divide_curve(dividelist, data, slices, p):
    # dividelist: son los centros de las curvas que necesitan division
    # data viene con lista de cpas x y y +lista de alturas z
    data=data[0]
    # print("Buscar poligono...")
    list_total = []  # Lista para nuevo "data"
    for capa in range(len(data)):
        list_capa = []  # Lista para capas
        for subc in range(len(data[capa])):
            curva = data[capa][subc]
            point_collection = MultiPoint(list(curva))  # envelope is a Polygon of shapely
            envelope, poligono, s_poly, c_centro,buffer_centro = shapely_elements(curva,p) # Función para obtener elementos de shapely
            #REVISAR SI EL CENTRO DE CADA ELEMENTO DE DIVIDE LIST ESTA CONTENIDO EN ESE BUFFER       
            for element in dividelist:
                centro = Point(element)
                contiene =  buffer_centro.contains(centro) 
            # si el centro coincide con alguno de la lista se divide
            if contiene  == True:
                arrc = points_concaves(curva)  # encontrar puntos concavos
                multils, df_lines = filter_lines(arrc, poligono)  # Eliminar lineas repetidas o fuera
                lines_select = cut_coeficient(poligono, multils, df_lines, point_collection,
                                              slices)  # Seleccionar lineas por su coeficiente
                results = gen_subplot(lines_select, poligono)  # Lista de poligonos resultantes
                # plot poligono original
                Fig, ax = plt.subplots(figsize=[20, 10], sharex=True, sharey=True)
                spec = gridspec.GridSpec(ncols=slices+1, nrows=2, figure=Fig)
                Fig.suptitle('Capa {}, Curva original'.format(capa + 1), fontsize=20)
                ax = plt.gca()
                ax.axis('equal')
                ax.set_axis_off()
                ax1 = Fig.add_subplot(spec[0, :])  # Curva original
                ax1.plot(curva[:, 0], curva[:, 1], color=colorp, alpha=alfap,
                         linewidth=3, solid_capstyle='round', zorder=2)
                # Plot de lineas de división
                plt.set_cmap = "seaborn",
                plot_lsimple(ax1, lines_select)  # plot de lineas de corte
                ax1 = plt.gca()
                ax1.axis('equal')
                ax1.set_axis_off()
                # Guardar poligono como nueva curva
                for spl in range(len(results)):
                    # print("Entra a guardar c/subpoligono ")
                    c_nueva = np.array(list((results[spl]).exterior.coords))  # Nuevo array de pts
                    list_capa.append(c_nueva)
                    poligono = Polygon(MultiPoint(list(c_nueva)))
                    #Plot de subdivisiones
                    ax2 = Fig.add_subplot(spec[1, spl])  # Curva original
                    ax2.set_title("Parte {}".format(spl + 1), fontsize=15)
                    ax2.plot(c_nueva[:, 0], c_nueva[:, 1], color=colorp, alpha=alfap,
                             linewidth=3, solid_capstyle='round', zorder=2)
                    ax2 = plt.gca()
                    ax2.axis('equal')
                    ax2.set_axis_off()
        list_total.append(list_capa)
    return list_total


def divide_save_curve(dividelist, data, slices, p):
    # entrada: data esta en 2D
    # esta función debera entregar data update como lo
    # entrega testing (2 listas: una de coordenadas x y y o tra lista de alturas)
    list_total = []  # Lista para nuevo "data"
    for capa in range(len(data)):
        list_capa = []  # Lista para capas
        for subc in range(len(data[capa])):
            curva = data[capa][subc]
            envelope, poligono, s_poly, c_centro, buffer_centro = shapely_elements(curva,p)
            #Función para obtener elementos de shapely
            point_collection = MultiPoint(list(curva)) #envelope is a Polygon of shapely                    
            #si el centro coincide con alguno de la lista se divide
            for element in dividelist:
                centro = Point(element)
                contiene = buffer_centro.contains(centro) 
            if contiene  == True:
                arrc = points_concaves(curva) #encontrar puntos concavos              
                multils, df_lines = filter_lines(arrc, poligono) #Eliminar lineas repetidas o fuera 
                lines_select = cut_coeficient(poligono, multils, df_lines, point_collection, slices) #Seleccionar lineas por su coeficiente
                results = gen_subplot(lines_select, poligono) #Lista de poligonos resultantes
                #Guardar poligono como nueva curva
                for spl in range(len(results)):
                    c_nueva = np.array(list((results[spl]).exterior.coords)) #Nuevo array de pts
                    list_capa.append(c_nueva)
            else:
                list_capa.append(curva)  # se añade para relocalizar curvas
        list_total.append(list_capa)
    return list_total

# %%
# =============================================================================
#                           RESULTADOS 
# =============================================================================
# FUNCIÓN PARA IDENTIFICAR DIVISIÓN O GENERACIÓN DE TRAYECTORIAS
def generation_paths(anglevalues, data, nameoption, dividelist, areacompare,areadivision, o, p, w, h, S, MD):
    # anglevalues: valor de angulo de inclinacion en caso de usar algun rotatorio
    # data: son la lista de curvas originales
    # nameoption: lista de nombre de estrategia y centro que se ocuparan p/rellenar en caso que no requiera división (List
    # of tuples)
    # dividelist: nombre estrategia y centros de las curvas que se recomiendan dividirse, si la lista esta vacia se evita
    # division (List of tuples)
    # para divir necesitar solo la primera lista pero para generar trayectorias es la lista entera
    # areacompare: lista de  áreas max que se puede cubrir de la curva original, sirve para comparar resultados
    slices = 1  # Cantidad de lineas para dividir la curva
    # Si hay elementos en divide list se hace división
    if len(dividelist) >= 1:
        print("\nPASO 4.PLUS - DIVISIÓN DE POLIGONO")        
        for ccut in range(len(dividelist)):
            # print("Centro {}:{} ".format(ccut+1,dividelist[ccut][1]))
            data_update = divide_curve([dividelist[ccut][1]], data, slices,p) #entrega las nuevas curvas generadas de la división
            print("\n Realizar testeo en nuevas curvas")
            c_amount = 0 #Variable para verificar cantidad de curvas resultantes
            for layer in data_update:
                c_layer = len(layer)
                c_amount += c_layer
            #SE REALIZA TESTEO NUEVAMENTE
            anglevalues2, data2, nameoption2, dividelist2, areacompare2, areadivision2 = testing(data_update,o,p,w,h,S,MD)
            c_amount_final = 0 
            #se revisa cantidad de curvas para verificar que ninguna se elimino, en [0] porque se añadio una lista 
            for layer in data2[0]:
                c_layer = len(layer)
                c_amount_final += c_layer
            # areadivision2 son las areas maximas que pueden cubrirse si se divide
            results_avg = round(mean(areadivision2),1) #promedio de los resultados            
            if c_amount_final < c_amount:
                #en el testeo puede no resultar debido al tamaño del cordón en relación con la división, si se elimina un contorno 
                # se evita la división 
                print("Se evita división:", end=" ")
                print("Original contiene {} y partición entrega {}".format(c_amount,c_amount_final)) 
                print("Se recomienda disminuir ancho de cordón para cubrir un mayor porcentaje de área")                   
                #Se añade la mejor opcion original en nameoption
                nameoption.append(dividelist[ccut])
                data2 = data[0] #Los datos de capa serian los originales, sin division
            elif results_avg <= areacompare[ccut]:
                #comparar con areacompare #<= menor o igual
                print("Se evita división:", end=" ")
                print("Partición cubre {}% y original {}%".format(results_avg,areacompare[ccut]))
                print("Se recomienda disminuir ancho de cordón para cubrir un mayor porcentaje de área")                
                #Se añade la mejor opcion original en nameoption
                nameoption.append(dividelist[ccut])
                data2 = data[0] #Los datos de capa serian los originales, sin division
            else:
                print("Se añaden nuevas curvas:", end=" ")
                print("Partición cubre {}% y original {}%".format(results_avg,areacompare[ccut])) 
                #si la division es buena para c/parte es nameoption = nameoption+nameoption2
                #dividelist2 deberia estar vacia si funciono, pero en ocasiones el promedio ayuda
                #si dividelist tiene elementos se añade
                dividelist2 = dividelist2.tolist()
                #Se añaden la nueva informacion para nuevas trayectorias nuevas
                nameoption = nameoption+nameoption2
                nameoption = nameoption+dividelist2
                anglevalues.update(anglevalues2) #centros y mejor opción
                #data2 solo lista 2D de todas las curvas
                data2 = divide_save_curve([dividelist[ccut][1]],  data[0], slices,p) #entrega todas las curas en la capa correspondiente
        #Se generan las trayectorias en todas las capas
        print("\nPASO 5- GENERACIÓN DE TRAYECTORIAS")
        df_final, list_totalp = gen_path(data2, nameoption, anglevalues,o,p,w,h,S,MD) #Función para calcular valores totales y plotear la estrategia elegida

    else:
        # print("No es necesario dividir")
        print("\nPASO 5- GENERACIÓN DE TRAYECTORIAS")
        df_final, list_totalp = gen_path(data[0], nameoption, anglevalues, o, p, w, h, S,
                                         MD)  # Función para calcular valores totales y plotear la estrategia elegida

    data_3d = [list_totalp]
    return df_final, data_3d

def get_cmap(n, name='hsv'):
    '''Returns a function that maps each index in 0, 1, ..., n-1 to a distinct 
    RGB color; the keyword argument name must be a standard mpl colormap name.'''
    return plt.cm.get_cmap(name, n)

# USAR LA ESTRATEGIA SELECCIONADA
# Genera la estrategia seleccionada para cada curva en todas las capas
def gen_path(data, option, anglevalues, o, p, w, h, S, MD):
    # start_time = time.time()
    # Crear diccionario de funciones con descripción
    dict_strat = {
        rot_raster: 'Raster Discrete',
        rot_continuos: 'Raster Continuos',
        rot_zigzag: 'Raster Zigzag',
        offset_closed: 'Contour Discrete',
        offset_spiral: 'Contour Continuos'
    }
    # Es necesario que las curvas de cada capa esten identificadas correctamente para asignarles su estrategia
    # se opta identificarlas por su centro y buscarlas en un circulo 
    # Recorrer por capa, especificando curva y guardar datos
    list_df = []  # lista de resultados de trayectorias
    list_totalp = []  # lista para ptos de trayectorias
    dict_points = {} #diccionario que se actualiza en cada capa con el ultimo punto y centro 
    l = len(data)
    printProgressBar(0, l, prefix='Progress:', suffix='Complete', length=50)  # Imprimir 0% progreso
    endpoint = (None, None) #Valor incial de punto final 
    fig = plt.figure()
    ax = plt.axes(projection='3d')# Data for a three-dimensional line
    cmap = get_cmap(len(data))
    for capa in range(len(data)):
        # print("\nCapa {} de {}".format(capa+1,(len(data))))
        if len(data[capa]) == 0:
            print("Capa vacía", capa)
        else:
            # Fig, ax = plt.subplots(nrows=1, ncols=1, figsize=[12, 12])
            list_ptos = []  # lista para ptos de trayectorias
            for subc in range(len(data[capa])):
                curva = data[capa][subc]
                # print(("Curva {} de {}:".format(subc+1,(len(data[capa])))),end="")
                # Función para obtener elementos de shapely
                envelope, poligono, s_poly, c_centro, buffer_centro = shapely_elements(curva,p)
                # Busco centro en la lista de option
                for nc in range(len(option)):
                    # Obtengo el nombre relacionado a ese centro
                    try:
                        option_l = eval(option[nc][1])
                    except:
                        option_l = (option[nc][1])  # con una curva no es de tipo string
                    #Si el centro esta dentro del buffer del punto seleccionado
                    centro_test = Point(c_centro) #CEntro actual a testear
                    buffer_option = Point(option_l).buffer(2) #Poligono buffer en el que se verfica pto
                    if buffer_option.contains(centro_test):
                        #Se encontro un buffer al que pertenece, se ocupa el centro de ese para buscar angulo
                        # es decir: option_l # Usando el nombre busco la función
                        n_key = -1  # Encontrar indice de la opción
                        for function, name in dict_strat.items():
                            n_key += 1
                            if name == option[nc][0]:
                                break
                        input_o = (list(dict_strat.keys())[n_key])  # Cambia el numero, cambia estrategia
                        # En caso de ser una opción rotatoria se busca su ángulo
                        for key, value in anglevalues.items():
                            if option_l == key:
                                grados = value
                                break
                        #Buscar ultimo punto correspondiente a ese daño 
                        for key, value in dict_points.items():
                            if option_l == key:
                                endpoint = value
                                break
                # FUNCIÓN DE ESTRATEGIA                        
                if n_key == 0:
                    # Si la opción elegida es rotatoria añadir los grados
                    opcion = 'raster'
                    lineas, subp_lines, points_final = input_o(curva, grados, poligono, s_poly, o, p, w)
                elif n_key == 1 or n_key == 2:
                    opcion = 'raster_c'
                    lineas, subp_lines, points_final, unionls = input_o(curva, grados, poligono, s_poly, o, p, w)
                elif n_key == 3 or n_key == 4:
                    opcion = 'contorno'
                    lineas, subp_lines, unionls = input_o(curva, poligono, s_poly, envelope, o, p, w, endpoint)
                
                # FUNCIÓN DE PARÁMETROS
                elements, area_capa, vol_capa, areacordon, vol_cover, percent_areac, percent_vvoids, time_pc, W_filler, percent_out, percent_excs = parameters_gral(
                        lineas, subp_lines, poligono,opcion, h, w, p, MD, S)
                # #PLOT 2D
                # if n_key == 3:
                #     plot_contours(lineas, subp_lines, w)
                # elif n_key == 4:
                #     plot_contours_union(lineas, subp_lines, w)
                # else:
                #     plot_only(lineas, w)
                # x_p, y_p = poligono.exterior.coords.xy
                # ax.plot(x_p, y_p, label=subc + 1, linewidth=4, zorder=3)  # plot del poligono
                # ax.legend(title='Curva', loc="upper center", bbox_to_anchor=(0.5, -0.05), fancybox=True, shadow=True,
                #           ncol=len(option))  
                #GUARDAR INFORMACIÓN DE RELLENO
                center = poligono.centroid  # centroide
                new_row = (capa, subc, center, elements, area_capa, areacordon, percent_areac, vol_capa, vol_cover, percent_vvoids)
                list_df.append(new_row)
                #GUARDAR LINEAS DE REPARACIÓN
                if n_key == 3:
                    if (len(subp_lines)) == 0:
                        data_layer = lineas
                    else:
                        data_layer = unionls
                elif n_key == 4 or n_key == 1 or n_key == 2:
                    data_layer = unionls 
                else:
                    data_layer = lineas
                list_ptos.append(data_layer)
                #GUARDAR ÚLTIMO PUNTO DEL ÚLTIMO ELEMENTO, para evitar terminar en el mismo lugar
                p_end = Point(list(data_layer[-1].coords)[-1])
                endpoint = (int(p_end.x), int(p_end.y))
                dict_points[option_l] = endpoint #Guardar punto para el centro del contorno correspondiente
                #PLOT 3D 
                zdata = curva[:, 2]                       
                ydata = curva[:, 1]
                xdata = curva[:, 0]  
                ax.plot3D(xdata, ydata, zdata,c = cmap(capa),  label = capa)
                plot_lines_3DZ(ax, data_layer ,capa)
            # ax.set_title(f"Capa {capa + 1}")
            ax.legend(title='Capa', loc="upper right", bbox_to_anchor=(1.05, 1), borderaxespad=0., fancybox=True, shadow=True, 
                                    ncol=1)  
            new_capa = list_ptos
            list_totalp.append(new_capa)
        #3D PLOT TOTAL
        ax.set_xlabel('x')
        ax.set_ylabel('y')
        plt.show()
        time.sleep(0.1)
        printProgressBar(capa + 1, l, prefix='Progress:', suffix='Complete', length=50)
    # CREAR DATAFRAME DE RESULTADOS FINALES
    df_final = pd.DataFrame(list_df,
                            columns=['Capa', 'Curva', 'Centro', 'Elementos', 'Área Capa', 'Área C', '% Área C', 'Vol Capa',
                                     'Vol C', '% Vol NC'])
                            
    capas = coordinates(list_totalp) #Descomponer en puntos
    return df_final, capas

def coordinates(data):
    #Función para decomponer elementos de trayectorias en puntos
    capas = data # CAPAS ES UNA LISTA
    for layer, capa in enumerate(data):
        #layer index, capa n MLS
        for curve, curva in enumerate(capa):
            #Conjunto de lineas (N cantidad de LS's)
            multilines = list(curva.geoms)  # LISTA DE LINES QUE COMPONEN CURVA
            puntos_curva = []            
            for linea in multilines:
                #Lista de puntos de c/LS
                puntos_curva.append(list(linea.coords)) 
            puntos_curva = np.asarray(puntos_curva)
            capa[curve] = puntos_curva
        capas[layer] = capa
    return capas


# CALCULO DE PARÁMETROS EN EL VOLUMEN TOTAL
def results_(df):
    # Crear condicion si solo hay una curva en el daño
    damages = df['Curva'].unique()
    ndamage = len(damages)  # cantidad de daños
    # print(ndamage)
    if ndamage == 1:
        # Unica curva-->Resultados directos:
        # volumen de la ultima capa es diferente poque puede haber material por fuera
        # del daño real
        volreal_0 = df.loc[:, 'Vol Capa'].sum(axis=0)
        volc_0 = df.loc[:, 'Vol C'].sum(axis=0)
        voids_0 = round((volreal_0 - volc_0) / 1000, 2)  # volumen real - cubierto
        print("Volumen s/cubrir: {} cm^3".format(voids_0))
        areareal = df.loc[:, 'Área Capa'].sum(axis=0)
        areacover = df.loc[:, 'Área C'].sum(axis=0)
        voids_area = round((areareal - areacover) / 100, 2)  # volumen real - cubierto
        print("Área s/cubrir: {} cm^2".format(voids_area))
    else:
        # obtener ultima capa (se asume que contiene el max de curvas)
        layers = df['Capa'].unique()
        # print("Layers", layers)
        max_damages = 0 #canrtidad inicial de daños
        for l in layers:
            df_filter = df[df['Capa'] == l]
            amount = len(df_filter)
            # print(l,amount)
            if amount > max_damages:
                max_damages = amount
                capa_usar = l
        #Definir centros a usar
        df_end = df[df['Capa'] == capa_usar]
        centro_ = df_end.loc[:, 'Centro'].tolist()
        plus = 2  # margen de diferencia entre centroides
        # opcion para dividir y mostrar resultados
        # (solo se guarda el ultimo valor de 'Tipo')
        for op in range(len(damages)):
            # añade nueva clasificación comparando distancia con c/pto
            df['Tipo'] = [op if centro_[op].distance(x) < plus
                          else 99 for x in df['Centro']]
            curve_0 = df.loc[df['Tipo'] == (damages[op])]
            volreal_0 = curve_0.loc[:, 'Vol Capa'].sum(axis=0)
            volc_0 = curve_0.loc[:, 'Vol C'].sum(axis=0)
            voids_0 = round((volreal_0 - volc_0) / 1000, 2)  # volumen real - cubierto
            print("Volumen s/cubrir Curva {}: {} cm^3".format(op + 1, voids_0))