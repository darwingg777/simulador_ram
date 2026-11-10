# =================================================================
#  SIMULADOR DE RAM Y CPU - VERSIÓN CON CICLO FETCH-DECODE-EXECUTE
#  Arquitectura de Computadores - Actividad evaluativa, segundo corte
#
#  Se parte del simulador ampliado (SUB, MUL, INC, historial,
#  validaciones, RAM configurable) y se integra:
#   1. Ciclo Fetch-Decode-Execute visible, con ejecución paso a paso.
#      Registros visibles: PC, IR (instrucción actual) y ACC, más la RAM.
#   2. Gestor de RAM configurable: posiciones, ancho de palabra,
#      capacidad en bits/bytes, valor máximo, direcciones y datos en
#      decimal y binario, y validación según la configuración.
# =================================================================

import math

# ----------------- CONFIGURACIÓN INICIAL DE LA MÁQUINA -----------------
bits = 8                     # ancho de palabra (bits por posición)
capacidad = 16               # cantidad de posiciones de memoria
maximo = 2**bits - 1         # mayor valor representable (255 con 8 bits)
ram = [None] * capacidad     # None representa una posición vacía

# Registros de la CPU
acc = None                   # acumulador: guarda el resultado de las operaciones
pc = 0                       # contador de programa: índice de la próxima instrucción
ir = None                    # registro de instrucción: instrucción actual (operacion, direccion)

programa = []                # instrucciones cargadas: lista de (operacion, direccion)
historial = []               # filas del historial de la última ejecución
ciclo_num = 0                # número de ciclo Fetch-Decode-Execute en curso

# Instrucciones que reconoce la CPU
CON_DIRECCION = ("LOAD", "STORE", "ADD", "SUB", "MUL")   # llevan dirección
SIN_DIRECCION = ("INC",)                                 # no llevan dirección
LEEN_RAM = ("LOAD", "ADD", "SUB", "MUL")                 # necesitan un dato en RAM
USAN_ACC = ("STORE", "ADD", "SUB", "MUL", "INC")         # necesitan un valor en ACC


# ----------------------- FUNCIONES DE APOYO -----------------------
def pedir_numero(mensaje, minimo=None, limite=None):
    """Pide un entero y repite la pregunta hasta que sea válido y esté
    dentro del rango. El programa nunca se cierra por una entrada mala."""
    while True:
        texto = input(mensaje).strip()
        try:
            numero = int(texto)
        except ValueError:
            print("Entrada no válida: ingrese un número entero.")
            continue
        if minimo is not None and numero < minimo:
            print(f"Error: el valor debe ser mayor o igual a {minimo}.")
            continue
        if limite is not None and numero > limite:
            print(f"Error: el valor debe ser menor o igual a {limite}.")
            continue
        return numero


def bits_direccion():
    """Bits necesarios para numerar todas las posiciones de la RAM."""
    return max(1, math.ceil(math.log2(capacidad)))


def a_binario(dato):
    """Dato en binario con el ancho de palabra configurado."""
    return format(dato, f"0{bits}b")


def dir_binario(direccion):
    """Dirección en binario con los bits de dirección necesarios."""
    return format(direccion, f"0{bits_direccion()}b")


def texto_valor(valor):
    """Texto para mostrar un valor que puede estar vacío."""
    return "vacío" if valor is None else str(valor)


def texto_instr(instruccion):
    """Instrucción (operacion, direccion) como texto, p. ej. 'ADD 1'."""
    if instruccion is None:
        return "-"
    operacion, direccion = instruccion
    return operacion if direccion is None else f"{operacion} {direccion}"


def ajustar_al_registro(resultado):
    """Ajusta un resultado al tamaño del registro (comportamiento modular).
    Como en una CPU real, el registro conserva los bits que caben y se
    avisa el desbordamiento. Ejemplo con 8 bits: 200 + 100 = 300 -> 44."""
    desborde = resultado < 0 or resultado > maximo
    return resultado % (maximo + 1), desborde


# ------------------------ OPERACIONES DE RAM ------------------------
def escribir():
    """Guarda un dato en una dirección (se valida con la configuración actual)."""
    direccion = pedir_numero(f"Dirección de memoria (0-{capacidad - 1}): ", 0, capacidad - 1)
    dato = pedir_numero(f"Dato a guardar (0-{maximo}): ", 0, maximo)
    anterior = ram[direccion]
    ram[direccion] = dato
    if anterior is None:
        print(f"WRITE: se guardó {dato} en la dirección {direccion}.")
    else:
        print(f"OVERWRITE: la dirección {direccion} cambió de {anterior} a {dato}.")


