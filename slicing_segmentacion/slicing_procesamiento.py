import open3d as o3d
import numpy as np
import matplotlib.pyplot as plt
from itertools import combinations
import skimage.segmentation
import random as rd


def slice_nube(nube, tipo_geom='placa'):
    # CORTA LA NUBE EN CAPAS, NO DIFERENCIA ENTRE DISTINTAS ESTRUCTURA, ESENCIALMENTE PRODUCE CORTES DE NIVEL
    # SE CENTRA EN ORIGEN Y LUEGOS SE COLOCA EN EL OCTANTE POSITIVO, ESQUINA INFERIOR IZQUIERDA EN ORIGEN
    if tipo_geom == 'placa':
        nube.translate((-nube.get_min_bound()[0], -nube.get_min_bound()[1], -nube.get_min_bound()[2]), relative=True)
    elif tipo_geom == 'cilindro':
        nube.translate((0, -nube.get_min_bound()[1], -nube.get_min_bound()[2]), relative=True)
        nube_cilin_coords_np, nube = cambio_a_cilin(nube)  # NUBE AHORA SE TRANSFORMA A UNA PLACA AL ESTAR EN COORDENADAS CILÍNDRICAS
        nube.translate((-nube.get_min_bound()[0], -nube.get_min_bound()[1], -nube.get_min_bound()[2]), relative=True)
    # FACTOR PARA ENCONTRAR POSICIONES ADECUADAS
    i = 0
    j = 2
    # LARGO DE LA ARISTA DE VOXEL CORRESPONDE A 4 VECES LA DISTANCIA PROM ENTRE PTOS, SIGUE LÓGICA DE DBSCAN
    dist_prom = np.round(np.mean(nube.compute_nearest_neighbor_distance()), decimals=5)
    arista_voxel = np.round(dist_prom * 4, 5)
    # SE VOXELIZA, OBTIENE LISTA COMPLETA DE VOXELS (ÍNDICES Y COLORES) Y SE RESCATAN LOS ÍNDICES
    voxelgrid = o3d.geometry.VoxelGrid.create_from_point_cloud(input=nube, voxel_size=arista_voxel)
    lista_total_voxels = np.asarray(voxelgrid.get_voxels())
    voxels_indices = np.asarray([lista_total_voxels[i].grid_index for i in range(len(lista_total_voxels))])
    # SE CREA DICCIONARIO PARA GUARDAR LAS CAPAS, CAPA ES EL VALOR Y LA LLAVE ES EL NÚMERO DE SU NIVEL
    # CADA CAPA ES UNA GRILLA CORRESPONDIENTE AL VOXELGRID, ES DEL MISMO TAMAÑO EN EL PLANO XY
    diccionario_capas = {}
    capa = {(x, y): ['white'] for y in range(voxelgrid.get_voxel(voxelgrid.get_max_bound())[1] + 1) for x in range(voxelgrid.get_voxel(voxelgrid.get_max_bound())[0] + 1)}
    # SE TOMA UN RANGO IGUAL A LA CANTIDAD DE VOXELS EN DIRECCIÓN Z
    for nivel in range(voxelgrid.get_voxel(voxelgrid.get_max_bound())[j] - 1):
        # SE CREA LA CAPA, SE RENUEVA CADA CICLO, NO BORRA EL DICCIONARIO NI LO REEMPLAZA POR OTRO NUEVO
        capa.update((k, ['white']) for k in capa)
        # SE BUSCAN TODOS LOS VOXEL QUE ESTÁN EN EL MISMO NIVEL Y POR SOBRE EL NIVEL
        # EQUIVALENTE A PARARSE ENTRE MEDIO DE LOS DOS NIVELES
        voxels_capa = voxels_indices[np.logical_or(voxels_indices[:, j] == nivel, voxels_indices[:, j] == nivel + 1)]
        # SE BUSCA POR NIVEL PRIMERO, LUEGO SE COLOCA COLOR SEGÚN ÍNDICES (X, Y)
        for voxel in voxels_capa:
            if voxel[j] == nivel:  # ESTO QUIERE DECIR QUE ESTÁ ABAJO
                capa[(voxel[i], voxel[i+1])][0] = 'blue'
        for voxel in voxels_capa:
            if voxel[j] > nivel:  # ESTO QUIERE DECIR QUE ESTÁ ARRIBA, DUH
                if capa[(voxel[i], voxel[i+1])][0] == 'white':  # SI NO SE MARCÓ EN LA PASADA ANTERIOR, SE MARCA ROJO
                    capa[(voxel[i], voxel[i+1])][0] = 'red'
                if capa[(voxel[i], voxel[i+1])][0] == 'blue':  # SI YA ESTABA MARCADO DE AZUL, SE MARCA NEGRO
                    capa[(voxel[i], voxel[i+1])][0] = 'black'
        # AHORA SE REVISA LA INTERFAZ ENTRE RED Y BLUE, SI HAY INTERFAZ RED-BLUE AMBOS SE PONEN NEGRO
        voxels_pintados = [voxel for voxel in voxels_capa if capa[(voxel[i], voxel[i+1])][0] != 'black' and capa[(voxel[i], voxel[i+1])][0] != 'white']
        for voxel in voxels_pintados:
            color = capa[(voxel[i], voxel[i+1])][0]
            # ES NECESARIO PORQUE A PRIORI LAS CELDAS SOLOS ON ROJAS-AZULES, PERO PUEDEN CAMBIAR A NEGRO ANTES DE CHEQUEAR
            if color != 'black':
                try:
                    color_der = capa[(voxel[i] + 1, voxel[i+1])][0]
                    if color != color_der and color_der != 'white' and color_der != 'black':
                        capa[(voxel[i], voxel[i+1])][0] = 'black'
                        capa[(voxel[i] + 1, voxel[i+1])][0] = 'black'
                except KeyError:
                    pass

                try:
                    color_diag_der_sup = capa[(voxel[i] + 1, voxel[i+1] + 1)][0]
                    if color != color_diag_der_sup and color_diag_der_sup != 'white' and color_diag_der_sup != 'black':
                        capa[(voxel[i], voxel[i+1])][0] = 'black'
                        capa[(voxel[i] + 1, voxel[i+1] + 1)][0] = 'black'
                except KeyError:
                    pass

                try:
                    color_up = capa[(voxel[i], voxel[i+1] + 1)][0]
                    if color != color_up and color_up != 'white' and color_up != 'black':
                        capa[(voxel[i], voxel[i+1])][0] = 'black'
                        capa[(voxel[i], voxel[i+1] + 1)][0] = 'black'
                except KeyError:
                    pass

                try:
                    color_diag_izq_sup = capa[(voxel[i] - 1, voxel[i+1] + 1)][0]
                    if color != color_diag_izq_sup and color_diag_izq_sup != 'white' and color_diag_izq_sup != 'black':
                        capa[(voxel[i], voxel[i+1])][0] = 'black'
                        capa[(voxel[i] - 1, voxel[i+1] + 1)][0] = 'black'
                except KeyError:
                    pass

                try:
                    color_izq = capa[(voxel[i] - 1, voxel[i+1])][0]
                    if color != color_izq and color_izq != 'white' and color_izq != 'black':
                        capa[(voxel[i], voxel[i+1])][0] = 'black'
                        capa[(voxel[i] - 1, voxel[i+1])][0] = 'black'
                except KeyError:
                    pass

                try:
                    color_diag_izq_inf = capa[(voxel[i] - 1, voxel[i+1] - 1)][0]
                    if color != color_diag_izq_inf and color_diag_izq_inf != 'white' and color_diag_izq_inf != 'black':
                        capa[(voxel[i], voxel[i+1])][0] = 'black'
                        capa[(voxel[i] - 1, voxel[i+1] - 1)][0] = 'black'
                except KeyError:
                    pass

                try:
                    color_down = capa[(voxel[i], voxel[i+1] - 1)][0]
                    if color != color_down and color_down != 'white' and color_down != 'black':
                        capa[(voxel[i], voxel[i+1])][0] = 'black'
                        capa[(voxel[i], voxel[i+1] - 1)][0] = 'black'
                except KeyError:
                    pass

                try:
                    color_diag_der_inf = capa[(voxel[i] + 1, voxel[i+1] - 1)][0]
                    if color != color_diag_der_inf and color_diag_der_inf != 'white' and color_diag_der_inf != 'black':
                        capa[(voxel[i], voxel[i+1])][0] = 'black'
                        capa[(voxel[i] + 1, voxel[i+1] - 1)][0] = 'black'
                except KeyError:
                    pass

        # ELIMINO TODAS LAS CELDAS QUE NO SEAN NEGRAS PARA AHORRAR ESPACIO, DICCIONARIO FINAL, CADA NIVEL ES UNA LLAVE, CADA VALOR ES UN DICCIONARIO DE LA CAPA
        diccionario_capas[nivel] = {celda: ['nonvisited', 'nocenter'] for celda, color in capa.items() if color[0] == 'black'}
    return diccionario_capas, arista_voxel


