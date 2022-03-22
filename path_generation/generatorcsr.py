"""
Version 5

FUNCION:
        Generar archivo .csr, con base en:
        Operation Instruction 
        Integrated PC Tool Software
        DTPS
        
Notas:
    -Esta opción genera el código por capas.
    -La version de CSR es la rescatada de versiones anteriores, la traduccion en DTPS no se ve afectada.
    -En v3 se combinan las funciones de -Pose-, -Command-, pero se generan dos listas diferentes p/escritura.
    -En v4 se añade generación de suprogramas en caso de acumular mas de 20000 comandos
    -En v5 se mejora uso de eje externo para cilindros y lineas x,y,z
    -Eje externo: caso simple de lineas en cilindros con fallas planas.
    -Para uso de eje externo coincidir el numero de mecanismo y eje asignado en el DTPS
Pendiente:
*Definicion de variable para reconocer coordenadas de usuario
*Definir comando para pausar reparación hasta obtener aprobación de usuario
*Uso de eje externo para trayectorias
"""

# Librerias externas
import datetime
import sys
import pandas as pd
import numpy as np
import re
import json
import time
import math
from scipy.spatial.transform import Rotation
# Librerias locales
from path_generation.selection import seleccion_puntos


def description():
    # ---------[DESCRIPTION]------------
    with open(r'./descripcion.txt') as json_file:
        data = json.load(json_file)
        
    robot_model = data['Modelo']
    comment = data['Comentario']  # Comentario max 30 chars
    mechanism = data['Mecanismo']  # No. de mecanismo (1-5)
    external_axis = data['Eje externo']  # Yes or Not
    number_axis = data['Cantidad ejes']
    tool_number = data['Numero herramienta']  # No. de Herramienta
    file_creator = data['Usuario']  # Nombre del usuario, Max. 16 chars
    file_name = data['Nombre archivo']  # Nombre del archivo, Max. 32 chars
    user_cords = data['Coordenadas de usuario']  # Coordenadas del usuario
    edit = data['Permitir edicion']  # 0:default, 1: solo posición es editable, 2:Prohibido

    if len(comment) > 30:
        print("Error! Solo se permiten 30 caracteres")
        sys.exit()

    if external_axis == "Y":
        number_axis = int(input("Cant. ejes: "))  # No. de ejes, se crea 4 digitos hexadecimales en DTPS
        number_axis = "000{}".format(number_axis) #En la instalación se configuro el 4 para el eje rotatorio.
    elif external_axis == "N":
        number_axis = "0001"

    today = datetime.datetime.now()  # Fecha del dia en curso
    create_date = '{}, {}, {}, {}, {}, {}'.format(today.strftime('%Y'), today.strftime('%m'), today.strftime('%d'), today.strftime('%H'), today.strftime('%M'),
                                                  today.strftime('%S'))  # (Year, Month, Day, Hour, Minute, Sec")
    update = '{}, {}, {}, {}, {}, {}'.format(today.strftime('%Y'), today.strftime('%m'), today.strftime('%d'), today.strftime('%H'), today.strftime('%M'), today.strftime('%S'))

    if edit == "Y":
        edit = "0"
    elif edit == "N":
        edit = "2"  # Default

    # Propiedades a ser mostradas
    part_description = '''[Description] \nRobot, {} \nComment, {}\nSubComment1,\nSubComment2, \nMechanism, {}({}) \nTool, {}:TOOL0{} \nCreator, {} \nUser coordinates, {} \nCreate, {}\nUpdate, {} \nOriginal, \nEdit, {}\n'''.format(
        robot_model, comment, mechanism, number_axis, tool_number, tool_number, file_creator, user_cords, create_date, update, edit)

    return part_description, file_name, number_axis, tool_number

def variable():
    # -----------[VARIABLE]-------------
    p_variable = []  # List
    var_types = ['LB', 'LI', 'LL', 'LR']  # Variable type:character string
    var_comn = " "                        # Commment, max 32 chars
    var_value = 0                         # Initial value
    l = 0                                 # Contador para cambiar la variable local
    n = 0                                 # Contador para valor de variable
    info_row = '\n[Variable]'             # Linea de titulo
    p_variable.append(info_row)
    for var in range(20):
        var_name = '{}00{}'.format(var_types[l], (n + 1))  # max 8 chrs ej.LB0001
        variable = '{}, {}, {}, {}'.format(var_types[l], var_name, var_comn, var_value)
        p_variable.append(variable)
        n += 1
        if n == 5:
            l += 1
            n = 0
    return p_variable