def leer_dato():
    """Lee el dato de una dirección de la RAM."""
    direccion = pedir_numero(f"Dirección de memoria (0-{capacidad - 1}): ", 0, capacidad - 1)
    dato = ram[direccion]
    if dato is None:
        print(f"READ: la dirección {direccion} está vacía.")
    else:
        print(f"READ: la dirección {direccion} = {dato} (binario: {a_binario(dato)})")


def mostrar_memoria():
    """Muestra toda la RAM: dirección (decimal y binario) y dato (decimal y binario)."""
    ancho_dir = max(8, bits_direccion())
    ancho_dec = max(7, len(str(maximo)))
    ancho_bin = max(bits, 7)
    linea = "-" * (9 + ancho_dir + ancho_dec + ancho_bin + 9)
    print(f"\n====== MEMORIA RAM ({capacidad} posiciones x {bits} bits) ======")
    print(f"{'Dirección':>9} | {'Dir.bin':<{ancho_dir}} | {'Entero':<{ancho_dec}} | Binario")
    print(linea)
    for direccion, dato in enumerate(ram):
        decimal = texto_valor(dato)
        binario = "-" * bits if dato is None else a_binario(dato)
        print(f"{direccion:9} | {dir_binario(direccion):<{ancho_dir}} | {decimal:<{ancho_dec}} | {binario}")
    ocupadas = sum(dato is not None for dato in ram)
    print(linea)
    print(f"Posiciones ocupadas: {ocupadas}/{capacidad}")


def mostrar_ram_ocupada(resaltar=None):
    """Vista compacta para el paso a paso: solo las posiciones con datos.
    Marca con '<-- cambió' la posición que acaba de modificar la instrucción."""
    ocupadas = [(d, v) for d, v in enumerate(ram) if v is not None]
    print(f"  RAM ({capacidad} x {bits} bits), posiciones con datos:")
    if not ocupadas:
        print("    (vacía)")
    for direccion, dato in ocupadas:
        marca = "   <-- cambió" if direccion == resaltar else ""
        print(f"    [{direccion:>3}] ({dir_binario(direccion)}) = {dato:>{len(str(maximo))}}  ({a_binario(dato)}){marca}")


# ------------------ CONFIGURACIÓN Y CAPACIDAD DE LA RAM ------------------
def calcular_capacidad(posiciones, ancho):
    """Calcula las características de una memoria de 'posiciones' x 'ancho' bits."""
    total_bits = posiciones * ancho
    return {
        "posiciones": posiciones,
        "bits": ancho,
        "maximo": 2**ancho - 1,
        "total_bits": total_bits,
        "bytes": total_bits / 8,
        "bits_direccion": max(1, math.ceil(math.log2(posiciones))),
    }


def formato_bytes(valor):
    """Muestra los bytes sin decimales cuando son exactos."""
    return str(int(valor)) if valor == int(valor) else f"{valor:.3f}"


def mostrar_info_memoria():
    """Muestra el análisis de la configuración actual."""
    c = calcular_capacidad(capacidad, bits)
    print("\n====== CONFIGURACIÓN ACTUAL ======")
    print(f"Posiciones de memoria : {c['posiciones']}")
    print(f"Ancho de palabra      : {c['bits']} bits")
    print(f"Valor máximo por dato : {c['maximo']}  (2^{c['bits']} - 1)")
    print(f"Capacidad total       : {c['total_bits']} bits = {formato_bytes(c['bytes'])} bytes")
    print(f"Bits de dirección     : {c['bits_direccion']}  (direcciones 0 a {capacidad - 1})")


def configurar_ram():
    """Cambia la cantidad de posiciones y el ancho de palabra."""
    global bits, capacidad, maximo, ram, acc, pc, ir, programa, historial, ciclo_num
    mostrar_info_memoria()
    nueva_capacidad = pedir_numero("\nNueva cantidad de posiciones (1-256): ", 1, 256)
    nuevos_bits = pedir_numero("Nuevo ancho de palabra en bits (1-32): ", 1, 32)
    confirmacion = input("Se borrará la RAM, la CPU y el programa cargado. ¿Continuar? (s/n): ").strip().lower()
    if confirmacion != "s":
        print("Configuración cancelada.")
        return
    capacidad = nueva_capacidad
    bits = nuevos_bits
    maximo = 2**bits - 1
    ram = [None] * capacidad
    acc, pc, ir = None, 0, None
    programa, historial, ciclo_num = [], [], 0
    print("RAM reconfigurada.")
    mostrar_info_memoria()


