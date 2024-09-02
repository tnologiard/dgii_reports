# Copyright (c) 2024, TnologiaRD and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import cstr, cint, flt, formatdate, format_datetime
from frappe.model.document import Document
from frappe.utils.csvutils import UnicodeWriter
from datetime import datetime, date
import time
from frappe import _

class Reporte606(Document):
	pass

@frappe.whitelist()
def validate_pending_invoices(from_date, to_date):
    draft_invoices = frappe.db.sql("""
        SELECT 
            COUNT(*) 
        FROM 
            `tabPurchase Invoice` 
        WHERE 
            docstatus = 0 AND posting_date BETWEEN '%s' AND '%s'
    """ % (from_date, to_date))

    if draft_invoices[0][0] > 0:
        frappe.log_error("Facturas pendientes encontradas", "validate_pending_invoices")
        return {"message": "Hay facturas de compra pendientes de procesar. Por favor, complete las facturas pendientes antes de generar el reporte."}
    
    frappe.log_error("No hay facturas pendientes", "validate_pending_invoices")
    return {"message": ""}


def format_amount(amount):
    if amount == '' or amount == 0 or amount == '0.000000000':
        return ''
    try:
        amount = abs(float(amount))  # Convertir a valor absoluto
    except ValueError:
        return amount
    if amount == int(amount):
        return str(int(amount))
    else:
        return f"{amount:.2f}"

def format_date_aaaammdd(date_value):
    if isinstance(date_value, date):
        return date_value.strftime("%Y%m%d")
    elif isinstance(date_value, str):
        return datetime.strptime(date_value, "%Y-%m-%d").strftime("%Y%m%d")
    return ''

