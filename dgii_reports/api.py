import frappe
import os
import zipfile
import pandas as pd

# def get_tax_amount_for(doctype, docname, tax_type):
# 	doc = frappe.get_doc(doctype, docname)

# 	for row in doc.taxes:
# 		tax_types = row.meta.get_field("tax_type").options
		
# 		if not tax_type in tax_types.split("\n"):
# 			frappe.throw(_("The tax type provided was not found in the system!"))

# 		if row.tax_type == tax_type:
# 			return row.tax_amount

# 	return 0.000
	
# def update_taxes_to_purchases():
# 	from dgii.hook.purchase_invoice import validate
# 	for name, in frappe.get_list("Purchase Invoice", as_list=True):
# 		doc = frappe.get_doc("Purchase Invoice", name )
# 		validate(doc, {})
# 		if doc.excise_tax or doc.legal_tip:
# 			doc.db_update()
# 			# print(
# 			# 	"""Added to {name}\n
# 			# 		\tExcise:{excise_tax}
# 			# 		\tLegal:{legal_tip} """.format(**doc.as_dict())
# 			# )

# @frappe.whitelist()
# def validate_ncf_limit(serie):
# 	# serie : ABC.####
# 	# next: 3
# 	# Yefri este codigo es provisional, reservar cualquier comentario gracias!

# 	limit = frappe.get_doc("NCF",{"serie":serie}, "max_limit").max_limit
# 	serie = serie.replace(".","").replace("#","")
# 	current = frappe.get_doc("Series",{"name":serie},"current").current
	
# 	return True if  current + 1  <  limit else False


# ------------------------------------------------------------------------------------------
# Define una función para obtener los detalles del RNC desde la URL
# ------------------------------------------------------------------------------------------
# @frappe.whitelist()
# def get_rnc_details(tax_id):
#     # url = "https://dgii.gov.do/app/WebApps/ConsultasWeb2/ConsultasWeb/consultas/rnc.aspx"
#     url="https://dgii.gov.do/app/WebApps/ConsultasWeb/consultas/rnc.aspx"
#     headers = {
#         "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
#     }

#     # Paso 1: Realizar una solicitud GET para obtener el HTML y extraer los valores dinámicos
#     try:
#         response = requests.get(url, timeout=100)
#         response.raise_for_status()  # Lanza un error para códigos de estado HTTP 4xx/5xx
#         print(response.status_code)
#         print(response.text[:200])  # Muestra solo los primeros 200 caracteres para verificar
#         soup = BeautifulSoup(response.content, 'html.parser')

#         # Extraer los valores de __VIEWSTATE, __VIEWSTATEGENERATOR y __EVENTVALIDATION
#         viewstate = soup.find('input', {'name': '__VIEWSTATE'})['value']
#         viewstategenerator = soup.find('input', {'name': '__VIEWSTATEGENERATOR'})['value']
#         eventvalidation = soup.find('input', {'name': '__EVENTVALIDATION'})['value']

#         # Paso 2: Preparar el payload para la solicitud POST
#         payload = {
#             "ctl00$smMain": "ctl00$cphMain$upBusqueda|ctl00$cphMain$btnBuscarPorRNC",
#             "ctl00$cphMain$txtRNCCedula": tax_id,
#             "ctl00$cphMain$btnBuscarPorRNC": "BUSCAR",
#             "__VIEWSTATE": viewstate,
#             "__VIEWSTATEGENERATOR": viewstategenerator,
#             "__EVENTVALIDATION": eventvalidation,
#             "__ASYNCPOST": True
#         }

#         # Paso 3: Realizar la solicitud POST con el payload actualizado
#         response = requests.post(url, headers=headers, data=payload, timeout=100)
#         response.raise_for_status()  # Lanza un error para códigos de estado HTTP 4xx/5xx

#         if response.status_code == 200:
#             soup = BeautifulSoup(response.content, 'html.parser')
#             table = soup.find('table', id='cphMain_dvDatosContribuyentes')

#             if table and len(list(table.children)) > 1:
#                 company_name = table.find_all('tr')[1].find_all('td')[1].text
#                 brand_name = table.find_all('tr')[2].find_all('td')[1].text
#                 status = table.find_all('tr')[5].find_all('td')[1].text

#                 return {
#                     "tax_id": tax_id,
#                     "company_name": company_name,
#                     "brand_name": brand_name,
#                     "status": status
#                 }
#             else:
#                 return {}
#         else:
#             return {}
#     except requests.exceptions.RequestException as e:
#         print(f"Request failed: {e}")
#         return {}

# ------------------------------------------------------------------------------------------
# Define una función para obtener los detalles del RNC desde el archivo local ZIP
# ------------------------------------------------------------------------------------------
# @frappe.whitelist()
# def get_rnc_details(tax_id):
#     # Función para eliminar espacios extra intermedios y al inicio/final de cada campo
#     def clean_spaces(s):
#         return ' '.join(s.split())

#     # Obtenemos el directorio del archivo actual
#     current_dir = os.path.dirname(os.path.abspath(__file__))
#     # Construimos el path relativo para el archivo ZIP 
#     zip_path = os.path.join(current_dir, 'DGII_RNC.zip')
#     output_path = os.path.join(current_dir, 'processed_lines.txt')
#     print("\nZIP Path:", zip_path)  # Imprimimos para debuggear

