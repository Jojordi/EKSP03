# -*- coding: utf-8 -*-
import wx
import vedo
import copy
import trimesh
import utilidades
import numpy as np
from shapely.geometry import Polygon
from datospieza import DatosPieza
from procesador import Procesador
from path_generation import generatorcsr
from interfaz.interfaz_IMA import MainFrame, VerPiezaFrame, DividirFrame, OrientarFrame, HardfacingFrame
from typing import List, Union

# BASES DE DATOS DE MATERIALES NECESARIOS PARA TODO EL SISTEMA
BASE_DATOS_SOLDADURAS = r'./path_generation/database/BaseInfoSoldadura.xls'
BASE_DATOS_MATERIALES = r'./path_generation/database/BaseInfoMateriales.xls'


class VentanaVerPieza(VerPiezaFrame):
    """
        Implementa interfaz para visualizar la malla cargada.
        Hereda de la clase VerPiezaFrame para tener acceso a los
        elementos y widgets de la GUI.

        Methods
        -------
        mostrar_ventana
            muestra la ventana para visualizar la pieza cargada.
        
        onclose
            cierra ventana, ocultándola, o cerrandola por completo si se cierra ventana padre.
    """

    def __init__(self, *args, **kwds) -> None:
        """
            Constructor de la clase.
            Inicializa el Plotter asociado al panel de visualización, con el uso que se le quiere dar.
        """

        VerPiezaFrame.__init__(self, *args, **kwds)
        self.panel_3d.iniciar_plotter(uso="ver")
        self.Bind(wx.EVT_CLOSE, self.onclose)

    def mostrar_ventana(self) -> None:
        """
            Muestra la ventana para visualizar la pieza cargada.
        """
        self.panel_3d.plotter.render()
        self.Show(True)

    def onclose(self, event: wx.CommandEvent, desde_padre: bool=False) -> None:
        """
            Cierra ventana, ocultándola, o cerrandola por completo si se cierra ventana padre.
        
            Parameters
            ----------
            event : wx.CommandEvent
                evento entregado a método desde botón.
            
            desde_padre : bool, optional
                indicador para el cierre de ventana.
                En caso de ser True el cierre es definitivo,
                en el caso contrario, solo se esconde la ventana, by default False
        """

        if desde_padre:
            self.panel_3d.plotter.close()
            self.Destroy()
        else:
            self.Show(False)


class VentanaOrientacion(OrientarFrame):
    """
        Implementa interfaz para visualizar la malla cargada e interactuar con ella.
        Hereda de la clase OrientarFrame para tener acceso a los elementos y widgets de la GUI.
        Se inicia el Plotter del panel de visualización con el uso de orientación para tener las
        variables y métodos necesarios.
        Método y número de marcadores para orientación dependen del tipo de pieza que se haya indicado
        en la ventana principal.
        
        Attributes
        ----------
        parent
            padre de la ventana, usado para obtener inputs de tipo de pieza y entregar los datos
            de la pieza que se está usando cuando se orienta y se calcula el descriptor de pieza.
               
        Methods
        -------
        mostrar_ventana
            muestra la ventana para visualizar la pieza cargada.
        
        onclose
            cierra ventana, ocultándola, o cerrandola por completo si se cierra ventana padre.
        
        reset_pts_elegidos
            reinicia panel de visualización, Plotter de panel, y reinicia variables a valores por defecto.
            Al reiniciar se eliminan marcadores colocados, y se reinicia la posición de malla cargada 
            a la última orientación que se haya guardado.
            Al reiniciar se vuelve a revisar y guardar el tipo de pieza ingresada.

        guardar_orientacion_pieza
            guarda la orientación de la pieza.
            Esta orientación pasa a ser la nueva orientación base.
            Se envían datos de pieza orientada y descriptor de pieza al padre de la ventana.
            
        eleccion_tipo_orientacion
            actualiza el tipo de orientacion utilizada
    """

    def __init__(self, *args, procesador: Procesador=None, **kwds) -> None:
        """
            Constructor de la clase.
            Inicializa el Plotter asociado al panel de visualización, con el uso que se le quiere dar.
            Le entrega una instancia de Procesador al panel de visualización para realizar los cálculos
            de orientación necesarios.
            
            Parameters
            ----------
            procesador
                instancia de Procesador que se le entrega al panel de visualización e interacción.
        """

        OrientarFrame.__init__(self, *args, **kwds)
        self.parent = self.GetParent()
        self.panel_3d.iniciar_plotter(uso="orientar", procesador=procesador)
        self.panel_3d.tipo_pieza = self.parent.radio_box_tipo_pieza.GetSelection()
        self.Bind(wx.EVT_CLOSE, self.onclose)

    def onclose(self, event: wx.CommandEvent, desde_padre: bool=False) -> None:
        """
            Cierra ventana, ocultándola, o cerrandola por completo si se cierra ventana padre.
        
            Parameters
            ----------
            event : wx.CommandEvent
                evento entregado a método desde botón.
            
            desde_padre : bool, optional
                indicador para el cierre de ventana.
                En caso de ser True el cierre es definitivo,
                en el caso contrario, solo se esconde la ventana, by default False
        """

        if desde_padre:
            self.panel_3d.plotter.close()
            self.Destroy()
        else:
            self.Show(False)

    def mostrar_ventana(self) -> None:
        """
            Muestra la ventana para visualizar la pieza cargada y poder interactuar con esta.
        """
        self.panel_3d.plotter.render()
        self.Show()
        
    def reset_ptos_elegidos(self, event: wx.CommandEvent) -> None:
        """
            Reinicia panel de visualización, Plotter de panel, y reinicia variables a valores por defecto.
            Al reiniciar se eliminan marcadores colocados, y se reinicia la posición de malla cargada 
            a la última orientación que se haya guardado.
            Al reiniciar se vuelve a revisar y guardar el tipo de pieza ingresada.
            
            Parameters
            ----------
            event : wx.CommandEvent
                evento enviado desde botón, no utilizado
        """

        self.panel_3d.reiniciar_panel()
        self.panel_3d.tipo_pieza = self.parent.radio_box_tipo_pieza.GetSelection()

    def guardar_orientacion_pieza(self, event: wx.CommandEvent) -> None:
        """
            Guarda la orientación de la pieza.
            Esta orientación pasa a ser la nueva orientación base.
            Se envían datos de pieza orientada y descriptor de pieza al padre de la ventana.

            Parameters
            ----------
            event : wx.CommandEvent
                evento enviado desde botón, no utilizado
        """
        self.parent.datos_pieza.pieza_trmsh = self.panel_3d.extraer_pieza_orientada()
        self.parent.datos_pieza.descriptor_cilindro_cono = self.panel_3d.extraer_descriptor()
        self.parent.mostrar_msge('PIEZA ORIENTADA!\n')
        self.onclose(wx.EVT_CLOSE, desde_padre=False)
        
    def eleccion_tipo_orientacion(self, event: wx.CommandEvent) -> None:
        """
            Actualiza el tipo de orientacion elegida.

            Parameters
            ----------
            event : wx.CommandEvent
                evento de radiobox, no utilizado
        """

        self.parent.tipo_orientacion = self.radio_box_elegir_tipo_orientacion.GetSelection()


class VentanaVerCortes(VerPiezaFrame):
    """
        Implementa interfaz para visualizar la malla cargada junto con los cortes calculados.
        Hereda de la clase VerPiezaFrame para tener acceso a los elementos y widgets de la GUI.

        Methods
        -------
        mostrar_ventana
            muestra la ventana para visualizar la pieza cargada.
        
        onclose
            cierra ventana, ocultándola, o cerrandola por completo si se cierra ventana padre.
    """

    def __init__(self, *args, **kwds) -> None:
        """
            Constructor de la clase.
            Inicializa el Plotter asociado al panel, con el uso que se le quiere dar.
        """
        VerPiezaFrame.__init__(self, *args, **kwds)
        self.panel_3d.iniciar_plotter(uso="ver")
        self.Bind(wx.EVT_CLOSE, self.onclose)

    def mostrar_ventana(self) -> None:
        """
            Muestra la ventana para visualizar la pieza cargada junto con los cortes hechos sobre esta.
        """
        self.panel_3d.plotter.render()
        self.Show(True)

    def onclose(self, event: wx.CommandEvent, desde_padre: bool=False) -> None:
        """
            Cierra ventana, ocultándola, o cerrandola por completo si se cierra ventana padre.
        
            Parameters
            ----------
            event : wx.CommandEvent
                evento entregado a método desde botón.
            
            desde_padre : bool, optional
                indicador para el cierre de ventana.
                En caso de ser True el cierre es definitivo,
                en el caso contrario, solo se esconde la ventana, by default False
        """

        if desde_padre:
            self.panel_3d.plotter.close()
            self.Destroy()
        else:
            self.Show(False)