def buscar_marcar_vecinos(celda_inicial, capa_busqueda):
    # FUNCIÓN PARA BUSCAR CELDAS VECINAS EN LAS CURVAS DE LA CAPA, DADA UNA CELDA INICIAL Y UN DICCIONARIO CON TODOS LOS PUNTOS
    # TOMO LA CELDA Y VEO SUS 8 VECINOS, LOS MARCO TODOS COMO VISITED, CELDA ELEGIDA ADEMÁS SE MARCA COMO CENTER
    capa_busqueda[celda_inicial][0] = 'visited'
    capa_busqueda[celda_inicial][1] = 'center'
    # HAY QUE USAR TRY PORQUE PUEDE QUE SE PASE A CELDAS BLANCAS, NO IMPORTA ESO PORQUE NO HAY PUNTOS AHÍ, NO AFECTA
    try:  # REVISO DERECHA
        capa_busqueda[(celda_inicial[0] + 1, celda_inicial[1])][0] = 'visited'
    except KeyError:
        pass
    try:  # REVISO DIAGONAL SUPERIOR DERECHA
        capa_busqueda[(celda_inicial[0] + 1, celda_inicial[1] + 1)][0] = 'visited'
    except KeyError:
        pass
    try:  # REVISO ARRIBA
        capa_busqueda[(celda_inicial[0], celda_inicial[1] + 1)][0] = 'visited'
    except KeyError:
        pass
    try:  # REVISO DIAGONAL IZQUIERDA SUPERIOR
        capa_busqueda[(celda_inicial[0] - 1, celda_inicial[1] + 1)][0] = 'visited'
    except KeyError:
        pass
    try:  # REVISO IZQUIERDA
        capa_busqueda[(celda_inicial[0] - 1, celda_inicial[1])][0] = 'visited'
    except KeyError:
        pass
    try:  # REVISO DIAGONAL IZQUIERDA INFERIOR
        capa_busqueda[(celda_inicial[0] - 1, celda_inicial[1] - 1)][0] = 'visited'
    except KeyError:
        pass
    try:  # REVISO ABAJO
        capa_busqueda[(celda_inicial[0], celda_inicial[1] - 1)][0] = 'visited'
    except KeyError:
        pass
    try:  # REVISO DIAGONAL INFERIOR DERECHA
        capa_busqueda[(celda_inicial[0] + 1, celda_inicial[1] - 1)][0] = 'visited'
    except KeyError:
        pass