#     try:
#         with zipfile.ZipFile(zip_path, 'r') as thezip:
#             print("Inside the first with")  # Imprimimos para debuggear
#             for zipinfo in thezip.infolist():
#                 # Verificamos si el archivo está en el directorio TMP 
#                 if zipinfo.filename.startswith('TMP/') and zipinfo.filename.endswith('.TXT'):
#                     with thezip.open(zipinfo) as thefile:
#                         # Leemos el archivo como archivo de texto
#                         lines = thefile.read().decode('latin1').splitlines()[:55]
                        
#                         # Especificamos las columnas de manera manual
#                         columns = [
#                             'RNC_CEDULA', 'NOMBRE_COMERCIAL', 'RAZON_SOCIAL', 'ACTIVIDAD_ECONOMICA', 
#                             'DIRECCION', 'TELEFONO', 'FAX', 'EMAIL', 'FECHA_INSCRIPCION', 'ESTATUS', 'TIPO'
#                         ]
                        
#                         # Creamos una lista para almacenar las líneas procesadas
#                         processed_lines = []
                        
#                         for line in lines:
#                             parts = line.split('|')
                            
#                             # Aseguramos que haya exactamente 11 campos
#                             while len(parts) < 11:
#                                 parts.append('')
#                             parts = parts[:11]
                            
#                             # Limpiamos espacios extra dentro de cada campo
#                             parts = [clean_spaces(part) for part in parts]
                            
#                             # Combinamos descripciones de actividad si es necesario
#                             if len(parts[3]) > 0 and len(parts[4]) > 0:
#                                 parts[3] = f"{parts[3]} {parts[4]}".strip()
#                                 parts[4] = ''
                            
#                             processed_lines.append(parts)
                        
#                         # Guardamos las primeras 55 líneas procesadas en un nuevo archivo, preservando el orden original
#                         with open(output_path, 'w', encoding='latin1') as outfile:
#                             for processed_line in processed_lines:
#                                 outfile.write('|'.join(processed_line) + '\n')
                        
#                         print(f"Processed lines saved to {output_path}")

#                         # Buscamos el registro correspondiente al tax_id
#                         for parts in processed_lines:
#                             if parts[0] == tax_id:
#                                 company_name = parts[1]
#                                 brand_name = parts[2]
#                                 status = parts[9]
                                
#                                 return {
#                                     "tax_id": tax_id,
#                                     "company_name": company_name,
#                                     "brand_name": brand_name,
#                                     "status": status
#                                 }
                        
#                         return {
#                             "error": "Tax ID not found"
#                         }
#     except Exception as e:
#         return {
#             "error": f"An error occurred: {str(e)}"
#         }

@frappe.whitelist()
def get_rnc_details(tax_id):
    # Obtenemos el directorio del archivo actual
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Construimos el path relativo para el archivo ZIP 
    zip_path = os.path.join(current_dir, 'DGII_RNC.zip')
    print("\nZIP Path:", zip_path)  # Imprimimos para debuggear

    try:
        with zipfile.ZipFile(zip_path, 'r') as thezip:
            print("Inside the first with")  # Imprimimos para debuggear
            for zipinfo in thezip.infolist():
                # Verificamos si el archivo está en el directorio TMP 
                if zipinfo.filename.startswith('TMP/') and zipinfo.filename.endswith('.TXT'):
                    with thezip.open(zipinfo) as thefile:
                        # Leemos el archivo como archivo de texto
                        lines = thefile.read().decode('latin1').splitlines()
                        
                        # Especificamos las columnas de manera manual
                        columns = [
                            'RNC_CEDULA', 'NOMBRE_COMERCIAL', 'RAZON_SOCIAL', 'ACTIVIDAD_ECONOMICA', 
                            'DIRECCION', 'TELEFONO', 'FAX', 'EMAIL', 'FECHA_INSCRIPCION', 'ESTATUS', 'TIPO'
                        ]
                        
                        # Creamos una lista para almacenar las líneas procesadas
                        data = [line.split('|') for line in lines]
                        
                        # Aseguramos que cada línea tenga exactamente 11 columnas
                        for i in range(len(data)):
                            while len(data[i]) < 11:
                                data[i].append('')
                            data[i] = data[i][:11]
                        
                        # Creamos un DataFrame
                        df = pd.DataFrame(data, columns=columns)
                        
                        # Limpiamos y normalizamos la data (eliminar espacios extra intermedios, etc.)
                        df = df.applymap(lambda x: ' '.join(x.split()) if isinstance(x, str) else x)
                        
                        # Buscamos el registro correspondiente al tax_id
                        result = df[df['RNC_CEDULA'] == tax_id]
                        
                        if not result.empty:
                            company_name = result.iloc[0]['NOMBRE_COMERCIAL']
                            brand_name = result.iloc[0]['RAZON_SOCIAL']
                            status = result.iloc[0]['ESTATUS']
                            
                            return {
                                "tax_id": tax_id,
                                "company_name": company_name,
                                "brand_name": brand_name,
                                "status": status
                            }
                        else:
                            return {
                                "error": "Tax ID not found"
                            }
    except Exception as e:
        return {
            "error": f"Ocurrió un error: {str(e)}"
        }

