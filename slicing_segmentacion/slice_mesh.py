import numpy as np
import utilidades
import slicing_segmentacion.meshcut


def cortar_malla(malla_datos, alturas_cortes=None, pendiente=None):
    """Función que toma una malla de pieza
    y produce contornos de fallas.
    Argumentos:
        malla_datos [TriangleMesh]: pieza elegida por usuario en formato Meshcut.
        alto_cordon [Float]: alto de cordón de soldadura.

    Return:
        cortes [List]: lista de capas, cada capa otra lista.
                       cada contorno tiene un array de numpy
                       con los puntos de los contornos."""

    pendiente = pendiente
    plano_corte = 0

    if alturas_cortes is None:
        alturas_cortes = []

    lista_cortes = []
    # origen_plano = np.asarray([0.0, 0.0, 0.0])
    normal_plano = np.asarray([0, 0, 1])

    for i, altura_corte in enumerate(alturas_cortes):
        origen_plano = np.asarray([0, 0, altura_corte])
        plano_corte = utilidades.Plane(origen_plano, normal_plano)  # CREA UN PLANO EN EL FORMATO DE MESHCUT

        corte = slicing_segmentacion.meshcut.cross_section_mesh(malla_datos, plano_corte, pendiente=pendiente)

        print("\nNÚMERO CONTORNOS: ", len(corte), ', CAPA:', i, ', ALTURA:', altura_corte)

        for contorno in corte:
            if not len(contorno):
                print('\nCONTORNO VACIO!')

        if corte:  # PARA EVITAR CORTES VACIOS
            lista_cortes.append(corte)

    return lista_cortes