def pose_comands(data, number_axis, type_piece, tool_number, speed, amperage, voltage,p_centro):
    #-----------[POSE]-----------------
    #NORMAL DATA
    format_names = ["AJ", "AV", "AU", "AP"]
    data_contents = ["Joint angle", "Position + Vector", "Position + UVW", "Pulse"]
    datas = []
    for i in range(31):
        data_ = 'Data '+ str(i)
        datas.append(data_)
    column_values = pd.Series(datas)
    poses = pd.DataFrame(columns=column_values)
    poses.insert(loc = 0,
              column = 'Content', 
              value = data_contents)
    poses.insert(loc = 0,
              column = 'Format', 
              value = format_names) 
    poses.iloc[[0,3],[2,3,4,5,6,7]] = ['RT','UA','FA','RW','BW' ,'TW']  #Joint angle [degree]
    poses.iloc[[1,2],[2,3,4]] = ['X','Y','Z']                           #Position [mm]
    poses.iloc[2,[5,6,7]] =['U','V','W']                                #Tool orientation [degree]
    poses.iloc[1,[5,6,7,8,9,10]] = ['XX','XY','XZ','ZX','ZY','ZZ']      #AV elements
    for i in range(21):
        axes_ = "G"+ str(i+1)
        poses.iloc[[0,2,3],8+i] = axes_
        poses.iloc[1,11+i] = axes_
    nvalues = {'AU': 6, 'AV': 10, 'AJ':6, 'AP':6}                       #Valores a mostrar de c/formato 
    movec_memory = 1 #Variable para contar cuantos comandos movec seguidos se han hecho
    
    #-----------[COMMAND]--------------
    #MOVE COMMANDS
    move_commands_normal = ['MOVEC','MOVECW' ,'MOVEL','MOVELW','WEAVEP', 'MOVEP'] #Comandos de movimiento 
    move_commands_external = ['MOVEC+','MOVECW+','MOVEL+','MOVELW+','WEAVEP+'] #Comandos de movimiento de eje externo 
    #IN/OUT COMMANDS 
    # io_commands = ['IN', 'OUT', 'PULSE']
    #FLOW COMMANDS
    flow_commands = ['CALL', 'DELAY', 'HOLD', 'IF', 'STOP', 'PAUSE']
    #WELDING CONTROL COMMANDS 
    welding_commands = ['AMP','ARC-OFF', 'ARC-ON', 'ARC-SET','CRATER']

    
    #PASO 1.-POSE- SELECCIONAR SISTEMA DE COORDENADAS
    y = int((re.findall(".",number_axis))[3])                           #Cantidad de columnas de ejes externos
    # print("Eje externo", y)
    if y>1:
        p_format= 'AU'                                      #Formato seleccionado
        print("Formato a usar:", p_format)
        pos_format = poses.loc[poses['Format'] == p_format] #Busca en el dataframe
        x = nvalues.get(p_format)                           #Cantidad de columnas
        plus = 2 + x                                        #Cantidad de etiquetas de 'Pose' a usar (2 es el inicio en df)
        head_= pos_format.iloc[:,2:plus].values             #Valores de las etiquetas
        plus2= plus +y-1-4                                  #Etiqueta del eje externo
        head_2 = (pos_format.iloc[:,plus2]).values[0]       #Valores de las etiquetas
        head_ = np.append(head_,head_2)
        head_ = np.array([head_])                           #Encabezado final con solo una etiqueta del eje externo 
        move_commands = move_commands_external              #comandos de movimiento con + adicional
    else:       
        #En otro caso se ocupa "AU" 
        p_format= 'AU'                                      #Formato seleccionado    
        print("Formato a usar:", p_format)
        pos_format = poses.loc[poses['Format'] == p_format] #Busca en el dataframe
        x = nvalues.get(p_format)                           #Cantidad de columnas
        plus = 2 + x + y                                    #Cantidad de etiquetas de 'Pose' a usar (2 es el inicio en df)
        head_= (pos_format.iloc[:,2:plus]).values           #Valores de las etiquetas
        move_commands = move_commands_normal 
    
    #PASO 2.-POSE-INFORMACIÓN PARA COORDENADAS    
    if p_format == 'AU':
        #Coordenadas cartesianas   
        # z_safe = 100                # [mm] Distancia elevada para evitar choques
        z_msafe = 30                # [mm] Distancia se seguridad para avitar choque entre lineas
        tool_x = 0                  # [degree] Orientacion de la herramienta x
        tool_z = 0                  # [degree] Orientacion de la herramienta z
        jang_ = 0                   # [degree] Ángulo articular de ejes externos
        
    
    #PASO 3.-COMMANDS-INFORMACIÓN PARA COMANDOS 
    speed_normal = speed                #Velocidad de movimiento de torcha
    speed_curve =round(speed*0.9, 2)    #Velocidad de movimiento de torcha en curvas, Sandiman recomienda de 10 a 15% menos
    speed_unit = 'm/min'                #Unidades de velocidad de torcha
    cl_no =0                            #Variable p/ comandos de movimiento
    air_cuted = 'N'                     #Para casos sin soldadura ("al aire")
    w_cuted = 'W'                       #Para activar soldadura    
    file_a = 'ArcStart1.rpg'            #Nombre de tabla de soldadura de inicio en DTPS
    file_b = 'ArcEnd1.rpg'              #Nombre de tabla de soldadura del final en DTPS
    tablenumber = 0                     #Número de la tabla de soldadura
    amperage2 = amperage                #[A] Amperaje del crater
    voltage2 = voltage                  #[V] Voltaje del crater
    time2 = 0                           #[seg] Tiempo del crater
    delaytime = 3                       #[seg] Tiempo de retardo del comando de flujo 
    command_safe = move_commands[2]     #Comando para subir en z y evitar chocar entre curvas
    msge = 'abc'                        #Mensaje opcional para comando de PAUSA 
    jang_safe = 0 
    tool_safe = 0                       #Volver a base 
    #PASO 4.- CREACIÓN DE LISTAS PARA ARCHIVO
    l_position =[]                      #Lista de posicionamientos 
    info_row = '\n[Pose]'               #Linea de titulo
    l_position.append(info_row)
    headers = '/Name, Type, {}, {}, {}, {}, {}, {}, {}'.format(head_[0,0],head_[0,1],head_[0,2],head_[0,3],head_[0,4],head_[0,5],head_[0,6])
    l_position.append(headers) 
    p_command = []                      #Lista de comandos
    info_row = '\n[Command]'            #Linea de titulo
    p_command.append(info_row)
    info_row = 'TOOL,{}:TOOL0{}'.format(tool_number,tool_number) 
    p_command.append(info_row)          #Leyenda de herramienta
    
    #PASO 5.- CREACION DE LINEAS DE POSICIONAMIENTO Y COMANDOS
    p_n = 1                             #contador de puntos
    subcsr_ =[]                         #Lista de listas de subprogramas
    el = 0                              #Variable para identificar el nro de prg creados
    l = len(data)
    printProgressBar(0, l, prefix = 'Progress:', suffix = 'Complete', length = 50)
    for layer in range(len(data)):  
        #Lista de curvas (n MLS)
        for curve in range(len(data[layer])):
            #Conjunto de lineas (N cantidad de LS's)            
            for mls in range(len(data[layer][curve])):
                #Lista de puntos de c/LS
                puntosls = data[layer][curve][mls]
                #Evaluar puntos concavos y convexo en cada linea
                puntosnew, amount_concaves,listmovel, p_curve = seleccion_puntos(puntosls, y, type_piece) #Encontrar puntos
                array_cc = np.array(puntosnew) #Lista de puntos filtrados, np array
                nps = len(array_cc)-2 #index p/identificar tres pts antes de finalizar linea, 3 error para figuras pequeñas?
                #DECISIÓN DE EJE EXTERNO 
                if y>1:
                    # print("Se usa el eje externo")
                    #SE REDEFINE COORDENADAS XYZ A CILINDRICA  S, seE CREA LISTA DE VALORES DE ÁNGULO EXTERNO
                    array_cc,jang_n, tool_y = cartesian_to_cilyndrical(array_cc, p_centro)
                    command = move_commands[0] #Movimientos circulares ---> prueba  
                else:
                    jang_n=[jang_]*len(array_cc) #el mismo valor para todos los puntos
                    tool_y =[0]*len(array_cc) #  [degree] Orientacion de la herramienta y
                    #Filtro de movimientos para movimientos en placa
                    if amount_concaves <6:
                        #Si la cantidad de puntos concavos es menor a 4 se utiliza MOVEL 
                        command = move_commands[2] #Movimientos lineales
                    else:
                        command = move_commands[0] #Movimientos circulares
                for p in range(len(array_cc)):
                    p_number= "P"+str(p_n) #p+1 porque la secuencia en csr inicia en 1
                    #Cambiar velocidad si el punto esta en lista de p_curves
                    p1 = array_cc[p].tolist() #tipo de variable lista para buscar 
                    if p1 in p_curve:
                        speed = speed_curve 
                    else:
                        speed = speed_normal
                    #COMANDOS
                    if p==0:
                        #AÑADIR COMANDO DE Z DE SEGURIDAD PAR ANO BAJAR EN DIAGONAL 
                        pto_safexy = [array_cc[p,0], array_cc[p,1],(array_cc[p,2]+z_msafe) ] #punto de seguridad
                        #AÑADIR SEGUNDO POSE DE SEGURIDAD PARA EVITAR BAJAR EN DIAGONAL 
                        pose_row = '{}, {}, {}, {}, {}, {}, {}, {}, {}'.format(p_number, p_format,pto_safexy[0],pto_safexy[1],pto_safexy[2],tool_x, tool_safe, tool_z, jang_safe) #Caso de AU
                        l_position.append(pose_row)
                        command_row = '{}, {}, {}, {}, {}, {}'.format(command_safe, p_number, speed, speed_unit, cl_no, air_cuted)
                        p_command.append(command_row)
                        p_n += 1  
                        p_number= "P"+str(p_n)
                        #Añadir COMANDO de inicio de soldadura
                        command_row = '{}, {}, {}, {}, {}, {}'.format(command_safe, p_number, speed, speed_unit, cl_no, air_cuted)
                        p_command.append(command_row)
                        #Repetir primer punto para evitar soldadura en uno
                        #Añadir COMANDO de inicio de soldadura- repetir primer punto para evitar soldadura en uno 
                        command_row = '{}, {}, {}, {}, {}, {}'.format(command, p_number, speed, speed_unit, cl_no, w_cuted)
                        # command_row = '{}, {}, {}, {}, {}, {}'.format(command_safe, p_number, speed, speed_unit, cl_no, w_cuted)
                        p_command.append(command_row)
                        #Al ser el primero de linea, activa la soldadura
                        welding_row = '{}, {}, {}, {}'.format(welding_commands[3], amperage, voltage, speed) #arc-set
                        p_command.append(welding_row)
                        welding_row = '{}, {}, {}'.format(welding_commands[2], file_a, tablenumber) #arc-on
                        p_command.append(welding_row)                    
                    if amount_concaves >= 6 and p >= nps:
                        # print("Entra aqui, en:",p)
                        if p == (len(array_cc)-1):
                            # print("Ultimo punto",p)
                            #Añadir COMANDO de movimiento sin soldadura si es ultimo punto
                            command_row = '{}, {}, {}, {}, {}, {}'.format(command, p_number, speed, speed_unit, cl_no, air_cuted)
                            p_command.append(command_row)
                        else:
                            #Si es MOVEC y tiene mayor a 4(o3) puntos, utilizar MOVEL en las uniones
                            # print("Ultimos 2 puntos de un MOVEC")
                            #Añadir COMANDO de movimiento
                            command_row = '{}, {}, {}, {}, {}, {}'.format(command_safe, p_number, speed, speed_unit, cl_no, w_cuted)
                            p_command.append(command_row)
                    elif p in listmovel:
                        # REpetir comando de MOVEL para caso de mvimientos curvos
                        # Añadir COMANDO de movimiento MOVEL
                        command_row = '{}, {}, {}, {}, {}, {}'.format(command_safe, p_number, speed, speed_unit, cl_no, w_cuted)
                        movec_memory = 1
                        p_command.append(command_row)  
                    else:
                        p_number= "P"+str(p_n)
                        if p ==0:
                            #Primer punto ya se considero
                            # print("No añade cero")
                            pass
                        elif p == (len(array_cc)-1):
                            # print("Ultimo punto",p)
                            #Añadir COMANDO de movimiento sin soldadura si es ultimo punto
                            command_row = '{}, {}, {}, {}, {}, {}'.format(command, p_number, speed, speed_unit, cl_no, air_cuted)
                            p_command.append(command_row)
                        else:                            
                            #Añadir COMANDO de movimiento
                            if command == move_commands[0]:
                                if movec_memory == 3: #Si es el tercer movec consecutivo, forzar split-off y empieza nuevo conteo de movec
                                    command_row = '{}, {}, {}, {}, {}, {}, 1, CIR_SPLIT-OFF'.format(command, p_number, speed, speed_unit, cl_no, w_cuted)
                                    movec_memory = 2
                                else: #Si es un movec pero no es el tercero seguido, escribir comando normal y registrar cuantos movec van
                                    command_row = '{}, {}, {}, {}, {}, {}'.format(command, p_number, speed, speed_unit, cl_no, w_cuted)
                                    movec_memory += 1
                            elif command == move_commands[2]:
                                command_row = '{}, {}, {}, {}, {}, {}'.format(command, p_number, speed, speed_unit, cl_no, w_cuted)
                                movec_memory = 1
                            else:
                                command_row = '{}, {}, {}, {}, {}, {}'.format(command, p_number, speed, speed_unit, cl_no, w_cuted)
                                movec_memory = 1
                                    
                                
                            p_command.append(command_row)       
                    #POSICIONAMIENTOS 
                    #Añadir POSE
                    xtest = array_cc[p,0] #Coordenada x
                    ytest = array_cc[p,1] #Coordenada y
                    z_s = array_cc[p,2] #Coordenada z
                    pose_row = '{}, {}, {}, {}, {}, {}, {}, {}, {}'.format(p_number, p_format,xtest,ytest,z_s,tool_x, tool_y[p], tool_z, jang_n[p] ) #Caso de AU
                    l_position.append(pose_row)
                    p_n += 1        
                #Añadir COMANDO crater al final de la linea y se desactiva soldadura, en el caso de estrategias continuas debe hacer crater al final de capa
                # print("CRATER DESPUES DE:",p_n)
                welding_row = '{}, {}, {}, {}'.format(welding_commands[4], amperage2, voltage2, time2)  #crater, solo en caso de raster
                p_command.append(welding_row)
                welding_row = '{}, {}, {}'.format(welding_commands[1], file_b, tablenumber) #arc-off
                p_command.append(welding_row)
                flow_row = '{}, {}'.format(flow_commands[1], delaytime) #delay                
                p_command.append(flow_row)
                #AÑADIR Z DE SEGURIDAD PARA NO CHOCAR ENTRE LINEAS DE UN MISMO Z 
                if y> 1:
                    pto_safe = [p_centro[0], ytest,(z_s+z_msafe) ]#[xtest-ancho, ytest,(z_s+z_msafe) ] #punto de seguridad, cilindros va a un punto medio?                     
                    jang_safe = jang_n[p] #0 #volver a la base en caso de cilindros
                    tool_safe = 0 #Volver a base
                else:
                    pto_safe = [xtest, ytest,(z_s+z_msafe) ] #punto de seguridad,       
                #Añadir POSE del z de seguridad al cambiar entre linea
                p_number= "P"+str(p_n) #p+1 porque la secuencia en csr inicia en 1
                # print("Acabo linea subir z pequeño", p_number)
                pose_row = '{}, {}, {}, {}, {}, {}, {}, {}, {}'.format(p_number, p_format,pto_safe[0],pto_safe[1],pto_safe[2],tool_x, tool_safe, tool_z, jang_safe ) #Caso de AU
                l_position.append(pose_row)
                #Añadir COMANDO del z de seguridad al cambiar entre curva--> MOVEL
                command_row = '{}, {}, {}, {}, {}, {}'.format(command_safe, p_number, speed, speed_unit, cl_no, air_cuted)
                p_command.append(command_row)
                p_n += 1
            #Añadir POSE del z de seguridad al cambiar entre curva 
            p_number= "P"+str(p_n) #p+1 porque la secuencia en csr inicia en 1
            pose_row = '{}, {}, {}, {}, {}, {}, {}, {}, {}'.format(p_number, p_format,pto_safe[0],pto_safe[1],pto_safe[2],tool_x, tool_safe, tool_z, jang_safe) #Caso de AU
            l_position.append(pose_row)
            #Añadir COMANDO del z de seguridad al cambiar entre curva--> MOVEL
            command_row = '{}, {}, {}, {}, {}, {}'.format(command_safe, p_number, speed, speed_unit, cl_no, air_cuted)
            p_command.append(command_row)
            p_n += 1
            # print("Acaba curva de daño n")
        # print("Acaba capa", layer)
        #Acaba capa, añadir COMANDO de PAUSE
        flow_row = '{}, {}'.format(flow_commands[5], msge) #Parada temporal, se reanuda con botón "Cycle start"               
        p_command.append(flow_row)
        #CREAR NUEVO ARCHIVO
        if p_n > 20000: #aproximadamente con 20'000 comandos el archivo pesa 1'500 KB
            # print("Crear nuevo archivo en pto:",p_n)
            file_x= [l_position, p_command]
            subcsr_.append(file_x) #Se añade elementos a lista
            #Se reinicia numeración p_n, lista de comandos y posicionamientos
            l_position =[]
            p_command = []
            #Se añaden las lineas de encabezados
            info_row = '\n[Pose]'               #Linea de titulo
            l_position.append(info_row)
            headers = '/Name, Type, {}, {}, {}, {}, {}, {}, {}'.format(head_[0,0],head_[0,1],head_[0,2],head_[0,3],head_[0,4],head_[0,5],head_[0,6])
            l_position.append(headers) 
            p_command = []                      #Lista de comandos
            info_row = '\n[Command]'            #Linea de titulo
            p_command.append(info_row)
            info_row = 'TOOL,{}:TOOL0{}'.format(tool_number,tool_number) 
            p_command.append(info_row)          #Leyenda de herramienta
            p_n = 0
            el += 1                
        elif curve == len(data[layer])-1 and layer == len(data)-1:
            # print("ultima curva de la última capa")
            if el >=1:
                # print("añadir a lista extra")
                file_x= [l_position, p_command]
                subcsr_.append(file_x) #Se añade elementos a lista       
        
        time.sleep(0.1)
        # Update Progress Bar
        printProgressBar(layer + 1, l, prefix = 'Progress:', suffix = 'Complete', length = 50)

    return l_position, p_command, subcsr_

