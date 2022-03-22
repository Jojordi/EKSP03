import wx
import shapely
import trimesh
import numpy as np
import numpy.linalg as la
from scipy.spatial.transform import Rotation
from typing import Callable, List, Union, Tuple


def angulo_entre_vectores(vector1: Tuple[float, float, float], vector2: Tuple[float, float, float]) -> float:
    """
        Calcula el ángulo que hay entre los vectores dados.
        Resultado se entrega en grados.

        Parameters
        ----------
        vector1 : Tuple[float, float, float]
            
        vector2 : Tuple[float, float, float]

        Returns
        -------
        float
            ángulo entre los vectores ingresados
    """

    vector1 = np.asarray(vector1)
    vector2 = np.asarray(vector2)
    dot_pr = vector1.dot(vector2)
    norms = np.linalg.norm(vector1) * np.linalg.norm(vector2)
    return np.rad2deg(np.arccos(dot_pr / norms))


def traslacion3d(puntos: np.ndarray, vector_traslacion: Tuple[float, float, float]=[0, 0, 0]) -> np.ndarray:
    """
        Traslada puntos una distancia indicada por vector_traslacion.

        Parameters
        ----------
        puntos : np.ndarray
            puntos que se quieren trasladar, por ejemplo: vértices de una pieza
        vector_traslacion : Tuple[float, float, float], optional
            vector para realizar la traslación, by default (0, 0, 0)

        Returns
        -------
        np.ndarray
            los puntos trasladados
    """
    return puntos + vector_traslacion


def rotar_pieza(pieza: np.ndarray, centro: Tuple[float, float, float], grados: Tuple[float, float, float]=[0, 0, 0]) -> np.ndarray:
    """
        Rota pieza, mediante sus vértices (n, 3) y los grados elegidos.\n
        Rotación se hace con respecto al centro de la pieza en orden 'zyx'

        Parameters
        ----------
        pieza : np.ndarray
            vértices de la pieza que se quiere rotar
        centro : Tuple[float, float, float]
            centroide de la pieza a rotar
        grados : Tuple[float, float, float], optional
            vector que contiene los grados a rotar, by default (0, 0, 0)

        Returns
        -------
        np.ndarray
            vértices rotados
    """
    
    # Centrar pieza para rotar respecto a centro
    pieza_rotada = pieza - centro
    r = Rotation.from_euler('zyx', [grados[2],
                                    grados[1],
                                    grados[0]], degrees=True)
    pieza_rotada = r.apply(pieza_rotada)
    # Devolver a posición original
    pieza_rotada += centro

    return pieza_rotada


def agregar_validador(elementos: List[wx.TextEntry], validador: Callable) -> None:
    """
        Realiza Bind de la función validadora a la lista de elementos.

        Parameters
        ----------
        elementos : List[wx.TextEntry]
            entradas de texto a las cuales se les quiere validar inputs
        validador : Callable
            función que valida inputs puestos en elementos
    """
    for elemento in elementos:
        try:
            elemento.Bind(wx.EVT_CHAR, validador)
        except AttributeError:
            continue


def validador_numerico_basico(event: wx.EVT_CHAR) -> None:
    """
        Valida que ingreso de string corresponda a número. 
        También permite se puedan borrar números y agregar un punto decimal.
        Útil para casos donde se quiere permitir solo números positivos.

        Parameters
        ----------
        event : wx.EVT_CHAR
    """

    dato_ingresado = chr(event.GetUnicodeKey())
    dato_uni = event.GetKeyCode()
    obj = event.GetEventObject()
    
    if obj.GetValue() == '':
        obj.SetValue('0')

    if dato_ingresado.isdigit():
        if obj.GetValue() == '0':
            obj.SetValue(dato_ingresado)
            obj.SetInsertionPointEnd()

        # Estas condiciones permiten casos como '0000012.' pero ese número puede ser convertido en float
        elif obj.GetInsertionPoint() == 0 and dato_ingresado == '0' and '.' not in obj.GetValue():
            pass

        else:
            event.Skip()
    
    elif dato_ingresado == '.' and dato_ingresado not in obj.GetValue():
        event.Skip()
        
    if dato_uni in [wx.WXK_BACK, wx.WXK_RIGHT, wx.WXK_LEFT, wx.WXK_DELETE]:
        event.Skip()


