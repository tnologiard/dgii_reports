from __future__ import unicode_literals

import frappe
import json
from frappe.utils import cint, getdate, nowdate
from frappe.model.naming import make_autoname

from frappe import _ as translate


MAX_VALUE_AVALIABLE = 250000

def autoname(doc, event):
    doc.name = make_autoname(doc.naming_series)

def before_insert(doc, event):
    print(f"before_insert: doc.is_return = {doc.is_return}")
    print(f"before_insert: doc.return_against = {doc.return_against}")
    print(f"before_insert: doc.custom_ncf (before) = {doc.custom_ncf}")

    # Validar el monto total y el RNC o Cédula del cliente
    validate_customer_tax_id(doc)

    # Verificar condiciones para asignar un NCF
    if doc.is_return:
        print("before_insert: Es una nota de crédito, llamando a handle_credit_note_link")
        handle_credit_note_link(doc)
    elif not should_assign_ncf(doc):
        print("before_insert: No se asignará un NCF")
        return False

    # Obtener el tipo de documento
    get_document_type(doc)
    print(f"before_insert: doc.custom_tipo_de_factura = {doc.custom_tipo_de_factura}")

    print(f"before_insert: doc.custom_ncf (after) = {doc.custom_ncf}")

    return True


def before_submit(doc, event):
    print(f"before_submit: doc.is_return = {doc.is_return}")
    print(f"before_submit: doc.custom_ncf (before) = {doc.custom_ncf}")

    # Evitar generar un nuevo NCF si is_opening es "Yes"
    if not doc.is_opening == "No":
        print("before_submit: is_opening es true, no se generará un nuevo NCF.")
        return

    # Verificar y generar un NCF único
    if not doc.custom_ncf:
        doc.custom_ncf = generate_new(doc)
        print(f"before_submit: Se ha generado un nuevo NCF = {doc.custom_ncf}")

    if doc.custom_tipo_comprobante in ["Factura de Crédito Fiscal","Factura de Consumo","Notas de Crédito","Comprobante para Regímenes Especiales","Comprobante Gubernamental","Comprobante para Exportaciones"] and not doc.amended_from:
        conf = get_serie_for_(doc)
        current = cint(conf.secuencia_actual) + 1
        conf.secuencia_actual = current
        conf.db_update()
        doc.custom_ncf = '{0}{1}{2:08d}'.format(conf.serie.split(".")[0], frappe.get_doc("Tipo Comprobante Fiscal", conf.document_type).codigo, current)
        doc.vencimiento_ncf = conf.expira_el
        print(f"before_save: Se ha generado un nuevo NCF = {doc.custom_ncf}")

    print(f"before_submit: doc.custom_ncf (after) = {doc.custom_ncf}")

def on_change(doc, event):
    fetch_print_heading_if_missing(doc)

def get_document_type(doc):
    conf = get_serie_for_(doc)
    tipo_comprobante_fiscal = frappe.get_doc("Tipo Comprobante Fiscal", conf.document_type)
    doc.custom_tipo_de_factura = tipo_comprobante_fiscal.codigo + "-" + tipo_comprobante_fiscal.tipo_comprobante


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

def validate_customer_tax_id(doc):
    if doc.base_net_total >= MAX_VALUE_AVALIABLE:
        ct = frappe.get_doc('Customer', doc.customer)
        if not ct.tax_id:
            frappe.throw('Para realizar ventas por un monto igual o mayor a los RD$250,000. El cliente debe de tener un RNC o Cédula asociado.')

def should_assign_ncf(doc):
    return not doc.naming_series or doc.amended_from or (doc.is_pos and doc.custom_ncf) or (doc.custom_ncf and not doc.is_return)

def handle_credit_note_link(doc):
    print(f"handle_credit_note_link: doc.return_against = {doc.return_against}")
    # Verificar si la nota de crédito está vinculada a una factura de venta
    if not doc.return_against:
        frappe.throw('Una nota de crédito debe estar vinculada a una factura de venta.')
    
    # Obtener la factura de venta original
    original_invoice = frappe.get_doc("Sales Invoice", doc.return_against)
    
    # Guardar el NCF de la factura de venta original en custom_return_against_ncf
    doc.custom_return_against_ncf = original_invoice.custom_ncf
    doc.custom_ncf = ''  # Dejar el NCF vacío en estado borrador

    print(f"handle_credit_note_link: doc.custom_return_against_ncf = {doc.custom_return_against_ncf}")
    print(f"handle_credit_note_link: doc.custom_ncf se ha dejado vacío = {doc.custom_ncf}")