def vecinos(p, tier=1):
    if tier == 0:
        return [[p[0] + 1, p[1] + 0],
                [p[0] - 1, p[1] + 0],
                [p[0] + 0, p[1] + 1],
                [p[0] + 0, p[1] - 1]]
    if tier == 1:
        return [[p[0] + 1, p[1] + 0],
                [p[0] + 1, p[1] + 1],
                [p[0] + 0, p[1] + 1],
                [p[0] - 1, p[1] + 1],
                [p[0] - 1, p[1] + 0],
                [p[0] - 1, p[1] - 1],
                [p[0] + 0, p[1] - 1],
                [p[0] + 1, p[1] - 1]]
    if tier == 2:
        return [[p[0] + 1, p[1] + 1],
                [p[0] + 1, p[1] + 0],
                [p[0] + 1, p[1] - 1],
                [p[0] - 1, p[1] + 1],
                [p[0] - 1, p[1] + 0],
                [p[0] - 1, p[1] - 1],
                [p[0] + 0, p[1] + 1],
                [p[0] + 0, p[1] - 1],
                [p[0] + 2, p[1] + 2],
                [p[0] + 2, p[1] + 1],
                [p[0] + 2, p[1] + 0],
                [p[0] + 2, p[1] - 1],
                [p[0] + 2, p[1] - 2],
                [p[0] - 2, p[1] + 2],
                [p[0] - 2, p[1] + 1],
                [p[0] - 2, p[1] + 0],
                [p[0] - 2, p[1] - 1],
                [p[0] - 2, p[1] - 2],
                [p[0] + 1, p[1] + 2],
                [p[0] + 0, p[1] + 2],
                [p[0] - 1, p[1] + 2],
                [p[0] + 1, p[1] - 2],
                [p[0] + 0, p[1] - 2],
                [p[0] - 1, p[1] - 2]]


