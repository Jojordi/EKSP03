import open3d as o3d
import numpy as np
import math
from scipy.spatial.transform import Rotation as R
import matplotlib.pyplot as plt
import copy
import matplotlib.animation as animation

# ------------------------------------------------------------------------------------------------------------------
#Parámetros de soldadura
def volt(ampere):
    '''
    volt(ampere):
    Función que retorna el valor del voltaje en función del amperaje, para el material acero AWS-ER70S-6, de diámetro
    0.99 [mm], con gas de soldadura de composición 80% Ar y 20% CO2.
    :param ampere: Valor del amperaje utilizado
    :return Volt: Valor del voltaje asociado a los ampere utilizados
    '''
    V=0.03153846*ampere+13.44615385
    return V
def beamgeoemetry(ampere,torchspeed):
    '''
    beamgeoemetry(ampere,torchspeed):
    Función que retorna la geometría del cordón de soldadura en función del amperaje, para el material acero
    AWS-ER70S-6, de diámetro 0.99 [mm], con gas de soldadura de composición 80% Ar y 20% CO2.
    :param ampere: Valor del amperaje utilizado
    :param torchspeed: Valor de la velocidad de herramienta utilizada
    :return [h,w]: h la altura del cordón de soldadura y w el ancho del cordón.
    '''
    if (torchspeed>=0.15) and (torchspeed<0.25):
        h=0.015*ampere + 1.085714286
        w=0.056964286*ampere -0.05
    elif (torchspeed >= 0.25) and (torchspeed < 0.35):
        h = 0.01285714 * ampere + 1.15714286
        w = 0.04964286 * ampere + 0.05714286
    elif (torchspeed>=0.35) and (torchspeed<0.45):
        h=0.010714286*ampere + 1.228571429
        w=0.042321429*ampere +0.164285714
    elif (torchspeed>=0.45) and (torchspeed<0.55):
        h=0.00857143*ampere + 1.3
        w=0.035*ampere -0.27142857
    elif (torchspeed>=0.55) and (torchspeed<0.65):
        h=0.006428571*ampere + 1.371428571
        w=0.027678571*ampere +0.378571429
    else:
        print('out of data')
    return [h,w]


# ------------------------------------------------------------------------------------------------------------------
#Funciones generadoras de nubes de puntos
def plane(p, b,d=1):
    '''
    plane(p,b,d=1)
    generación de nube de puntos planar, a partir de un punto p perteneciente al plano, una normal n, equidistanciados entre si en distancia d.
    :param p: Punto perteneciente al plano
    :param b: Ancho del plano
    :param d: Distancia entre los puntos del plano
    :return: Nube de puntos que contiene puntos ubicados en un mismo plano
    '''
    a = np.arange(-b / 2, b / 2, 1 / d)
    l = np.ones_like(a)
    X = []
    Y = []
    for i in np.arange(0, len(a), 1):
        x = l * a[i]
        y = a
        X = np.concatenate((X, x), axis=0)
        Y = np.concatenate((Y, y), axis=0)
    z = np.zeros_like(X)
    c = np.c_[X, Y, z]
    plane = o3d.geometry.PointCloud()
    plane.points = o3d.utility.Vector3dVector(c)
    plane.translate((p), False)
    plane.estimate_normals(search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=0.1, max_nn=30))
    return plane


def spiral(d, D,c=[0,0,0],clockwise=True,t=1):
    '''
    Genera una nube de puntos que siguen una espiral de euclides, con c= centro de la espiral, d el espacio entre ciclos

    :param d: Espaciado entre cordones de soldadura
    :param D: Diámetro de la espiral
    :param c: Coordenadas del centro de la espiral
    :param clockwise: Sentido de las agujas del reloj si es verdadero
    :return: Nube de puntos de la espiral con todos sus ciclos
    '''

    n = int((D * 0.5)/ d) + 1
    pcd_list = []
    if clockwise==False:
        h=1
    else:
        h=-1

    for i in np.arange(1, n, 1):
        o1 = (2 * np.pi * (i - 1))
        o2 = (2 * np.pi * (i))
        s1 = 0.5 * (d / (2 * np.pi)) * ((o1) * math.sqrt(1 + (o1 ** 2)) + np.log(1 + (o1 ** 2)))  # arco de la espiral
        s2 = 0.5 * (d / (2 * np.pi)) * ((o2) * math.sqrt(1 + (o2 ** 2)) + np.log(1 + (o2 ** 2)))
        s = s2 - s1
        n2 = s / t
        a = np.arange(o1, o2-(2 * np.pi / n2), 2 * np.pi / n2)
        r = np.arange((i - 1) * d, i * d-(d / n2), d / n2)
        X = (r * np.cos(a*h))
        Y = (r * np.sin(a*h))
        z = np.ones_like(X)
        v = np.c_[X+c[0], Y+c[1], z*c[2]]
        sp = o3d.geometry.PointCloud()
        sp.points = o3d.utility.Vector3dVector(v)
        R = sp.get_rotation_matrix_from_xyz((0,0, 0))
        sp.rotate(R)
        pcd_list.append(sp)
    add = addpoints(pcd_list)

    return [pcd_list, add]