def validador_numerico_general(event: wx.EVT_CHAR) -> None:
    """
        Valida que al ingresar dígitos, el string final corresponda a número, cumpliendo formatos válidos.
        Permite se puedan borrar números, agregar un punto decimal, y el ingreso del signo '-'.
        Evita que se puedan ingresar números como '.-12', '12-', o '-012'.

        Parameters
        ----------
        event : wx.EVT_CHAR
    """

    dato_ingresado = chr(event.GetUnicodeKey())
    dato_uni = event.GetKeyCode()
    obj = event.GetEventObject()

    if obj.GetValue() == '':
        obj.SetValue('0')

    if dato_uni in [wx.WXK_BACK, wx.WXK_RIGHT, wx.WXK_LEFT, wx.WXK_DELETE]:
        event.Skip()
    
    # Las situaciones son: ingresar dígito, '.', y '-'
    if dato_ingresado.isdigit():
        if obj.GetValue() == '0':
            obj.SetValue(dato_ingresado)
            obj.SetInsertionPointEnd()
        
        else:
            if obj.GetInsertionPoint() == 0:
                # Estas condiciones permiten casos como '0000012.' pero ese número puede ser convertido en float
                if dato_ingresado == '0' and '.' not in obj.GetValue():
                    pass
                # Condición evita casos como '12-'
                elif '-' not in obj.GetValue():
                    event.Skip()
            # Condición evita casos como -012
            elif obj.GetInsertionPoint() == 1 and '-' in obj.GetValue():
                if dato_ingresado == '0' and '.' not in obj.GetValue():
                    pass
                else:
                    event.Skip()
            else:
                event.Skip()
    
    # Con evita casos como '.-12'
    elif dato_ingresado == '.' and dato_ingresado not in obj.GetValue():
        if obj.GetInsertionPoint() != 0 or '-' not in obj.GetValue():
            event.Skip()
        
    elif dato_ingresado == '-' and dato_ingresado not in obj.GetValue():
        # De esta forma nos aseguramos que se coloque al principio
        if obj.GetValue() == '0':
            obj.SetValue(dato_ingresado)
            obj.SetInsertionPointEnd()
        else:
            # Condición evita casos como '-012'
            # Si encuentra un 0 como primer número, elimina todo 0 extra
            if obj.GetValue()[0] == '0':
                num = 0
                for char in obj.GetValue():
                    if char == '0':
                        num += 1
                    else:
                        break
                replaced = obj.GetValue().replace('0', '', num)
                if replaced[0] == '.':
                    obj.SetValue(dato_ingresado + '0' + replaced)
                else:
                    obj.SetValue(dato_ingresado + replaced)
            else:
                obj.SetValue(dato_ingresado + obj.GetValue())
            obj.SetInsertionPoint(1)