def obtener_curvas_en_capa(plano_capa):
    curvas = []
    while ['nonvisited', 'nocenter'] in plano_capa.values():  # CONDICIÓN PARA SEGUIR BUSCANDO EN LA CAPA
        celda_ini = [celda for celda, estado in plano_capa.items() if estado == ['nonvisited', 'nocenter']][0]  # CELDA INICIAL, NO IMPORTA CUAL SEA
        buscar_marcar_vecinos(celda_ini, plano_capa)  # SE BUSCAN LOS VECINOS PARA DAR UNA VECINDAD INICIAL
        while ['visited', 'nocenter'] in plano_capa.values():  # CONDICIÓN PARA SEGUIR BUSCANDO EN LA CURVA
            # SE ELIGE CUALQUIER PUNTO DE LOS VISITADOS QUE NO SEA CENTRO PARA SEGUIR
            celda = [celda for celda, estado in plano_capa.items() if estado == ['visited', 'nocenter']][0]
            buscar_marcar_vecinos(celda, plano_capa)
        # PARA GUARDARLAS TIENE QUE HABERSE VISITADO Y SIDO CENTRO Y ADEMÁS SE BUSCA QUE NO HAYAN SIDO VISTAS EN UN CICLO ANTERIOR
        puntos_curva = [celda for celda, estado in plano_capa.items() if estado == ['visited', 'center']]
        curvas.append(puntos_curva)  # A MEDIDA QUE RECONOCEMOS MÁS CURVAS, SE CONVIERTE EN EL AGREGADO

    x = []  # RESULTADO FINAL ES LISTA DE ARRAYS, CADA ARRAY ES UNA CURVA
    for i in range(len(curvas)):
        if i == 0:
            x.append(np.asarray(curvas[i]))
        else:
            x.append(np.asarray([punto for punto in curvas[i] if punto not in curvas[i - 1]]))
    return x


def tapar_hoyos(capa_de_curvas):
    capas = []
    for elemento in capa_de_curvas:
        vecinos_puntos = []
        # vecinos_puntos = [vecinos(punto, 0) for punto in elemento]
        for punto in elemento:
            vecinos_puntos.append(vecinos(punto, 0))
        vecinos_puntos = np.concatenate(vecinos_puntos)
        compartidos = np.unique(vecinos_puntos, return_counts=True, axis=0)
        indxs4 = np.where(compartidos[1] == 4)[0]
        indxs3 = np.where(compartidos[1] == 3)[0]
        indxs = np.concatenate((indxs4, indxs3))
        if len(indxs) != 0:
            puntos_faltantes = compartidos[0][indxs]
            curva_tapada = np.unique(np.vstack((elemento, puntos_faltantes)), axis=0)
            capas.append(curva_tapada)
        else:
            capas.append(elemento)
    return capas