def comparar_configuraciones():
    """Compara dos memorias, por ejemplo 16x8 bits contra 32x8 bits."""
    print("\nMemoria A")
    pos_a = pedir_numero("  Posiciones (1-1024): ", 1, 1024)
    bits_a = pedir_numero("  Bits por dato (1-64): ", 1, 64)
    print("Memoria B")
    pos_b = pedir_numero("  Posiciones (1-1024): ", 1, 1024)
    bits_b = pedir_numero("  Bits por dato (1-64): ", 1, 64)
    a = calcular_capacidad(pos_a, bits_a)
    b = calcular_capacidad(pos_b, bits_b)
    filas = [
        ("Posiciones", a["posiciones"], b["posiciones"]),
        ("Bits por dato", a["bits"], b["bits"]),
        ("Valor máximo", a["maximo"], b["maximo"]),
        ("Capacidad (bits)", a["total_bits"], b["total_bits"]),
        ("Capacidad (bytes)", formato_bytes(a["bytes"]), formato_bytes(b["bytes"])),
        ("Bits de dirección", a["bits_direccion"], b["bits_direccion"]),
    ]
    print(f"\n{'Característica':<18} | {'Memoria A':>20} | {'Memoria B':>20}")
    print("-" * 64)
    for nombre, valor_a, valor_b in filas:
        print(f"{nombre:<18} | {str(valor_a):>20} | {str(valor_b):>20}")
    print("-" * 64)
    print(f"La memoria B tiene {b['total_bits'] / a['total_bits']:.2f} veces la capacidad de la memoria A.")


# ------------------------- CARGA DEL PROGRAMA -------------------------
def validar_instruccion(linea):
    """Revisa una línea antes de aceptarla.
    Devuelve (operacion, direccion) o None si la línea no es válida."""
    partes = linea.split()
    operacion = partes[0]

    if operacion in SIN_DIRECCION:
        if len(partes) != 1:
            print(f"Error: {operacion} no lleva dirección. Ejemplo: {operacion}")
            return None
        return (operacion, None)

    if operacion in CON_DIRECCION:
        if len(partes) != 2:
            print(f"Error: {operacion} necesita una dirección. Ejemplo: {operacion} 3")
            return None
        try:
            direccion = int(partes[1])
        except ValueError:
            print("Error: la dirección debe ser un número entero.")
            return None
        if not 0 <= direccion < capacidad:
            print(f"Error: la dirección {direccion} está fuera del rango 0-{capacidad - 1}.")
            return None
        return (operacion, direccion)

    validas = ", ".join(CON_DIRECCION + SIN_DIRECCION)
    print(f"Error: instrucción '{operacion}' no reconocida. Válidas: {validas}")
    return None


def cargar_programa():
    """Pide las instrucciones una por una hasta escribir FIN y las guarda
    en 'programa'. Una línea incorrecta se rechaza y se puede reescribir."""
    global programa
    nuevas = []
    print("\nIngrese las instrucciones (FIN para terminar):")
    print("LOAD d | STORE d | ADD d | SUB d | MUL d | INC   (d = dirección)")
    while True:
        linea = input(f"Instrucción {len(nuevas)}: ").strip().upper()
        if linea == "":
            continue
        if linea == "FIN":
            break
        instruccion = validar_instruccion(linea)
        if instruccion is not None:
            nuevas.append(instruccion)
    programa = nuevas
    print(f"Programa cargado: {len(programa)} instrucciones.")


# --------------------- HISTORIAL DE EJECUCIÓN ---------------------
def imprimir_encabezado_historial():
    print(f"\n{'Ciclo':>5} | {'PC':>3} | {'IR':<8} | {'ACC antes':>9} | {'ACC después':>11} | {'RAM usada':<17} | Resultado")
    print("-" * 105)