def cartesian_to_cilyndrical(curva, p_centro):
    #curva: array de puntos de lineas
    #p_centro : punto de valores a origen original de cilindro
    #convertir coordenadas cartesianas en cilindricas
    #necesario modificar angulo de torcha
    tool_y = [] #Lista de valores para angulo de torcha en y - U 
    theta_axis =[] #Lista de valores de ángulo de rotación de eje externo    
    coords_modificados = np.zeros((curva.shape[0],3)) #Matriz del mismo tamaño de los datos   
    coords_modificados[:,1] = curva[:,1] #Coordenada Y se mantiene, corresponde al largo de la pieza    
    coords_modificados[:,0] = p_centro[0] #curva[0,0] #Coordenada x igual al primer valor #este punto ,me dice como gira theta_a
    for p in range (len(curva)):
        xs = curva[p][0] - p_centro[0] 
        zs = curva[p][2] -p_centro[1]
        #Radio
        radio_ = math.sqrt((xs**2+zs**2))
        theta = math.degrees(math.asin((xs/radio_)))
        theta_axis.append(theta)
        #Asignar su valor de Z    
        coords_modificados[p,2] = p_centro[1]+radio_ #antiguo
        angle_y = theta
        tool_y.append(angle_y)
    return coords_modificados, theta_axis, tool_y 