def cerrar_curvas(coleccion_curvas, plano):
    # IN: LISTA DE ARRAYS Y UN DICCIONARIO QUE DESCRIBE TODA LA CAPA
    # OUT: DICCIONARIO DEL PLANO CON LOS PTOS FALTANTES PARA CERRAR LAS CURVAS AGREGADOS
    plano.update((k, ['nonvisited', 'nocenter']) for k in plano)
    # LISTA DE LISTAS DONDE CADA LISTA CORRESPONDE A LOS VECINOS DE CADA CURVA
    vecinos_posibles = [np.unique(np.concatenate([vecinos(p, 2) for p in elemento]), axis=0) for elemento in coleccion_curvas]
    # SE JUNTAN TODOS, SE ENCUENTRAN LOS QUE SE REPITEN 2 VECES (UNIONES) Y SE GUARDAN
    if len(vecinos_posibles):
        puntos_posibles = []
        for mix in combinations(vecinos_posibles, r=2):  # COMBINACIONES DE VECINOS DE CADA CURVA
            mix = np.concatenate(mix)  # LOS JUNTA TODOS PARA PODER IDENTIFICAR SI ALGUNO APARECE 2 VECES O MÁS
            puntos_compartidos = np.unique(mix, return_counts=True, axis=0)
            indx_pc = np.where(puntos_compartidos[1] == 2)[0]
            if len(indx_pc) != 0:  # PARA ASEGURARSE QUE SE TENGAN ÍNDICES
                candidatos = puntos_compartidos[0][indx_pc]
                # SE CREA UN DICCIONARIO CON LOS PUNTOS OBTENIDOS
                capa_candidatos = {(candidate[0], candidate[1]): ['nonvisited', 'nocenter'] for candidate in candidatos}
                separados = obtener_curvas_en_capa(capa_candidatos)  # SE AISLAN LOS GRUPOS DE PUNTOS EN "CURVAS"
                for stem in separados:  # POR CADA CONJUNTO DE PUNTOS A AGREGAR
                    # QUEDARSE CON 1 O 2 PUNTOS POSIBLES
                    mid = np.mean(stem, axis=0)
                    top = np.ceil(mid).astype("int32")
                    bot = np.floor(mid).astype("int32")
                    if (top == bot).all():
                        stem = top
                        stem = np.asarray([stem])  # ES NECESARIO PARA PODER CONCATENAR DESPUÉS
                    else:
                        stem = np.vstack((top, bot))
                    puntos_posibles.append(stem)
        # AGREGAR TODOS LOS PUNTOS POSIBLES AL PLANO
        if len(puntos_posibles) != 0:  # EN CASO DE QUE EFECTIVAMENTE HAYAN PUNTOS POSIBLES
            puntos_posibles = np.concatenate(puntos_posibles, axis=0)  # SE CONCATENAN TODOS PARA PODER AGREGARLOS COMO LISTA
            for punto in puntos_posibles:
                punto_agregado = {(punto[0], punto[1]): ['nonvisited', 'nocenter']}
                plano.update(punto_agregado)
            nueva_coleccion_curvas = obtener_curvas_en_capa(plano)
            coleccion_curvas_tapada = tapar_hoyos(nueva_coleccion_curvas)
            return coleccion_curvas_tapada
        else:
            coleccion_curvas_tapada = tapar_hoyos(coleccion_curvas)
            return coleccion_curvas_tapada
    else:
        coleccion_curvas_tapada = tapar_hoyos(coleccion_curvas)
        return coleccion_curvas_tapada


def flood_curva(curva, valor_flood=2, relleno=False, valor_relleno=1):
    # IN: CURVA REPRESENTADA POR ARRAY
    # OUT: MASK DE LA CURVA LUEGO DE UN FLOODFILL
    matriz_binaria = np.zeros((max(curva[:, 1]) + 2, max(curva[:, 0]) + 2))  # SE AGRANDA EL BORDE DE UN BOUNDING BOX
    for punto in curva:  # LOS PUNTOS CORRESPONDIENTES AL BORDE SE MARCAN CON UN 1
        matriz_binaria[punto[1]][punto[0]] = 1
    # MATRIZ DE LA CAPA LLENADA, CONECTIVIDAD DE 4 VECINOS, RELLENA LOS CONECTADOS CON UN 2
    mask = skimage.segmentation.flood_fill(matriz_binaria, (0, 0), new_value=valor_flood, connectivity=1)
    if relleno:
        mask[np.where(mask == 0)] = valor_relleno
    return mask