def imprimir_fila_historial(fila):
    print(f"{fila['ciclo']:>5} | {fila['pc']:>3} | {fila['ir']:<8} | {fila['antes']:>9} | "
          f"{fila['despues']:>11} | {fila['ram']:<17} | {fila['resultado']}")


def mostrar_historial():
    """Vuelve a mostrar la tabla de la última ejecución."""
    if not historial:
        print("Todavía no se ha ejecutado ningún programa.")
        return
    imprimir_encabezado_historial()
    for fila in historial:
        imprimir_fila_historial(fila)


# ------------------ CICLO FETCH - DECODE - EXECUTE ------------------
def fetch():
    """FETCH: la CPU busca en el programa la instrucción que indica el PC,
    la copia al IR y avanza el PC a la siguiente instrucción."""
    global pc, ir
    pc_antes = pc
    ir = programa[pc]
    pc += 1
    print(f"  FETCH   : lee la instrucción de la posición {pc_antes} -> IR = {texto_instr(ir)}")
    print(f"            PC: {pc_antes} -> {pc}  (apunta a la siguiente instrucción)")
    return pc_antes


def decode(instruccion):
    """DECODE: identifica la operación y sus operandos. Si la operación
    necesita un dato de la RAM, lo lee. Devuelve (operando, error)."""
    operacion, direccion = instruccion
    operando = None
    if operacion in SIN_DIRECCION:
        print(f"  DECODE  : operación = {operacion}; sin dirección (usa solo el ACC)")
    else:
        print(f"  DECODE  : operación = {operacion}; dirección = {direccion} ({dir_binario(direccion)})")
        if operacion in LEEN_RAM:
            if ram[direccion] is None:
                return None, f"ERROR: RAM[{direccion}] está vacía"
            operando = ram[direccion]
            print(f"            dato leído de RAM[{direccion}] = {operando} ({a_binario(operando)})")
    if operacion in USAN_ACC and acc is None:
        return None, "ERROR: ACC vacío, use LOAD primero"
    return operando, None


def execute(instruccion, operando):
    """EXECUTE: ejecuta la operación y actualiza ACC o la RAM.
    Devuelve (resultado, uso_ram, desborde, direccion_modificada)."""
    global acc
    operacion, direccion = instruccion
    acc_antes = acc
    desborde = False
    modificada = None

    if operacion == "LOAD":
        acc = operando
        uso_ram, resultado = f"RAM[{direccion}] leída", f"ACC <- {acc}"
    elif operacion == "STORE":
        ram[direccion] = acc
        modificada = direccion
        uso_ram, resultado = f"RAM[{direccion}] escrita", f"RAM[{direccion}] <- {acc}"
    elif operacion == "ADD":
        real = acc + operando
        acc, desborde = ajustar_al_registro(real)
        uso_ram, resultado = f"RAM[{direccion}] leída", f"{acc_antes} + {operando} = {real}"
    elif operacion == "SUB":
        real = acc - operando
        acc, desborde = ajustar_al_registro(real)
        uso_ram, resultado = f"RAM[{direccion}] leída", f"{acc_antes} - {operando} = {real}"
    elif operacion == "MUL":
        real = acc * operando
        acc, desborde = ajustar_al_registro(real)
        uso_ram, resultado = f"RAM[{direccion}] leída", f"{acc_antes} x {operando} = {real}"
    elif operacion == "INC":
        real = acc + 1
        acc, desborde = ajustar_al_registro(real)
        uso_ram, resultado = "-", f"{acc_antes} + 1 = {real}"

    if desborde:
        resultado += f"  [DESBORDAMIENTO: no cabe en {bits} bits, ACC = {acc}]"
    print(f"  EXECUTE : {resultado}")
    return resultado, uso_ram, desborde, modificada


def ejecutar_ciclo():
    """Un ciclo completo Fetch -> Decode -> Execute. Devuelve (ok, modificada)."""
    global ciclo_num
    ciclo_num += 1
    print(f"\n=== CICLO {ciclo_num} ===")
    acc_antes = acc

    pc_antes = fetch()
    operando, error = decode(ir)

    if error:
        print(f"  EXECUTE : {error}")
        historial.append({"ciclo": ciclo_num, "pc": pc_antes, "ir": texto_instr(ir),
                          "antes": texto_valor(acc_antes), "despues": texto_valor(acc),
                          "ram": "-", "resultado": error})
        print(f"\nPrograma detenido en la instrucción {pc_antes}. La RAM y el ACC quedan como estaban.")
        return False, None

    resultado, uso_ram, _, modificada = execute(ir, operando)
    historial.append({"ciclo": ciclo_num, "pc": pc_antes, "ir": texto_instr(ir),
                      "antes": texto_valor(acc_antes), "despues": texto_valor(acc),
                      "ram": uso_ram, "resultado": resultado})
    return True, modificada