# Imprimir iteracion de progreso
def printProgressBar(iteration, total, prefix='', suffix='', decimals=1, length=100, fill='█', printEnd="\r"):
    """
    Call in a loop to create terminal progress bar
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end=printEnd)
    # Print New Line on Complete
    if iteration == total:
        print()

def timer(start, end):
    hours, rem = divmod(end - start, 3600)
    minutes, seconds = divmod(rem, 60)
    et = "{:0>2}:{:0>2}:{:05.2f}".format(int(hours), int(minutes), seconds)
    return et

def pose_extra():
    l_position =[]
    p_n = 1
    p_format = 'AU'
    info_row = '\n[Pose]'               #Linea de titulo
    l_position.append(info_row)
    headers = '/Name, Type, X, Y, Z, U, V, W, G1'
    l_position.append(headers)
    p_number= "P"+str(p_n) #p+1 porque la secuencia en csr inicia en 1
    pose_row = '{}, {}, 600, 600, 200, 180, 0, 180, 0'.format(p_number, p_format) #Caso de AU
    l_position.append(pose_row)
    return l_position

def command_extra(names,tool_number):
    l_command = []
    info_row = '\n[Command]'            #Linea de titulo
    l_command.append(info_row)
    info_row = 'TOOL,{}:TOOL0{}'.format(tool_number,tool_number) 
    l_command.append(info_row)          #Leyenda de herramienta    
    flow_commands = ['CALL', 'DELAY', 'HOLD', 'IF', 'STOP']
    for name in names:
        command_row = '{}, {}'.format(flow_commands[0], name)
        l_command.append(command_row)
    return l_command

def write_code(list_liness, S,A, voltage, r_min, tipo_pieza):
    print("tipo", tipo_pieza)
    # list_liness = list_liness[0] #se desactiva usando interfaz, util usando module_pathg
    #DESCRIPCIÓN
    parte1, file_name, number_axis, tool_number= description()
    print("\n Guardando...")
    #POSE AND COMMANDS
    parte2, parte4, part_extra = pose_comands(list_liness, 
                                              number_axis,tipo_pieza, tool_number, 
                                              S,A, voltage,r_min) 
    #VARIABLE
    parte3 = variable()
    #si no hay elementos  en part_extra, entonces se guarda normal
    if len(part_extra) > 1:    
        #Varios archivos
        names_files = [] #Lista de nombres de archivos
        for subprg in range(len(part_extra)):
            filename = file_name+str(subprg)
            #Guardar nombres de archivo con formato de programa: .rpg para controlador G3
            names_files.append(filename+'.rpg')
            #Perte 2 y 4 cambian 
            parte2 = part_extra[subprg][0]
            parte4 = part_extra[subprg][1]
            outfilepath = r'{}'.format(filename+'.csr') #Abrir archivo
            with open(outfilepath, 'w', encoding='UTF-8') as file:
                    for line in parte1:
                        file.write(line)
                    for line in parte2:
                        file.write(line+'\n')
                    for line in parte3:
                        file.write(line+'\n')
                    for line in parte4:
                        file.write(line+'\n')
        #Al acabar de guardar las partes, se escribe el archivo que llamara a los otros
        filename = file_name+'_base'+'.csr'
        parte2_2 = pose_extra()
        parte4_2 = command_extra(names_files, tool_number)
        outfilepath = r'{}'.format(filename) #Abrir archivo
        with open(outfilepath, 'w', encoding='UTF-8') as file:
            for line in parte1:
                file.write(line)
            for line in parte2_2:
                file.write(line+'\n')
            for line in parte3:
                file.write(line+'\n')            
            for line in parte4_2:
                file.write(line+'\n')            
    else:
        file_name = file_name + '.csr'
        outfilepath = r'{}'.format(file_name) #Abrir archivo
        with open(outfilepath, 'w', encoding='UTF-8') as file:
                for line in parte1:
                    file.write(line)
                for line in parte2:
                    file.write(line+'\n')
                for line in parte3:
                    file.write(line+'\n')
                for line in parte4:
                    file.write(line+'\n')
    print("Archivo listo")