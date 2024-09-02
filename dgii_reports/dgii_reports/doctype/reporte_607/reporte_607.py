# Copyright (c) 2024, TnologiaRD and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import cstr, cint, flt, formatdate, format_datetime
from frappe.model.document import Document
from frappe.utils.csvutils import UnicodeWriter
import time
from datetime import datetime

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
        cust.tax_id, 
        cust.custom_tipo_rnc as tipo_identificacion,
        sinv.custom_ncf as ncf, 
        sinv.custom_return_against_ncf as ncf_modificado,
        tipo_ing.codigo as tipo_de_ingreso,  -- Recuperar la columna codigo de la tabla tabTipo de Ingreso
        sinv.posting_date as fecha_comprobante, 
        sinv.due_date as fecha_retencion,
        sinv.base_total as monto_facturado, 
        sinv.base_total_taxes_and_charges as itbis_facturado,
        '' as itbis_retenido_terceros,  -- No disponible en la tabla
        '' as itbis_percibido,  -- No disponible en la tabla
        '' as retencion_renta_terceros,  -- No disponible en la tabla
        '' as isr_percibido,  -- No disponible en la tabla
        '' as impuesto_selectivo_consumo,  -- No disponible en la tabla
        '' as otros_impuestos_tasas,  -- No disponible en la tabla
        '' as monto_propina_legal,  -- No disponible en la tabla
        CASE WHEN COALESCE(SUM(CASE WHEN pe.mode_of_payment = 'Efectivo' THEN pe.paid_amount ELSE 0 END), 0) = 0 THEN '' ELSE COALESCE(SUM(CASE WHEN pe.mode_of_payment = 'Efectivo' THEN pe.paid_amount ELSE 0 END), 0) END as efectivo,  -- Calcular el total de pagos con Modo de Pago Efectivo
        CASE WHEN COALESCE(SUM(CASE WHEN pe.mode_of_payment = 'Transferencia bancaria' THEN pe.paid_amount ELSE 0 END), 0) = 0 THEN '' ELSE COALESCE(SUM(CASE WHEN pe.mode_of_payment = 'Transferencia bancaria' THEN pe.paid_amount ELSE 0 END), 0) END as cheque_transferencia_deposito,  -- Calcular el total de pagos con Modo de Pago Transferencia bancaria
        CASE WHEN COALESCE(SUM(CASE WHEN pe.mode_of_payment = 'Tarjetas de credito' THEN pe.paid_amount ELSE 0 END), 0) = 0 THEN '' ELSE COALESCE(SUM(CASE WHEN pe.mode_of_payment = 'Tarjetas de credito' THEN pe.paid_amount ELSE 0 END), 0) END as tarjeta_debito_credito,  -- Calcular el total de pagos con Modo de Pago Tarjetas de credito
        '' as venta_credito,  -- No disponible en la tabla
        '' as bonos_certificados_regalo,  -- No disponible en la tabla
        '' as permuta,  -- No disponible en la tabla
        '' as otras_formas_ventas  -- No disponible en la tabla
    FROM 
        `tabSales Invoice` AS sinv 
    JOIN 
        tabCustomer AS cust on sinv.customer = cust.name 
    LEFT JOIN 
        `tabPayment Entry Reference` AS per ON per.reference_name = sinv.name
    LEFT JOIN 
        `tabPayment Entry` AS pe ON pe.name = per.parent
    LEFT JOIN 
        `tabTipo de Ingreso` AS tipo_ing ON sinv.custom_tipo_de_ingreso = tipo_ing.tipo_de_ingreso
    WHERE 
        sinv.custom_ncf NOT LIKE 'SINV-%%' AND sinv.docstatus = 1 AND sinv.posting_date BETWEEN %(from_date)s AND %(to_date)s
    GROUP BY 
        sinv.name
    """

    # Ejecutar la consulta
    result = frappe.db.sql(query, {"from_date": from_date, "to_date": to_date}, as_dict=True)

    # Número de registros
    numero_registros = len(result)

    # Crear el archivo en memoria usando UnicodeWriter
    w = UnicodeWriter()

    # Agregar la primera línea
    w.writerow([
        "607", 
        rnc, 
        periodo, 
        numero_registros
    ])

    def format_amount(amount):
        if amount == '':
            return amount
        try:
            amount = abs(float(amount))  # Convertir a valor absoluto
        except ValueError:
            return amount
        if amount == int(amount):
            return str(int(amount))
        else:
            return f"{amount:.{decimal_places}f}"
        
    for row in result:
        if row.tipo_identificacion == "RNC":
            tipo_identificacion = "1"
        elif row.tipo_identificacion == "Cédula":
            tipo_identificacion = "2"
        elif row.tipo_identificacion == "Pasaporte":
            tipo_identificacion = "3"
        else:
            tipo_identificacion = "2"  # Valor por defecto si no coincide con ninguno

        fecha_retencion = row.fecha_retencion.strftime("%Y%m%d") if row.fecha_retencion and row.retencion_renta_terceros not in ["", 0] else ""
        w.writerow([
            row.tax_id.replace("-", "") if row.tax_id else "", 
            tipo_identificacion, 
            row.ncf, 
            row.ncf_modificado, 
            int(row.tipo_de_ingreso),  # Convertir tipo_de_ingreso a entero
            row.fecha_comprobante.strftime("%Y%m%d") if row.fecha_comprobante else "", 
            fecha_retencion, 
            format_amount(row.monto_facturado), 
            format_amount(row.itbis_facturado), 
            row.itbis_retenido_terceros, 
            row.itbis_percibido, 
            row.retencion_renta_terceros, 
            row.isr_percibido, 
            row.impuesto_selectivo_consumo, 
            row.otros_impuestos_tasas, 
            row.monto_propina_legal, 
            format_amount(row.efectivo) if row.efectivo != 0 else "", 
            format_amount(row.cheque_transferencia_deposito) if row.cheque_transferencia_deposito != 0 else "", 
            format_amount(row.tarjeta_debito_credito) if row.tarjeta_debito_credito != 0 else "",
            row.venta_credito, 
            row.bonos_certificados_regalo, 
            row.permuta, 
            row.otras_formas_ventas
        ])

    # Convertir el contenido a texto con delimitador de pipes
    content = w.getvalue().replace(",", "|").replace('"', '')

    # Devolver el contenido del archivo de texto como descarga
    frappe.response['filename'] = "Reporte_607_%s.txt" % time.strftime("%Y%m%d_%H%M%S")
    frappe.response['filecontent'] = content
    frappe.response['type'] = 'download'