def select_layer(data: Union[trimesh.Trimesh, Tuple[trimesh.Trimesh, trimesh.Trimesh]], 
                height_cordon: float=0, width_cordon: float=0, 
                step_over: float=0) -> Tuple[np.ndarray, str]:
    """
        Calcula las alturas a usar para cortar pieza trimesh.Trimesh. En caso de ingresar una lista con 
        dos piezas, se asume que la primera es la dañada y la segunda es modelo ideal. En ese caso se
        usa la altura menor del modelo dañado y la mayor del ideal para definir la sección de alturas.
        Ese modo es útil para cuando se quieren cortar los modelos y luego comparar cortes.
        Retorna np.ndarray con las alturas calculadas para cortes. 
        Alturas son calculadas de acuerdo a la geometría de los cordones de soldadura.

        Parameters
        ----------
        data : trimesh.Trimesh o Tuple[trimesh.Trimesh, trimesh.Trimesh]
            pieza a la cual se le quiere realizar cortes para detección de daños
        height_cordon : float, optional
            altura de cordón de soldadura, by default 0
        width_cordon : float, optional
            ancho de cordón de soldadura, by default 0
        step_over : float, optional
            step-over entre cordones de soldadura, by default 0

        Returns
        -------
        Tuple[np.ndarray[float], str]
            array con las alturas a utilizar para cortes y mensaje indicando cantidad de alturas
    """
    # Como opción puedes dar lista con 2 modelos para elegir sección de alturas
    # útil para casos donde 
    if isinstance(data, list):
        start = data[0].bounds[0][2]  # Modelo dañado
        stop = data[1].bounds[1][2]  # Modelo ideal
    else:
        start = data.bounds[0][2]
        stop = data.bounds[1][2]
    # Alto de cordón de última capa, necesitas ser sobredimensionado para mecanizado
    t = height_cordon * (1 - ((step_over / width_cordon) ** 2))
    # Alturas de capas dependen de P, óptimo P == H
    # Alturas en milímetros, parte en altura H para dar espacio al cordón
    alturas_z = np.arange(start=start, stop=stop, step=t)
    # Espacio entre alturas de cordones y altura de las capas
    vacio_z = stop - alturas_z[-1]

    # Si diferencia mayor a T, agregar otra capa
    if vacio_z < t:
        msge = 'SE CUBRE DAÑO Y HAY EXCESO, '
    else:
        msge = 'ES NECESARIO AÑADIR CAPA EXTRA PARA CUBRIR DAÑO, '
        v_t = t + alturas_z[-1]
        alturas_z = np.append(alturas_z, v_t)

    msge += 'CANTIDAD DE CORTES A UTILIZAR: {}\n'.format(len(alturas_z))

    return alturas_z, msge


def calcular_cilindro(puntos: Tuple[Tuple[float, float, float],
                            Tuple[float, float, float],
                            Tuple[float, float, float]]) -> Tuple[Tuple[float, float], float]:
    """
        Estima centro y radio de un cilindro, dados 3 puntos en la circunferencia del círculo
        correpondiente a su seccion transversal. Centro corresponde a coordenadas en plano YZ.
        Se usa el método del determinante.

        Parameters
        ----------
        puntos : Tuple[Tuple[float, float, float], Tuple[float, float, float], Tuple[float, float, float]]
            3 puntos en la superficie sana (sin daños) del cilindro

        Returns
        -------
        Tuple[Tuple[float, float], float]
            centro y radio del cilindro
    """
    
    centro = [0, 0]
    p1 = puntos[0]
    p2 = puntos[1]
    p3 = puntos[2]
    
    matrix_a = np.asarray([[p1[1], p1[2], 1],
                        [p2[1], p2[2], 1],
                        [p3[1], p3[2], 1]])

    matrix_b = -1 * np.asarray([[p1[1]**2 + p1[2]**2, p1[2], 1],
                            [p2[1]**2 + p2[2]**2, p2[2], 1],
                            [p3[1]**2 + p3[2]**2, p3[2], 1]])

    matrix_c = np.asarray([[p1[1]**2 + p1[2]**2, p1[1], 1],
                        [p2[1]**2 + p2[2]**2, p2[1], 1],
                        [p3[1]**2 + p3[2]**2, p3[1], 1]])

    matrix_d = -1 * np.asarray([[p1[1]**2 + p1[2]**2, p1[1], p1[2]],
                            [p2[1]**2 + p2[2]**2, p2[1], p2[2]],
                            [p3[1]**2 + p3[2]**2, p3[1], p3[2]]])

    det_a = la.det(matrix_a)
    det_b = la.det(matrix_b)
    det_c = la.det(matrix_c)
    det_d = la.det(matrix_d)

    centro[0] = -det_b / (2 * det_a)
    centro[1] = -det_c / (2 * det_a)

    radio = np.sqrt((det_b**2 + det_c**2 - 4 * det_a * det_d) / (4 * det_a**2))

    return centro, radio