# ------------------------------------------------------------------------------------------------------------------
# Funciones extra para visualización y manipulación de nubes de puntos
def deleteintersect(pcd1, pcd2, e=0.01):
    '''
    deleteintersect(pcd1, pcd2, e=0.01)
    Elimina los puntos de la nube pcd1 que se intersecten con la nube pcd2, la intersección serán los puntos que tengan una distancia menor a e entre las nubes

    parámetros
    ----------
    pcd1: PCD
        Nube de puntos base
    pcd2: PCD
        Nube de puntos que se intersecará
    e: int
        Distancia entre puntos que se considerará como intersección

    Retorno
    ----------
    pcd: PCD
        Nube de puntos que contiene los puntos de pcd1 no intersecados.

    '''
    dist = np.asarray(pcd1.compute_point_cloud_distance(pcd2))
    ind = np.where(dist > e)[0]
    pcd = pcd1.select_by_index(ind)
    return pcd

def intersect(pcd1, pcd2, e=1):
    '''
    deleteintersect(pcd1, pcd2, e=0.01)

    Selecciona los puntos de la nube pcd1 que se intersecten con la nube pcd2, la intersección serán los puntos que tengan una distancia menor a e entre las nubes

    Parámetros
    ----------
    pcd1: PCD
        Nube de puntos base

    pcd2: PCD
        Nube de puntos que se intersecará

    e: int
        Distancia entre puntos que se considerará como intersección

    Retorno
    ----------
    pcd: PCD
        Nube de puntos que contiene los puntos de pcd1 intersecados.

    '''
    dist = np.asarray(pcd1.compute_point_cloud_distance(pcd2))
    ind = np.where(dist <= e)[0]
    pcd = pcd1.select_by_index(ind)
    return pcd



def cleanlayerpcd(originalpcd, pcd_list, r):
    '''
    cleanlayerpcd(originalpcd, pcd_list, r)

    Quita puntos dispersos que se encuentren dentro de una distancia r respecto a la nube de puntos anterior en la lista de nubes de puntos.

    Parámetros
    ----------
    original pcd: PCD
        Contiene la nube de puntos original.

    pcd_list: Lista de PCD
        Contiene las capas generadas a partir de la nube de puntos original.

    Retorno
    ----------
    clean_list: Lista de PCD
        Lista con las capas tras ser procesadas.

    '''
    clean_list = [deleteintersect(pcd_list[0], originalpcd, r)]
    i = 1
    while i < len(pcd_list):
        clean_list.append(deleteintersect(pcd_list[i], pcd_list[i - 1], r))
        i += 1
    return clean_list

def pcdlistvis(pcd_list, d=100, n=(0, 0,1)):
    '''
    vispcdlist(pcd_list, d=100, n=(0, 0,1))

    Visualización de la lista de PCD, desplaza cada elemento una distancia d en dirección n para visualizarlo mejor

    Parámetros
    ----------
    pcd_list : Lista de PCD

        Lista de PCD a visualizar
    d : int
        Distancia entre cada elemento de la lista

    n : array (x,y,z)
        Dirección en la que se desplazarán los elementos de la lista

    Retorno
    ----------


    '''
    c = 0
    n = np.asarray(n)
    v = n * d
    pcd_list2 = []
    for i in pcd_list:
        pcd_list2.append(i.translate(v * c))
        c += 1
    return pcd_list2


def color(pcd_list):
    '''
    color(pcd_list)
    Cambia los colores de los PCD de la lista para poder diferenciarlos entre si

    parámetros
    ----------
    pcd_list : Lista de PCD
        Lista de PCD a cambiar de color.

    Retorno
    ----------
    pcd_list : Lista de PCD
        Lista con los colores ya modificados.

    '''
    if len(pcd_list) == 0:
        return pcd_list
    n = 1 / len(pcd_list)
    j = 0
    for i in pcd_list:
        s = j / 4
        i.paint_uniform_color([0, 0.7 + s, 1 - j])
        j += n
    return pcd_list


def addpoints(pcd_list):
    '''
    addpoints(pcd_list)
    Combina los puntos de las nubes de punto de la lista para poder visualizarla como una misma nube.

    Parámetros
    ----------
    pcd_list : Lista de PCD
        Lista con los PCD para combinar

    Retorno
    ----------
    PCD : PCD
        PCD que contiene todos los puntos de las nubes en un mismo elemento

    '''
    pcd_points = np.asarray(pcd_list[0].points)
    for i in pcd_list[1:]:
        pcd_load = np.asarray(i.points)
        pcd_points = np.concatenate((pcd_points, pcd_load), axis=0)
    pcd_colors = np.asarray(pcd_list[0].colors)
    for i in pcd_list[1:]:
        pcd_loadc = np.asarray(i.colors)
        pcd_colors = np.concatenate((pcd_colors, pcd_loadc), axis=0)
    pcd_normals = np.asarray(pcd_list[0].normals)
    for i in pcd_list[1:]:
        pcd_loadn = np.asarray(i.normals)
        pcd_normals = np.concatenate((pcd_normals, pcd_loadn), axis=0)
    PCD = o3d.geometry.PointCloud()
    PCD.points = o3d.utility.Vector3dVector(pcd_points)
    PCD.colors = o3d.utility.Vector3dVector(pcd_colors)
    PCD.normals = o3d.utility.Vector3dVector(pcd_normals)
    return PCD


def colorindex(pcd, L):
    '''
    colorindex(pcd, L)

    Colorea los puntos contenidos en la lista L según su indice

    Parámetros
    ----------

    pcd : PCD
        Nube de puntos a colorear
    L : array
        Lista que contiene los índices de los puntos a modificar su color.

    Retorno
    ----------

    pcd : PCD
        Retorna la nube de puntos con sus elementos ya coloreados

    '''
    n = 0
    print('L', L)
    for i in L:
        n += 1
        pcd.colors[i] = [1, 0, 0]
    return pcd

