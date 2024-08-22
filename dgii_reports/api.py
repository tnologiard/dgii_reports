import frappe
from dgii_reports.servicios.consultas_web_dgii import ServicioConsultasWebDgii

@frappe.whitelist()
def get_rnc_details(tax_id):
    try:
        servicio = ServicioConsultasWebDgii()
        respuesta = servicio.consultar_rnc_contribuyentes(tax_id)
        if respuesta.success:        
            return {
                "tax_id": tax_id,
                "company_name": respuesta.nombre_o_razon_social,
                "brand_name": respuesta.nombre_comercial,
                "status": respuesta.estado
            }
        else:
            return {
                "error": "No se pudo obtener información para el RNC proporcionado."
            }
    except Exception as e:
        frappe.log_error(message=str(e), title="Error en get_rnc_details")
        return {
            "error": f"Ocurrió un error: {str(e)}"
        }

@frappe.whitelist()
def get_ncf_details(ncf, rnc, my_rnc=None, sec_code=None, req_sec_code=False):
    try:
        servicio = ServicioConsultasWebDgii()
        respuesta = servicio.consultar_ncf(ncf, rnc, my_rnc=my_rnc, sec_code=sec_code, req_sec_code=req_sec_code)
        
        if respuesta.success:
            return {
                "rnc_o_cedula": respuesta.rnc_o_cedula,
                "nombre_o_razon_social": respuesta.nombre_o_razon_social,
                "tipo_de_comprobante": respuesta.tipo_de_comprobante,
                "ncf": respuesta.ncf,
                "estado": respuesta.estado,
                "valido_hasta": respuesta.valido_hasta                
            }
        else:
            return {
                "error": respuesta.message or "No se pudo obtener información para el NCF proporcionado."
            }
    except Exception as e:
        frappe.log_error(message=str(e), title="Error en get_ncf_details")
        return {
            "error": f"Ocurrió un error: {str(e)}"
        }
