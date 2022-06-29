import wx
import vedo
import trimesh
import utilidades
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
# Por alguna razon se tiene que importar así o no reconoce el interactor
# from vtk.wx.wxVTKRenderWindowInteractor import wxVTKRenderWindowInteractor
from vtkmodules.wx.wxVTKRenderWindowInteractor import wxVTKRenderWindowInteractor
from typing import Callable, List, Tuple, Union


class CanvasPanel(FigureCanvas):
    """
        Clase de Canvas de matplotlib para insertar en un wx.Frame.
        Usado para mostrar figuras en 2D e interactuar con ellas.
        Hereda de la clase FigureCanvasWxAgg.

        Attributes
        ----------
        figure: matplotlib.figure.Figure
            figura para colocar los gráficos

        axes: matplotlib.axes.Axes
            axes de la figura
        
        Methods
        -------
        __init__(parent: wx.Frame, identificacion: wx.StandardID=wx.ID_ANY)
            constructor de la clase CanvasPanel
    """

    def __init__(self, parent: wx.Frame, identificacion: wx.StandardID=wx.ID_ANY) -> None:
        """
            Constructor de clase CanvasPanel

            Parameters
            ----------
            parent : wx.Frame
                padre de Canvas, donde estará ubicado
            identificacion : wx.StandardID, optional
                ID de Canvas, dado por wxPython, by default wx.ID_ANY
        """

        self.figure = Figure()
        self.figure.set_tight_layout('True')
        self.axes = self.figure.add_subplot(111, xlabel='X', ylabel='Y')
        self.axes.set_aspect('equal')
        FigureCanvas.__init__(self, parent, identificacion, self.figure)


