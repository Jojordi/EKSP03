import numpy as np
import datetime

# --------------------------------------------------------------PETICIÓN DE ARCHIVO DE DATOS A USUARIO--------------------------------------------------------------#
# DATOS DE LA BARRA USADA EN LA ÚLTIMA PRUEBA DE LA MEMORIA, EN SISTEMA CARTESIANO, ORIGEN EN EL CENTRO DE LA BARRA CON EL INICIO DE LA FALLA
# ARCHIVO TIENE QUE SER UN TXT
while True:
    archivo_datos_pieza_trabajo = input('INGRESAR NOMBRE DE ARCHIVO DE DATOS: ')
    if archivo_datos_pieza_trabajo.lower().endswith('.txt'):
        filepath_pieza_trabajo = r'..\Datos\{}'.format(archivo_datos_pieza_trabajo)
        print('GRACIAS!')
        break
    else:
        print('INGRESAR NOMBRE DEL ARCHIVO .TXT, INCLUYENDO FORMATO .TXT')
# CARGA DATOS EN UNA MATRIZ DE NUMPY CON COLUMNAS EN ORDEN X, Y, Z
datos_pieza_trabajo = np.loadtxt(filepath_pieza_trabajo, delimiter=',')

# --------------------------------------------------------------COSAS POR DEFECTO--------------------------------------------------------------#
# PARÁMETROS DE SOLDADURA POR DEFECTO TAMBIÉN (HAY QUE BUSCAR CUALES SON)
outfilename_default = 'outfile.csr' 
outfilepath_default = r'..\Programas Escritos\{}'.format(outfilename_default)
# PUNTO HOME, PRIMER PUNTO Y LUGAR DE INICIO POR DEFECTO
# NOMBRE, TIPO DE COORDENADAS, UA, FA, RW, BW, TW
home_default = 'P001, AJ, 0.000000000000000, -30.000000000000000, -30.000000000000000, 0.000000000000000, -90.000000000000000, 0.000000000000000'
modelo_robot_default = 'TM1400(Through-arm torch)'
fecha_actual = '{}, {}, {}, {}, {}, {}'.format(datetime.datetime.now().year, datetime.datetime.now().month, datetime.datetime.now().day,
                                               datetime.datetime.now().hour, datetime.datetime.now().minute, datetime.datetime.now().second)
creador_default = r'IMA+'
mechanism_default = '1'
external_axis_default = '(0000)'  # POR DEFECTO NO SE TIENE NINGÚN EJE EXTERNO
tool_default = '1:TOOL01'
user_coordinates_default = 'None'
edit_default = '0'
# DISTANCIA A PIEZA DE TRABAJO POR DEFECTO EN SISTEMA GLOBAL, EN MM
distanciax_pieza_default = 1000
distanciay_pieza_default = 0
distanciaz_pieza_default = 1000

linea_header_default = '''[Description]
Robot, {}
Comment, 
SubComment1, 
SubComment2, 
Mechanism, {}{}
Tool, {}
Creator, {}
User coordinates, {}
Create, {}
Update, {}
Original, 
Edit, {}\n\n'''.format(modelo_robot_default, mechanism_default, external_axis_default, tool_default, creador_default,
                       user_coordinates_default, fecha_actual, fecha_actual, edit_default)

linea_puntos_default = '''[Pose]
/Name, Type, X, Y, Z, U, V, W
{}\n\n'''.format(home_default)

# VARIABLES POR DEFECTO, DADAS POR PROGRAMA DTPS (HAY QUE REVISAR SI SON NECESARIAS Y PORQUE SON ESTAS)
linea_variables_default = '''[Variable]
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
LR, LR005, , 0.000000000000000\n\n'''

linea_comandos_default = '''[Command]
TOOL, 1:TOOL01
MOVEP, P001, 15.00, m/min, N, -1\n\n'''

# --------------------------------------------------------------COSAS DADAS POR USUARIO/PROGRAMA--------------------------------------------------------------#
linea_header = linea_header_default

linea_puntos = '''[Pose]
/Name, Type, X, Y, Z, U, V, W
P001, AU, 519.999000000000024, 0.000000000000000, 444.973999999999933, 180.000000000000000, 43.469000000000001, 180.000000000000000
P002, AU, 1080.093000000000075, 0.000000000000000, 115.044999999999959, 180.000000000000000, 43.457999999999991, 180.000000000000000
P003, AU, 1218.811999999999898, 149.997000000000014, 22.591000000000008, 180.000000000000000, 43.467999999999989, 180.000000000000000
P004, AU, 1150.021999999999935, 149.997999999999990, -49.977999999999952, 180.000000000000000, 43.467000000000006, 180.000000000000000
P005, AU, 1087.030999999999949, 198.305000000000007, -50.029999999999973, -89.999000000000009, 43.468000000000011, -179.998999999999995
P006, AU, 1053.847999999999956, 130.901999999999987, -49.971000000000004, 0.005000000024070, 43.470999999999997, -179.991999999982511
P007, AU, 985.051000000000045, 130.909999999999997, 22.602999999999952, 0.005999999994310, 43.471000000000011, -179.992000000004140
P008, AU, 519.999000000000024, 0.000000000000000, 444.973999999999933, 180.000000000000000, 43.469000000000001, 180.000000000000000\n\n'''

linea_variables = linea_variables_default

linea_comandos = '''[Command]
TOOL, 1:TOOL01
MOVEP, P001, 15.00, m/min, N, -1
MOVEP, P002, 15.00, m/min, N, -1
MOVEL, P003, 15.00, m/min, 0, N, -1
MOVEC, P004, 15.00, m/min, 0, W, -1, CIR_NORMAL
ARC-SET, 250, 27.2, 0.50
ARC-ON, ArcStart1.rpg, 0
MOVEC, P005, 15.00, m/min, 0, W, -1, CIR_NORMAL
MOVEC, P006, 15.00, m/min, 0, N, -1, CIR_NORMAL
CRATER, 200, 20.7, 0.00
ARC-OFF, ArcEnd1.rpg, 0
MOVEL, P007, 15.00, m/min, 0, N, -1
MOVEP, P008, 15.00, m/min, N, -1 \n'''

# COLOCAR PIEZA A LA DISTANCIA ESTABLECIDA

# --------------------------------------------------------------COMIENZA ESCRITURA DE ARCHIVO CSR--------------------------------------------------------------#
# ARCHIVO EN EL QUE SE VA A ESCRIBIR EL PROGRAMA CSR
# POR CADA LÍNEA SE ESCRIBE EN EL PROGRAMA Y LUEGO SE CIERRA
lineas_programa = [linea_header, linea_puntos, linea_variables, linea_comandos]
try:
    fileID = open(outfilename_default, mode='x', encoding='UTF-8')
    for linea in lineas_programa:
        fileID.write(linea)
    fileID.close()
except FileExistsError:
    print('EXISTE')
