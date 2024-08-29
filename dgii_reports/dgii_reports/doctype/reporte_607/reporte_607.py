# Copyright (c) 2024, TnologiaRD and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import cstr, cint, flt, formatdate, format_datetime
from frappe.model.document import Document
from frappe.utils.csvutils import UnicodeWriter
import time

class Reporte607(Document):
	pass


@frappe.whitelist()
def validate_pending_invoices(from_date, to_date):
    draft_invoices = frappe.db.sql("""
        SELECT 
            COUNT(*) 
        FROM 
            `tabSales Invoice` 
        WHERE 
            docstatus = 0 AND posting_date BETWEEN '%s' AND '%s'
    """ % (from_date, to_date))

    if draft_invoices[0][0] > 0:
        frappe.log_error("Facturas pendientes encontradas", "validate_pending_invoices")
        return {"message": "Hay facturas de venta pendientes de procesar. Por favor, complete las facturas pendientes antes de generar el reporte."}
    
    frappe.log_error("No hay facturas pendientes", "validate_pending_invoices")
    return {"message": ""}


@frappe.whitelist()
def get_file_address(from_date, to_date):
    # Obtener los datos para el reporte
    result = frappe.db.sql("""
        SELECT 
            cust.tax_id, 
            sinv.custom_ncf as ncf, 
            sinv.posting_date, 
            sinv.base_total_taxes_and_charges, 
            sinv.custom_tipo_de_ingreso as tipo_de_ingreso, 
            sinv.base_total 
        FROM 
            `tabSales Invoice` AS sinv 
        JOIN 
            tabCustomer AS cust on sinv.customer = cust.name 
        WHERE 
            sinv.custom_ncf NOT LIKE '%s' AND sinv.docstatus = 1 AND sinv.posting_date BETWEEN '%s' AND '%s'
    """ % ("SINV-%", from_date, to_date), as_dict=True)

    # Generar el archivo CSV
    w = UnicodeWriter()
    w.writerow(['RNC', 'Tipo de RNC', 'NCF', 'NCF modificado', 'Fecha de impresion', 'ITBIS facturado', 'Tipo de Ingreso', 'Monto Total'])
        
    for row in result:
        tipo_rnc = frappe.get_value("Customer", {"tax_id": row.tax_id }, ["custom_tipo_rnc"])
        w.writerow([row.tax_id.replace("-", "") if row.tax_id else "", tipo_rnc, row.ncf, "", row.posting_date.strftime("%Y%m%d"), row.base_total_taxes_and_charges, row.tipo_de_ingreso, row.base_total])

    # Devolver el contenido del archivo CSV
    frappe.response['result'] = cstr(w.getvalue())
    frappe.response['type'] = 'csv'
    frappe.response['doctype'] = "Reporte_607_" + str(int(time.time()))