class VentanaVerTrayectorias(VerPiezaFrame):
    """
        Implementa interfaz para visualizar la malla cargada junto con las trayectorias calculadas.
        Hereda de la clase VerPiezaFrame para tener acceso a los elementos y widgets de la GUI.

        Methods
        -------
        mostrar_ventana
            muestra la ventana para visualizar la pieza cargada.
        
        onclose
            cierra ventana, ocultándola, o cerrandola por completo si se cierra ventana padre.
    """

    def __init__(self, *args, **kwds) -> None:
        """
            Constructor de la clase.
            Inicializa el Plotter asociado al panel, con el uso que se le quiere dar.
        """

        VerPiezaFrame.__init__(self, *args, **kwds)
        self.panel_3d.iniciar_plotter(uso="ver")
        self.Bind(wx.EVT_CLOSE, self.onclose)

    def mostrar_ventana(self) -> None:
        """
            Muestra la ventana para visualizar la pieza cargada junto con las trayectorias calculadas.
        """

        self.panel_3d.plotter.render()
        self.Show(True)

    def onclose(self, event: wx.CommandEvent, desde_padre: bool=False) -> None:
        """
            Cierra ventana, ocultándola, o cerrandola por completo si se cierra ventana padre.
        
            Parameters
            ----------
            event : wx.CommandEvent
                evento entregado a método desde botón.
            
            desde_padre : bool, optional
                indicador para el cierre de ventana.
                En caso de ser True el cierre es definitivo,
                en el caso contrario, solo se esconde la ventana, by default False
        """

        if desde_padre:
            self.panel_3d.plotter.close()
            self.Destroy()
        else:
            self.Show(False)


class VentanaHardfacing(HardfacingFrame):
    """
        Implementa interfaz para visualizar la malla cargada e interactuar con ella.
        Hereda de la clase HardfacingFrame para tener acceso a los elementos y widgets de la GUI.
        Se inicia el Plotter del panel de visualización con el uso de hardfacing para tener las
        variables y métodos necesarios.
        
        Attributes
        ----------
        parent
            padre de la ventana, usado para entregar indicador de que se desea hacer hardfacing.
        
        cantidad_capas
            número de capas que se quieren usar en el hardfacing, by default 1
        
        Methods
        -------
        mostrar_ventana
            muestra la ventana para visualizar la pieza cargada.
        
        onclose
            cierra ventana, ocultándola, o cerrandola por completo si se cierra ventana padre.
        
        cambiar_cant_capas
            actualiza la cantidad de capas que se quieren utilizar en el hardfacing.

        reiniciar_panel
            reinicia panel de visualización, Plotter de panel, y reinicia variables a valores por defecto.
            Al reiniciar se elimina el área seleccionada.
        
        guardar_eleccion
            guarda la selección hecha sobre la pieza.
            Esa selección es la nueva base sobre la que se obtendrán contornos para crear trayectorias.
            Se envía marcador de que se desea hacer hardfacing.
    """

    def __init__(self, *args, **kwds) -> None:
        """
            Constructor de la clase.
            Inicializa el Plotter asociado al panel de visualización, con el uso que se le quiere dar.
        """

        HardfacingFrame.__init__(self, *args, **kwds)
        self.parent = self.GetParent()
        self.panel_3d.iniciar_plotter(uso="hardfacing")
        self.cantidad_capas = 1
        self.Bind(wx.EVT_CLOSE, self.onclose)

    def onclose(self, event: wx.CommandEvent, desde_padre: bool=False) -> None:
        """
            Cierra ventana, ocultándola, o cerrandola por completo si se cierra ventana padre.
        
            Parameters
            ----------
            event : wx.CommandEvent
                evento entregado a método desde botón.
            
            desde_padre : bool, optional
                indicador para el cierre de ventana.
                En caso de ser True el cierre es definitivo,
                en el caso contrario, solo se esconde la ventana, by default False
        """

        if desde_padre:
            self.panel_3d.plotter.close()
            self.Destroy()
        else:
            self.Show(False)

    def mostrar_ventana(self) -> None:
        """
            Muestra la ventana para visualizar la pieza cargada y poder interactuar con esta.
        """

        self.panel_3d.plotter.render()
        self.Show()
    
    def cambiar_cant_capas(self, event: wx.CommandEvent) -> None:
        """
            Actualiza la cantidad de capas que se quieren utilizar en el hardfacing.

            Parameters
            ----------
            event : wx.CommandEvent
                evento dado por combobox, no utilizado
        """
        self.cantidad_capas = int(self.spin_ctrl_cantidad_capas.GetValue())

    def reiniciar_panel(self, event: wx.CommandEvent) -> None:
        """
            Reinicia panel de visualización, Plotter de panel, y reinicia variables a valores por defecto.
            Al reiniciar se elimina el área seleccionada.
            
            Parameters
            ----------
            event : wx.CommandEvent
                evento enviado desde botón, no utilizado
        """

        self.panel_3d.reiniciar_panel()
        self.parent.hacer_hardfacing = False
        self.cantidad_capas = 1
        self.spin_ctrl_cantidad_capas.SetValue(1)

    def guardar_eleccion(self, event: wx.CommandEvent) -> None:
        """
            Guarda la selección hecha sobre la pieza.
            Esa selección es la nueva base sobre la que se obtendrán contornos para crear trayectorias.
            Se envía marcador de que se desea hacer hardfacing.

            Parameters
            ----------
            event : wx.CommandEvent
                evento enviado desde botón, no utilizado
        """

        self.parent.hardfacing = True
        self.parent.mostrar_msge('DATOS GUARDADOS!\n')
        self.onclose(wx.EVT_CLOSE, desde_padre=False)


class Node:
    """
        Implementa una clase para poder establecer relaciones de padre e hijo entre distintos nodos haciendo uso de librería Shapely.
        Un nodo A se considera hijo de un nodo B cuando su información permite generar un polígono que está contenido dentro de B.
        Un nodo B se considera padre de un nodo A cuando su información permite generar un polígono que contenga el polígono del nodo A.
        
        Attributes
        ----------
        data
            información utilizada para definir los polígonos de Shapely. data es un array con coordenadas X,Y de puntos
            
        childs
            lista con todos los nodos que cumplen la condición de ser hijo del nodo, by default una lista vacía
        
        parent
            indicador de cual es el nodo padre del nodo actual, by default None
            
        Methods
        -------
        set_parent
            define como padre del nodo al nodo entregado como argumento
            
        set_child
            define como hijo del nodo al nodo entregado como argumento, agregandolo a la lista de hijos
            
        node_is_parent
            realiza un chequeo automático para definir si el nodo entregado como argumento es padre del nodo.
    """
    
    def __init__(self, data):
        self.data = data
        self.childs = []
        self.parent = None

    def set_parent(self, parent):
        """
            Método para definir otro nodo como padre del nodo que llama el método
            
            Parameters
            ----------
            parent
                instancia de la clase Node
        """
        self.parent = parent

    def set_child(self, child):
        """
            Método para definir otro nodo como hijo del nodo que llama el método, agregandolo a una lista de hijos del nodo
            
            Parameters
            ----------
            child
                instancia de la clase Node
        """
        self.childs.append(child)

    def node_is_parent(self, node):
        """
            Realiza un chequeo automático para definir si el nodo entregado como argumento es padre del nodo.
            Si relación se cumple, entrega como resultado un bool True.

            Parameters
            ----------
            node : Instancia clase Node
                nodo que se verifica si es padre del nodo que llama el método
    
            Returns
            -------
            bool
                True si el nodo es padre

        """
        auxiliar_polygon = Polygon()
        if isinstance(self.data,type(auxiliar_polygon)):
            contained = self.data.difference(node.data)
        else:
            poligono_hijo = Polygon(self.data)
            poligono_padre = Polygon(node.data)
            contained = poligono_hijo.difference(poligono_padre)
        try:
            if contained.exterior.coords == []:
                return True
            else:
                return False
        except:
            return False