def pathvis(completepath):
    '''
    pathvis(completepath)

    Visualiza el camino completepath con la librería matplotlib

    Parámetros
    ----------
    completepath: array
        Arreglo con las coordenadas a recorrer
    x : List[int]
        Límite inferior y superior del eje X
    y : List[int]
        Límite inferior y superior del eje Y
    z : List[int]
        Límite inferior y superior del eje Z
    Retorno
    ----------

    '''
    ax = plt.axes(projection='3d')
    X = []
    Y = []
    Z = []
    for i in completepath:
        points=np.asarray(i.points)
        X.append(points[:, 0])
        Y.append(points[:, 1])
        Z.append(points[:, 2])
    X = np.hstack(X)
    Y = np.hstack(Y)
    Z = np.hstack(Z)
    ax.plot3D(X, Y, Z, 'blue',linewidth=0.5, alpha=1)
    # parámetros gráfico
    all=addpoints(completepath)
    max=all.get_max_bound()
    min=all.get_min_bound()
    xl=max[0]-min[0]
    yl = max[1] - min[1]
    zl = max[2] - min[2]
    maxlimit=np.max([xl,yl,zl])
    ax.set_xlim3d([((max[0]+min[0])/2)-(maxlimit/2),((max[0]+min[0])/2)+(maxlimit/2)])
    ax.set_xlabel('X')
    ax.set_ylim3d([((max[1]+min[1])/2)-(maxlimit/2),((max[1]+min[1])/2)+(maxlimit/2)])
    ax.set_ylabel('Y')
    ax.set_zlim3d([((max[2]+min[2])/2)-(maxlimit/2),((max[2]+min[2])/2)+(maxlimit/2)])
    ax.set_zlabel('Z')
    # ax.set_aspect(auto)
    # ax.autoscale()

    plt.show()
def update_lines(num, dataLines, lines):
    for line, data in zip(lines, dataLines):
        # NOTE: there is no .set_data() for 3 dim data...
        line.set_data(data[0:2, :num])
        line.set_3d_properties(data[2, :num])
    return lines

def animate(completepath,t=1000):
    '''
    animate(completepath,x=[-100,100],y=[-100,100],z=[-100,100],t=1000)

    Visualiza una animación del camino completepath con la librería matplotlib

    Parámetros
    ----------
    completepath: array
        Arreglo con las coordenadas a recorrer
    x : List[int]
        Límite inferior y superior del eje X
    y : List[int]
        Límite inferior y superior del eje Y
    z : List[int]
        Límite inferior y superior del eje Z
    t : int
        Intervalo de tiempo entre cada cuadro de animación, en ms

    Retorno
    ----------
    '''
    fig = plt.figure()
    ax = plt.axes(projection='3d')
    X = []
    Y = []
    Z = []
    for i in completepath:
        points=np.asarray(i.points)
        X.append(points[:, 0])
        Y.append(points[:, 1])
        Z.append(points[:, 2])
    X = np.hstack(X)
    Y = np.hstack(Y)
    Z = np.hstack(Z)
    data = [np.array([X, Y, Z])]
    lines = [ax.plot(dat[0, 0:1], dat[1, 0:1], dat[2, 0:1])[0] for dat in data]
    #ax.set_title('3D Test')
    all=addpoints(completepath)
    max=all.get_max_bound()
    min=all.get_min_bound()
    xl=max[0]-min[0]
    yl = max[1] - min[1]
    zl = max[2] - min[2]
    maxlimit=np.max([xl,yl,zl])
    ax.set_xlim3d([((max[0]+min[0])/2)-(maxlimit/2),((max[0]+min[0])/2)+(maxlimit/2)])
    ax.set_xlabel('X')
    ax.set_ylim3d([((max[1]+min[1])/2)-(maxlimit/2),((max[1]+min[1])/2)+(maxlimit/2)])
    ax.set_ylabel('Y')
    ax.set_zlim3d([((max[2]+min[2])/2)-(maxlimit/2),((max[2]+min[2])/2)+(maxlimit/2)])
    ax.set_zlabel('Z')
    # corre animación

    line_ani = animation.FuncAnimation(fig, update_lines, frames=2000, fargs=(data, lines), interval=t, blit=False)
    plt.show()
# ------------------------------------------------------------------------------------------------------------------
# Generación de capas
def offset3d(pcd, h, n):
    '''
    offset3dproc(pcd, d, n)
    Generación de capas no planares desplazadas en direcciones normales a la superficie

    parámetros
    ----------
    pcd: PCD
        Nube de puntos base
    h: int
        Altura del cordón de soldadura
    n: int
        Número de capas a realizar

    Retorno
    ----------
    pcd_list: Lista de PCD
        Lista que contiene las capas generadas en formato PCD

    '''
    pcd_list = []
    pcd_list.append(normtrans(pcd, h))
    for i in range(n):
        pcd_list.append(normtrans(pcd_list[-1], h))
    pcd_list=cleanlayerpcd(pcd,pcd_list,h - h*0.2)
    return pcd_list