@frappe.whitelist()
def generate_new(doc):
    # Convertir el JSON recibido en un diccionario de Python
    if isinstance(doc, str):
        doc = json.loads(doc)

    conf = get_serie_for_(doc)

    if not conf or not conf.serie or not conf.document_type:
        return {
            'custom_ncf': '',
            'vencimiento_ncf': ''
        }

    tipo_comprobante_fiscal = frappe.get_doc("Tipo Comprobante Fiscal", conf.document_type)

    validate_fiscal_document_expiry(conf)

    if len(tipo_comprobante_fiscal.codigo) != 2:
        frappe.throw("El código del tipo de comprobante fiscal debe tener exactamente 2 dígitos.")

    current = cint(conf.secuencia_actual) + 1

    if cint(conf.secuencia_final) and current >= cint(conf.secuencia_final):
        frappe.throw("Ha llegado al máximo establecido para esta serie de comprobantes!")
   
    custom_ncf = '{0}{1}{2:08d}'.format(conf.serie.split(".")[0], tipo_comprobante_fiscal.codigo, current)

    validate_unique_ncf(custom_ncf)

    vencimiento_ncf = conf.expira_el

    return {
        'custom_ncf': custom_ncf,
        'vencimiento_ncf': vencimiento_ncf
    }

def get_serie_for_(doc):
    if isinstance(doc, str):
        doc = json.loads(doc)

    if doc.get('custom_tipo_comprobante') not in ["Factura de Crédito Fiscal","Factura de Consumo","Notas de Crédito","Comprobante para Regímenes Especiales","Comprobante Gubernamental","Comprobante para Exportaciones"]:
        return None

    if not doc.get('custom_tipo_comprobante'):
        frappe.throw("Favor seleccionar un tipo de comprobante")

    # Obtener el name del Tipo Comprobante Fiscal
    try:
        tipo_comprobante = frappe.db.get_value("Tipo Comprobante Fiscal", {"tipo_comprobante": doc.get('custom_tipo_comprobante')}, "name")
    except Exception as e:
        tipo_comprobante = None
        frappe.throw(f"Error al obtener el tipo de comprobante fiscal: {str(e)}")

    if not tipo_comprobante:
        frappe.throw(f"No ha configurado el tipo de comprobante fiscal '{doc.get('custom_tipo_comprobante')}'")

    try:
        conf = frappe.get_doc("Comprobantes Fiscales NCF", {
            "company": doc.get('company'),
            "document_type": tipo_comprobante
        })
    except frappe.DoesNotExistError:
        frappe.throw(f"No ha configurado los Comprobantes Fiscales NCF para la compañía '{doc.get('company')}' del tipo '{tipo_comprobante}'")
    
    return conf

def validate_fiscal_document_expiry(conf):
    if conf.expira_el and getdate(nowdate()) > getdate(conf.expira_el):
        frappe.msgprint("Los comprobantes fiscales seleccionados han expirado.")
        raise frappe.ValidationError("Comprobantes fiscales expirados.")

def validate_unique_ncf(nuevo_ncf):
    existing_invoice = frappe.db.get_value("Sales Invoice", {"custom_ncf": nuevo_ncf}, "name")
    if existing_invoice:
        invoice_link = frappe.utils.get_url_to_form("Sales Invoice", existing_invoice)
        frappe.throw(f"El NCF generado ({nuevo_ncf}) ya ha sido usado en otra factura de venta: <a href='{invoice_link}'>{existing_invoice}</a>")


@frappe.whitelist()
def get_custom_tipo_comprobante_options():
    options = []

    # Obtener el doctype single del tipo 'DGII Reports Settings'
    dgii_reports_settings = frappe.get_single('DGII Reports Settings')

    # Obtener los valores del campo 'sales_ncf_list_settings'
    sales_ncf_list_settings = dgii_reports_settings.get('sales_ncf_list_settings')

    for setting in sales_ncf_list_settings:
        # Obtener el valor del campo 'tipo_comprobante' del documento enlazado 'Comprobantes Fiscales Settings'
        tipo_comprobante = frappe.get_value('Tipo Comprobante Fiscal', setting.tipo_comprobante_fiscal, 'tipo_comprobante')
        # Verificar si el campo 'visible_en_factura' es verdadero
        if setting.visible_en_factura:
            options.append(tipo_comprobante)

    # Devolver una lista de opciones únicas manteniendo el orden de la tabla
    return list(dict.fromkeys(options))