class Failures:
    """
        Implementa clase Failures que se relaciona con la clase Node, para poder borrar un conjunto de curvas determinadas.
        La clase permite que al borrar una curva que tiene un padre, el padre también sea borrado, y de manera recursiva su padre.
        
        Attributes
        ----------
        layers
            lista de capas, cada capa tiene un array de puntos definiendo las posiciones que permiten definir una curva, by default vacía
        
        reversal
            lista para poder regresar desde la clase Failures a una lista que se puede usar fuera de la clase, by default vacía
            
        Methods
        -------
        add_layer_curves
            agrega curvas a layers desde una lista
            
        del_curve_parent
            elimina una curva y a su padre, de manera recursiva para luego eliminar al padre del padre
            
        get_curve
            entrega la información de la curva solicitada
            
        get_relevant_curves
            entrega una lista de curvas tal que solo se tienen aquellas que tienen más de un único hijo
            
        back_to_input
            actualiza el atributo reversal para que refleje la información de layers fuera de la clase Failures
            
    """
    def __init__(self):
        self.layers = []
        self.reversal = []

    def add_layer_curves(self, cortes):
        """
            toma como argumento una lista de cortes y la incorpora al atributo layers, para guardar la información como Nodes y 
            teniendo la información de cuales curvas son curva padre de otra
    
            Parameters
            ----------
            cortes : lista
                una lista que contiene listas, y estas contienen arrays de puntos X,Y
    
            Returns
            -------
            None.

        """
        for capa in cortes:
            self.layers.append([])
            if len(self.layers) == 1:
                for curve in capa:
                    self.layers[-1].append(Node(curve))
            else:
                prev_layer = self.layers[-2]
                for curve in capa:
                    current_node = Node(curve)
                    self.layers[-1].append(current_node)
                    for lower_node in prev_layer:
                        if lower_node.node_is_parent(current_node):
                            if lower_node.parent == None:
                                lower_node.set_parent(current_node)
                            if len(lower_node.parent.data) < len(current_node.data):
                                lower_node.set_parent(current_node)
                            current_node.set_child(lower_node)

    def del_curve_parent(self,num_layer, num_curve):
        """
            elimina la curva indicada por los argumentos y su padre, si el padre a su vez tiene un padre, vuelve a llamar el método
            pero ahora sobre el padre. La función se llama recursivamente hasta que elimine una curva sin padre.

            Parameters
            ----------
            num_layer : int
                número de la capa en que se encuentra la curva a eliminar.
            num_curve : int
                número de la curva que se desea eliminar en determinada capa.
    
            Returns
            -------
            None.

        """
        node = self.layers[num_layer][num_curve]
        parental = node.parent
        if parental == None:
            del self.layers[num_layer][num_curve]
            return
        else:
            upper_layer = self.layers[num_layer + 1]
            idx_parent = self.layers[num_layer + 1].index(parental)
            self.del_curve_parent(num_layer + 1, idx_parent)
            try:
                if node in parental.childs:
                    upper_layer.remove(parental)
            except:
                None
        del self.layers[num_layer][num_curve]

    def get_curve(self, num_layer, num_curve):
        """
            entrega los puntos X,Y que definen la curva definida por los argumentos en un array.

            Parameters
            ----------
            num_layer : int
                número de la capa en que se encuentra la curva a eliminar.
            num_curve : int
                número de la curva que se desea eliminar en determinada capa.
                
            Returns
            -------
            array
                array de puntos X,Y que representan la curva solicitada.

        """
        return self.layers[num_layer][num_curve]

    def get_relevant_curves(self, from_layer_num=0):
        """
            entrega una lista creada a partir de las curvas de manera tal que al momento de visualizar las capas, solamente
            se vean curvas cuando estas presentan divergencia. si una curva en una capa superior tiene un único hijo en la capa
            inferior que viene inmediatamente después, esta curva hijo no se agregará a la lista, pero si en una siguiente capa
            en vez de ser un único hijo fueran dos, estos dos hijos si se agregarán a la lista.

        Parameters
        ----------
        from_layer_num : int, optional
            define desde que capa se quiere considerar las curvas relevantes. By default es desde la capa 0.

        Returns
        -------
        relevant : lista
            lista con las curvas que si se usarán para visualización.

        """
        first_layer = self.layers[from_layer_num]
        relevant = [node.data for node in first_layer]
        for layer in self.layers[from_layer_num:0:-1]:
            for node in layer:
                childs = node.childs
                if len(childs) > 1:
                    try: 
                        if len(node.data)>len(childs[0].data) and childs[0].parent == node:
                            relevant.extend([node.data for node in childs])
                    except:
                        continue
        return relevant

    def back_to_input(self):
        """
            actualiza el atributo reversal para que sea una lista que contiene la información de las curvas contenida en layers
            pero sin mantener la relación con la clase Node, para poder usar independiente de la clase

        Returns
        -------
        None.

        """
        for i in range(len(self.layers)):
            self.reversal.append([])
            for j in range(len(self.layers[i])):
                self.reversal[-1].append(self.layers[i][j].data)