def mostrar_estado(modificada):
    """Estado de la CPU y de la RAM al terminar un ciclo."""
    acc_bin = "" if acc is None else f"  ({a_binario(acc)})"
    print("  ---- Estado de la CPU ----")
    print(f"  PC = {pc} | IR = {texto_instr(ir)} | ACC = {texto_valor(acc)}{acc_bin}")
    mostrar_ram_ocupada(modificada)


def ejecutar_programa():
    """Ejecuta el programa cargado, paso a paso o completo."""
    global pc, ir, historial, ciclo_num
    if not programa:
        print("No hay programa cargado. Use la opción 4 primero.")
        return

    print("\nPrograma cargado:")
    for i, instruccion in enumerate(programa):
        print(f"  {i}: {texto_instr(instruccion)}")
    print("\nModo de ejecución:\n  1. Paso a paso\n  2. Completo (muestra todos los ciclos)")
    paso_a_paso = pedir_numero("Seleccione el modo: ", 1, 2) == 1

    pc, ir, historial, ciclo_num = 0, None, [], 0
    detenido = False

    while pc < len(programa):
        ok, modificada = ejecutar_ciclo()
        if not ok:
            detenido = True
            break
        mostrar_estado(modificada)

        if paso_a_paso and pc < len(programa):
            while True:
                eleccion = input("\n[Enter] siguiente | m = ver RAM completa | a = ejecutar el resto | s = salir: ").strip().lower()
                if eleccion == "m":
                    mostrar_memoria()
                    continue
                break
            if eleccion == "a":
                paso_a_paso = False
            elif eleccion == "s":
                print("Ejecución interrumpida por el usuario.")
                detenido = True
                break

    if not detenido:
        print("\nPrograma finalizado.")
    print(f"ACC final: {texto_valor(acc)} | PC final: {pc} | Ciclos ejecutados: {ciclo_num}")
    mostrar_historial()


# ------------------------------ REINICIO ------------------------------
def reiniciar_RAM():
    """Borra la RAM, los registros y el historial, previa confirmación.
    El programa cargado se conserva."""
    global ram, acc, pc, ir, historial, ciclo_num
    confirmacion = input("Se borrarán los datos en la memoria. ¿Continuar? (s/n): ").strip().lower()
    if confirmacion == "s":
        ram = [None] * capacidad
        acc, pc, ir = None, 0, None
        historial, ciclo_num = [], 0
        print("RAM y CPU reiniciadas.")
    else:
        print("Reinicio cancelado.")


# -------------------------------- MENÚ --------------------------------
def menu():
    while True:
        print(f"\n==== SIMULADOR DE RAM ({capacidad} x {bits} bits) ====")
        print("1. Mostrar memoria RAM")
        print("2. Escribir un dato en RAM")
        print("3. Leer un dato de la RAM")
        print("4. Ingresar un programa")
        print("5. Ejecutar el programa (ciclo Fetch-Decode-Execute)")
        print("6. Ver historial de la última ejecución")
        print("7. Configurar la RAM (posiciones y bits)")
        print("8. Comparar dos configuraciones de memoria")
        print("9. Reiniciar RAM y CPU")
        print("10. Salir del programa")
        opcion = pedir_numero("Seleccione una opción: ", 1, 10)
        if opcion == 1:
            mostrar_memoria()
        elif opcion == 2:
            escribir()
        elif opcion == 3:
            leer_dato()
        elif opcion == 4:
            cargar_programa()
        elif opcion == 5:
            ejecutar_programa()
        elif opcion == 6:
            mostrar_historial()
        elif opcion == 7:
            configurar_ram()
        elif opcion == 8:
            comparar_configuraciones()
        elif opcion == 9:
            reiniciar_RAM()
        elif opcion == 10:
            print("Hasta luego...")
            break


if __name__ == "__main__":
    try:
        menu()
    except (KeyboardInterrupt, EOFError):
        print("\nPrograma cerrado.")