def randomize_join(curva, n=3, p=0.05):
    # IN: UNA CURVA REPRESENTADA POR UN ARRAY, CANTIDAD DE VECES A RANDOMIZAR Y EL % DE PTOS A ELIMINAR
    # OUT: UN ARRAY DE LA CURVA CON LOS PUNTOS FALTANTES PARA QUE ESTÉ CERRADA
    # FUNCIÓN PARA CERRAR CURVAS TIPO "C": AL TOMAR UN ARRAY DE LOS PTOS DE LA CURVA ELIMINA EL 5% 3 VECES Y LOS UNE
    pl = []  # LISTA PARA PONER LAS CURVAS RANDOMIZADAS
    for i in range(n):
        indx = rd.sample(range(len(curva)), int(len(curva) * (1 - p)))  # GUARDAR INDX DE LOS PUNTOS ELIMINADOS
        curva_random = curva[indx]  # SE TOMAN SOLO LOS PUNTOS NO ELIMINADOS
        capa_rand = {(punto[0], punto[1]): ['nonvisited', 'nocenter'] for punto in curva_random}
        curvas_rand = obtener_curvas_en_capa(capa_rand)
        curvas_rand = cerrar_curvas(curvas_rand, capa_rand)
        # pl.append(curvas_rand)
        if len(curvas_rand) == 1:
            pl.append(curvas_rand[0])
        elif len(curvas_rand) > 1:
            pl.append(np.concatenate(curvas_rand))
    try:
        joined_pl = np.unique(np.concatenate(pl), axis=0)  # SE CONCATENAN Y HACEN ÚNICOS LOS PUNTOS PARA VOLVER A TENER LA CURVA
        capa_random = {(punto[0], punto[1]): ['nonvisited', 'nocenter'] for punto in joined_pl}
        # plano_random_cerrado = cerrar_curvas([pl], capa_random)  # SE AGREGAN LOS PUNTOS AL PLANO Y SE CIERRA DE NUEVO
        curvas_cerradas_rand = obtener_curvas_en_capa(capa_random)  # SE SACAN LAS CURVAS DE LA CAPA ENTERA DE NUEVO, AHORA CON LA CURVA CERRADA
        # SE DEVUELVE SOLO EL PRIMER ELEMENTO PORQUE ES UNA LISTA DE ARRAYS DE LARGO 1, ÚNICO ELEMENTO = CURVA RANDOMIZADA
        return curvas_cerradas_rand[0]
    except ValueError:
        return []


def eliminar_extras(plano_curvas):
    # TOMA UN ARRAY DE LAS CURVAS Y SEGMENTA ENTRE INTERIOR Y EXTERIOR, INTERIOR QUEDA EN 0, NUBE QUEDA EN 1 Y EXTERIOR QUEDA EN 2
    # SE ELIMINAN TODOS LOS PUNTOS DEL INTERIOR DE LA CURVA
    new_plano = []
    for curva in plano_curvas:  # CADA CURVA ES UN ARRAY
        mask = flood_curva(curva, relleno=False)
        # TODO: MOVER A CERRAR CURVA (BAJA PRIORIDAD)
        # SE REVISA CUANTOS VALORES ÚNICOS HAY EN LA MÁSCARA, SI HAY SOLO 2 ---> CURVA ABIERTA
        count = 0
        while len(np.unique(mask)) == 2:
            if count > 50:
                mask = []
                break
            cu = randomize_join(curva)
            if len(cu) != 0:
                mask = flood_curva(cu)
            count += 1
        if len(mask) != 0:
            mask[np.where(mask == 0)] = 1
            mask = skimage.segmentation.find_boundaries(mask, mode='inner', background=2)
            new_curva = np.asarray([[x, y] for x in range(mask.shape[1]) for y in range(mask.shape[0]) if mask[y, x]])
            new_plano.append(new_curva)
    return new_plano