def multioffset3d(pcd, h, n,px=False,py=False,pz=True,nx=False,ny=False,nz=False):
    '''
    offset3dproc(pcd, d, n)
    Generación de capas no planares desplazadas en direcciones normales a la superficie

    parámetros
    ----------
    pcd: PCD
        Nube de puntos base
    h: int
        Altura del cordón de soldadura
    n: int
        Número de capas a realizar

    Retorno
    ----------
    pcd_list: Lista de PCD
        Lista que contiene las capas generadas en formato PCD

    '''
    pcd_list = []
    if pz == True:
        layer = normtrans(pcd, h, cam=[0, 0, 1])
    if py == True:
        layerf = normtrans(pcd, h, cam=[0, 1, 0])
        layer = addpoints([layer, layerf])
    if px == True:
        layerbk = normtrans(pcd, h, cam=[1, 0, 0])
        layer = addpoints([layer, layerbk])
    if nx == True:
        layerl = normtrans(pcd, h, cam=[-1, 0, 0])
        layer = addpoints([layer, layerl])
    if ny == True:
        layerr = normtrans(pcd, h, cam=[0, -1, 0])
        layer = addpoints([layer, layerr])
    if nz == True:
        layerb = normtrans(pcd, h, cam=[0, 0, -1])
        layer = addpoints([layer, layerb])

    pcd_list.append(layer)

    for i in range(n):
        if pz==True:
            layer=normtrans(pcd_list[-1], h,cam=[0,0,1])
        if py==True:
            layerf = normtrans(pcd_list[-1], h,cam=[0,1,0])
            layer=addpoints([layer,layerf])
        if px==True:
            layerbk = normtrans(pcd_list[-1], h, cam=[1, 0, 0])
            layer = addpoints([layer, layerbk])
        if nx==True:
            layerl = normtrans(pcd_list[-1], h, cam=[-1, 0, 0])
            layer = addpoints([layer, layerl])
        if ny==True:
            layerr = normtrans(pcd_list[-1], h, cam=[0, -1, 0])
            layer = addpoints([layer, layerr])
        if nz==True:
            layerb = normtrans(pcd_list[-1], h, cam=[0, 0, -1])
            layer = addpoints([layer, layerb])

        pcd_list.append(layer)

    return pcd_list

def normtrans(pcd,h,cam=[0,0,1]):
    '''
    normtransproc(pcd,h)
    Crea una capa sobre la superficie de la nube de puntos, trasladando cada punto de la nube PCD una distancia h en la dirección de su normal

    parámetros
    ----------
    pcd: PCD
        Nube de puntos base
    h: int
        Altura del cordón de soldadura

    Retorno
    ----------
    d: PCD
        Nube de puntos de la capa generada sobre la superficie de la nube de puntos base

    '''
    c = o3d.geometry.PointCloud()
    p1 = np.asarray(pcd.points)  # puntos de la nube
    v1 = np.asarray(pcd.normals)  # vectores normales de la nube
    p2 = p1 + v1 * h
    c.points = o3d.utility.Vector3dVector(p2)
    c.colors = o3d.utility.Vector3dVector(np.asarray(pcd.colors))
    c.estimate_normals()
    c.orient_normals_to_align_with_direction(np.asarray(cam))
    c.remove_statistical_outlier(5, h)
    diameter = np.linalg.norm(np.asarray(c.get_max_bound()) - np.asarray(c.get_min_bound()))
    camera = np.asarray(cam)*diameter
    radius = diameter * 1000
    _, pt_map = c.hidden_point_removal(camera, radius)
    d = c.select_by_index(pt_map)
    return d

# Separación en secciones
# ----------------------------------------------------------------------------------------------------
def preslice01(pcd, d=3, v=(0.85, 0.85, 0 ),voxel_size=0.05) :
    '''
    slice01(pcd, w=1, v=(0, 1, 0))
    secciona la nube de puntos intersecando planos equiespaciados en distancia d , con normal en v

    parámetros
    ----------
    pcd: PCD
        Nube de puntos base a intersecar
    d : int
        Distancia que separa a los planos
    v : array (x,y,z)
        Vector que indica la normal de los planos

    Retorno
    ----------
    [pcd_list, pcd_tot]
    pcd_list: Lista de PCD
        Contiene las intersecciones de los planos con la superficie de la nube base.
    pcd_tot:
        Nube de puntos que contiene todas las intersecciones.

    '''
    pcd=copy.deepcopy(pcd)

    points = np.asarray(pcd.points)
    center=pcd.get_center()
    newpoints=points-center
    A=np.asarray(v)*(-1)
    ind = np.argmax(np.dot(newpoints,A))
    p=points[ind]
    minbound=pcd.get_min_bound()
    maxbound=pcd.get_max_bound()
    b=np.linalg.norm(maxbound-minbound)*2
    pl = plane(p,b, d)
    R = pl.get_rotation_matrix_from_xyz((np.pi / 2, 0, 0))
    pl.rotate(R)
    R2 = pl.get_rotation_matrix_from_xyz((0,0,np.arccos(v[0])-np.pi/2))  # -np.pi/4
    pl.rotate(R2)
    pcd_list = []
    pcd_list.append(intersect(pcd, pl,d/4))
    while len(np.asarray(pcd_list[-1].points)) != 0:
        pl = pl.translate(np.array(v) * d)
        pcd_list.append(intersect(pcd, pl, d/4))
    pcd_list.pop(-1)
    pcd_list = color(pcd_list)
    return pcd_list

