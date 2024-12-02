"""NCF (Números de Comprobante Fiscal, Dominican Republic receipt number).

El NCF se utiliza para numerar facturas y otros documentos con el propósito de la declaración de impuestos.
El e-CF (Comprobante Fiscal Electrónico) se utiliza junto con un certificado digital para el mismo propósito. 
El número puede tener 19, 11 o 13 dígitos en el caso del e-CF.

El número de 19 dígitos comienza con una letra (A o P) para indicar que el número fue asignado por el 
contribuyente o la DGII, seguido de un número de unidad de negocio de 2 dígitos, un número de ubicación 
de 3 dígitos, un identificador de mecanismo de 3 dígitos, un tipo de documento de 2 dígitos y un número 
de serie de 8 dígitos.

El número de 11 dígitos siempre comienza con una "B", seguido de un tipo de documento de 2 dígitos 
y un número de serie de 8 dígitos.

El e-CF de 13 dígitos comienza con una "E", seguido de un tipo de documento de 2 dígitos y un número 
de serie de 10 dígitos.

Más información:

 * https://www.dgii.gov.do/
 * https://dgii.gov.do/workshopProveedoresTI-eCE/Documents/Norma05-19.pdf
 * https://dgii.gov.do/cicloContribuyente/facturacion/comprobantesFiscales/Paginas/tiposComprobantes.aspx

>>> validate('E310000000005')  # formato desde 2019-04-08
'E310000000005'
>>> validate('B0100000005')  # formato desde 2018-05-01
'B0100000005'
>>> validate('A020010210100000005')  # formato antes de 2018-05-01
'A020010210100000005'
>>> validate('Z0100000005')
Traceback (most recent call last):
    ...
InvalidFormat: ...
"""

from stdnum.exceptions import *
from stdnum.util import clean, isdigits
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import requests
import time
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# Suppress InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def compact(number):
    """Convierte el número a su representación mínima. Esto elimina
    cualquier separador válido y los espacios en blanco circundantes."""
    return clean(number, ' ').strip().upper()


# Los siguientes tipos de documentos son conocidos:
_ncf_document_types = (
    '01',  # facturas para declaración fiscal
    '02',  # facturas para consumidor final
    '03',  # nota de débito
    '04',  # nota de crédito (reembolsos)
    '11',  # facturas de proveedores informales (compras)
    '12',  # facturas de ingresos únicos
    '13',  # facturas de gastos menores (compras)
    '14',  # facturas para clientes especiales (turistas, zonas francas)
    '15',  # facturas para el gobierno
    '16',  # facturas para exportación
    '17',  # facturas para pagos en el extranjero
)

_ecf_document_types = (
    '31',  # facturas para declaración fiscal
    '32',  # facturas para consumidor final
    '33',  # nota de débito
    '34',  # nota de crédito (reembolsos)
    '41',  # facturas de proveedores (compras)
    '43',  # facturas de gastos menores (compras)
    '44',  # facturas para clientes especiales (turistas, zonas francas)
    '45',  # facturas para el gobierno
    '46',  # facturas para exportación
    '47',  # facturas para pagos en el extranjero
)


def validate(number):
    """Verifica si el número proporcionado es un NCF válido."""
    number = compact(number)
    if len(number) == 13:
        if number[0] != 'E' or not isdigits(number[1:]):
            raise InvalidFormat()
        if number[1:3] not in _ecf_document_types:
            raise InvalidComponent()
    elif len(number) == 11:
        if number[0] != 'B' or not isdigits(number[1:]):
            raise InvalidFormat()
        if number[1:3] not in _ncf_document_types:
            raise InvalidComponent()
    elif len(number) == 19:
        if number[0] not in 'AP' or not isdigits(number[1:]):
            raise InvalidFormat()
        if number[9:11] not in _ncf_document_types:
            raise InvalidComponent()
    else:
        raise InvalidLength()
    return number


def is_valid(number):
    """Verifica si el número proporcionado es un NCF válido."""
    try:
        return bool(validate(number))
    except ValidationError:
        return False


def _convert_result(result):
    """Translate SOAP result entries into dictionaries."""
    translation = {
        'NOMBRE': 'name',
        'COMPROBANTE': 'proof',
        'ES_VALIDO': 'is_valid',
        'MENSAJE_VALIDACION': 'validation_message',
        'RNC': 'rnc',
        'NCF': 'ncf',
        u'RNC / Cédula': 'rnc',
        u'RNC/Cédula': 'rnc',
        u'Nombre / Razón Social': 'name',
        u'Nombre/Razón Social': 'name',
        'Estado': 'status',
        'Tipo de comprobante': 'type',
        u'Válido hasta': 'valid_until',
        u'Código de Seguridad': 'security_code',
        'Rnc Emisor': 'issuing_rnc',
        'Rnc Comprador': 'buyer_rnc',
        'Monto Total': 'total',
        'Total de ITBIS': 'total_itbis',
        'Fecha Emisi&oacuten': 'issuing_date',
        u'Fecha Emisión': 'issuing_date',
        u'Fecha de Firma': 'signature_date',
        'e-NCF': 'ncf',
    }
    return {translation.get(key, key): value for key, value in result.items()}