def get_payment_methods(invoice_name):
    payment_entries = frappe.db.sql("""
        SELECT DISTINCT pe.mode_of_payment
        FROM `tabPayment Entry Reference` per
        JOIN `tabPayment Entry` pe ON per.parent = pe.name
        WHERE per.reference_name = %s
    """, (invoice_name,), as_dict=True)
    
    # Debugging output
    print("\n\n\n")
    print("Invoice Name:", invoice_name)
    print("Payment Entries:", payment_entries)
    
    if len(payment_entries) > 1:
        return '07'  # Mixta
    elif len(payment_entries) == 1:
        forma_de_pago = payment_entries[0].mode_of_payment
        return '01' if forma_de_pago == 'Efectivo' else '02' if forma_de_pago == 'Transferencia bancaria' else '03' if forma_de_pago == 'Tarjetas de credito' else ''
    return ''

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
    facturas = frappe.db.sql("""
        SELECT
            pinv.tax_id AS `RNC o Cedula`,
            CASE
                WHEN LENGTH(pinv.tax_id) = 9 THEN '1'
                WHEN LENGTH(pinv.tax_id) = 11 THEN '2'
                ELSE '3'
            END AS `Tipo Id`,
            pinv.tipo_bienes_y_servicios_comprados AS `Tipo Bienes y Servicios Comprados`,
            pinv.bill_no AS `NCF`,
            '' AS `NCF o Documento Modificado`,  # No disponible
            pinv.bill_date AS `Fecha Comprobante`,
            pe.reference_date AS `Fecha Pago`,
            pinv.monto_facturado_servicios AS `Monto Facturado en Servicios`,
            pinv.monto_facturado_bienes AS `Monto Facturado en Bienes`,
            pinv.base_total AS `Total Monto Facturado`,
            pinv.total_itbis AS `ITBIS Facturado`,
            pinv.retention_amount AS `ITBIS Retenido`,
            '' AS `ITBIS sujeto a Proporcionalidad (Art. 349)`,  # No disponible
            '' AS `ITBIS llevado al Costo`,  # No disponible
            '' AS `ITBIS por Adelantar`,  # No disponible
            '' AS `ITBIS percibido en compras`,  # No disponible
            pinv.retention_type AS `Tipo de Retencion en ISR`,
            pinv.isr_amount AS `Monto Retención Renta`,
            '' AS `ISR Percibido en compras`,  # No disponible
            pinv.excise_tax AS `Impuesto Selectivo al Consumo`,
            pinv.other_taxes AS `Otros Impuesto/Tasas`,
            pinv.legal_tip AS `Monto Propina Legal`,
            pinv.is_return AS `Es Nota de Débito`,
            pinv.return_against AS `Factura Original`,
            pinv.name AS `Factura Actual`
        FROM `tabPurchase Invoice` pinv
        LEFT JOIN `tabSupplier` supl ON supl.name = pinv.supplier
        LEFT JOIN `tabPayment Entry Reference` per ON per.reference_name = pinv.name
        LEFT JOIN `tabPayment Entry` pe ON pe.name = per.parent
        WHERE pinv.docstatus = 1
        AND pinv.bill_date BETWEEN %s AND %s
    """, (from_date, to_date), as_dict=True)

    # Calcular el número de registros
    numero_registros = len(facturas)

    # Crear el archivo TXT
    w = UnicodeWriter()

    # Agregar la primera línea
    w.writerow([
        "606", 
        rnc, 
        periodo, 
        numero_registros
    ])

    # Llenar las columnas del reporte 606 con los datos obtenidos
    for factura in facturas:
        ncf_modificado = ''
        # forma_de_pago = get_payment_methods(factura['Factura Original'] if factura['Es Nota de Débito'] else factura['Factura Actual'])
        forma_de_pago = get_payment_methods(factura['Factura Actual'])

        if factura['Es Nota de Débito']:
            original_invoice = frappe.get_doc("Purchase Invoice", factura['Factura Original'])
            ncf_modificado = original_invoice.bill_no
            forma_de_pago = "06" # "Nota de Crédito"

        tipo_bienes_y_servicios = factura['Tipo Bienes y Servicios Comprados']
        if tipo_bienes_y_servicios:
            tipo_bienes_y_servicios = tipo_bienes_y_servicios.split('-')[0]

        # Verificar si alguna columna de retención tiene un monto mayor a cero
        fecha_pago = ''
        if (factura['ITBIS Retenido'] and float(factura['ITBIS Retenido']) > 0) or \
           (factura['Monto Retención Renta'] and float(factura['Monto Retención Renta']) > 0):
            fecha_pago = format_date_aaaammdd(factura['Fecha Pago'])

        w.writerow([
            factura['RNC o Cedula'] or '',
            factura['Tipo Id'] or '',
            tipo_bienes_y_servicios or '',
            factura['NCF'] or '',
            ncf_modificado,
            format_date_aaaammdd(factura['Fecha Comprobante']),
            fecha_pago,
            format_amount(factura['Monto Facturado en Servicios']),
            format_amount(factura['Monto Facturado en Bienes']),
            format_amount(factura['Total Monto Facturado']),
            format_amount(factura['ITBIS Facturado']),
            format_amount(factura['ITBIS Retenido']),
            factura['ITBIS sujeto a Proporcionalidad (Art. 349)'] or '',
            factura['ITBIS llevado al Costo'] or '',
            factura['ITBIS por Adelantar'] or '',
            factura['ITBIS percibido en compras'] or '',
            factura['Tipo de Retencion en ISR'] or '',
            format_amount(factura['Monto Retención Renta']),
            factura['ISR Percibido en compras'] or '',
            format_amount(factura['Impuesto Selectivo al Consumo']),
            format_amount(factura['Otros Impuesto/Tasas']),
            format_amount(factura['Monto Propina Legal']),
            forma_de_pago
        ])

    # Convertir el contenido a texto con delimitador de pipes
    content = w.getvalue().replace(",", "|").replace('"', '')

    # Devolver el contenido del archivo de texto como descarga
    frappe.response['filename'] = "Reporte_606_%s.txt" % time.strftime("%Y%m%d_%H%M%S")
    frappe.response['filecontent'] = content
    frappe.response['type'] = 'download'
