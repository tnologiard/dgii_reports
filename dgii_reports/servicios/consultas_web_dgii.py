import requests
from lxml import html

class RespuestaConsultaRncContribuyentes:
    def __init__(self, cedula_o_rnc='', nombre_o_razon_social='', nombre_comercial='', categoria='', regimen_de_pagos='', estado='', actividad_economica='', administracion_local='', success=False, message=''):
        self.cedula_o_rnc = cedula_o_rnc
        self.nombre_o_razon_social = nombre_o_razon_social
        self.nombre_comercial = nombre_comercial
        self.categoria = categoria
        self.regimen_de_pagos = regimen_de_pagos
        self.estado = estado
        self.actividad_economica = actividad_economica
        self.administracion_local = administracion_local
        self.success = success
        self.message = message

class RespuestaConsultaRncRegistrados:
    def __init__(self, nombre='', estado='', tipo='', rnc_o_cedula='', actividad='', success=False, message=''):
        self.nombre = nombre
        self.estado = estado
        self.tipo = tipo
        self.rnc_o_cedula = rnc_o_cedula
        self.actividad = actividad
        self.success = success
        self.message = message

class RespuestaConsultaNcf:
    def __init__(self, rnc_o_cedula='', nombre_o_razon_social='', tipo_de_comprobante='', ncf='', estado='', valido_hasta='', success=False, message=''):
        self.rnc_o_cedula = rnc_o_cedula
        self.nombre_o_razon_social = nombre_o_razon_social
        self.tipo_de_comprobante = tipo_de_comprobante
        self.ncf = ncf
        self.estado = estado
        self.valido_hasta = valido_hasta
        self.success = success
        self.message = message