def preslice02(pcd, d=1,voxel_size=0.05,center=[0,0,0],clockwise=False ) :
    '''
    slice02(pcd, d=1, v=(0, 1, 0))
    secciona la nube de puntos intersecando espirales de euclides con distancia entre ciclos d, con normal en v

    parámetros
    ----------
    pcd: PCD
        Nube de puntos base a intersecar
    d : int
        Distancia que separa a los planos
    v : array (x,y,z)
        Vector que indica la normal de los planos

    Retorno
    ----------
    [pcd_list, pcd_tot]
    pcd_list: Lista de PCD
        Contiene las intersecciones de los planos con la superficie de la nube base.
    pcd_tot:
        Nube de puntos que contiene todas las intersecciones.

    '''
    pcdp = copy.deepcopy(pcd)  # Nube de puntos a proyectar, crea una copia para no modificar la original
    points = np.asarray(pcdp.points)
    c= o3d.geometry.PointCloud()
    c.points=o3d.utility.Vector3dVector(np.c_[center[0],center[1],center[2]])
    dist = np.asarray(pcdp.compute_point_cloud_distance(c))
    ind = np.where(dist==np.min(dist))[0][0]
    minbound=pcdp.get_min_bound()
    maxbound=pcdp.get_max_bound()
    p=points[ind]
    q=copy.deepcopy(p)
    q[2]=minbound[2]
    D=np.linalg.norm(maxbound-minbound)*2
    sp = spiral(d, D,c=q,clockwise=clockwise,t=int(d/4))  # crea espiral
    pcd_list = []
    i=1
    n=int(maxbound[2]-minbound[2])+1
    pr = projection(sp[0], n, (0, 0, -1), 1)  # proyecta la espiral
    pcd_list.append(intersect(pcdp, pr[0],d/6)) #intersecta la espiral
    while len(np.asarray(pcd_list[-1].points)) != 0 and i < len(pr):
            pcd_list.append(intersect(pcdp, pr[i],d/6))
            i += 1

    pcd_list.pop(-1)
    pcd_list = color(pcd_list)

    return pcd_list

def projection(pcd_list, n=10, v=(0, 0, 1), d=0.5):  # repite n veces la nube PCD en la dirección v
    '''
    projection(pcd_list, n=10, v=(0, 0, 1), d=1)

    Repite n veces la nube PCD en la dirección v, con una separación d

    Parámetros
    ----------
    pcd_list: Lista de PCD
        Contiene una lista con archivos PCD
    n: int
        Número de repeticiones
    v : array (x,y,z)
        Vector en que se repetirán las nubes de puntos
    d : int
       Distancia de separación entre repeticiones

    Retorno
    ----------
    pcd_list2 : Lista de PCD
        Contiene las proyecciones de cada nube de puntos de la lista de PCD original.

    '''

    pcd_list2 = []
    for i in pcd_list:
        i.translate((np.array(v) * (-d)*(n+1)))
        pr = o3d.geometry.PointCloud()
        pcd_points = np.asarray(i.points)
        for j in np.arange(1, n*2, 1):
            pcd_load = np.asarray(i.points)
            pcd_points = np.concatenate((pcd_points, pcd_load), axis=0)
            i.translate((np.array(v) * d))
            pr.points = o3d.utility.Vector3dVector(pcd_points)
        pcd_list2.append(pr)
    return pcd_list2
# ------------------------------------------------------------------------------------------------------------------
#Recorrido
def slice01(pcd, v=(1, 0, 0), d=5):
    '''
    slice01(pcd, v=(1, 0, 0), d=5):
    Función que se encarga de generar una trayectoria con puntos distanciados en distacncia d, que recorren la línea de
    puntos pcd, en la dirección del vector v
    :param pcd: Nube de puntos a recorrer
    :param v: Vector que indica la dirección en que se recorrerá
    :param d: Distancia entre los puntos a recorrer
    :return pathpcd: Nube de puntos con los puntos de la trayectoria
    '''
    pcd = copy.deepcopy(pcd)
    pcd.normalize_normals()
    pcd_tree = o3d.geometry.KDTreeFlann(pcd)
    path = []
    points = np.asarray(pcd.points)
    points2 = [arr.tolist() for arr in points]
    normals= np.asarray(pcd.normals)
    center=pcd.get_center()
    newpoints=points-center
    A=np.asarray(v)*(-1)
    ind = np.argmax(np.dot(newpoints,A))
    ind2 = ind + 1
    i = 0
    c1=[]
    c2=[]
    c3=[]
    n1=[]
    n2=[]
    n3=[]
    c1.append(points[ind][0])
    c2.append(points[ind][1])
    c3.append(points[ind][2])
    n1.append(normals[ind][0])
    n2.append(normals[ind][1])
    n3.append(normals[ind][2])
    while ind not in path: #Se detiene al elegir un punto ya contenido en la trayectoria (lo cual puede indicar un borde)
        path.append(ind)
        [k, idx, _] = pcd_tree.search_radius_vector_3d(pcd.points[ind], d)
        # np.asarray(pcd.colors)[idx[1:], :] = [0, 1, 0]
        np.asarray(pcd.colors)[ind] = [1, 0, 0]
        [k, idx2, _] = pcd_tree.search_knn_vector_3d(pcd.points[ind], 5)  # selección de los vecinos de ind
        ns = np.asarray(pcd.normals)[idx2]  # array para trabajar con ellos
        [x, y, z] = [np.mean(ns[:, 0]), np.mean(ns[:, 1]),np.mean(ns[:, 2])]  # promedio de las normales de los vecinos de ind
        c = np.c_[x, y, z]  # nueva normal
        np.asarray(pcd.normals)[ind] = o3d.utility.Vector3dVector(c)  # reescribe la normal del punto seleccionado con el promedio de sus vecinos
        h = points[idx]
        h2 = h - (np.ones_like(h) * points[ind])  # cambia el 0 de los puntos
        dot = np.dot(h2, v)  # producto punto para determinar los vecinos ubicados en la dirección deseada
        max = h[np.argmax(dot)]  # selección del vecino más lejano en la dirección deseada
        if path[0] in idx and i>2:
            path.pop(-1)
            c1.pop(-1)
            c2.pop(-1)
            c3.pop(-1)
            n1.pop(-1)
            n2.pop(-1)
            n3.pop(-1)
            print('break',i)
            break
        ind2 = ind
        max2=np.asarray(max)
        max2=[arr.tolist() for arr in max2]
        ind= points2.index(max2)
        i += 1
        c1.append(points[ind][0])
        c2.append(points[ind][1])
        c3.append(points[ind][2])
        n1.append(normals[ind][0])
        n2.append(normals[ind][1])
        n3.append(normals[ind][2])

    pathpoints=np.c_[c1, c2, c3]
    pathnormals = np.c_[n1, n2, n3]
    pathpcd = o3d.geometry.PointCloud()
    pathpcd.points = o3d.utility.Vector3dVector(pathpoints)
    pathpcd.normals = o3d.utility.Vector3dVector(pathnormals)
    pathpcd.paint_uniform_color((0,0,1))
    return pathpcd