def _get_form_parameters(document):
    """Extracts necessary form parameters from the HTML document."""
    return {
        '__EVENTVALIDATION': document.find('.//input[@name="__EVENTVALIDATION"]').get('value'),
        '__VIEWSTATE': document.find('.//input[@name="__VIEWSTATE"]').get('value'),
        '__VIEWSTATEGENERATOR': document.find('.//input[@name="__VIEWSTATEGENERATOR"]').get('value'),
    }


def _parse_result(document, ncf):
    """Parses the HTML document to extract the result."""
    result_path = './/div[@id="cphMain_PResultadoFE"]' if ncf.startswith(
        'E') else './/div[@id="cphMain_pResultado"]'
    result = document.find(result_path)

    if result is not None:
        lbl_path = './/*[@id="cphMain_lblEstadoFe"]' if ncf.startswith(
            'E') else './/*[@id="cphMain_lblInformacion"]'
        data = {
            'validation_message': document.findtext(lbl_path).strip(),
        }
        data.update({
            key.text.strip(): value.text.strip()
            for key, value in zip(result.findall('.//th'), result.findall('.//td/span'))
            if key.text and value.text
        })
        return _convert_result(data)

    return None


def _build_post_data(rnc, ncf, form_params, buyer_rnc=None, security_code=None):
    """Builds the data dictionary for the POST request."""
    data = {
        **form_params,
        '__ASYNCPOST': "true",
        'ctl00$smMain': 'ctl00$upMainMaster|ctl00$cphMain$btnConsultar',
        'ctl00$cphMain$btnConsultar': 'Buscar',
        'ctl00$cphMain$txtNCF': ncf,
        'ctl00$cphMain$txtRNC': rnc,
    }

    if ncf.startswith('E'):
        data['ctl00$cphMain$txtRncComprador'] = buyer_rnc
        data['ctl00$cphMain$txtCodigoSeg'] = security_code

    return data


def check_dgii(rnc, ncf, buyer_rnc=None, security_code=None, timeout=30):  # pragma: no cover
    """Valida la combinación de RNC y NCF utilizando el servicio web en línea de la DGII.

    Esto utiliza el servicio de validación proporcionado por la Dirección General de
    Impuestos Internos (DGII) de la República Dominicana para verificar si la combinación 
    de RNC y NCF es válida. El tiempo de espera es en segundos.

    Retorna un diccionario con la siguiente estructura para un NCF::

        {
            'name': 'El nombre registrado',
            'status': 'VIGENTE',
            'type': 'FACTURAS DE CREDITO FISCAL',
            'rnc': '123456789',
            'ncf': 'A020010210100000005',
            'validation_message': 'El NCF digitado es válido.',
        }

    Para un ECNF::

        {
            'status': 'Aceptado',
            'issuing_rnc': '1234567890123',
            'buyer_rnc': '123456789',
            'ncf': 'E300000000000',
            'security_code': '1+2kP3',
            'issuing_date': '2020-03-25',
            'signature_date': '2020-03-22',
            'total': '2203.50',
            'total_itbis': '305.10',
            'validation_message': 'Aceptado',
        }

    Retorna None si el número es inválido o desconocido."""
    import lxml.html
    import requests
    from stdnum.do.rnc import compact as rnc_compact  # noqa: I003
    rnc = rnc_compact(rnc)
    ncf = compact(ncf)
    if buyer_rnc:
        buyer_rnc = rnc_compact(buyer_rnc)
    url = 'https://dgii.gov.do/app/WebApps/ConsultasWeb2/ConsultasWeb/consultas/ncf.aspx'
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (python-stdnum)',
    })

    # Configurar retries para la sesión
    retries = Retry(
        total=5,  # Número total de reintentos
        backoff_factor=0.5,  # Tiempo de espera entre reintentos (exponencial)
        # Retrys solo en estos códigos de estado
        status_forcelist=[500, 502, 503, 504],
        raise_on_status=False  # No levantar excepción si el status no es exitoso
    )
    session.mount('https://', HTTPAdapter(max_retries=retries))

    response = session.get(url, timeout=timeout, verify=False)
    response.raise_for_status()
    document = lxml.html.fromstring(response.text)

    # Extract necessary form parameters
    form_params = _get_form_parameters(document)

    # Build data for the POST request
    post_data = _build_post_data(
        rnc, ncf, form_params, buyer_rnc, security_code)
    # Obtén la página para obtener los parámetros necesarios del formulario
    # Do the actual request
    response = session.post(url, data=post_data, timeout=timeout, verify=False)
    response.raise_for_status()
    document = lxml.html.fromstring(response.text)

    # Parse and return the result
    return _parse_result(document, ncf)
