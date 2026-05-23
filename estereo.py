"""
estereo.py

Nombre: Alvaro Ramo Irurre

Fichero con funciones para manejar señales de audio estéreo en formato WAVE.
Permite separar canales, combinarlos y codificar/decodificar usando 32 bits.

Solo se usa la librería struct :)
"""

import struct


def leer_cabecera(f):
    # Lee y comprueba la cabecera de un fichero WAVE
    # Devuelve num_canales, frec_muestreo, bits_por_muestra, tamaño_datos
    if f.read(4) != b'RIFF':
        raise ValueError("El fichero no tiene formato RIFF")
    f.read(4)  # tamaño total del fichero, no lo necesitamos
    if f.read(4) != b'WAVE':
        raise ValueError("El fichero no es WAVE")

    if f.read(4) != b'fmt ':
        raise ValueError("No se encuentra el bloque fmt")
    fmt_size = struct.unpack('<I', f.read(4))[0]
    audio_format = struct.unpack('<H', f.read(2))[0]
    if audio_format != 1:
        raise ValueError("Solo se admite PCM lineal")
    num_canales = struct.unpack('<H', f.read(2))[0]
    frec_muestreo = struct.unpack('<I', f.read(4))[0]
    f.read(4)  # byte rate
    f.read(2)  # block align
    bits = struct.unpack('<H', f.read(2))[0]
    if fmt_size > 16:
        f.read(fmt_size - 16)  # bytes extra del bloque fmt

    if f.read(4) != b'data':
        raise ValueError("No se encuentra el bloque data")
    tam_datos = struct.unpack('<I', f.read(4))[0]

    return num_canales, frec_muestreo, bits, tam_datos


def escribir_cabecera(f, num_canales, frec_muestreo, bits, num_muestras):
    # Escribe la cabecera estándar de un fichero WAVE (44 bytes)
    block_align = num_canales * bits // 8
    byte_rate = frec_muestreo * block_align
    tam_datos = num_muestras * block_align

    f.write(b'RIFF')
    f.write(struct.pack('<I', 36 + tam_datos))
    f.write(b'WAVE')
    f.write(b'fmt ')
    f.write(struct.pack('<I', 16))
    f.write(struct.pack('<H', 1))  # PCM lineal
    f.write(struct.pack('<H', num_canales))
    f.write(struct.pack('<I', frec_muestreo))
    f.write(struct.pack('<I', byte_rate))
    f.write(struct.pack('<H', block_align))
    f.write(struct.pack('<H', bits))
    f.write(b'data')
    f.write(struct.pack('<I', tam_datos))


def estereo2mono(ficEste, ficMono, canal=2):
   
    with open(ficEste, 'rb') as f:
        num_canales, frec_muestreo, bits, tam_datos = leer_cabecera(f)
        if num_canales != 2:
            raise ValueError("El fichero de entrada no es estéreo")
        if bits != 16:
            raise ValueError("El fichero debe tener 16 bits por muestra")
        num_muestras = tam_datos // 4
        datos = struct.unpack(f'<{2 * num_muestras}h', f.read(tam_datos))

    L = datos[0::2]
    R = datos[1::2]

    if canal == 0:
        mono = L
    elif canal == 1:
        mono = R
    elif canal == 2:
        mono = tuple((l + r) // 2 for l, r in zip(L, R))
    elif canal == 3:
        mono = tuple((l - r) // 2 for l, r in zip(L, R))
    else:
        raise ValueError(f"Canal no válido: {canal}. Debe ser 0, 1, 2 o 3")

    with open(ficMono, 'wb') as f:
        escribir_cabecera(f, 1, frec_muestreo, 16, num_muestras)
        f.write(struct.pack(f'<{num_muestras}h', *mono))


def mono2estereo(ficIzq, ficDer, ficEste):
    
    with open(ficIzq, 'rb') as f:
        nc_izq, fs_izq, bits_izq, tam_izq = leer_cabecera(f)
        if nc_izq != 1:
            raise ValueError("ficIzq debe ser un fichero mono")
        if bits_izq != 16:
            raise ValueError("ficIzq debe tener 16 bits por muestra")
        n = tam_izq // 2
        L = struct.unpack(f'<{n}h', f.read(tam_izq))

    with open(ficDer, 'rb') as f:
        nc_der, fs_der, bits_der, tam_der = leer_cabecera(f)
        if nc_der != 1:
            raise ValueError("ficDer debe ser un fichero mono")
        if bits_der != 16:
            raise ValueError("ficDer debe tener 16 bits por muestra")
        n_der = tam_der // 2
        R = struct.unpack(f'<{n_der}h', f.read(tam_der))

    if fs_izq != fs_der:
        raise ValueError("Los dos ficheros deben tener la misma frecuencia de muestreo")
    if n != n_der:
        raise ValueError("Los dos ficheros deben tener el mismo número de muestras")

    muestras = [v for par in zip(L, R) for v in par]

    with open(ficEste, 'wb') as f:
        escribir_cabecera(f, 2, fs_izq, 16, n)
        f.write(struct.pack(f'<{2 * n}h', *muestras))


def codEstereo(ficEste, ficCod):
    
    with open(ficEste, 'rb') as f:
        num_canales, frec_muestreo, bits, tam_datos = leer_cabecera(f)
        if num_canales != 2:
            raise ValueError("El fichero de entrada no es estéreo")
        if bits != 16:
            raise ValueError("El fichero debe tener 16 bits por muestra")
        num_muestras = tam_datos // 4
        datos = struct.unpack(f'<{2 * num_muestras}h', f.read(tam_datos))

    L = datos[0::2]
    R = datos[1::2]

    codificadas = [((l + r) // 2 & 0xFFFF) << 16 | ((l - r) // 2 & 0xFFFF)
                   for l, r in zip(L, R)]

    with open(ficCod, 'wb') as f:
        escribir_cabecera(f, 1, frec_muestreo, 32, num_muestras)
        f.write(struct.pack(f'<{num_muestras}I', *codificadas))


def decEstereo(ficCod, ficEste):
    
    with open(ficCod, 'rb') as f:
        num_canales, frec_muestreo, bits, tam_datos = leer_cabecera(f)
        if num_canales != 1:
            raise ValueError("El fichero de entrada debe ser mono")
        if bits != 32:
            raise ValueError("El fichero debe tener 32 bits por muestra")
        num_muestras = tam_datos // 4
        datos = struct.unpack(f'<{num_muestras}I', f.read(tam_datos))

    # Extraer semisuma y semidiferencia como enteros con signo de 16 bits
    semisuma = [struct.unpack('<h', struct.pack('<H', c >> 16))[0] for c in datos]
    semidiferencia = [struct.unpack('<h', struct.pack('<H', c & 0xFFFF))[0] for c in datos]

    L = [s + d for s, d in zip(semisuma, semidiferencia)]
    R = [s - d for s, d in zip(semisuma, semidiferencia)]

    muestras = [v for par in zip(L, R) for v in par]

    with open(ficEste, 'wb') as f:
        escribir_cabecera(f, 2, frec_muestreo, 16, num_muestras)
        f.write(struct.pack(f'<{2 * num_muestras}h', *muestras))