def arctanfull(y,x):
    '''
    arctanfull(y,x):
    Función que devuelve la arcotangente de x/y, se diferencia de arctan2 ya que su recorrido va de 0 a 2pi
    :param y: Valor en y
    :param x: Valor en x
    :return angle: Valor del ángulo en el plano
    '''
    angle=np.arctan2(y,x)
    ind=np.where(angle<0)[0]
    negativeangle=2*np.pi+angle
    angle[ind]=negativeangle[ind]
    return angle

def slice02(pcd, d=5,clockwise=False,center=[0,0,0]):
    '''
    slice02(pcd, d=5,clockwise=False):
    Función que se encarga de generar una trayectoria con puntos distanciados en distacncia d, que recorren la línea de
    puntos en espiral pcd , en sentido horario o antihorario
    :param pcd: Nube de puntos
    :param d: Ancho del cordón de soldadura
    :param clockwise: Indica el sentido de la espiral recorrida
    :return:
    '''

    pcd = copy.deepcopy(pcd)
    #pcd.normalize_normals()
    pcd_tree = o3d.geometry.KDTreeFlann(pcd)
    path = []
    points = np.asarray(pcd.points)
    points2 = [arr.tolist() for arr in points]
    normals= np.asarray(pcd.normals)
    c = o3d.geometry.PointCloud()
    c.points = o3d.utility.Vector3dVector(np.c_[center[0], center[1], center[2]])
    angle = arctanfull(points[:,1]-center[1],points[:,0]-center[0])
    if clockwise==True:
        cw=-1
        ind = np.where(angle == np.max(angle))[0][0]
    else:
        cw=1
        ind = np.where(angle == np.min(angle))[0][0]
    p = points[ind]
    theta=angle[ind]
    v=(np.cos(theta+(np.pi/2)*cw),np.sin(theta+(np.pi/2)*cw),0)
    ind2 = ind + 1
    # dirección sugerida para buscar el máximo
    i = 0
    c1=[]
    c2=[]
    c3=[]
    n1=[]
    n2=[]
    n3=[]
    c1.append(points[ind][0])
    c2.append(points[ind][1])
    c3.append(points[ind][2])
    n1.append(normals[ind][0])
    n2.append(normals[ind][1])
    n3.append(normals[ind][2])
    #while theta<=(np.pi*2):
    while ind not in path:  # Se detiene al quedar en el mismo punto
        path.append(ind)
        [k, idx, _] = pcd_tree.search_radius_vector_3d(pcd.points[ind], d)
        np.asarray(pcd.colors)[ind] = [1, 0, 0]
        [k, idx2, _] = pcd_tree.search_knn_vector_3d(pcd.points[ind], 5)  # selección de los vecinos de ind
        ns = np.asarray(pcd.normals)[idx2]  # array para trabajar con ellos
        [x, y, z] = [np.mean(ns[:, 0]), np.mean(ns[:, 1]),
                     np.mean(ns[:, 2])]  # promedio de las normales de los vecinos de ind
        c = np.c_[x, y, z]  # nueva normal
        np.asarray(pcd.normals)[ind] = o3d.utility.Vector3dVector(c)  # reescribe la normal del punto seleccionado con el promedio de sus vecinos
        h = points[idx]
        h2 = h - (np.ones_like(h) * points[ind])  # cambia el 0 de los puntos
        dot = np.dot(h2, v)  # producto punto para determinar los vecinos ubicados en la dirección deseada
        max = h[np.argmax(dot)]  # selección del vecino más lejano en la dirección deseada
        if path[0] in idx and i > 2:
            path.pop(-1)
            c1.pop(-1)
            c2.pop(-1)
            c3.pop(-1)
            n1.pop(-1)
            n2.pop(-1)
            n3.pop(-1)
            break
        if  i > 3:
            if path[-1] in idx:
                path.pop(-1)
                c1.pop(-1)
                c2.pop(-1)
                c3.pop(-1)
                n1.pop(-1)
                n2.pop(-1)
                n3.pop(-1)
                break
        ind2 = ind
        max2=np.asarray(max)
        max2=[arr.tolist() for arr in max2]
        ind= points2.index(max2)

        i += 1
        c1.append(points[ind][0])
        c2.append(points[ind][1])
        c3.append(points[ind][2])
        n1.append(normals[ind][0])
        n2.append(normals[ind][1])
        n3.append(normals[ind][2])
        norm = np.linalg.norm(
            points[ind2] - points[ind])  # norma del vector, para poder convertirlo en vector unitario
        if norm == 0:
            break
        v = np.transpose((points[ind] - points[ind2]) / norm)
        p=points[ind]
        theta=arctanfull([p[1]-center[1]],[p[0]-center[0]])
        v2 = (np.cos(theta + (np.pi / 2) * cw), np.sin(theta + (np.pi / 2) * cw), 0)
        turn=np.dot(v, v2)
        v=v2
        #print(turn)
        if turn < 0:
            break
        # ind = np.where(dist == np.min(dist))[0][0]
        # p = points[ind]
        # theta = np.arccos(p[0] / np.sqrt(((p[0] - center[0]) ** 2 + (p[1] - center[1]) ** 2)))
    pathpoints=np.c_[c1, c2, c3]
    pathnormals = np.c_[n1, n2, n3]
    pathpcd = o3d.geometry.PointCloud()
    pathpcd.points = o3d.utility.Vector3dVector(pathpoints)
    pathpcd.normals = o3d.utility.Vector3dVector(pathnormals)
    pathpcd.paint_uniform_color((0,0,1))
    return pathpcd

