# -*- coding: utf-8 -*-
import vedo
import trimesh

class DatosPieza:
    """"
        Clase para centralizar los datos de la pieza cargada a la Herramienta.
        Encargada de dar acceso a los datos de la pieza, cambiar formatos, cortes, etc.

        Attributes
        ----------
        path_pieza : str
            string que guarda path al objeto cargado\n
            default = ""
        
        pieza_trmsh : trimesh.Trimesh
            pieza cargada en la herramienta usando cargar_malla(path)\n
            default = None
        
        tipo_pieza : int
            número que indica tipo de geometría de pieza: 0 = placa, 1 = cilindro, 2 = cono\n
            default = 0

        hardfacing : bool
            indicador de uso de hardfacing en vez de corte de pieza cargada\n
            default = False

        descriptor_cilindro_cono : list [radio : float, angulo : float]
            lista que contiene descriptor de pieza para cilindros y conos.
            El primer valor indica el radio, el segundo indica el ángulo de apertura\n
            default = [1, None]

        curvas_por_capa : list[capa : list[contorno : np.array]]
            lista que contiene los cortes de la malla. Cada capa contiene una lista de contornos\n
            default = []
        
        curvas_por_capa_modificada : list[capa : list[contorno : np.array]]
            lista para cuando se modifican los cortes de las piezas mediante la eliminación de alguna curva\n
            default = []
        
        step_over : float
            step-over entre cordones de soldadura. Calculado en base a ancho de cordones de soldadura\n
            default = None
        
        puntos_ancla_trayectorias : list
            lista que contiene los puntos que describen las trayectorias\n
            default = []
        
        pto_to_origen : list [x : float, z : float]
            TODO\n
            default = [0, 0]

        Methods
        -------
        cargar_malla
            Carga la malla indicada en el path.
            Se carga usando Trimesh, y se guarda en el atributo pieza_trmsh
        
        get_vedo_format
            Retorna la malla guardada en pieza_trmsh como malla de tipo vedo.Mesh
        
        get_trimesh_format
            Retorna la malla guardada en pieza_trmsh como malla de tipo trimesh.Trimesh
        
        get_cortes
            Retorna la malla guardada en pieza_trmsh como malla de tipo trimesh.Trimesh
        
        get_trayectorias
            Retorna la malla guardada en pieza_trmsh como malla de tipo trimesh.Trimesh
        
        reiniciar_cortes
            Reinicia curvas_por_capa a [], no retorna nada
        
        reiniciar_trayectorias
            Reinicia puntos_ancla_trayectorias a [], no retorna nada
        """

    def __init__(self) -> None:
        self.path_pieza = ""
        self.pieza_trmsh = None
        self.tipo_pieza = 0
        self.hardfacing = False
        self.descriptor_cilindro_cono = [1, None] 
        self.curvas_por_capa = []
        self.curvas_por_capa_modificada = []
        self.step_over = None
        self.puntos_ancla_trayectorias = []
        self.pto_to_origen = [0, 0]  # [x,z], UTIL EN CASO DE CILINDROS
    
    def cargar_malla(self, path: str) -> str:
        """
        Carga la malla indicada por path y la guarda como malla trimesh.Trimesh

        Parameters
        ----------
        path : str
            Path al archivo que se cargará
        
        Returns
        ----------
        msge : str
            Mensaje indicando que operación se llevó a cabo con éxito
        """
        
        # TODO: Revisar si validación es necesaria
        self.path_pieza = path
        self.pieza_trmsh = trimesh.load_mesh(path, file_type=None, process=True, validate=True)

        # SE ELIMINAN VÉRTICES SOBRANTES DUPLICADOS
        # RECORDAR QUE HAY VÉRTICES DUPLICADOS YA QUE SE COMPARTEN ENTRE TRIÁNGULOS
        self.pieza_trmsh.remove_duplicate_faces()
        self.pieza_trmsh.remove_degenerate_faces(height=1e-08)
        self.pieza_trmsh.remove_unreferenced_vertices()
        self.pieza_trmsh.remove_infinite_values()

        msge = 'ARCHIVO CARGADO CORRECTAMENTE!\n'
        self.reiniciar_cortes()
        self.reiniciar_trayectorias()

        return msge
    
    def get_vedo_format(self) -> vedo.Mesh:
        """Entrega la malla cargada en pieza_trmsh en formato Vedo.

        Parameters
        ----------
        None
        
        Returns
        ----------
        vedo.Mesh
            Malla en formato vedo.Mesh
        """

        return vedo.utils.trimesh2vedo(self.pieza_trmsh)

    def get_trimesh_format(self) -> trimesh.Trimesh:
        """
            Entrega la malla cargada en pieza_trmsh.

            Parameters
            ----------
            None
            
            Returns
            ----------
            pieza_trmsh : trimesh.Trimesh
                Malla cargada previamente con cargar_malla
        """

        return self.pieza_trmsh
    
    def get_cortes(self) -> list:
        """
            Entrega los cortes hechos con la malla cargada.

            Parameters
            ----------
            None
            
            Returns
            ----------
            curvas_por_capa : list
                Lista que contiene las capas de los cortes.
                Cada elemento de la lista es una lista que contiene los contornos encontrados.
                Cada elemento de esta segunda lista es una np.array que contiene los puntos que
                conforman cada contorno.
        """

        return self.curvas_por_capa
    
    def get_trayectorias(self) -> list:
        """
            Entrega las trayectorias calculadas sobre los cortes hechos con la malla cargada.

            Parameters
            ----------
            None
            
            Returns
            ----------
            puntos_ancla_trayectorias : list
                Lista que contiene las trayectorias calculadas.
                TODO: agregar mayor descripción
        """

        return self.puntos_ancla_trayectorias

    def reiniciar_cortes(self) -> None:
        """
            Devuelve los cortes a su valor por defecto de lista vacía.

            Parameters
            ----------
            None
            
            Returns
            ----------
            None
        """

        self.curvas_por_capa = []
        self.curvas_por_capa_modificada = []
    
    def reiniciar_trayectorias(self) -> None:
        """
            Devuelve las trayectorias a su valor por defecto de lista vacía.

            Parameters
            ----------
            None
            
            Returns
            ----------
            None
        """

        self.puntos_ancla_trayectorias = []
