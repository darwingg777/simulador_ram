"# simulador_ram" 
Al iniciar aparece un menú con 10 opciones. Cualquier entrada inválida se rechaza y se vuelve a preguntar; el programa no se cierra por errores de digitación.

Componentes simulados
Componente	Variable	Función
RAM	ram	Lista de posiciones con dirección; None significa posición vacía
PC (Program Counter)	pc	Índice de la próxima instrucción a ejecutar
IR (Instruction Register)	ir	Instrucción que se está ejecutando
ACC (Acumulador)	acc	Guarda el resultado de las operaciones

Configuración inicial: 16 posiciones × 8 bits (valor máximo 255).

Instrucciones disponibles
Instrucción	Efecto
LOAD d	ACC ← RAM[d]
STORE d	RAM[d] ← ACC
ADD d	ACC ← ACC + RAM[d]
SUB d	ACC ← ACC − RAM[d]
MUL d	ACC ← ACC × RAM[d]
INC	ACC ← ACC + 1

d es una dirección de memoria. Si un resultado no cabe en el ancho de palabra, el ACC conserva los bits que caben (aritmética modular) y se muestra un aviso de DESBORDAMIENTO. Ejemplo con 8 bits: 200 + 100 = 300 → ACC = 44.

Menú
Opción	Qué hace
1	Muestra la RAM completa (dirección y dato, en decimal y binario)
2	Escribe un dato en una dirección
3	Lee el dato de una dirección
4	Ingresa un programa (instrucciones una por una; FIN para terminar)
5	Ejecuta el programa con el ciclo Fetch–Decode–Execute
6	Muestra el historial de la última ejecución
7	Configura la RAM (posiciones y bits por dato)
8	Compara dos configuraciones de memoria
9	Reinicia la RAM y la CPU (conserva el programa cargado)
10	Sale del programa
Ejecución paso a paso

Al elegir la opción 5 se pide el modo: 1 = paso a paso o 2 = completo. En cada ciclo se muestran las tres etapas:

FETCH: copia programa[pc] al IR y avanza el PC.
DECODE: identifica la operación y la dirección (también en binario) y lee el dato de la RAM si lo necesita.
EXECUTE: realiza la operación y actualiza el ACC o la RAM.

Después de cada ciclo se imprimen PC, IR, ACC y las posiciones de RAM con datos, marcando con <-- cambió la que se modificó. En modo paso a paso las teclas son:

Tecla	Acción
Enter	Siguiente ciclo
m	Ver la RAM completa
a	Ejecutar el resto sin pausas
s	Salir de la ejecución
RAM configurable

La opción 7 cambia las posiciones (1–256) y el ancho de palabra (1–32 bits). Borra la RAM, la CPU y el programa cargado, por lo que pide confirmación. Se calculan:

Valor máximo: 2^bits − 1
Capacidad en bits: posiciones × bits
Capacidad en bytes: bits ÷ 8
Bits de dirección: ⌈log₂(posiciones)⌉

Direcciones y datos se validan siempre contra la configuración actual.

Ejemplo de uso

Con la configuración inicial (16 × 8 bits):

Opción 2: guardar 5 en la dirección 0.
Opción 2: guardar 3 en la dirección 1.
Opción 4: ingresar LOAD 0, ADD 1, STORE 2 y FIN.
Opción 5, modo 1, y pulsar Enter en cada ciclo.

Resultado: el ACC pasa de vacío a 5 y luego a 8, y la dirección 2 queda con el valor 8 (00001000) tras 3 ciclos.

Pruebas realizadas
Prueba	Datos y programa	Resultado
1. Paso a paso	RAM[0]=5, RAM[1]=3; LOAD 0, ADD 1, STORE 2	ACC final = 8, RAM[2] = 8, 3 ciclos
2. Desbordamiento	RAM[0]=200, RAM[1]=100; LOAD 0, ADD 1, SUB 1, MUL 1, INC	ACC: 200 → 44 → 200 → 32 → 33, con aviso de desbordamiento en 3 pasos
3. RAM configurable	32 posiciones × 4 bits	Capacidad 128 bits = 16 bytes, máximo 15, 5 bits de dirección; dirección 40 y dato 20 son rechazados
Estructura del código
Sección	Funciones principales
Configuración inicial	Variables bits, capacidad, maximo, ram, acc, pc, ir
Funciones de apoyo	pedir_numero, a_binario, dir_binario, ajustar_al_registro
Operaciones de RAM	escribir, leer_dato, mostrar_memoria, mostrar_ram_ocupada
Configuración de RAM	calcular_capacidad, configurar_ram, comparar_configuraciones
Carga del programa	validar_instruccion, cargar_programa
Ciclo de instrucción	fetch, decode, execute, ejecutar_ciclo, ejecutar_programa
Historial	mostrar_historial
Menú	menu