def completepath01(pcd_list,v,d):
    '''
    completepath(pcd_list)

    Recorre la lista de nubes de puntos con la función slice01 para raster

    Parámetros
    ----------

    pcd_list : Lista de PCD
        Lista que contiene los PCD a recorrer

    Retorno
    ----------
    [completepath, completepathpcd]

    completepath : Lista
        Lista con las coordenadas de cada recorrido

    completepathpcd : Lista de PCD
        Lista con las nubes de puntos de los recorridos
    '''
    completepathpcd = []
    n=0
    for i in pcd_list:
        p = slice01(i,v,d)
        completepathpcd.append(p)
        nointer=deleteintersect(i,p,d)
        while len(np.asarray(nointer.points))!=0:
            n+=1
            p=slice01(nointer,v,d)
            nointer=deleteintersect(nointer,p,d)
            completepathpcd.append(p)
        v=(np.ones_like(v)*(-1))*v

    return completepathpcd

def completepath02(pcd_list,d,clockwise=False,center=[0,0,0]):
    '''
    completepath(pcd_list)

    Recorre la lista de nubes de puntos con la función rec1 para raster

    Parámetros
    ----------

    pcd_list : Lista de PCD
        Lista que contiene los PCD a recorrer

    Retorno
    ----------
    [completepath, completepathpcd]

    completepath : Lista
        Lista con las coordenadas de cada recorrido

    completepathpcd : Lista de PCD
        Lista con las nubes de puntos de los recorridos
    '''
    completepathpcd = []
    n = 0
    for i in pcd_list:
        D=np.linalg.norm(i.points[0]-center)
        s = 0
        if D < 3*d:
            ini=0.5
        else:
            ini=1
        p = slice02(i,d*ini,clockwise)
        completepathpcd.append(p)
        nointer=deleteintersect(i,p,d*1.2*ini)
        n+=1
        while len(np.asarray(nointer.points))!=0:
            p = slice02(nointer, d*ini, clockwise)
            nointer = deleteintersect(nointer, p, d*1.2*ini)
            completepathpcd.append(p)
            #print(n,s)
            s+=1
    return completepathpcd

def addsafepoints(completepathpcd,h,d):
    '''
    addsafepoints(completepathpcd,h,d):
    Añade puntos a la trayectoria permitiendo que la herramienta se levante 5 veces h, cuando la distancia entre 2 puntos supera
    en 2.5 veces la distancia d
    :param completepathpcd:
    :param h: Altura del cordón
    :param d: Distancia entre cordones
    :return: Nube de puntos con la trayectoria con puntos donde se levanta la herramienta
    '''
    completepathpcdsp=copy.deepcopy(completepathpcd)
    for i in np.arange(0,len(np.asarray(completepathpcdsp))-1,1):
        dist= np.linalg.norm( completepathpcd[i+1].points[0]-completepathpcd[i].points[-1])
        if dist > 2.5*d:
            fin=edgepoint(completepathpcdsp[i],5*h,end=True)
            ini=edgepoint(completepathpcdsp[i+1],5*h,end=False)
            completepathpcdsp[i].colors[-1]= ((1,0,0))
            completepathpcdsp[i+1].colors[0] = ((0, 1, 0))
            completepathpcdsp[i+1]=addpoints([fin,ini,completepathpcdsp[i+1]])
    return completepathpcdsp

def uniquepoints(pcd_list):
    completepath=addpoints(pcd_list)
    ind=np.unique(np.asarray(completepath.points),return_index=True)[1]
    unique=o3d.geometry.PointCloud()
    points= np.asarray(completepath.points)[ind]
    colors=np.asarray(completepath.colors)[ind]
    normals= np.asarray(completepath.normals)[ind]
    unique.points = o3d.utility.Vector3dVector(np.c_[points[:,0], points[:,1], points[:,2]])
    unique.colors = o3d.utility.Vector3dVector(np.c_[colors[:,0], colors[:,1], colors[:,2]])
    unique.normals = o3d.utility.Vector3dVector(np.c_[normals[:,0], normals[:,1], normals[:,2]])
    return unique

def edgepoint(pcd,L,end=False):
    '''
        endpoint(pcd,L,end=False)):
        Función utilizada para agregar puntos finales e iniciales en la trayectoria
    :param pcd:
    :param L: Indica la distancia de elevación para el nuevo punto
    :param end: Indica si es un punto terminal o no, si es Falso, significa que es un punto inicial

    :return:  Retorna una nube de puntos de un solo punto
    '''
    pcd=copy.deepcopy(pcd)
    p = o3d.geometry.PointCloud()
    if end==True:
        i=-1
    else:
        i = 0
    c = np.asarray(pcd.points)[i]
    c[2]=c[2]+L
    p.points = o3d.utility.Vector3dVector(np.c_[c[0], c[1], c[2]])
    p.paint_uniform_color((1,0,0))
    p.normals = o3d.utility.Vector3dVector(np.c_[0, 0, 1])
    #print(np.asarray(p.points),np.asarray(pcd.points)[-1],np.asarray(pcd.points)[0])
    return p