def ordenar_curva(curva):
    indx_ant, indx_act, pto_ant = 0, 0, 0
    pto_act = curva[indx_act]
    curva_ordenada = np.asarray([[pto_act[0], pto_act[1]]])
    while len(curva_ordenada) < len(curva):
        largo_anterior = len(curva_ordenada)
        vec = np.asarray(vecinos(pto_act, tier=1))  # POR CADA PUNTO LE SACO LOS 8 VECINOS, ORDENADOS DESDE EL PTO A LA DERECHA A CONTRARELOJ
        if len(curva_ordenada) > 1:
            indx_ant = np.where((vec == pto_ant).all(axis=1))[0][0]
        for i in range(len(vec)):  # RECORRO LA LISTA DE VECINOS NO SE PUEDE CAMBIAR EL RANGE UNA VEZ QUE SE CREO
            pto_pos = np.take(vec, i+indx_ant, axis=0, mode='wrap')  # EL PTO SGTE SE SACA DE LOS VECINOS, CONTANDO DESDE EL ANTERIOR EN ADELANTE A CONTRARELOJ
            indx_pos_og = np.where((curva == pto_pos).all(axis=1))[0]
            indx_pos_ord = np.where((curva_ordenada == pto_pos).all(axis=1))[0]
            if len(indx_pos_og) != 0:  # ESTÁ EN LA CURVA ORIGINAL
                if len(indx_pos_ord) == 0:  # NO ESTÁ EN LA CURVA ORDENADA AÚN
                    pto_ant = pto_act
                    pto_act = pto_pos  # SE ACTUALIZA EL PTO ACTUAL == SE MUEVE LA BÚSQUEDA
                    curva_ordenada = np.concatenate((curva_ordenada, np.asarray([[pto_act[0], pto_act[1]]])), axis=0)
                    break
        check_si_termino = np.where((vecinos(curva_ordenada[0], tier=1) == curva_ordenada[-1]).all(axis=1))[0]
        if len(check_si_termino) > 0 and len(curva_ordenada) > 4:  # SE DETIENE CUANDO ÚLTIMO E INICIAL ESTÁN EN VECINDAD
            break
        if largo_anterior == len(curva_ordenada):  # SI SON IGUALES ENTONCES NO SE HA AGREGADO NINGÚN PUNTO
            curva_ordenada = np.delete(curva_ordenada, -1, axis=0)
            curva = np.delete(curva, np.where((curva == pto_act).all(axis=1))[0], axis=0)
            try:
                pto_act = curva_ordenada[-1]
                pto_ant = curva_ordenada[-2]
            except IndexError:
                print('ERROR: CURVA NO SE PUDO ORDENAR, ELIMINADA')
                return []
    return curva_ordenada


def ordenar_curvas(plano):
    plano_ordenado = []
    for curva in plano:
        curva_ordenada = ordenar_curva(curva)
        if len(curva_ordenada) > 0:
            plano_ordenado.append(curva_ordenada)
    return plano_ordenado


def cambio_a_cilin(nube_cart):
    # SE INGRESA UNA NUBE DE PUNTOS  DE OPEN3D EN COORDENADAS CARTESIANAS Y SE TRASPASA A UN ARRAY EN COORDENADAS CILÍNDRICAS
    cil_arr_cart = np.asarray(nube_cart.points)  # ORIGINAL
    cil_arr_cilin = np.zeros(cil_arr_cart.shape)  # PLACEHOLDER COORD CILÍNDRICAS

    cil_arr_cilin[:, 2] = np.sqrt(cil_arr_cart[:, 0] ** 2 + cil_arr_cart[:, 1] ** 2)  # OBTENCIÓN DE R, SE TOMA EN DIRECCIÓN DE Z
    cil_arr_cilin[:, 1] = np.rad2deg(np.arctan2(cil_arr_cart[:, 1], cil_arr_cart[:, 0]))  # OBTENCIÓN DE THETA, SE TOMA EN DIRECCIÓN DE Y
    cil_arr_cilin[:, 0] = cil_arr_cart[:, 2]  # Z SE MANTIENE IGUAL, SE TOMA EN DIRECCIÓN X

    cil = o3d.geometry.PointCloud()
    cil.points = o3d.utility.Vector3dVector(cil_arr_cilin)
    cil.estimate_normals()

    return cil_arr_cilin, cil


def visualizar_nube(nube):
    nube.translate((0, 0, 0), relative=False)
    coord_frame = o3d.geometry.TriangleMesh.create_coordinate_frame(size=10, origin=[0, 0, 0])
    o3d.visualization.draw_geometries([nube, coord_frame])