class VentanaEliminacionCurvas(DividirFrame):
    """
        Implementa interfaz para visualizar cortes hechos sobre una malla cargada e interactuar con ellos.
        Hereda de la clase DividirFrame para tener acceso a los elementos y widgets de la GUI.
        
        Attributes
        ----------
        cortes_originales
            cortes ingresados originalmente a la ventana.
            Se guardan para poder tener un reinicio de los cortes después de eliminar alguna curva.
        
        cortes_modificados
            cortes originales a los cuales se les eliminó al menos una curva.
            Estos son enviados al padre cuando se guarda y cierra la ventana.
        
        capa_actual
            indicador de la capa en la que se está visualizando actualmente.
        
        graf
            guarda patchcollection entregado por scatter, permite manipular y elegir curvas individualmente
        
        parent
            padre de la ventana, usado para entregar indicador de que se desea hacer hardfacing.
        
        Methods
        -------
        onclose
            cierra ventana.
        
        ingresar_cortes
            ingresa cortes a visualización, y le da valores a los atributos de cortes_originales y cortes_modificados.
            En caso de que no se detecte un parámetro de alto de cordón en la ventana padre, se asume que no se han
            calculado o ingresado los parámetros de soldadura aún.

        graficar_capa
            grafica la capa ingresada.
            En caso que ya se esté visualizando una capa, la ventana se actualiza a la nueva capa ingresada.

        guardar_eliminaciones_salir
            envia los cambios hechos a los cortes ingresados a la ventana padre.
            Una vez enviados la ventana es cerrada.
        
        eliminar_curvas
            elimina la curva seleccionada.
            En caso de que tenga curvas que dependan de la curva eliminada, estas también se eliminan.
            Actualiza la visualización, quitando la curva eliminada.
        
        reiniciar_capas
            reinicia los cambios hechos a los cortes, vuelve a estado inicial.
        
        moverse_grafico_anterior
            actualiza la visualización para mostrar la capa anterior a la que se visualiza actualmente.

        moverse_grafico_siguiente
            actualiza la visualización para mostrar la capa siguiente a la que se visualiza actualmente.
    """
    
    def __init__(self, cortes: List[List[np.ndarray]], *args, **kwds) -> None:
        """
            Constructor de la clase.
            Además de inicializar los atributos usados, también ingresa los cortes a la instancia para poder
            visualizar e interactuar con ellos.

            Parameters
            ----------
            cortes : List[List[np.ndarray]]
                cortes hechos sobre una malla en la ventana padre.
        """
        
        DividirFrame.__init__(self, *args, **kwds)
        self.cortes_originales = None  # guarda todos los cortes de las capas
        self.cortes_modificados = None  # guarda los cortes después de eliminar alguno de los originales
        self.capa_actual = 0
        self.graf = []  # Guarda patchcollection entregado por scatter, permite manipular y elegir curvas individualmente
        self.parent = self.GetParent()
        self.parent.ventana_eliminacion_curvas_manual_is = 1
        self.panel_grafico.set_window_title('PANEL DE GRÁFICOS')
        self.panel_grafico.set_window_title('PANEL DE GRÁFICOS')
        self.selector = None  # NECESARIO PARA MANTENER REFERENCIA Y QUE SE ACTUALICE EN LA VENTANA
        self.lista_poligonos = []
        self.Bind(wx.EVT_CLOSE, self.onclose)
        self.ingresar_cortes(cortes)
        self.Bind(wx.EVT_CLOSE, self.onclose)

    def onclose(self, event: wx.CommandEvent) -> None:
        """
            Cierra ventana.
        
            Parameters
            ----------
            event : wx.CommandEvent
                evento entregado a método desde botón, no utilizado.
        """
        self.parent.ventana_eliminacion_curvas_manual = None
        self.Destroy()

    def ingresar_cortes(self, cortes: List[List[np.ndarray]]) -> None:
        """
            Ingresa cortes a visualización, y le da valores a los atributos de cortes_originales y cortes_modificados.
            En caso de que no se detecte un parámetro de alto de cordón en la ventana padre, se asume que no se han
            calculado o ingresado los parámetros de soldadura aún.

            Parameters
            ----------
            cortes : List[List[np.ndarray]]
                cortes de una malla ingresada a la ventana padre
        """
        if not self.parent.text_ctrl_alto_cordon.GetValue():
            error = 'CALCULAR GEOMETRÍA DE CORDONES DE SOLDADURA PRIMERO!\n'
            error += 'INGRESANDO AMPERAJE, ELIGIENDO VELOCIDAD, DIÁMETRO, Y MATERIAL!\n'
            error = 'CALCULAR GEOMETRÍA DE CORDONES DE SOLDADURA PRIMERO!\n'
            error += 'INGRESANDO AMPERAJE, ELIGIENDO VELOCIDAD, DIÁMETRO, Y MATERIAL!\n'
            self.parent.mostrar_msge(error)
            self.parent.ventana_eliminacion_curvas_manual_is = None
            return
        self.cortes_originales = cortes
        self.cortes_modificados = copy.deepcopy(self.cortes_originales)
        self.spin_ctrl_seleccion_curva.SetRange(minVal=0, maxVal=len(self.cortes_originales[self.capa_actual]) - 1)
        self.panel_grafico.figure.set_size_inches(4, 4)
        self.graficar_capa(self.capa_actual)

    def graficar_capa(self, capa: int) -> None:
        """
            Grafica la capa ingresada.
            En caso que ya se esté visualizando una capa, la ventana se actualiza a la nueva capa ingresada.

            Parameters
            ----------
            capa : int
                indicador de la capa en la que se encuentra actualmente.
                usado para acceder capas por índice en los atributos de cortes.
        """
        self.graf = []
        curvas = self.cortes_modificados[capa]
        fallas = Failures()
        fallas.add_layer_curves(self.cortes_modificados)
        curvas = fallas.get_relevant_curves(capa)
        self.panel_grafico.axes.cla()
        self.panel_grafico.axes.set_xlabel('X [mm]')
        if self.parent.radio_box_tipo_pieza.GetSelection() == 0:
            self.panel_grafico.axes.set_ylabel('Y [mm]')
        elif self.parent.radio_box_tipo_pieza.GetSelection() == 1:
            self.panel_grafico.axes.set_ylabel('Y [grados]')
        for i in range(len(curvas)):
            self.graf.append(self.panel_grafico.axes.scatter(curvas[i][:, 0], curvas[i][:, 1], picker=True,
                                                            s=8, alpha=1, label=f'Curva {i}'))
            self.panel_grafico.axes.plot(curvas[i][:, 0], curvas[i][:, 1], linewidth=1.5, markersize=12)
        self.panel_grafico.axes.set_title(f"Capa {self.capa_actual}")
        self.panel_grafico.axes.grid(True, which='both')
        self.panel_grafico.axes.set_aspect('equal')
        self.panel_grafico.axes.minorticks_on()
        opcionesCapa = len(self.cortes_modificados[self.capa_actual]) - 1
        if opcionesCapa < 0:
            opcionesCapa = 0
        self.spin_ctrl_seleccion_curva.SetRange(minVal=0, maxVal=opcionesCapa)
        self.panel_grafico.axes.legend()
        margen = max(self.parent.datos_pieza.pieza_trmsh.extents)
        self.panel_grafico.axes.set_xlim(left=-margen+self.parent.centroide[0], right=margen+self.parent.centroide[0])
        self.panel_grafico.axes.set_ylim(bottom=-margen+self.parent.centroide[1], top=margen+self.parent.centroide[1])
        self.panel_grafico.draw()

    def guardar_eliminaciones_salir(self, event: wx.CommandEvent) -> None:
        """
            Envia los cambios hechos a los cortes ingresados a la ventana padre.
            Una vez enviados la ventana es cerrada.
        
            Parameters
            ----------
            event : wx.CommandEvent
                evento entregado a método desde botón, no utilizado.
        """

        self.parent.datos_pieza.curvas_por_capa_modificada = self.cortes_modificados
        self.parent.ventana_eliminacion_curvas_manual = None
        self.Destroy()

    def eliminar_curvas(self, event: wx.CommandEvent) -> None:
        """
            Elimina la curva seleccionada.
            En caso de que tenga curvas que dependan de la curva eliminada, estas también se eliminan.
            Actualiza la visualización, quitando la curva eliminada.

            Parameters
            ----------
            event : wx.CommandEvent
                evento enviado desde botón, no utilizado
        """

        fallas = Failures()
        fallas.add_layer_curves(self.cortes_modificados)
        fallas.del_curve_parent(self.capa_actual, self.spin_ctrl_seleccion_curva.GetValue())
        fallas.back_to_input()
        self.cortes_modificados = copy.deepcopy(fallas.reversal)
        self.graficar_capa(self.capa_actual)

    def reiniciar_capas(self, event: wx.CommandEvent):
        """
            Reinicia los cambios hechos a los cortes, vuelve a estado inicial.

            Parameters
            ----------
            event : wx.CommandEvent
                evento entregado a método desde botón, no utilizado.
        """

        self.cortes_modificados = copy.deepcopy(self.parent.datos_pieza.curvas_por_capa)
        self.graficar_capa(self.capa_actual)

    def moverse_grafico_anterior(self, event: wx.CommandEvent) -> None:
        """
            Actualiza la visualización para mostrar la capa anterior a la que se visualiza actualmente.

            Parameters
            ----------
            event : wx.CommandEvent
                evento enviado desde botón, no utilizado
        """
        
        if (self.capa_actual - 1) >= 0:
            if self.capa_actual > 0:
                self.capa_actual -= 1
            self.spin_ctrl_seleccion_curva.SetRange(minVal=0,
                                                    maxVal=len(self.cortes_originales[self.capa_actual]) - 1)
            self.graficar_capa(self.capa_actual)
        else:
            pass

    def moverse_grafico_siguiente(self, event: wx.CommandEvent) -> None:
        """
            Actualiza la visualización para mostrar la capa siguiente a la que se visualiza actualmente.

            Parameters
            ----------
            event : wx.CommandEvent
                evento enviado desde botón, no utilizado
        """

        try:
            self.capa_actual += 1
            self.spin_ctrl_seleccion_curva.SetRange(minVal=0,
                                                    maxVal=len(self.cortes_originales[self.capa_actual]) - 1)
            self.graficar_capa(self.capa_actual)
        except IndexError:
            # Suma por IndexError en índices de capas
            # CAPA_ACTUAL es contador, no tiene límite a priori
            self.capa_actual -= 1


