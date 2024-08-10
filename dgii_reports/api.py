import frappe
import os
import zipfile
import pandas as pd

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