def encontrar_plano_cono(puntos: Tuple[np.ndarray, np.ndarray, np.ndarray]) -> np.ndarray:
    """
        Estima normal del plano de la base del cono.
        Asume que base es circunferencial.

        Parameters
        ----------
        puntos : Tuple[np.ndarray, np.ndarray, np.ndarray]
            puntos pertenecientes a la circunferencia de la base del cono

        Returns
        -------
        np.ndarray
            vector normal de la base del cono
    """

    p1 = puntos[0]
    p2 = puntos[1]
    p3 = puntos[2]

    vector1 = p2 - p1
    vector2 = p3 - p1
    normal = np.cross(vector1, vector2)
    normal = abs(normal / np.linalg.norm(normal))
    return normal


def transform_cilindrical(points: np.ndarray, radio: float=1, inv: bool=False) -> np.ndarray:
    """
        Transforma ndarray desde un sistema de coordenadas Cartesianas a Cilíndricas. Útil para casos
        de piezas cilíndricas o cónicas. Mediante la variable inv se indica si se quiere transformar
        hacia coordenadas Cilíndricas o se quiere transformar desde Cilíndricas a Cartesianas.
        Mapeo corresponde a [X, Y, Z] ---> [X, Theta, Radio]

        Parameters
        ----------
        points : np.ndarray
            ndarray de puntos, con forma (n, 3)
        radio : float, optional
            radio de cilindro o radios de cono, by default 1
        inv : bool, optional
            indicador de transformación hacia o desde coordenadas Cilíndricas, by default False

        Returns
        -------
        np.ndarray
            puntos en coordenadas Cilíndricas
    """

    if not isinstance(points, np.ndarray):
        points = np.asarray(points)
    
    # Transformación a coordenadas cilíndricas
    if not inv:
        arr_cilin = np.zeros(points.shape)  # Placeholder de nuevas coordenadas

        arr_cilin[:, 0] = points[:, 0]  # LARGO SE MANTIENE IGUAL, SE TOMA EN X
        arr_cilin[:, 1] = np.arctan2(points[:, 1], points[:, 2])*radio  # POSIBLE ALTERNATIVA, SACADO DE MENPO3D CYLINDRICAL UNWRAPPING
        arr_cilin[:, 2] = np.sqrt(points[:, 1] ** 2 + points[:, 2] ** 2)  # R, SE TOMA EN Z
        # arr_cilin[:, 1] = np.rad2deg(np.arctan2(points[:, 2], points[:, 1]))  # THETA, SE TOMA EN Y

        return arr_cilin
    
    # Transformación a coordenadas cartesianas
    if inv:
        arr_cart = np.zeros(points.shape)  # Placeholder de nuevas coordenadas

        arr_cart[:, 0] = points[:, 0]
        arr_cart[:, 1] = points[:, 2] * np.sin(points[:, 1]/radio)
        arr_cart[:, 2] = points[:, 2] * np.cos(points[:, 1]/radio)

        return arr_cart


def transform_cilindrical_pieza(pieza: trimesh.Trimesh, radio: Union[float, np.ndarray]=1, inv: bool=False) -> trimesh.Trimesh:
    """
        Transforma coordendas de vértices de pieza ingresada entre los sistemas Cartesiano y Cilíndrico.
        Útil para casos de piezas cilíndricas o cónicas. Mediante la variable inv se indica si se quiere transformar
        hacia coordenadas Cilíndricas o se quiere transformar desde Cilíndricas a Cartesianas.
        Mapeo corresponde a [X, Y, Z] ---> [X, Theta, Radio]

        Parameters
        ----------
        pieza : trimesh.Trimesh
            pieza de trimesh.Trimesh que se quiere transformar
        radio : float o np.ndarray, optional
            radio de cilindro o radios de cono, solo usado en esos casos, by default 1
        inv : bool, optional
            indicador de transformación hacia o desde coordenadas Cilíndricas, by default False

        Returns
        -------
        trimesh.Trimesh
            pieza en coordenadas cilíndricas
    """
    puntos_trnsfrm = transform_cilindrical(pieza.vertices, radio, inv)
    malla_trmsh = trimesh.base.Trimesh(vertices=puntos_trnsfrm, faces=pieza.faces, process=True, validate=True)
    
    return malla_trmsh