class VedoPanel(wx.Panel):
    """
        Implementa panel de Vedo usado para visualización e interacción de datos. Permite inserción de panel en GUI de wxPython. 
        Panel cambia su funcionalidad y variables de acuerdo a su uso.
        Uso = 'ver': panel configurado solo para visualización e interacción básica
        Uso = 'orientar': panel configurado para visualización e interacción de orientación.
                Permite elección de puntos en superficie de malla cargada para elegir origen y orientación
        Uso = 'hardfacing': panel configurado para visualización e interacción de hardfacing.
                Permite pintado de áreas y señala a ventana principal que se quiere hacer hardfacing

        
        Parameters
        ----------
        parent: wx.Frame, by default None
            wx.Frame donde se coloca el panel

        id: wx.StandardID, by default wx.ID_ANY
            ID para reconocer al panel

        Attributes
        ----------
        widget: vtk.wx.wxVTKRenderWindowInteractor.wxVTKRenderWindowInteractor, by default wxVTKRenderWindowInteractor(self, -1)
            RenderInteractor para realizar visualizaciones e insertar panel en un wx.Frame
        
        uso: str, by default "ver"
            indicador del uso que se quiere dar al panel.
            opciones son: "ver", "orientar", "hardfacing"
        
        plotter: vedo.plotter.Plotter, by default None
            Plotter para realizar visualizaciones e interacciones
        
        mesh: vedo.mesh.Mesh, by default None
            malla cargada o por cargar en el panel
        
        axes: vedo.addons.Axes, by default None
            instancia de Axes para visualización
        
        cortes: bool, by default False
            indicador de visualización de cortes
            si cortes se insertan en panel cortes=True

        trayectorias: bool, by default = False
            indicador de visualización de trayectorias
            si trayectorias se insertan en panel trayectorias=True
        
        procesador: procesador.Procesador, by default None
            instancia de Procesador para realizar cálculos

        self.sizer: wx.BoxSizer(wx.VERTICAL)
            sizer para colocar panel

        Methods
        -------
        crear_para_orientacion
            inicializa las variables necesarias para el uso del panel en modo orientación

        crear_para_hardfacing
            inicializa las variables necesarias para el uso del panel en modo hardfacing
        
        iniciar_plotter
            inicializa instancia de Plotter del panel, las variables a usar, e inserta callbacks para interacción
            según uso que se le quiere dar

        insertar_pieza
            inserta malla Trimesh o carga malla ingresada en file al Plotter del panel.
            En caso de que ya haya una malla cargada la reemplaza.
        
        insertar_axes
            Inicializa e inserta ejes de coordenadas en el panel, usando las dimensiones 
            de la malla cargada para establecer los límites.
            Dimensiones se asumen en milímetros, pero unidades de medida dependen de unidades de malla.
            Usado también para actualizar ejes si la malla o su posición cambian.

        insertar_cortes
            Inserta los cortes ingresados al panel para su visualización.
            Cortes son actualizados en caso de que ya se hayan insertado antes.

        insertar_trayectorias
            inserta las trayectorias ingresadas al panel para su visualización.
            Trayectorias son actualizadas en caso de que ya se hayan insertado antes.

        on_left_click_orient
            inserta un marcador en el panel y en la lista interna de marcadores indicando el punto 
            donde se hizo click en la superficie de la malla.
            Colores varían de acuerdo al número del marcador: primer marcador es negro, 
            segundo es rojo, tercero es verde, y cuarto es azul.
            Solo usada en caso de que uso='orientar'.

        on_right_click_orient
            quita el último marcador ingresado tanto del panel como de la lista interna de marcadores.
            Solo usada en caso de que uso='orientar'.

        on_right_click_paint
            toggle para variable pintar. Permite elegir cuando se quiere seleccionar un area
            para hardfacing y cuando se quiere mover el mouse sin realizar la selección.
            Toggle hecho con click derecho del mouse.

        paint_cells
            'Pinta' área seleccionada mediante el movimiento del mouse.
            Área de búsqueda corresponde a la intersección de la malla con una esfera, radio depende de dimensiones de malla.
            El área 'pintada' se marca mediante esferas colocadas en los vértices que caen dentro
            del radio de búsqueda.

        insertar_callbacks
            inserta los callbacks asociados a los eventos dentro de sus tuplas respectivas.
        
        orientar_pieza
            orienta la pieza de acuerdo al tipo de geometría base indicada (placa, cilindro, cono), y
            los puntos elegidos en la superficie, indicados por marcadores.
            Para caso de placas se usan 3 marcadores, para el caso de cilindros y conos se necesitan 4.
            Actualiza y muestra malla en su orientación base necesaria para procesamiento de datos.
            Solo utilizada si uso='orientar'.

        extraer_pieza_orientada
            entrega la malla ingresada, pero orientada según los marcadores dados.
        
        extraer_descriptor
            entrega descriptor_cilindro_cono con los valores obtenidos de orientación

        reiniciar_orientacion_pieza
            reinicia posición de pieza a la última orientación guardada.
        
        eliminar_marcadores
            elimina los marcadores de orientación puestos.

        reiniciar_panel
            reinicia elementos en Plotter de panel, y reinicia variables a valores por defecto.
            las variables reiniciadas dependen del uso que se le de al panel.
            al reiniciar, en visualización solo queda la pieza ingresada y los axes.
    """

    def __init__(self, parent: wx.Frame=None, id: wx.StandardID=wx.ID_ANY) -> None:
        """
        Constructor para clase VedoPanel.
        Inicializa variables usada más adelante con sus valores por defecto.

        Parameters
        ----------
        parent : wx.Frame, optional
            wx.Frame donde se inserta el panel, by default None
        id : wx.StandardID, optional
            ID para identificar panel, by default wx.ID_ANY
        """

        wx.Panel.__init__(self, parent, id)
        self.widget = wxVTKRenderWindowInteractor(self, -1)
        self.widget.Enable(1)
        self.widget.AddObserver("ExitEvent", lambda o,e,f=self: f.Close())
        self.uso = "ver"
        self.plotter = None
        self.mesh = None
        self.axes = None
        self.cortes = False
        self.trayectorias = False
        self.procesador = None

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.widget, 1, wx.EXPAND)
        self.SetSizer(self.sizer)
        self.Layout()
    
    def crear_para_orientacion(self) -> None:
        """
            Inicializa las variables utilizadas en el caso de usar panel para orientar.
            Variables inicializadas son:
            
            colors: List, by default [(0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)]
                lista de colores RGB para marcadores de orientación
            
            marcadores_orientacion: List, by default []
                lista para guardar referencia a objetos de marcadores
            
            descriptor_cilindro_cono: List, by default [1, 0]
                lista que contiene radio y ángulo de apertura
            
            tipo_pieza: int, by default 0
                indicador del tipo de pieza: 0=placa, 1=cilindro, 2=cono
            
            tipo_orientacion: int, by default 0
                indicador del tipo de orientacion: 0=automática, 1=manual
            
            rotaciones: List, by default []
                lista para guardar las rotaciones aplicadas a orientación.
                usado cuando se quiere reiniciar orientación
        """
        # Variables usadas cuando se quiere orientar
        self.colors = [(0, 0, 0),
                       (1, 0, 0),
                       (0, 1, 0),
                       (0, 0, 1)]
        self.marcadores_orientacion = []
        # Descriptor [radio base, ángulo de apertura]
        # Radio 1 por defecto permite cortes de cilindros sin necesariamente orientar
        # Conos requiere tener ángulo de apertura
        # No es recomendable cortar sin orientar, no hay garantías que funcione bien
        self.descriptor_cilindro_cono = [1, 0]
        self.tipo_pieza = 0
        self.tipo_orientacion = 0
        self.rotaciones = []
    
    def crear_para_hardfacing(self) -> None:
        """
            Inicializa las variables utilizadas en el caso de usar panel para realizar hardfacing.
            Variables inicializadas son:
            
            pintar: bool, by default False
                indicador de pintado, si falso no se pinta superficie ni extraen puntos
            
            radio_busqueda: float, by default 0
                radio de esfera con la que se pintará y extraerán puntos
            
            puntos_pintados: np.ndarray, by default None
                ndarray que se usa para guardar puntos extraídos de la selección de áreas
            
            esfera_seleccion: vedo.shapes.Sphere, by default None
                esfera usada para intersectar con pieza cargada
        """

        self.pintar = False
        self.radio_busqueda = 0
        self.puntos_pintados = None
        self.esfera_seleccion = None
    
    def iniciar_plotter(self, uso: str="ver", procesador=None) -> None:
        """
            Inicializa instancia de Plotter del panel, las variables a usar, e inserta callbacks para interacción
            según uso que se le quiere dar.

            Parameters
            ----------
            uso : str, optional
                indicador de uso del panel, opciones son 'ver', 'orientar', y 'hardfacing', by default 'ver'
            procesador : Procesador, optional
                instancia de Procesador usada para los calculos de orientación o hardfacing, by default None
        """

        self.uso = uso
        self.procesador = procesador
        self.plotter = vedo.Plotter(N=1, bg='blue2', bg2='blue8', wxWidget=self.widget)
        self.plotter.addGlobalAxes(axtype=4, c=None)

        if uso == "orientar":
            self.crear_para_orientacion()
            lista = [("RightButton", self.on_right_click_orient), 
                    ("LeftButton", self.on_left_click_orient)]
            self.insertar_callbacks(lista)
        if uso == "hardfacing":
            self.crear_para_hardfacing()
            lista = [('RightButtonPress', self.on_right_click_paint),
                    ("MouseMove", self.paint_cells)]
            self.insertar_callbacks(lista)

    def insertar_pieza(self, file: Union[trimesh.Trimesh, str]=None, centrada: bool=False) -> None:
        """
            Inserta malla Trimesh o carga malla ingresada en file al Plotter del panel.
            En caso de que ya haya una malla cargada la reemplaza.

            Parameters
            ----------
            file : trimesh.Trimesh o str, optional
                malla que se quiere ingresar al panel, by default None
            centrada : bool, optional
                indicador de centrado de pieza al ingresarla, by default False
        """
        if self.mesh is not None:
            self.reiniciar_panel()
            self.plotter.remove([self.mesh], at=0)
        
        if isinstance(file, trimesh.base.Trimesh):
            self.mesh = vedo.utils.trimesh2vedo(file)
        if isinstance(file, str):
            self.mesh = vedo.Mesh(file)

        if centrada:
            self.mesh.shift(dx=-self.mesh.centerOfMass()[0], dy=-self.mesh.centerOfMass()[1], dz=-self.mesh.centerOfMass()[2])
            self.mesh.origin(x=self.mesh.centerOfMass()[0], y=self.mesh.centerOfMass()[1], z=self.mesh.centerOfMass()[2])

        self.mesh.computeNormals()
        self.mesh.color("tan")
        self.plotter.add([self.mesh], at=0).resetCamera()
        self.insertar_axes(self.mesh)
        
    def insertar_axes(self, mesh: vedo.Mesh=None) -> None:
        """
            Inicializa e inserta ejes de coordenadas en el panel, usando las dimensiones 
            de la malla cargada para establecer los límites.
            Dimensiones se asumen en milímetros, pero unidades de medida dependen de unidades de malla.
            Usado también para actualizar ejes si la malla o su posición cambian.

            Parameters
            ----------
            mesh : vedo.Mesh, optional
                malla de pieza cargada en el panel, by default None
        """

        if self.axes is not None:
            self.plotter.remove([self.axes], at=0)
        
        # Range es arbitrario pero ayuda para tener una idea del espacio
        range = 300
        if mesh is not None:
            xrange = (mesh.bounds()[0]-range, mesh.bounds()[1]+range)
            yrange = (mesh.bounds()[2]-range, mesh.bounds()[3]+range)
            zrange = (mesh.bounds()[4]-range, mesh.bounds()[5]+range)
        else:
            xrange=(0, 1000)
            yrange=(0, 1000)
            zrange=(0, 1000)
        
        # Asegura que plano XY esté en Z=0
        xyshift = 1 - (zrange[1]/(zrange[1]-zrange[0]))
        self.axes = vedo.addons.Axes(obj=None, xtitle="X", ytitle="Y", ztitle="Z", axesLineWidth=1.5, gridLineWidth=1.5, xyAlpha=0.1,
                                     xrange=xrange, yrange=yrange, zrange=zrange,
                                     xyGrid=True, zxGrid=False, yzGrid=False,
                                     xHighlightZero=False, yHighlightZero=False, zHighlightZero=False,
                                     xHighlightZeroColor='r', yHighlightZeroColor='g', zHighlightZeroColor='b',
                                     xyShift=xyshift, yzShift=0, zxShift=0,
                                     xShiftAlongY=0.5, xShiftAlongZ=0,
                                     yShiftAlongX=0.5, yShiftAlongZ=0,
                                     zShiftAlongX=0.5, zShiftAlongY=0.5,
                                     xMinorTicks=4, yMinorTicks=4, zMinorTicks=4,
                                     xLineColor="red", yLineColor="lime", zLineColor="blue",
                                     xTickLength=0.035, yTickLength=0.035, zTickLength=0.035)
        self.plotter.add([self.axes], at=0)

    def insertar_cortes(self, cortes: List[List[np.ndarray]]=None) -> None:
        """
            Inserta los cortes ingresados al panel para su visualización.
            Cortes son representados usando vedo.shape.Line.
            Cada elemento de la lista es una capa, y cada capa contiene los contornos en forma de arrays.
            Cortes son actualizados en caso de que ya se hayan insertado antes.

            Parameters
            ----------
            cortes : List[List[np.ndarray]], optional
                cortes a cargar, by default None
        """
        if cortes is None:
            return
        
        if self.cortes:
            lineas = [actor for actor in self.plotter.actors if isinstance(actor, vedo.shapes.Line) or isinstance(actor, vedo.shapes.Spheres)]
            self.plotter.remove(lineas, at=0, render=True)
        
        self.cortes = True
        for capa in cortes:
            for contorno in capa:
                linea = vedo.shapes.Line(contorno, closed=True, c='black', alpha=1, lw=2)
                self.plotter.add([linea], at=0)

                # puntos = vedo.shapes.Spheres(contorno, r=0.2)
                # self.plotter.add([puntos], at=0)

    def insertar_trayectorias(self, trayectorias: List[List[List[np.ndarray]]]=None) -> None:
        """
            Inserta las trayectorias ingresadas al panel para su visualización.
            Trayectorias son representados usando vedo.shape.Line.
            Cada elemento de la lista es una capa, y cada capa contiene curvas de las trayectorias, 
            a su vez las curvas contienen arrays para representar las líneas que componen cada movimiento.
            Trayectorias son actualizadas en caso de que ya se hayan insertado antes.

            Parameters
            ----------
            trayectorias : List[List[List[np.ndarray]]], optional
                trayectorias a cargar, by default None
        """

        if trayectorias is None:
            return
        
        # Necesita tomar primero porque vienen con forma (1, N, 3)
        #TODO: HACER EL INGRESO DE TRAYECTORIAS MÁS GENERAL
        if self.trayectorias:
            lineas = [actor for actor in self.plotter.actors if isinstance(actor, vedo.shapes.Line) or isinstance(actor, vedo.shapes.Spheres)]
            self.plotter.remove(lineas, at=0, render=True)
        
        self.trayectorias = True
        for capa in trayectorias:
            for contorno in capa:
                for movimiento in contorno:
                    linea = vedo.shapes.Line(movimiento, closed=True, c='black', alpha=1, lw=2)
                    self.plotter.add([linea], at=0)
                    
                    # puntos = vedo.shapes.Spheres(contorno, r=0.2)
                    # self.plotter.add([puntos], at=0)

    def on_left_click_orient(self, event: vedo.utils.dotdict) -> None:
        """
            Inserta un marcador en el panel y en la lista interna de marcadores indicando el punto 
            donde se hizo click en la superficie de la malla.
            Se pueden tener un máximo de 4 marcadores al mismo tiempo, colores varían de acuerdo al número del 
            marcador: primer marcador es negro, segundo es rojo, tercero es verde, y cuarto es azul.
            Solo usada en caso de que uso='orientar'.

            Parameters
            ----------
            event : vedo.utils.dotdict
                evento de Vedo de 'LeftButtonPress' asociado a la función
        """

        if event.picked3d is not None:
            if len(self.marcadores_orientacion) < len(self.colors):
                ax = vedo.shapes.Cross3D(pos=event.picked3d, s=5.0, thickness=0.3, alpha=1)
                ax.origin(x=0, y=0, z=0)
                self.marcadores_orientacion.append(ax)
                ax.color(self.colors[len(self.marcadores_orientacion)-1])
                self.plotter.add([ax], at=0)  
                self.orientar_pieza(self.tipo_pieza, self.tipo_orientacion)

    def on_right_click_orient(self, event: vedo.utils.dotdict) -> None:
        """
            Quita el último marcador ingresado tanto del panel como de la lista interna de marcadores.
            Funciona realizando un click derecho del mouse en cualquier lugar de la visualización.
            Solo usada en caso de que uso='orientar'.

            Parameters
            ----------
            event : vedo.utils.dotdict
                evento de Vedo de 'RightButtonPress' asociado a la función
        """

        if len(self.marcadores_orientacion) > 0:
            last_marker = self.marcadores_orientacion.pop()
            self.plotter.remove(last_marker, at=0)

    def on_right_click_paint(self, event: vedo.utils.dotdict) -> None:
        """
            Toggle para variable pintar. Permite elegir cuando se quiere seleccionar un area
            para hardfacing y cuando se quiere mover el mouse sin realizar la selección.
            Toggle hecho con click derecho del mouse.
            Solo usada en caso que uso='hardfacing'.

            Parameters
            ----------
            event : vedo.utils.dotdict
                evento de Vedo de 'RightButtonPress' asociado a la función
        """

        self.pintar = not self.pintar

    def paint_cells(self, event: vedo.utils.dotdict) -> None:
        """
            'Pinta' área seleccionada mediante el movimiento del mouse.
            Área de búsqueda corresponde a la intersección de la malla con una esfera, radio depende de dimensiones de malla.
            El área 'pintada' se marca mediante esferas colocadas en los vértices que caen dentro
            del radio de búsqueda.
            Solo usada en caso que uso='hardfacing'.

            Parameters
            ----------
            event : vedo.utils.dotdict
                evento de Vedo de 'MouseMove' asociado a la función
        """

        # Radio de búsqueda es del 5% de la dimensión mayor de la pieza
        rangex = self.mesh.bounds()[1] - self.mesh.bounds()[0]
        rangey = self.mesh.bounds()[3] - self.mesh.bounds()[2]
        rangez = self.mesh.bounds()[5] - self.mesh.bounds()[4]
        self.radio_busqueda = 0.05*np.amax([rangex, rangey, rangez])
        if event.picked3d is not None:
            # Esfera se agrega y quita contínuamente para actualizar posición
            self.plotter.remove(self.esfera_seleccion)
            self.esfera_seleccion = vedo.shapes.Sphere(pos=event.picked3d, r=self.radio_busqueda, c='black', alpha=0.4, res=30)
            self.plotter.add(self.esfera_seleccion)
            if self.pintar:
                contour = self.mesh.closestPoint(event.picked3d, radius=self.radio_busqueda, returnPointId=False, returnCellId=False)
                self.plotter.add(vedo.Mesh(vedo.Points(contour)).c('red5'))
                if self.puntos_pintados is None:
                    self.puntos_pintados = contour
                else:
                    self.puntos_pintados = np.append(self.puntos_pintados, contour, axis=0)
                    self.puntos_pintados = np.unique(self.puntos_pintados, axis=0)
            self.widget.Render()

    def insertar_callbacks(self, lista_callbacks: List[Tuple[str, Callable]]=()) -> None:
        """
            Inserta los callbacks asociados a los eventos dentro de las tuplas respectivas.

            Parameters
            ----------
            lista_callbacks : List[Tuple[str, func]], optional
                lista de tuplas de la forma (Event, Func) para agregar al panel para agregar interacción, by default ()
        """
        for callback in lista_callbacks:
            self.plotter.addCallback(callback[0], callback[1])

    def orientar_pieza(self, tipo_pieza: int, tipo_orientacion: int) -> None:
        """
            Orienta la pieza de acuerdo al tipo de geometría base indicada (placa, cilindro, cono), y
            los puntos elegidos en la superficie, indicados por marcadores.
            Para caso de placas se usan 3 marcadores, para el caso de cilindros y conos se necesitan 4.
            En caso de escoger una orientación automática, se requiere un único marcador para definir cual es la cara
            a orientar con el eje Z.
            Actualiza y muestra malla en su orientación base necesaria para procesamiento de datos.
            Cálculos de orientación son hechos a través de instancia de Procesador.
            Solo utilizada si uso='orientar'.

            Parameters
            ----------
            tipo_pieza : int
                indicador de tipo de pieza, 0=placas, 1=cilindros, 2=conos
        """
        
        # Se calcula orientación para la malla, ingresando el tipo de pieza y la lista de marcadores correspondiente
        # No es necesaria condición especial de placa, no requiere cálculos especiales
        self.rotaciones, self.mesh, self.marcadores_orientacion = self.procesador.orientar_malla(self.mesh, 
                                                                                                self.marcadores_orientacion, 
                                                                                                self.rotaciones, 
                                                                                                self.tipo_pieza,
                                                                                                self.tipo_orientacion)
        # TODO: MOVER CÁLCULO DE DESCRIPTORES A OBJETO DATOS
        # Para casos de cilindros y conos hay que calcular el descriptor
        # Caso de cilindros solo se estima el radio
        if tipo_pieza == 1 and len(self.marcadores_orientacion) == 4:
            punto_origen = np.asarray(self.marcadores_orientacion[0].getTransform().GetPosition())
            punto_y_positivo = np.asarray(self.marcadores_orientacion[2].getTransform().GetPosition())
            punto_final_circulo = np.asarray(self.marcadores_orientacion[3].getTransform().GetPosition())
            
            _, radio = utilidades.calcular_cilindro([punto_origen, punto_y_positivo, punto_final_circulo])
            self.descriptor_cilindro_cono[0] = radio

        # Caso de conos estima radio de base (disponible en la malla, no teórica) y ángulo de apertura
        if tipo_pieza == 2 and len(self.marcadores_orientacion) == 4:
            punto_origen = np.asarray(self.marcadores_orientacion[0].getTransform().GetPosition())
            punto_y_positivo = np.asarray(self.marcadores_orientacion[2].getTransform().GetPosition())
            punto_final_circulo = np.asarray(self.marcadores_orientacion[3].getTransform().GetPosition())
            
            _, radio = utilidades.calcular_cilindro([punto_origen, punto_y_positivo, punto_final_circulo])
            self.descriptor_cilindro_cono[0] = radio
            
            punto_origen = np.asarray(self.marcadores_orientacion[0].getTransform().GetPosition())
            self.descriptor_cilindro_cono[1] = self.procesador.calcular_angulo_apertura_cono(vedo.utils.vedo2trimesh(self.mesh), punto_origen)            
        # Actualizar axes con nueva posición de malla
        self.insertar_axes(self.mesh)

    def extraer_pieza_orientada(self) -> trimesh.Trimesh:
        """
            Entrega la malla ingresada, pero orientada según los marcadores dados.

            Returns
            -------
            trimesh.Trimesh
                pieza orientada según marcadores
        """
        if self.mesh is not None:
            return vedo.utils.vedo2trimesh(self.mesh)
        else:
            return None

    def extraer_descriptor(self) -> Tuple[float, float]:
        """
            Entrega descriptor_cilindro_cono con los valores obtenidos de orientación
        """
        return self.descriptor_cilindro_cono
    
    def reiniciar_orientacion_pieza(self) -> None:
        """
            Reinicia posición de pieza a la última orientación guardada.
        """
        # Único reinicio 'completo' se da durante la primera orientación
        # reinicio se da con respecto a la última orientación guardada
        # Hecho así porque STLs pueden ser pesados, y para tener la orientación inicial
        # se tendría que tener una copia de la malla al momento de cargarla
        # Para reiniciar completamente hay que ingresar la malla de nuevo
        
        # Roatación hecha con respecto al centro de la malla
        rotacion_final = None
        self.mesh.shift(dx=-self.mesh.centerOfMass()[0], dy=-self.mesh.centerOfMass()[1], dz=-self.mesh.centerOfMass()[2])
        # Rotaciones inversas son concatenadas
        # Creo que debería empezar al revés (de fin a principio, pero funciona)
        for rotacion in self.rotaciones:
            if rotacion_final is None:
                rotacion_final = rotacion.inv()
            else:
                rotacion_final *= rotacion.inv()
        # Rotación final es 'Single Rotation', se usa sola, no es subscribible
        if rotacion_final is not None:
            self.mesh.applyTransform(rotacion_final.as_matrix(), reset=True)
        self.rotaciones = []

    def eliminar_marcadores(self) -> None:
        """
            Elimina los marcadores de orientación puestos.
        """
        self.plotter.remove(self.marcadores_orientacion)
        self.marcadores_orientacion = []

    def reiniciar_panel(self) -> None:
        """
            Reinicia elementos en Plotter de panel, y reinicia variables a valores por defecto.
            Las variables reiniciadas dependen del uso que se le de al panel.
            Al reiniciar, en visualización solo queda la pieza ingresada y los axes.
        """
        # No tiene sentido reiniciar el panel si no interactúas
        # Si solo lo usas para visualizar solo importa el estado actual
        if self.uso == "orientar":
            self.descriptor_cilindro_cono = [1, 0]
            self.eliminar_marcadores()
            self.reiniciar_orientacion_pieza()
            # Así axes se dibujan en nueva posición
            self.insertar_axes(self.mesh)
        if self.uso == "hardfacing":
            # Se elimina todo menos lo necesario
            # Hecho así porque no guardamos referencias a esferas de zona "pintada"
            self.plotter.remove([actor for actor in self.plotter.actors if actor not in [self.mesh, self.axes]], render=False)
            self.esfera_seleccion = None
            # Resetear variables relevantes a hardfacing
            self.crear_para_hardfacing()
        self.plotter.resetCamera()
        self.widget.Render()
