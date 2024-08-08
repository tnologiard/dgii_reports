# Copyright (c) 2024, TnologiaRD and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe
import json
from frappe.utils import cstr, cint, flt, now_datetime
from frappe.model.naming import make_autoname

from frappe import _ as translate

MAX_VALUE_AVALIABLE = 250000

def autoname(doc, event):
    doc.name = make_autoname(doc.naming_series)

def before_insert(doc, event):
    # Verificar que el monto total base no supere el límite sin un RNC o Cédula asociado
    if doc.base_total >= MAX_VALUE_AVALIABLE:
        ct = frappe.get_doc('Customer', doc.customer)
        if not ct.tax_id:
            frappe.throw('Para realizar ventas por un monto igual o mayor a los RD$250,000. El cliente debe de tener un RNC o Cédula asociado.')

    # Verificar condiciones para asignar un NCF
    if not doc.naming_series or doc.amended_from or (doc.is_pos and doc.custom_ncf) or doc.custom_ncf:
        return False

    if doc.is_return:
        doc.custom_return_against_ncf = doc.custom_ncf

    # Generar un nuevo NCF
    doc.custom_ncf = generate_new(doc)

    # Obtener el tipo de documento
    get_document_type(doc)

    return True

def on_change(doc, event):
    fetch_print_heading_if_missing(doc)

def get_document_type(doc):
    conf = get_serie_for_(doc)
    doc.custom_tipo_de_factura = conf.document_type

def generate_new(doc):
    conf = get_serie_for_(doc)
    
    if not conf.serie or not conf.document_type:
        return ''
    
    # Obtener el código del tipo de comprobante fiscal
    tipo_comprobante_fiscal = frappe.get_doc("Tipo Comprobante Fiscal", conf.document_type)
    codigo = tipo_comprobante_fiscal.codigo

    if len(codigo) != 2:
        frappe.throw("El código del tipo de comprobante fiscal debe tener exactamente 2 dígitos.")

    current = cint(conf.secuencia_actual)

    if cint(conf.secuencia_final) and current >= cint(conf.secuencia_final):
        frappe.throw("Ha llegado al máximo establecido para esta serie de comprobantes!")

    current += 1

    conf.secuencia_actual = current
    conf.db_update()

    # Formato: Serie (parcial) + Código de tipo de comprobante (2 dígitos) + Secuencia (8 dígitos)
    return '{0}{1}{2:08d}'.format(conf.serie.split(".")[0], codigo, current)

def get_serie_for_(doc):
    if not doc.tax_category:
        frappe.throw("Favor seleccionar en el cliente alguna categoria de impuestos")
    
    return frappe.get_doc("Comprobantes Fiscales NCF", {
        "company": doc.company,
        "tax_category": doc.tax_category
    })

def fetch_print_heading_if_missing(doc, go_silently=False):
    if doc.select_print_heading:
        return False

    try:
        conf = get_serie_for_(doc)
    except:
        return False

    if not conf.select_print_heading:
        infomsg = translate("Print Heading was not specified on {doctype}: {name}")

        if not go_silently:
            frappe.msgprint(infomsg.format(**conf.as_dict()))

        return False

    doc.select_print_heading = conf.select_print_heading

    doc.db_update()