def transform_cilindrical_cortes(cortes: List[List[np.ndarray]], radio: float=1, inv: bool=False) -> List[List[np.ndarray]]:
    """
        Transforma lista de listas de np.ndarrays desde un sistema de coordenadas Cartesiano a uno Cilíndrico.
        Para la transformación se usa el radio ideal que debería haber en cada punto, dado por la variable radio.
        Mediante la variable inv se indica si se quiere transformar hacia coordenadas Cilíndricas o 
        se quiere transformar desde Cilíndricas a Cartesianas.
        Mapeo de coordenadas corresponde a [X, Y, Z] ---> [X, Theta, Radio]

        Parameters
        ----------
        cortes : List[List[np.ndarray]]
            cortes de pieza en coordenadas Cartesianas
        radio : float, optional
            radio para casos que cortes son sobre pieza cilindrica, by default 1
        inv : bool, optional
            indicador de transformación hacia o desde coordenadas Cilíndricas, by default False

        Returns
        -------
        List[List[np.ndarray]]
            cortes de pieza en coordenadas Cilíndricas
    """

    for i, capa in enumerate(cortes):
        for j, curva in enumerate(capa):
            cortes[i][j] = transform_cilindrical(curva, radio, inv)
    
    return cortes


def transform_cilindrical_cortes_conos(cortes: List[List[np.ndarray]], descriptor: Tuple[float, float]=[0, 0], inv: bool=False) -> List[List[np.ndarray]]:
    """
        Transforma lista de listas de np.ndarrays desde un sistema de coordenadas Cartesiano a uno Cilíndrico.
        Mediante la variable inv se indica si se quiere transformar hacia coordenadas Cilíndricas o 
        se quiere transformar desde Cilíndricas a Cartesianas.
        Mapeo de coordenadas corresponde a [X, Y, Z] ---> [X, Theta, Radio].
        Para el caso de conos es necesario calcular el radio ideal en cada punto, usando coordenada X.

        Parameters
        ----------
        cortes : List[List[np.ndarray]]
            lista de cortes hecha sobre un cono, en coordenadas Cartesianas
        descriptor : Tuple[float, float], optional
            lista de descriptores de cono, correspondientes a [radio base, ángulo apertura], by default [0, 0]
        inv : bool, optional
            indicador de transformación hacía o desde coordenadas Cilíndricas, by default False

        Returns
        -------
        List[List[np.ndarray]]
            lista de cortes en coordenadas Cilíndricas
    """

    for i, capa in enumerate(cortes):
        for j, curva in enumerate(capa):
            # Radio de conos es variable, hay que calcularlo para cada punto según posición X
            radio_cono = -1*(np.tan(np.deg2rad(descriptor[1]))*curva[:, 0] - descriptor[0])
            cortes[i][j] = transform_cilindrical(curva, radio_cono, inv)
    
    return cortes


def filtrar_poly(poly: Union[shapely.geometry.polygon.Polygon, 
                            shapely.geometry.multipolygon.MultiPolygon], 
                            ancho_cordon: float) -> Union[shapely.geometry.polygon.Polygon,
                                                        shapely.geometry.multipolygon.MultiPolygon, 
                                                        None]:
    """
        Filtra shapely Polygon o Multipolygon de acuerdo a una serie de filtros consecutivos.
        Primer filtro es de área mínima, correspondiente a un círculo con el diámetro de cordon
        Segundo filtro es sobre ancho/alto de Polygon vs ancho/alto de cordón de soldadura.
        Tercer filtro es sobre su relación de área vs perímetro, para casos de Polygon "raros"
        o irregulares.

        Parameters
        ----------
        poly : shapely.geometry.polygon.Polygon o shapely.geometry.multipolygon.MultiPolygon
            Polygon o Multipolygon a filtrar
        ancho_cordon : float
            ancho de cordón de soldadura

        Returns
        -------
        shapely.geometry.polygon.Polygon o shapely.geometry.multipolygon.MultiPolygon o None
            Polygon o MultiPolygon si pasa el filtro, None en caso contrario
    """
    min_areacover = np.pi*((ancho_cordon/2)**2)  # [mm^2]
    # Primer filtro: área mínima
    if poly.area >= min_areacover:
        x_min, y_min, x_max, y_max = poly.envelope.bounds
        ancho = x_max - x_min
        alto = y_max - y_min
        # Segundo filtro: dimensiones generales
        if ancho > ancho_cordon and alto > ancho_cordon:
            # Tercer filtro: relación entre área y perímetro
            # Considerar relación área polygon/área oobb como opción
            if poly.area/poly.length >= ancho_cordon/2.5:
                return poly
    return None