class ServicioConsultasWebDgii:
    REQUEST_URL_CONSULTA_RNC = "https://dgii.gov.do/app/WebApps/ConsultasWeb2/ConsultasWeb/consultas/rnc.aspx"
    REQUEST_URL_CONSULTA_CIUDADANOS = "https://dgii.gov.do/app/WebApps/ConsultasWeb2/ConsultasWeb/consultas/ciudadanos.aspx"
    REQUEST_URL_CONSULTA_NCF = "https://dgii.gov.do/app/WebApps/ConsultasWeb2/ConsultasWeb/consultas/ncf.aspx"

    def _load_page(self, request_url, session):
        response = session.get(request_url)
        response.raise_for_status()
        return html.fromstring(response.content)

    def _post_data(self, request_url, form_data, session):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Referer': request_url
        }

        try:
            response = session.post(request_url, data=form_data, headers=headers, timeout=60)
            response.raise_for_status()

            # Imprimir el contenido de la respuesta
            # print("Respuesta del servidor:")
            # print(response.text)

            # Analizar el contenido HTML
            x_document = html.fromstring(response.content)

            # Ejemplo de impresión del contenido de una etiqueta específica
            # print("Contenido de la etiqueta <title>:")
            # title = x_document.xpath('//title/text()')
            # print(title[0] if title else 'No se encontró la etiqueta <title>')

            # Imprimir todo el HTML formateado
            # print("HTML formateado:")
            # print(html.tostring(x_document, pretty_print=True).decode())

            return x_document
        except requests.exceptions.Timeout:
            print("La solicitud ha superado el tiempo de espera.")
            raise
        except requests.exceptions.RequestException as e:
            print(f"Error en la solicitud: {e}")
            raise

    def consultar_rnc_registrados(self, rnc_o_cedula):
        session = requests.Session()

        html_document = self._load_page(self.REQUEST_URL_CONSULTA_CIUDADANOS, session)

        viewstate = html_document.xpath("//input[@name='__VIEWSTATE']/@value")[0]
        eventvalidation = html_document.xpath("//input[@name='__EVENTVALIDATION']/@value")[0]
        viewstategenerator = html_document.xpath("//input[@name='__VIEWSTATEGENERATOR']/@value")[0]

        form_data = {
            "ctl00$smMain": "ctl00$cphMain$upBusqueda|ctl00$cphMain$btnBuscarCedula",
            "ctl00$cphMain$txtCedula": rnc_o_cedula,
            "ctl00$cphMain$txtRazonSocial": "",
            "__EVENTTARGET": "",
            "__EVENTARGUMENT": "",
            "__VIEWSTATEGENERATOR": viewstategenerator,
            "__VIEWSTATE": viewstate,
            "__EVENTVALIDATION": eventvalidation,
            "__ASYNCPOST": "true",
            "ctl00$cphMain$btnBuscarCedula": "Buscar"
        }

        x_document = self._post_data(self.REQUEST_URL_CONSULTA_CIUDADANOS, form_data, session)

        response = RespuestaConsultaRncRegistrados()
        if x_document.xpath("//*[@id='cphMain_dvResultadoCedula']//tr[1]/td[2]"):
            response.nombre = x_document.xpath("//*[@id='cphMain_dvResultadoCedula']//tr[1]/td[2]/text()")[0].strip()
            response.estado = x_document.xpath("//*[@id='cphMain_dvResultadoCedula']//tr[2]/td[2]/text()")[0].strip()
            response.tipo = x_document.xpath("//*[@id='cphMain_dvResultadoCedula']//tr[3]/td[2]/text()")[0].strip()
            response.rnc_o_cedula = x_document.xpath("//*[@id='cphMain_dvResultadoCedula']//tr[4]/td[2]/text()")[0].strip()
            response.actividad = x_document.xpath("//*[@id='cphMain_dvResultadoCedula']//tr[5]/td[2]/text()")[0].strip()
            response.success = True
        else:
            response.message = x_document.xpath("//*[@id='cphMain_divAlertDanger']/text()")[0]

        return response

    def consultar_rnc_contribuyentes(self, rnc_o_cedula):
        session = requests.Session()

        html_document = self._load_page(self.REQUEST_URL_CONSULTA_RNC, session)

        viewstate = html_document.xpath("//input[@name='__VIEWSTATE']/@value")[0]
        eventvalidation = html_document.xpath("//input[@name='__EVENTVALIDATION']/@value")[0]
        viewstategenerator = html_document.xpath("//input[@name='__VIEWSTATEGENERATOR']/@value")[0]

        form_data = {
            "ctl00$smMain": "ctl00$cphMain$upBusqueda|ctl00$cphMain$btnBuscarPorRNC",
            "ctl00$cphMain$txtRNCCedula": rnc_o_cedula,
            "ctl00$cphMain$txtRazonSocial": "",
            "__EVENTTARGET": "",
            "__EVENTARGUMENT": "",
            "__VIEWSTATEGENERATOR": viewstategenerator,
            "__VIEWSTATE": viewstate,
            "__EVENTVALIDATION": eventvalidation,
            "__ASYNCPOST": "true",
            "ctl00$cphMain$btnBuscarPorRNC": "BUSCAR"
        }

        x_document = self._post_data(self.REQUEST_URL_CONSULTA_RNC, form_data, session)

        response = RespuestaConsultaRncContribuyentes()
        if x_document.xpath("//*[@id='cphMain_dvDatosContribuyentes']//tr"):
            response.cedula_o_rnc = x_document.xpath("//tr[1]/td[2]/text()")[0].strip()
            response.nombre_o_razon_social = x_document.xpath("//tr[2]/td[2]/text()")[0].strip()
            response.nombre_comercial = x_document.xpath("//tr[3]/td[2]/text()")[0].strip()
            response.categoria = x_document.xpath("//tr[4]/td[2]/text()")[0].strip()
            response.regimen_de_pagos = x_document.xpath("//tr[5]/td[2]/text()")[0].strip()
            response.estado = x_document.xpath("//tr[6]/td[2]/text()")[0].strip()
            response.actividad_economica = x_document.xpath("//tr[7]/td[2]/text()")[0].strip()
            response.administracion_local = x_document.xpath("//tr[8]/td[2]/text()")[0].strip()
            response.success = True
        else:
            response.message = x_document.xpath("//*[@id='cphMain_lblInformacion']/text()")[0]
        return response

    def consultar_ncf(self, ncf, rnc, my_rnc=None, sec_code=None, req_sec_code=False):
        session = requests.Session()

        html_document = self._load_page(self.REQUEST_URL_CONSULTA_NCF, session)

        viewstate = html_document.xpath("//input[@name='__VIEWSTATE']/@value")[0]
        eventvalidation = html_document.xpath("//input[@name='__EVENTVALIDATION']/@value")[0]
        viewstategenerator = html_document.xpath("//input[@name='__VIEWSTATEGENERATOR']/@value")[0]

        form_data = {
            "ctl00$smMain": "ctl00$upMainMaster|ctl00$cphMain$btnConsultar",
            "ctl00$cphMain$txtRNC": rnc,
            "ctl00$cphMain$txtNCF": ncf,
            "__EVENTTARGET": "",
            "__EVENTARGUMENT": "",
            "__VIEWSTATEGENERATOR": viewstategenerator,
            "__VIEWSTATE": viewstate,
            "__EVENTVALIDATION": eventvalidation,
            "__ASYNCPOST": "true",
            "ctl00$cphMain$btnConsultar": "Consultar"
        }
        if req_sec_code:
            if my_rnc:
                form_data["ctl00$cphMain$txtRncComprador"] = my_rnc
            if sec_code:
                form_data["ctl00$cphMain$txtCodigoSeg"] = sec_code

        x_document = self._post_data(self.REQUEST_URL_CONSULTA_NCF, form_data, session)

        response = RespuestaConsultaNcf()
        if x_document.xpath("//tr[1]/td/span/text()"):
            response.rnc_o_cedula = x_document.xpath("//tr[1]/td/span/text()")[0].strip()
            response.nombre_o_razon_social = x_document.xpath("//tr[2]/td/span/text()")[0].strip()
            response.tipo_de_comprobante = x_document.xpath("//tr[3]/td/span/text()")[0].strip()
            response.ncf = x_document.xpath("//tr[4]/td/span/text()")[0].strip()
            response.estado = x_document.xpath("//tr[5]/td/span/text()")[0].strip()
            response.valido_hasta = x_document.xpath("//tr[6]/td/span/text()")[0].strip()
            response.success = True
        else:
            response.message = x_document.xpath("//*[@id='cphMain_lblInformacion']/text()")[0]

        return response