if __name__ == '__main__':
    import time
    tiempo_ini = time.time()
    # DIMENSIONES ESTÁN EN MM, OPEN3D USA CM
    nubes_placas = [r'../piezas-stl-pcd/placas/placa_pitting_ransac.pcd', r'../piezas-stl-pcd/placas/placa_bolsillo_ransac.pcd',
                    r'../piezas-stl-pcd/placas/placa_adhesion_ransac.pcd', r'../piezas-stl-pcd/placas/placa_abrasion_ransac.pcd',
                    r'../piezas-stl-pcd/placas/placa_abrasion_punto_silla_ransac.pcd', r'../piezas-stl-pcd/placas/placa_bolsillo_esfera.pcd',
                    r'../piezas-stl-pcd/placas/placa_pitting_esfera.pcd', r'../piezas-stl-pcd/placas/placa_daños_esfera.pcd',
                    r'../piezas-stl-pcd/placas/placa_daños_esfera2.pcd']

    nubes_cilindros = [r'../piezas-stl-pcd/cilindros/cilindro-abrasion1.pcd', r'../piezas-stl-pcd/cilindros/cilindro-abrasion2.pcd',
                       r'../piezas-stl-pcd/cilindros/cilindro-abrasion3.pcd', r'../piezas-stl-pcd/cilindros/cilindro-abrasion4.pcd',
                       r'../piezas-stl-pcd/cilindros/cilindro-pitting1.pcd', r'../piezas-stl-pcd/cilindros/cilindro-pitting2.pcd',
                       r'../piezas-stl-pcd/cilindros/cilindro-pitting3.pcd', r'../piezas-stl-pcd/cilindros/cilindro-pitting1-profundo.pcd',
                       r'../piezas-stl-pcd/cilindros/cilindro-pitting1-profundo2.pcd', r'../piezas-stl-pcd/cilindros/cilindro-abrasion2-menos-profundo.pcd']

    nube_datos = o3d.io.read_point_cloud(filename=nubes_cilindros[2], format='pcd')
    geometria = 'cilindro'
    # nube_datos = o3d.io.read_point_cloud(filename=nubes_placas[8], format='pcd')
    # geometria = 'placa'
    # PASO 1: CORTAR LA NUBE
    capas, arista_vox = slice_nube(nube_datos, tipo_geom=geometria)  # CON ESTO OBTENEMOS TODOS LOS PUNTOS DIVIDIDO EN CAPAS
    # PASO 2: ENCONTRAR LAS CURVAS EN CADA CAPA
    curvas_por_capa = []
    counter = 0
    for capa in capas.keys():
        print('PROCESANDO CAPA:', counter)
        print('PASO 1: ENCONTRAR CURVAS')
        curvas_encontradas = obtener_curvas_en_capa(capas[capa])
        print('PASO 2: CERRAR CURVAS')
        plano_cerrado = cerrar_curvas(curvas_encontradas, capas[capa])
        print('PASO 3: ELIMINAR PUNTOS SOBRANTES')
        nuevo_plano = eliminar_extras(plano_cerrado)
        print('PASO 4: ORDENAR PUNTOS')
        plano_ordenado = ordenar_curvas(nuevo_plano)
        curvas_por_capa.append(plano_ordenado)  # CADA CAPA ES 1 LISTA, CADA LISTA TIENE UNA LISTA DE ARRAYS, CADA ARRAY ES UNA CURVA
        print()
        counter += 1
    print(time.time() - tiempo_ini)

    for plano in range(len(curvas_por_capa)):
        Fig, Ax = plt.subplots(nrows=1, ncols=1, figsize=[25, 25])
        for curva in curvas_por_capa[plano]:
            Ax.scatter(curva[:, 0], curva[:, 1], s=8)
            Ax.set_xlim(0, 800)
            Ax.set_ylim(0, 800)
            plt.gca().set_aspect('equal')
            Ax.get_xaxis().set_ticks([])
            Ax.get_yaxis().set_ticks([])
            Ax.set_title(f"Capa {plano}")
        plt.show()
    visualizar_nube(nube_datos)