# ------------------------------------------------------------------------------------------------------------------
#Escritura programa
def wristvector(normal):
    '''
        wristvector(normal)
        Función que entrega el vector que indica la orientacíon de la "muñeca" del robot panasonic según la normal de la superficie
    :param normal:
    :return wv: Vector que indica la dirección de la muñeca del robot
    '''
    wv=copy.deepcopy(normal)
    wv[2]=0
    wv[0] = 1
    wv[1] = 0
    #print('wv',wv)
    return wv

def dtpspoints(path_list,name='outfile',s=0.2,ampere=100):
    '''
    dtpspoints(path_list)
    Crea un archivo CSR para ser leído por el programa DTPS

    parámetros
    ----------
    path_list : array
        Lista que contiene las coordenadas

    Retorno
    ----------
    none

    '''
    outfilename_default = name+'.csr'
    outfilepath_default = r'..\Programas Escritos\{}'.format(outfilename_default)
    #Strings de parámetros
    description= '''[Description]
Robot, TM1400(G3) 
Comment, 
SubComment1,
SubComment2, 
Mechanism, 1(0001) 
Tool, 1:TOOL01 
Creator, IMA+ 
User coordinates, None 
Create, 2021, 03, 17, 11, 05, 26
Update, 2021, 03, 17, 11, 05, 26 
Original, 
Edit, 0

[Work]
Position, 5, 0, 0, 10, -0, 0, 0

[Pose]
/Name, Type, X, Y, Z, X1, X2, X3, Z1, Z2, Z3, G4'''+'\n'
    variable='''[Variable]
LB, LB001, , 0
LB, LB002, , 0
LB, LB003, , 0
LB, LB004, , 0
LB, LB005, , 0
LI, LI001, , 0
LI, LI002, , 0
LI, LI003, , 0
LI, LI004, , 0
LI, LI005, , 0
LL, LL001, , 0
LL, LL002, , 0
LL, LL003, , 0
LL, LL004, , 0
LL, LL005, , 0
LR, LR001, , 0.000000000000000
LR, LR002, , 0.000000000000000
LR, LR003, , 0.000000000000000
LR, LR004, , 0.000000000000000
LR, LR005, , 0.000000000000000

[Command]
TOOL, 1:TOOL01'''+'\n'
    l=1
    command=[]
    try:
        fileID = open(outfilename_default, mode='x', encoding='UTF-8')
        fileID.write(description)
        for i in np.arange(0,len(path_list),1):
            points=path_list[i].points
            normals=path_list[i].normals
            colors=path_list[i].colors
            for j in np.arange(0,len(points),1):
                if colors[j][0]==1:
                    if colors[j-1][2]==1:
                        command.append('ARC-OFF, ArcEnd1.rpg, 0'+'\n'+'DELAY, 3'+ '\n')
                    command.append('MOVEL, P' + str(l) + ','+str(50) +', m/min, 0, N, -1' + '\n')
                if colors[j][1]==1:
                    command.append('ARC-SET,' +str(ampere)+','+str(volt(ampere))+ ',0.5'+'\n'+'ARC-ON, ArcStart1.rpg, 0'+'\n')
                    command.append('MOVEL, P' + str(l) + ','+str(s) +', m/min, 0, W, -1' + '\n')
                if colors[j][2]==1:
                    command.append('MOVEL, P' + str(l) + ','+str(s) +', m/min, 0, W, -1' + '\n')
                #Código con herramienta que sigue la orientaicón normal a la superficie---------------------------------
                # fileID.write('P' + str(l) + ', AV,' + np.array2string(points[j], separator=',', prefix='',
                #                                                       suffix='').translate(
                #     {ord(h): None for h in '[]'}) + ',' + np.array2string(normals[j] * (-1), separator=',', prefix='',
                #                                                           suffix='').translate(
                #     {ord(h): None for h in '[]'})+','+ np.array2string(wristvector(normals[j]), separator=',', prefix='',
                #                                                           suffix='').translate(
                #     {ord(h): None for h in '[]'}) +'\n')
                #Código con orientación de la herramienta fija--------------------------------------------------------
                #
                fileID.write('P' + str(l) + ', AV,' + np.array2string(points[j], separator=',', prefix='',
                                                                      suffix='').translate(
                    {ord(h): None for h in '[]'}) + ',' + "0,0,-1,1,0,0" +'\n')
                #------------------------------------------------------------------------------------------
                l+=1
        fileID.write(variable)
        fileID.write('MOVEL, P' + str(1) + ','+str(s) +', m/min, 0, N, -1' + '\n')
        #fileID.write('MOVEL, P' + str(1) + ',' + str(s) + ', m/min, 0, N, -1' + '\n')
        fileID.write('''ARC-SET, '''+str(ampere)+','+str(volt(ampere)) +''', 0.50
ARC-ON, ArcStart1.rpg, 0'''+'\n')
        for n in command:
            fileID.write(n)
        fileID.write('''CRATER, '''+str(ampere)+','+str(volt(ampere)) +''', 0.00
ARC-OFF, ArcEnd1.rpg, 0
DELAY, 3''')
        fileID.close()
    except FileExistsError:
        print('EXISTE')

