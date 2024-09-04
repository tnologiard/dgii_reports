"""RNC (Registro Nacional del Contribuyente, número de identificación fiscal de la República Dominicana).

El RNC es el número de registro de contribuyente de la República Dominicana para
instituciones. El número consta de 9 dígitos.

>>> validate('1-01-85004-3')
'101850043'
>>> validate('1018A0043')
Traceback (most recent call last):
    ...
InvalidFormat: ...
>>> validate('101850042')
Traceback (most recent call last):
    ...
InvalidChecksum: ...
>>> format('131246796')
'1-31-24679-6'
"""

import json

from stdnum.exceptions import *
from stdnum.util import clean, isdigits

from zeep import Client, Transport
import requests
import urllib3

# Deshabilitar advertencias de SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Lista de RNC que no coinciden con el checksum pero que son válidos
whitelist = set('''
101581601 101582245 101595422 101595785 10233317 131188691 401007374
501341601 501378067 501620371 501651319 501651823 501651845 501651926
501656006 501658167 501670785 501676936 501680158 504654542 504680029
504681442 505038691
'''.split())


dgii_wsdl = 'https://www.dgii.gov.do/wsMovilDGII/WSMovilDGII.asmx?WSDL'
"""La URL WSDL del servicio de validación de la DGII."""


def get_soap_client(wsdl_url, timeout=30):
    """Crea un cliente SOAP utilizando Zeep y deshabilitando la verificación SSL."""
    session = requests.Session()
    session.verify = False
    transport = Transport(session=session, timeout=timeout)
    return Client(wsdl=wsdl_url, transport=transport)
    

def compact(number):
    """Convierte el número a su representación mínima. Esto elimina los
    separadores válidos y los espacios en blanco alrededor del número."""
    return clean(number, ' -').strip()


def calc_check_digit(number):
    """Calcula el dígito de verificación."""
    weights = (7, 9, 8, 6, 5, 4, 3, 2)
    check = sum(w * int(n) for w, n in zip(weights, number)) % 11
    return str((10 - check) % 9 + 1)


def validate(number):
    """Verifica si el número proporcionado es un RNC válido."""
    number = compact(number)
    if not isdigits(number):
        raise InvalidFormat()  # Lanza una excepción si el formato no es válido
    if number in whitelist:
        return number  # Si está en la lista blanca, se considera válido
    if len(number) != 9:
        raise InvalidLength()  # Lanza una excepción si la longitud no es la esperada
    if calc_check_digit(number[:-1]) != number[-1]:
        raise InvalidChecksum()  # Lanza una excepción si el dígito de verificación es incorrecto
    return number


def is_valid(number):
    """Verifica si el número proporcionado es un RNC válido."""
    try:
        return bool(validate(number))  # Devuelve True si el número es válido
    except ValidationError:
        return False  # Devuelve False si ocurre una excepción de validación


def format(number):
    """Reformatea el número al formato estándar de presentación."""
    number = compact(number)
    return '-'.join((number[:1], number[1:3], number[3:-1], number[-1]))


def _convert_result(result):  # pragma: no cover
    """Traduce las entradas del resultado SOAP a diccionarios."""
    translation = {
        'RGE_RUC': 'rnc',
        'RGE_NOMBRE': 'name',
        'NOMBRE_COMERCIAL': 'commercial_name',
        'CATEGORIA': 'category',
        'REGIMEN_PAGOS': 'payment_regime',
        'ESTATUS': 'status',
        'RNUM': 'result_number',
    }
    return dict(
        (translation.get(key, key), value)
        for key, value in json.loads(result.replace('\n', '\\n').replace('\t', '\\t')).items())


def check_dgii(number, timeout=30):  # pragma: no cover
    """Consulta el número usando el servicio web en línea de la DGII.

    Utiliza el servicio de validación de la Dirección General de
    Impuestos Internos, el departamento de impuestos de la República Dominicana,
    para buscar la información de registro del número. El tiempo de espera es en segundos.

    Devuelve un diccionario con la siguiente estructura::

        {
            'rnc': '123456789',     # El número solicitado
            'name': 'Nombre registrado',
            'commercial_name': 'Nombre comercial adicional',
            'status': '2',          # 1: inactivo, 2: activo
            'category': '0',        # ¿siempre 0?
            'payment_regime': '2',  # 1: N/D, 2: NORMAL, 3: PST
        }

    Devuelve None si el número es inválido o desconocido."""
    # Esta función no se prueba automáticamente porque requeriría
    # acceso a la red para las pruebas y cargaría innecesariamente el servicio en línea
    number = compact(number)
    client = get_soap_client(dgii_wsdl, timeout)
    result = client.GetContribuyentes(
        value=number,
        patronBusqueda=0,   # tipo de búsqueda: 0=por número, 1=por nombre
        inicioFilas=1,      # resultado de inicio (basado en 1)
        filaFilas=1,        # resultado final
        IMEI='')
    if result and 'GetContribuyentesResult' in result:
        result = result['GetContribuyentesResult']  # Solo PySimpleSOAP
    if result == '0':
        return
    result = [x for x in result.split('@@@')]
    return _convert_result(result[0])


def search_dgii(keyword, end_at=10, start_at=1, timeout=30):  # pragma: no cover
    """Busca en el servicio web en línea de la DGII usando la palabra clave.

    Utiliza el servicio de validación de la Dirección General de
    Impuestos Internos, el departamento de impuestos de la República Dominicana,
    para buscar la información de registro usando la palabra clave.

    El número de entradas devueltas se puede ajustar con los argumentos `end_at` y
    `start_at`. El tiempo de espera es en segundos.

    Devuelve una lista de diccionarios con la siguiente estructura::

        [
            {
                'rnc': '123456789',     # El número encontrado
                'name': 'Nombre registrado',
                'commercial_name': 'Nombre comercial adicional',
                'status': '2',          # 1: inactivo, 2: activo
                'category': '0',        # ¿siempre 0?
                'payment_regime': '2',  # 1: N/D, 2: NORMAL, 3: PST
                'result_number': '1',   # índice del resultado
            },
            ...
        ]

    Devuelve una lista vacía si el número es inválido o desconocido."""
    # Esta función no se prueba automáticamente porque requeriría
    # acceso a la red para las pruebas y cargaría innecesariamente el servicio en línea
    client = get_soap_client(dgii_wsdl, timeout)
    results = client.GetContribuyentes(
        value=keyword,
        patronBusqueda=1,       # tipo de búsqueda: 0=por número, 1=por nombre
        inicioFilas=start_at,   # resultado de inicio (basado en 1)
        filaFilas=end_at,       # resultado final
        IMEI='')
    if results and 'GetContribuyentesResult' in results:
        results = results['GetContribuyentesResult']  # Solo PySimpleSOAP
    if results == '0':
        return []
    return [_convert_result(result) for result in results.split('@@@')]
