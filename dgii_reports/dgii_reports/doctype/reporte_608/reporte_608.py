# Copyright (c) 2024, TnologiaRD and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import cstr, cint, flt, formatdate, format_datetime
from frappe.model.document import Document
from frappe.utils.csvutils import UnicodeWriter
import time
from datetime import datetime


class Reporte608(Document):
	pass

@frappe.whitelist()
def validate_pending_invoices(from_date, to_date):
    # Consulta para facturas de venta
    draft_sales_invoices = frappe.db.sql("""
        SELECT 
            COUNT(*) 
        FROM 
            `tabSales Invoice` 
        WHERE 
            docstatus = 0 AND posting_date BETWEEN '%s' AND '%s'
    """ % (from_date, to_date))

    # Consulta para facturas de compra
    draft_purchase_invoices = frappe.db.sql("""
        SELECT 
            COUNT(*) 
        FROM 
            `tabPurchase Invoice` 
        WHERE 
            docstatus = 0 AND posting_date BETWEEN '%s' AND '%s'
    """ % (from_date, to_date))

    # Sumar los resultados de ambas consultas
    total_draft_invoices = draft_sales_invoices[0][0] + draft_purchase_invoices[0][0]

    if total_draft_invoices > 0:
        frappe.log_error("Facturas pendientes encontradas", "validate_pending_invoices")
        return {"message": "Hay facturas de venta o compra pendientes de procesar. Por favor, complete las facturas pendientes antes de generar el reporte."}
    
    frappe.log_error("No hay facturas pendientes", "validate_pending_invoices")
    return {"message": ""}

@frappe.whitelist()
def get_file_address(from_date, to_date, decimal_places=2):
    # Obtener el tax_id del doctype Company
    company = frappe.get_doc("Company", frappe.defaults.get_user_default("Company"))
    rnc = company.tax_id.replace("-", "") if company.tax_id else ""

    # Calcular el periodo
    from_date_obj = datetime.strptime(from_date, "%Y-%m-%d")
    to_date_obj = datetime.strptime(to_date, "%Y-%m-%d")
    periodo = f"{from_date_obj.year}{min(from_date_obj.month, to_date_obj.month):02d}"

    # Consulta SQL para obtener los datos necesarios
    query = """
        SELECT 
            sinv.custom_ncf as ncf, 
            sinv.posting_date as fecha_comprobante,
            sinv.custom_codigo_de_anulacion as tipo_anulacion  -- Recuperar la columna codigo de la tabla tabTipo de Anulacion
        FROM 
            `tabSales Invoice` AS sinv 
        WHERE 
            sinv.docstatus = 2 AND sinv.posting_date BETWEEN %(from_date)s AND %(to_date)s

        UNION

        SELECT 
            pinv.bill_no as ncf, 
            pinv.posting_date as fecha_comprobante,
            pinv.custom_codigo_de_anulacion as tipo_anulacion  -- Recuperar la columna codigo de la tabla tabTipo de Anulacion
        FROM 
            `tabPurchase Invoice` AS pinv 
        WHERE 
            pinv.docstatus = 2 AND pinv.posting_date BETWEEN %(from_date)s AND %(to_date)s
            AND (pinv.bill_no LIKE 'B13%%' OR pinv.bill_no LIKE 'B11%%')
    """
    # Ejecutar la consulta
    result = frappe.db.sql(query, {"from_date": from_date, "to_date": to_date}, as_dict=True)    # Número de registros
    numero_registros = len(result)

    # Crear el archivo en memoria usando UnicodeWriter
    w = UnicodeWriter()

    # Agregar la primera línea
    w.writerow([
        "608", 
        rnc, 
        periodo, 
        numero_registros
    ])

    for row in result:
        w.writerow([
            row.ncf, 
            row.fecha_comprobante.strftime("%Y%m%d") if row.fecha_comprobante else "", 
            row.tipo_anulacion
        ])

    # Convertir el contenido a texto con delimitador de pipes
    content = w.getvalue().replace(",", "|").replace('"', '')

    # Devolver el contenido del archivo de texto como descarga
    frappe.response['filename'] = "Reporte_607_%s.txt" % time.strftime("%Y%m%d_%H%M%S")
    frappe.response['filecontent'] = content
    frappe.response['type'] = 'download'