def filtrar_cortes(lista_cortes_multipolygon: List[Union[shapely.geometry.polygon.Polygon, shapely.geometry.multipolygon.MultiPolygon]], 
                ancho_cordon: float) -> List[shapely.geometry.multipolygon.MultiPolygon]:
    """
        Filtra una lista de Polygon o Multipolygon recorriendo la lista 
        y aplicando la función de filtro a cada elemento. Se aplican tres filtros consecutivos:
        primer filtro es de área mínima, correspondiente a un círculo con el diámetro de cordon.
        Segundo filtro es sobre ancho/alto de Polygon vs ancho/alto de cordón de soldadura.
        Tercer filtro es sobre su relación de área vs perímetro, para casos de Polygon "raros"
        o irregulares.
        
        Parameters
        ----------
        lista_cortes_multipolygon : List[shapely.geometry.polygon.Polygon o shapely.geometry.multipolygon.MultiPolygon]
            lista de Polygon o Multipolygon representando los cortes de una pieza
        ancho_cordon : float
            ancho de cordón de soldadura

        Returns
        -------
        List[shapely.geometry.multipolygon.MultiPolygon]
            lista de cortes con los elementos que pasaron los filtros
    """

    for i, capa in enumerate(lista_cortes_multipolygon):
        filtered_capa = []
        if isinstance(capa, shapely.geometry.polygon.Polygon):
            filtered_poly = filtrar_poly(capa, ancho_cordon)
            if filtered_poly:
                filtered_capa.append(filtered_poly)
        if isinstance(capa, shapely.geometry.multipolygon.MultiPolygon):
            for poly in capa.geoms:
                filtered_poly = filtrar_poly(poly, ancho_cordon)
                if filtered_poly:
                    filtered_capa.append(filtered_poly)
        if filtered_capa:
            lista_cortes_multipolygon[i] = shapely.geometry.multipolygon.MultiPolygon(filtered_capa)
        else:
            lista_cortes_multipolygon[i] = None
    
    return lista_cortes_multipolygon


def extraer_coords(poly: Union[shapely.geometry.polygon.Polygon, 
                            shapely.geometry.multipolygon.MultiPolygon]) -> List[np.ndarray]:
    """
        Extrae las coordenadas de los puntos que componen al polígono o polígonos.
        En caso de MultiPolygon cada Polygon que lo componga se retorna como un array individual.
        Anillos interiores se tratan de la misma forma que MultiPolygon.

        Parameters
        ----------
        poly : shapely.geometry.polygon.Polygon o shapely.geometry.multipolygon.MultiPolygon

        Returns
        -------
        List[np.ndarray]
            lista compuesta de arrays de numpy con las coordenadas de los puntos que conforman al polígono.\n
            arrays tienen forma de (n, 3)
    """
    curvas = []

    if isinstance(poly, shapely.geometry.multipolygon.MultiPolygon):
        for geom in poly.geoms:
            if not geom.is_empty:
                curvas.append(np.asarray(geom.exterior.coords))
                for interior in geom.interiors:
                    curvas.append(np.asarray(interior.coords))

    elif isinstance(poly, shapely.geometry.polygon.Polygon):
        if not poly.is_empty:
            curvas.append(np.asarray(poly.exterior.coords))
            for interior in poly.interiors:
                curvas.append(np.asarray(interior.coords))

    return curvas