class HerramientaIMA(MainFrame):
    """
        Clase principal de la aplicación.
        Funciona como conexión entre GUI, Procesador, DatosPieza, y funciones de utilidades.
        Permite la interacción general de usuario con los datos, y el ingreso de inputs.

        Attributes
        ----------
        procesador: procesador.Procesador, by default Procesador()

        datos_pieza: datospieza.DatosPieza, by default DatosPieza()
            datos de malla cargada, permite cargar malla, tener acceso a sus propiedades, y guardar inputs, como tipo de pieza, o
            el descriptor de pieza para casos de cilindros y conos.
        
        tipo_orientacion
            número que indica tipo de orientacion utilizada: 0 = automática, 1 = manual
            default = 0
        
        hardfacing: bool, by default False
            indicador para realizar hardfacing en vez de cortes y cálculo de trayectorias sobre la malla cargada
        
        ventana_ver_pieza: VentanaVerPieza, by default VentanaVerPieza(parent=self)
            ventana para visualizar la malla cargada
        
        ventana_ver_cortes: VentanaVerCortes, by default VentanaVercortes(parent=self)
            ventana para visualizar los cortes hechos sobre la malla cargada
        
        ventana_orientar_manual: VentanaOrientacion, by default VentanaOrientacion(parent=self, procesador=self.procesador)
            ventana para orientar la malla cargada
        
        ventana_ver_trayectorias: VentanaVerTrayectorias, by default VentanaVerTrayectorias(parent=self)
            ventana para visualizar las trayectorias calculadas para cortes hechos en la malla cargada
        
        ventana_hardfacing: VentanaHardfacing, by default VentanaHardfacing(parent=self)
            ventana para interactuar y realizar hardfacing a la malla cargada
        
        ventana_eliminacion_curvas_manual: VentanaEliminacionCurvas, by default None
            ventana para interactuar y eliminar curvas una vez hechos los cortes sobre una malla cargada
        
        Methods
        -------
        on_close
            cierra la ventana principal y todas las ventanas hijas.
        
        close_children
            cierra las ventanas hijas de la ventana principal, según el indicador desde_padre.
        
        eleccion_tipo_pieza
            actualiza el tipo de pieza elegido.
        
        preguntar_usuario_eleccion_pieza
            inicia dialogo para que usuario confirme elección de archivo de malla.
        
        elegir_archivo_datos_pieza
            crea un dialogo para elegir un archivo de STL.
            En caso que se esté eligiendo el mismo archivo se pregunta confirmación a usuario.
            Muestra mensajes de la operación en la consola de la ventana principal.
        
        mallas_iguales
            compara dos mallas para ver si son iguales.
            Esta comparación es sobre sus vértices y es exacta, por lo que si las mallas corresponden
            a la misma pieza, pero están en posiciones distintas, retornará que no son iguales.
        
        orientar_visualmente
            carga la malla elegida en la ventana de orientación, y luego muestra la ventana.
            En caso de que no se haya cargado la pieza aún, se da aviso en la consola de la ventana principal.
            En caso de que la malla que se está intentando cargar es la misma que ya se cargó con anterioridad, 
            solo se muestra la ventana, sin cargar la malla de nuevo.
            Permite la orientación de la malla mediante la elección de puntos en su superficie.
        
        mostrar_msge
            muestra el mensaje ingresado en la consola de la ventana principal.
        
        visualizar_pieza_elegida
            carga la malla elegida en la ventana de visualizacion, y luego muestra la ventana.
            En caso de que no se haya cargado la pieza aún, se da aviso en la consola de la ventana principal.
            En caso de que la malla que se está intentando cargar es la misma que ya se cargó con anterioridad, 
            solo se muestra la ventana, sin cargar la malla de nuevo.
        
        cortar_pieza
            se corta la malla cargada de acuerdo al tipo de pieza indicada.
            En caso de que se haya hecho hardfacing, cortes se hacen sobre la extrusión del área elegida.
            Se asume que malla ya fue orientada, no se checkea.
            Se requieren parámetros de soldadura, en caso de que no se hayan ingresado/calculado se da aviso.
        
        hacer_hardfacing
            carga la malla elegida en la ventana de hardfacing, y luego muestra la ventana.
            En caso de que no se haya cargado la pieza aún, se da aviso en la consola de la ventana principal.
            Permite la selección de un área para hacer hardfacing/surfacing sobre la superficie de la malla,
            mediante la interacción del mouse.

        eliminar_contornos_de_cortes
            carga cortes hechos sobre una malla en la ventana de eliminación de cortes.
            En caso de que no se haya cortado la malla aún, se da aviso en la consola de la ventana principal.
            Permite la eliminación de cortes mediante la interfaz.
        
        ver_cortes
            carga la malla elegida y los cortes hechos sobre esta en la ventana de visualizacion, y luego muestra la ventana.
            En caso de que no se haya cargado o cortado la pieza aún, se da aviso en la consola de la ventana principal.
            En caso de que la malla que se está intentando cargar es la misma que ya se cargó con anterioridad, 
            solo se muestra la ventana, sin cargar la malla de nuevo.

        calcular_geometria_cordones
            estima el alto y ancho de los cordones de soldadura.
            Basado en el material y diámetro del alambre de soldadura, la velocidad de soldadura, y el amperaje a usar.
            Los valores también pueden ser modificados en la pantalla principal.
        
        calcular_voltaje
            estima el voltaje a usar en la soldadura, basado en el alambre y el amperaje a usar.
            El valor también puede ser modificado en la pantalla principal.
        
        calcular_trayectorias_relleno
            calcula las trayectorias para rellenar los cortes hechos en la malla cargada.
            Requiere los parámetros de soldadura, y de posición y ubicación.
            Una vez calculadas las trayectorias, estas y la malla sobre la que se calculan 
            se posicionan de acuerdo a inputs de posición y orientación de pantalla principal.

        ver_trayectorias_generadas
            carga la malla elegida y las trayectorias calculadas sobre esta en la ventana de visualizacion, y luego muestra la ventana.
            En caso de que no se haya cargado o cortado la pieza aún, se da aviso en la consola de la ventana principal.
            En caso de que la malla que se está intentando cargar sea la misma que ya se cargó con anterioridad, 
            solo se muestra la ventana, sin cargar la malla de nuevo.

        guardar_resultados_trayectorias
            escribe archivo .csr con los movimientos necesarios para llevar a cabo las trayectorias calculadas.
            Requiere que las trayectorias estén calculadas, en caso de que no lo estén, se da aviso en la pantalla principal.
            Archivo .csr se guarda en la carpeta donde se encuentra main.py.
    """

    def __init__(self, *args, **kwds) -> None:
        """
            Constructor de la clase HerramientaIMA.
            Inicializa todas las variables usadas, y las instancias de Ventanas, Procesador y DatosPieza.
            Inicializa validadores para los inputs de usuarios.
        """

        MainFrame.__init__(self, *args, **kwds)
        # PROCESADOR ENCARGADO DE LOS CÁLCULOS
        self.procesador = Procesador()
        msge = self.procesador.cargar_archivo_materiales(BASE_DATOS_MATERIALES)
        self.mostrar_msge(msge)
        msge = self.procesador.cargar_archivo_soldaduras(BASE_DATOS_SOLDADURAS)
        self.mostrar_msge(msge)

        self.datos_pieza = DatosPieza()
        self.hardfacing = False
        
        self.tipo_orientacion=0
        
        self.centroide = None

        self.ventana_ver_pieza = VentanaVerPieza(parent=self)
        self.ventana_ver_cortes = VentanaVerCortes(parent=self)
        self.ventana_orientar_manual = VentanaOrientacion(parent=self, procesador=self.procesador)
        self.ventana_ver_trayectorias = VentanaVerTrayectorias(parent=self)
        self.ventana_hardfacing = VentanaHardfacing(parent=self)
        self.ventana_eliminacion_curvas_manual = None
        
        # TODO: QUE MATERIALES Y GASES ESTÉN DE ACUERDO A BASE DE DATOS
        textos_posicion = [self.text_ctrl_posicion_x, self.text_ctrl_posicion_y, self.text_ctrl_posicion_z,
                        self.text_ctrl_angulo_x, self.text_ctrl_angulo_y, self.text_ctrl_angulo_z]

        textos_soldadura = [self.text_ctrl_voltaje, self.text_ctrl_amperaje,
                        self.combo_box_diametros_alambre, self.combo_box_velocidades,
                        self.text_ctrl_ancho_cordon, self.text_ctrl_alto_cordon]

        utilidades.agregar_validador(textos_posicion, utilidades.validador_numerico_general)
        utilidades.agregar_validador(textos_soldadura, utilidades.validador_numerico_basico)

        self.Bind(wx.EVT_CLOSE, self.on_close)

    def on_close(self, event: wx.CommandEvent) -> None:
        """
            Cierra la ventana principal y todas las ventanas hijas.

            Parameters
            ----------
            event : wx.CommandEvent
                evento de cierre, no utilizado.
        """
        self.close_children(event, desde_padre=True)
        self.Destroy()

    def close_children(self, event: wx.CommandEvent, desde_padre: bool=False) -> None:
        """
            Cierra las ventanas hijas de la ventana principal, según el indicador desde_padre

            Parameters
            ----------
            event : wx.CommandEvent
                evento de cierre, no utilizado
            
            desde_padre : bool, optional
                indicador de cierre total para las ventanas hijas, by default False
        """

        if self.ventana_ver_pieza:
            self.ventana_ver_pieza.onclose(event, desde_padre=desde_padre)
        if self.ventana_orientar_manual:
            self.ventana_orientar_manual.onclose(event, desde_padre=desde_padre)
        if self.ventana_ver_cortes:
            self.ventana_ver_cortes.onclose(event, desde_padre=desde_padre)
        if self.ventana_ver_trayectorias:
            self.ventana_ver_trayectorias.onclose(event, desde_padre=desde_padre)

    def eleccion_tipo_pieza(self, event: wx.CommandEvent) -> None:
        """
            Actualiza el tipo de pieza elegido.

            Parameters
            ----------
            event : wx.CommandEvent
                evento de radiobox, no utilizado
        """

        self.datos_pieza.tipo_pieza = self.radio_box_tipo_pieza.GetSelection()

    def preguntar_usuario_eleccion_pieza(self) -> bool:
        """
            Inicia dialogo para que usuario confirme elección de archivo de malla.

            Returns
            -------
            bool
                confirmación o cancelación de la elección de archivo.
        """
        with wx.MessageDialog(self, message="Estás eligiendo la misma pieza que tienes, estás seguro?", style=wx.OK | wx.CANCEL) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                return True
            else:
                return False

    def elegir_archivo_datos_pieza(self, event: wx.CommandEvent) -> None:
        """
            Crea un dialogo para elegir un archivo de STL.
            En caso que se esté eligiendo el mismo archivo se pregunta confirmación a usuario.
            Muestra mensajes de la operación en la consola de la ventana principal.

            Parameters
            ----------
            event : wx.CommandEvent
                evento dado por botón, no utilizado
        """
        filedialog = wx.FileDialog(self, message="Elegir archivo de pieza", defaultDir="", defaultFile="",
                                wildcard="STL files (*.stl)|*.stl", style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        filedialog.ShowModal()

        if not filedialog.GetPath():
            filedialog.Destroy()
            return
        
        if self.datos_pieza.path_pieza == filedialog.GetPath():
            # Caso en el que se está eligiendo la misma pieza
            # Se pregunta confirmación porque esto resetea todo
            eleccion = self.preguntar_usuario_eleccion_pieza()
            if not eleccion:
                return

        msge = "Ingresando pieza ubicada en:\n{}\n".format(filedialog.GetPath())
        self.mostrar_msge(msge)

        wx.BeginBusyCursor(cursor=wx.HOURGLASS_CURSOR)
        self.close_children(event=wx.EVT_CLOSE, desde_padre=False)

        msge = self.datos_pieza.cargar_malla(filedialog.GetPath())
        
        # En caso de cambio de pieza se reinicia marcador de hardfacing
        self.hardfacing = False

        self.button_corte_pieza.Enable()
        self.radio_box_tipo_pieza.Enable()
        filedialog.Destroy()
        wx.EndBusyCursor()

        self.mostrar_msge(msge)

    def mallas_iguales(self, malla1: Union[trimesh.Trimesh, vedo.Mesh]=None, malla2: Union[trimesh.Trimesh, vedo.Mesh]=None) -> bool:
        """
            Compara dos mallas para ver si son iguales.
            Esta comparación es sobre sus vértices y es exacta, por lo que si las mallas corresponden
            a la misma pieza, pero están en posiciones distintas, retornará que no son iguales.

            Parameters
            ----------
            malla1 : trimesh.Trimesh, o vedo.Mesh, optional
                primera malla de comparación, by default None

            malla2 : trimesh.Trimesh, o vedo.Mesh, optional
                segunda malla de comparación, by default None

            Returns
            -------
            bool
                indicador de comparación de mallas
        """

        if malla1 is None or malla2 is None:
            return False

        if isinstance(malla1, trimesh.base.Trimesh):
            puntos1 = malla1.vertices
        elif isinstance(malla1, vedo.mesh.Mesh):
            puntos1 = malla1.points()
        
        if isinstance(malla2, trimesh.base.Trimesh):
            puntos2 = malla2.vertices
        elif isinstance(malla2, vedo.mesh.Mesh):
            puntos2 = malla2.points()
        
        if np.array_equal(puntos1, puntos2):
            return True
        else:
            return False

    def orientar_visualmente(self, event: wx.CommandEvent) -> None:
        """
            Carga la malla elegida en la ventana de orientación, y luego muestra la ventana.
            En caso de que no se haya cargado la pieza aún, se da aviso en la consola de la ventana principal.
            En caso de que la malla que se está intentando cargar es la misma que ya se cargó con anterioridad, 
            solo se muestra la ventana, sin cargar la malla de nuevo.
            Permite la orientación de la malla mediante la elección de puntos en su superficie.

            Parameters
            ----------
            event : wx.CommandEvent
                evento de botón, no utilizado
        """

        if self.datos_pieza.path_pieza:
            if not self.mallas_iguales(self.datos_pieza.pieza_trmsh, self.ventana_orientar_manual.panel_3d.mesh):
                self.ventana_orientar_manual.panel_3d.insertar_pieza(self.datos_pieza.pieza_trmsh, centrada=True)
            self.ventana_orientar_manual.panel_3d.tipo_pieza = self.datos_pieza.tipo_pieza
            self.ventana_orientar_manual.panel_3d.tipo_orientacion = self.tipo_orientacion
            self.ventana_orientar_manual.mostrar_ventana()
        else:
            msge = 'CARGAR ARCHIVO CON DATOS DE PIEZA!\n'
            self.mostrar_msge(msge)

    def mostrar_msge(self, mensaje: str) -> None:
        """
            Muestra el mensaje ingresado en la consola de la ventana principal.
        """
        self.text_ctrl_consola.AppendText('{}\n'.format(mensaje))

    def visualizar_pieza_elegida(self, event: wx.CommandEvent) -> None:
        """
            Carga la malla elegida en la ventana de visualizacion, y luego muestra la ventana.
            En caso de que no se haya cargado la pieza aún, se da aviso en la consola de la ventana principal.
            En caso de que la malla que se está intentando cargar es la misma que ya se cargó con anterioridad, 
            solo se muestra la ventana, sin cargar la malla de nuevo.

            Parameters
            ----------
            event : wx.CommandEvent
                evento de botón, no utilizado
        """

        if self.datos_pieza.path_pieza:
            if not self.mallas_iguales(self.datos_pieza.pieza_trmsh, self.ventana_ver_pieza.panel_3d.mesh):
                self.ventana_ver_pieza.panel_3d.insertar_pieza(self.datos_pieza.pieza_trmsh)
            self.ventana_ver_pieza.mostrar_ventana()
        else:
            msge = 'CARGAR ARCHIVO CON DATOS DE PIEZA!\n'
            self.mostrar_msge(msge)

    def cortar_pieza(self, event: wx.CommandEvent) -> None:
        # TODO: AGREGAR PARADA DE EMERGENCIA
        """
            Se corta la malla cargada de acuerdo al tipo de pieza indicada.
            En caso de que se haya hecho hardfacing, cortes se hacen sobre la extrusión del área elegida.
            Se asume que malla ya fue orientada, no se checkea.
            Se requieren parámetros de soldadura, en caso de que no se hayan ingresado/calculado se da aviso.
            
            Parameters
            ----------
            event : wx.CommandEvent
                evento de botón, no utilizado
        """

        if self.ventana_ver_cortes:
            self.ventana_ver_cortes.onclose(wx.EVT_CLOSE)

        if not self.datos_pieza.path_pieza:
            self.text_ctrl_consola.AppendText('INGRESAR DATOS DE PIEZA!\n')
            return

        if not self.text_ctrl_alto_cordon.GetValue():
            error = 'CALCULAR GEOMETRÍA DE CORDONES DE SOLDADURA PRIMERO!\n'
            error += 'INGRESANDO AMPERAJE, ELIGIENDO VELOCIDAD, DIÁMETRO, Y MATERIAL!\n'
            self.mostrar_msge(error)
            return

        wx.BeginBusyCursor(cursor=wx.HOURGLASS_CURSOR)
        self.button_corte_pieza.Disable()
        self.button_hardfacing.Disable()
        self.radio_box_tipo_pieza.Disable()

        msge = 'PROCESAMIENTO DE LA NUBE DE PUNTOS EN PROGRESO!\n'
        self.mostrar_msge(msge)
        alto = float(self.text_ctrl_alto_cordon.GetValue())
        ancho = float(self.text_ctrl_ancho_cordon.GetValue())
        self.datos_pieza.reiniciar_cortes()
        self.datos_pieza.reiniciar_trayectorias()
        
        if self.hardfacing:
            area_seleccion = self.ventana_hardfacing.panel_3d.puntos_pintados
            cant_capas = self.ventana_hardfacing.cantidad_capas
            
            # if self.datos_pieza.tipo_pieza == 2:
            #     self.datos_pieza.descriptor_cilindro_cono = [115, 25]
            #     self.datos_pieza.descriptor_cilindro_cono = [364, 10]
            self.datos_pieza.curvas_por_capa = self.procesador.calcular_hardfacing_malla(area_seleccion, ancho, alto, cant_capas,
                                                                                         self.datos_pieza.tipo_pieza, 
                                                                                         self.datos_pieza.descriptor_cilindro_cono,
                                                                                         self.ventana_hardfacing.panel_3d.radio_busqueda)
                                                                                         
        else:
            pieza_cortar_trmsh = self.datos_pieza.pieza_trmsh
            self.datos_pieza.curvas_por_capa = self.procesador.calcular_cortes_malla(pieza_cortar_trmsh, ancho, alto, 
                                                                                     self.datos_pieza.step_over, 
                                                                                     self.datos_pieza.tipo_pieza, 
                                                                                     self.datos_pieza.descriptor_cilindro_cono)

        if len(self.datos_pieza.curvas_por_capa) == 0:
            msge = 'NO SE ENCONTRARON CONTORNOS!\nCORTES VACÍOS!\n'
            self.mostrar_msge(msge)

        msge = 'TERMINADO!\n'
        self.mostrar_msge(msge)

        wx.EndBusyCursor()
        self.radio_box_tipo_pieza.Enable()
        self.button_hardfacing.Enable()
        self.button_corte_pieza.Enable()
        self.centroide = self.datos_pieza.pieza_trmsh.centroid

    def hacer_hardfacing(self, event: wx.CommandEvent) -> None:
        """
            Carga la malla elegida en la ventana de hardfacing, y luego muestra la ventana.
            En caso de que no se haya cargado la pieza aún, se da aviso en la consola de la ventana principal.
            Permite la selección de un área para hacer hardfacing/surfacing sobre la superficie de la malla,
            mediante la interacción del mouse.

            Parameters
            ----------
            event : wx.CommandEvent
                evento de botón, no utilizado
        """

        if self.datos_pieza.path_pieza:
            self.ventana_hardfacing.panel_3d.insertar_pieza(self.datos_pieza.pieza_trmsh, centrada=False)
            self.ventana_hardfacing.mostrar_ventana()
        else:
            msge = 'CARGAR ARCHIVO CON DATOS DE PIEZA!\n'
            self.mostrar_msge(msge)

    def eliminar_contornos_de_cortes(self, event: wx.CommandEvent) -> None:
        """
            Carga cortes hechos sobre una malla en la ventana de eliminación de cortes.
            En caso de que no se haya cortado la malla aún, se da aviso en la consola de la ventana principal.
            Permite la eliminación de cortes mediante la interfaz.
            
            Parameters
            ----------
            event : wx.CommandEvent
                evento de botón, no utilizado
        """

        msge = 'NO SE PUEDE MOSTRAR, CORTAR NUBE DE DATOS!'
        try:
            if not self.ventana_eliminacion_curvas_manual:
                if self.datos_pieza.curvas_por_capa:
                    if self.datos_pieza.curvas_por_capa_modificada:
                        self.ventana_eliminacion_curvas_manual = VentanaEliminacionCurvas(self.datos_pieza.curvas_por_capa_modificada, self)
                    else:
                        self.ventana_eliminacion_curvas_manual = VentanaEliminacionCurvas(self.datos_pieza.curvas_por_capa, self)
                    self.ventana_eliminacion_curvas_manual.Show()
                else:
                    self.mostrar_msge(msge)
                    self.ventana_eliminacion_curvas_manual = None
        except AttributeError as error:
            print(error)
            self.mostrar_msge(msge)
            self.ventana_eliminacion_curvas_manual = None

    def ver_cortes(self, event: wx.CommandEvent) -> None:
        """
            Carga la malla elegida y los cortes hechos sobre esta en la ventana de visualizacion, y luego muestra la ventana.
            En caso de que no se haya cargado o cortado la pieza aún, se da aviso en la consola de la ventana principal.
            En caso de que la malla que se está intentando cargar es la misma que ya se cargó con anterioridad, 
            solo se muestra la ventana, sin cargar la malla de nuevo.

            Parameters
            ----------
            event : wx.CommandEvent
                evento de botón, no utilizado
        """

        if not self.datos_pieza.pieza_trmsh:
            msge = 'CARGAR DATOS DE PIEZA!\n'
            self.mostrar_msge(msge)
            return

        # SE CARGA ACÁ PARA QUE CORTES CORRESPONDAN CON PIEZA ORIENTADA
        if not self.mallas_iguales(self.datos_pieza.pieza_trmsh, self.ventana_ver_cortes.panel_3d.mesh):
            self.ventana_ver_cortes.panel_3d.insertar_pieza(file=self.datos_pieza.pieza_trmsh)

        if self.datos_pieza.curvas_por_capa_modificada:
            self.ventana_ver_cortes.panel_3d.insertar_cortes(self.datos_pieza.curvas_por_capa_modificada)
            self.ventana_ver_cortes.mostrar_ventana()
        else:
            if self.datos_pieza.curvas_por_capa:
                self.ventana_ver_cortes.panel_3d.insertar_cortes(self.datos_pieza.curvas_por_capa)
                self.ventana_ver_cortes.mostrar_ventana()
            else:
                msge = 'CORTAR PIEZA PRIMERO!\n'
                self.mostrar_msge(msge)
                return
        self.ventana_ver_cortes.mostrar_ventana()

    def calcular_geometria_cordones(self, event: wx.CommandEvent) -> None:
        """
            Estima el alto y ancho de los cordones de soldadura.
            Basado en el material y diámetro del alambre de soldadura, la velocidad de soldadura, y el amperaje a usar.
            Los valores también pueden ser modificados en la pantalla principal.

            Parameters
            ----------
            event : wx.CommandEvent
                evento de botón, no utilizado
        """
        try:
            amperaje = float(self.text_ctrl_amperaje.GetValue())
            velocidad = float(self.combo_box_velocidades.GetValue())
            material = self.combo_box_materiales_alambre.GetValue()
            diametro = float(self.combo_box_diametros_alambre.GetValue())
            alto, ancho, step_over = self.procesador.calcular_cordones(material, diametro, velocidad, amperaje)
        except ValueError:
            alto = 0
            ancho = 0
            step_over = 0
        
        self.datos_pieza.step_over = step_over
        self.text_ctrl_alto_cordon.SetValue(str(round(alto, 2)))
        self.text_ctrl_ancho_cordon.SetValue(str(round(ancho, 2)))

    def calcular_voltaje(self, event: wx.CommandEvent) -> None:
        """
            Estima el voltaje a usar en la soldadura, basado en el alambre y el amperaje a usar.
            El valor también puede ser modificado en la pantalla principal.

            Parameters
            ----------
            event : wx.CommandEvent
                evento de botón, no utilizado
        """
        try:
            material = self.combo_box_materiales_alambre.GetValue()
            amperaje = float(self.text_ctrl_amperaje.GetValue())
            voltaje = self.procesador.calcular_voltaje(material, amperaje)
        except ValueError:
            voltaje = 0
        self.text_ctrl_voltaje.SetValue(str(round(voltaje, 3)))

    def calcular_trayectorias_relleno(self, event: wx.CommandEvent) -> None:
        """
            Calcula las trayectorias para rellenar los cortes hechos en la malla cargada.
            Requiere los parámetros de soldadura, y de posición y ubicación.
            Una vez calculadas las trayectorias, estas y la malla sobre la que se calculan 
            se posicionan de acuerdo a inputs de posición y orientación de pantalla principal.

            Parameters
            ----------
            event : wx.CommandEvent
                evento de botón, no utilizado
        """
        msge = 'CALCULANDO TRAYECTORIAS!\n'
        self.mostrar_msge(msge)

        if self.ventana_ver_trayectorias:
            self.ventana_ver_trayectorias.Show(False)

        if self.datos_pieza.curvas_por_capa_modificada:
            cortes = copy.deepcopy(self.datos_pieza.curvas_por_capa_modificada)
        else:
            cortes = copy.deepcopy(self.datos_pieza.curvas_por_capa)

        # Revisar que hay inputs (si están vacíos valor de input es '')
        try:
            vector_traslacion = np.asarray([float(self.text_ctrl_posicion_x.GetValue()),
                                            float(self.text_ctrl_posicion_y.GetValue()),
                                            float(self.text_ctrl_posicion_z.GetValue())])
        except ValueError:
            vector_traslacion = np.array([0, 0, 0])
            msge = 'INGRESAR INPUT EN POSICIÓN DE PIEZA!\n'
            self.mostrar_msge(msge)
            return

        try:
            grados_rotacion = np.asarray([float(self.text_ctrl_angulo_x.GetValue()),
                                        float(self.text_ctrl_angulo_y.GetValue()),
                                        float(self.text_ctrl_angulo_z.GetValue())])
        except ValueError:
            grados_rotacion = np.array([0, 0, 0])
            msge = 'INGRESAR INPUT EN ORIENTACIÓN DE PIEZA!\n'
            self.mostrar_msge(msge)
            return

        material = self.combo_box_materiales_alambre.GetValue()
        width = float(self.text_ctrl_ancho_cordon.GetValue())
        height = float(self.text_ctrl_alto_cordon.GetValue())
        velocidad = float(self.combo_box_velocidades.GetValue())
        offset = width * 0.3
        
        capas = self.procesador.calcular_trayectorias(cortes, width, height, offset, 
                                                    self.datos_pieza.step_over, velocidad, material, 
                                                    self.datos_pieza.tipo_pieza, descriptor_pieza = self.datos_pieza.descriptor_cilindro_cono)


        # TODO: MOVER ESTO A SU PROPIA FUNCIÓN/MÉTODO
        # Posicionar las trayectorias y pieza en ubicación y orientación correcta
        # Se referencia con respecto a la referencia del mundo real
        centro = self.datos_pieza.pieza_trmsh.centroid

        verts = utilidades.rotar_pieza(self.datos_pieza.pieza_trmsh.vertices, centro, grados_rotacion)
        verts = utilidades.traslacion3d(verts, vector_traslacion)
        self.datos_pieza.pieza_trmsh.vertices = verts

        for i, altura in enumerate(capas):
            for j, curva in enumerate(altura):
                for k, line in enumerate(curva):
                    capas[i][j][k] = utilidades.rotar_pieza(line, centro, grados_rotacion)
                    capas[i][j][k] = utilidades.traslacion3d(line, vector_traslacion)

        self.datos_pieza.puntos_ancla_trayectorias = capas

        msge = 'CÁLCULOS DE TRAYECTORIA LISTOS!\n'
        self.mostrar_msge(msge)

    def ver_trayectorias_generadas(self, event: wx.CommandEvent) -> None:
        """
            Carga la malla elegida y las trayectorias calculadas sobre esta en la ventana de visualizacion, y luego muestra la ventana.
            En caso de que no se haya cargado o cortado la pieza aún, se da aviso en la consola de la ventana principal.
            En caso de que la malla que se está intentando cargar sea la misma que ya se cargó con anterioridad, 
            solo se muestra la ventana, sin cargar la malla de nuevo.

            Parameters
            ----------
            event : wx.CommandEvent
                evento de botón, no utilizado
        """

        # En caso que no se cumplan condiciones, ventana se abre sin trayectorias
        # Se avisa en consola de GUI lo que falta por hacer
        if len(self.datos_pieza.puntos_ancla_trayectorias) <= 0:
            msge = 'CALCULAR TRAYECTORIAS!\n'
            self.mostrar_msge(msge)
            return
        
        if not self.mallas_iguales(self.datos_pieza.pieza_trmsh, self.ventana_ver_trayectorias.panel_3d.mesh):
            self.ventana_ver_trayectorias.panel_3d.insertar_pieza(self.datos_pieza.pieza_trmsh)
        self.ventana_ver_trayectorias.panel_3d.insertar_trayectorias(self.datos_pieza.puntos_ancla_trayectorias)
        self.ventana_ver_trayectorias.mostrar_ventana()

    def guardar_resultados_trayectorias(self, event: wx.CommandEvent) -> None:
        """
            Escribe archivo .csr con los movimientos necesarios para llevar a cabo las trayectorias calculadas.
            Requiere que las trayectorias estén calculadas, en caso de que no lo estén, se da aviso en la pantalla principal.
            Archivo .csr se guarda en la carpeta donde se encuentra main.py.

            Parameters
            ----------
            event : wx.CommandEvent
                evento de botón, no utilizado
        """
        
        # TODO: CHECKEOS DE QUE TODO ESTÉ BIEN
        if len(self.datos_pieza.puntos_ancla_trayectorias) > 0:
            voltaje = int(float(self.text_ctrl_voltaje.GetValue()))
            amperaje = int(float((self.text_ctrl_amperaje.GetValue())))
            velocidad = float(self.combo_box_velocidades.GetValue())
            generatorcsr.write_code(self.datos_pieza.puntos_ancla_trayectorias, velocidad,
                                    amperaje, voltaje, self.datos_pieza.pto_to_origen, self.radio_box_tipo_pieza.GetSelection())
            msge = 'ESCRITURA DE PROGRAMA CSR LISTA!\n'
            self.mostrar_msge(msge)
        else:
            msge = 'HACER CÁLCULO DE TRAYECTORIAS PRIMERO!\n'
            self.mostrar_msge(msge)


class MyApp(wx.App):
    def OnInit(self):
        self.topframe = HerramientaIMA(None, wx.ID_ANY, "")
        self.SetTopWindow(self.topframe)
        self.topframe.Show()
        return True


if __name__ == '__main__':
    app = MyApp()
    app.MainLoop()
