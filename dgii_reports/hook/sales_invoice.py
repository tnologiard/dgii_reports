from __future__ import unicode_literals

import frappe
import json
from frappe.utils import cint, getdate, nowdate
from frappe.model.naming import make_autoname

from frappe import _ as translate

# MAX_VALUE_AVALIABLE = 250000

# def autoname(doc, event):
#     doc.name = make_autoname(doc.naming_series)

# def before_insert(doc, event):
#     print(f"before_insert: doc.is_return = {doc.is_return}")
#     print(f"before_insert: doc.return_against = {doc.return_against}")
#     print(f"before_insert: doc.custom_ncf (before) = {doc.custom_ncf}")

#     # Verificar que el monto total base no supere el límite sin un RNC o Cédula asociado
#     if doc.base_total >= MAX_VALUE_AVALIABLE:
#         ct = frappe.get_doc('Customer', doc.customer)
#         if not ct.tax_id:
#             frappe.throw('Para realizar ventas por un monto igual o mayor a los RD$250,000. El cliente debe de tener un RNC o Cédula asociado.')

#     # Verificar condiciones para asignar un NCF
#     if not doc.naming_series or doc.amended_from or (doc.is_pos and doc.custom_ncf) or (doc.custom_ncf and not doc.is_return):
#         print("before_insert: No se asignará un NCF")
#         return False

#     if doc.is_return:
#         # Verificar si la nota de crédito está vinculada a una factura de venta
#         if not doc.return_against:
#             frappe.throw('Una nota de crédito debe estar vinculada a una factura de venta.')
        
#         # Obtener la factura de venta original
#         original_invoice = frappe.get_doc("Sales Invoice", doc.return_against)
        
#         # Guardar el NCF de la factura de venta original en custom_return_against_ncf
#         doc.custom_return_against_ncf = original_invoice.custom_ncf
#         doc.custom_ncf = ''  # Dejar el NCF vacío en estado borrador

#         print(f"before_insert: doc.custom_return_against_ncf = {doc.custom_return_against_ncf}")
#         print(f"before_insert: doc.custom_ncf se ha dejado vacío = {doc.custom_ncf}")

#     # Obtener el tipo de documento
#     get_document_type(doc)
#     print(f"before_insert: doc.custom_tipo_de_factura = {doc.custom_tipo_de_factura}")

#     print(f"before_insert: doc.custom_ncf (after) = {doc.custom_ncf}")

#     return True

# def before_submit(doc, event):
#     print(f"before_submit: doc.is_return = {doc.is_return}")
#     print(f"before_submit: doc.custom_ncf (before) = {doc.custom_ncf}")

#     # Verificar y generar un NCF único
#     if not doc.custom_ncf:
#         doc.custom_ncf = generate_new(doc)
#         print(f"before_submit: Se ha generado un nuevo NCF = {doc.custom_ncf}")

#     print(f"before_submit: doc.custom_ncf (after) = {doc.custom_ncf}")


# def on_change(doc, event):
#     fetch_print_heading_if_missing(doc)

# def get_document_type(doc):
#     conf = get_serie_for_(doc)
#     tipo_comprobante_fiscal = frappe.get_doc("Tipo Comprobante Fiscal", conf.document_type)
#     doc.custom_tipo_de_factura = tipo_comprobante_fiscal.codigo + "-" + tipo_comprobante_fiscal.tipo_comprobante

# def generate_new(doc):
#     conf = get_serie_for_(doc)
    
#     if not conf.serie or not conf.document_type:
#         return ''
    
#     # Obtener el tipo de comprobante fiscal
#     tipo_comprobante_fiscal = frappe.get_doc("Tipo Comprobante Fiscal", conf.document_type)
    
#     # Validar el código del tipo de comprobante fiscal
#     if doc.is_return:
#         if tipo_comprobante_fiscal.codigo != '04':
#             frappe.msgprint("Por favor, seleccione una categoría de impuestos adecuada para notas de crédito.")
#             raise frappe.ValidationError("Categoría de impuestos incorrecta para notas de crédito.")
#     else:
#         if tipo_comprobante_fiscal.codigo != '01':
#             frappe.msgprint("Por favor, seleccione una categoría de impuestos adecuada para facturas de crédito fiscal.")
#             raise frappe.ValidationError("Categoría de impuestos incorrecta para facturas de crédito fiscal.")
    
#     # Validar la vigencia de los comprobantes fiscales
#     if conf.expira_el and getdate(nowdate()) > getdate(conf.expira_el):
#         frappe.msgprint("Los comprobantes fiscales seleccionados han expirado.")
#         raise frappe.ValidationError("Comprobantes fiscales expirados.")
    
#     if len(tipo_comprobante_fiscal.codigo) != 2:
#         frappe.throw("El código del tipo de comprobante fiscal debe tener exactamente 2 dígitos.")

#     current = cint(conf.secuencia_actual)

#     if cint(conf.secuencia_final) and current >= cint(conf.secuencia_final):
#         frappe.throw("Ha llegado al máximo establecido para esta serie de comprobantes!")

#     current += 1

#     conf.secuencia_actual = current
#     conf.db_update()

#     # Formato: Serie (parcial) + Código de tipo de comprobante (2 dígitos) + Secuencia (8 dígitos)
#     nuevo_ncf = '{0}{1}{2:08d}'.format(conf.serie.split(".")[0], tipo_comprobante_fiscal.codigo, current)

#     # Validar que el nuevo NCF no se haya usado con anterioridad
#     existing_invoice = frappe.db.get_value("Sales Invoice", {"custom_ncf": nuevo_ncf}, "name")
#     if existing_invoice:
#         invoice_link = frappe.utils.get_url_to_form("Sales Invoice", existing_invoice)
#         frappe.throw(f"El NCF generado ({nuevo_ncf}) ya ha sido usado en otra factura de venta: <a href='{invoice_link}'>{existing_invoice}</a>")

#     return nuevo_ncf

# def get_serie_for_(doc):
#     if not doc.tax_category:
#         frappe.throw("Favor seleccionar alguna categoria de impuestos")
    
#     return frappe.get_doc("Comprobantes Fiscales NCF", {
#         "company": doc.company,
#         "tax_category": doc.tax_category
#     })

# def fetch_print_heading_if_missing(doc, go_silently=False):
#     if doc.select_print_heading:
#         return False

#     try:
#         conf = get_serie_for_(doc)
#     except:
#         return False

#     if not conf.select_print_heading:
#         infomsg = translate("Print Heading was not specified on {doctype}: {name}")

#         if not go_silently:
#             frappe.msgprint(infomsg.format(**conf.as_dict()))

#         return False

#     doc.select_print_heading = conf.select_print_heading

#     doc.db_update()



# MAX_VALUE_AVALIABLE = 250000

# def autoname(doc, event):
#     doc.name = make_autoname(doc.naming_series)

# def before_insert(doc, event):
#     print(f"before_insert: doc.is_return = {doc.is_return}")
#     print(f"before_insert: doc.return_against = {doc.return_against}")
#     print(f"before_insert: doc.custom_ncf (before) = {doc.custom_ncf}")

#     # Verificar que el monto total base no supere el límite sin un RNC o Cédula asociado
#     if doc.base_total >= MAX_VALUE_AVALIABLE:
#         ct = frappe.get_doc('Customer', doc.customer)
#         if not ct.tax_id:
#             frappe.throw('Para realizar ventas por un monto igual o mayor a los RD$250,000. El cliente debe de tener un RNC o Cédula asociado.')

#     # Validar la categoría de impuestos
#     validate_tax_category(doc)

#     # Verificar condiciones para asignar un NCF
#     if not doc.naming_series or doc.amended_from or (doc.is_pos and doc.custom_ncf) or (doc.custom_ncf and not doc.is_return):
#         print("before_insert: No se asignará un NCF")
#         return False

#     if doc.is_return:
#         # Verificar si la nota de crédito está vinculada a una factura de venta
#         if not doc.return_against:
#             frappe.throw('Una nota de crédito debe estar vinculada a una factura de venta.')
        
#         # Obtener la factura de venta original
#         original_invoice = frappe.get_doc("Sales Invoice", doc.return_against)
        
#         # Guardar el NCF de la factura de venta original en custom_return_against_ncf
#         doc.custom_return_against_ncf = original_invoice.custom_ncf
#         doc.custom_ncf = ''  # Dejar el NCF vacío en estado borrador

#         print(f"before_insert: doc.custom_return_against_ncf = {doc.custom_return_against_ncf}")
#         print(f"before_insert: doc.custom_ncf se ha dejado vacío = {doc.custom_ncf}")

#     # Obtener el tipo de documento
#     get_document_type(doc)
#     print(f"before_insert: doc.custom_tipo_de_factura = {doc.custom_tipo_de_factura}")

#     print(f"before_insert: doc.custom_ncf (after) = {doc.custom_ncf}")

#     return True

# def before_submit(doc, event):
#     print(f"before_submit: doc.is_return = {doc.is_return}")
#     print(f"before_submit: doc.custom_ncf (before) = {doc.custom_ncf}")

#     # Validar la categoría de impuestos
#     validate_tax_category(doc)

#     # Verificar y generar un NCF único
#     if not doc.custom_ncf:
#         doc.custom_ncf = generate_new(doc)
#         print(f"before_submit: Se ha generado un nuevo NCF = {doc.custom_ncf}")

#     print(f"before_submit: doc.custom_ncf (after) = {doc.custom_ncf}")

# def on_change(doc, event):
#     fetch_print_heading_if_missing(doc)

# def get_document_type(doc):
#     conf = get_serie_for_(doc)
#     tipo_comprobante_fiscal = frappe.get_doc("Tipo Comprobante Fiscal", conf.document_type)
#     doc.custom_tipo_de_factura = tipo_comprobante_fiscal.codigo + "-" + tipo_comprobante_fiscal.tipo_comprobante

# def generate_new(doc):
#     conf = get_serie_for_(doc)
    
#     if not conf.serie or not conf.document_type:
#         return ''
    
#     # Obtener el tipo de comprobante fiscal
#     tipo_comprobante_fiscal = frappe.get_doc("Tipo Comprobante Fiscal", conf.document_type)
    
#     # Validar el código del tipo de comprobante fiscal
#     if doc.is_return:
#         if tipo_comprobante_fiscal.codigo != '04':
#             frappe.msgprint("Por favor, seleccione una categoría de impuestos adecuada para notas de crédito.")
#             raise frappe.ValidationError("Categoría de impuestos incorrecta para notas de crédito.")
#     else:
#         if tipo_comprobante_fiscal.codigo != '01':
#             frappe.msgprint("Por favor, seleccione una categoría de impuestos adecuada para facturas de crédito fiscal.")
#             raise frappe.ValidationError("Categoría de impuestos incorrecta para facturas de crédito fiscal.")
    
#     # Validar la vigencia de los comprobantes fiscales
#     if conf.expira_el and getdate(nowdate()) > getdate(conf.expira_el):
#         frappe.msgprint("Los comprobantes fiscales seleccionados han expirado.")
#         raise frappe.ValidationError("Comprobantes fiscales expirados.")
    
#     if len(tipo_comprobante_fiscal.codigo) != 2:
#         frappe.throw("El código del tipo de comprobante fiscal debe tener exactamente 2 dígitos.")

#     current = cint(conf.secuencia_actual)

#     if cint(conf.secuencia_final) and current >= cint(conf.secuencia_final):
#         frappe.throw("Ha llegado al máximo establecido para esta serie de comprobantes!")

#     current += 1

#     conf.secuencia_actual = current
#     conf.db_update()

#     # Formato: Serie (parcial) + Código de tipo de comprobante (2 dígitos) + Secuencia (8 dígitos)
#     nuevo_ncf = '{0}{1}{2:08d}'.format(conf.serie.split(".")[0], tipo_comprobante_fiscal.codigo, current)

#     # Validar que el nuevo NCF no se haya usado con anterioridad
#     existing_invoice = frappe.db.get_value("Sales Invoice", {"custom_ncf": nuevo_ncf}, "name")
#     if existing_invoice:
#         invoice_link = frappe.utils.get_url_to_form("Sales Invoice", existing_invoice)
#         frappe.throw(f"El NCF generado ({nuevo_ncf}) ya ha sido usado en otra factura de venta: <a href='{invoice_link}'>{existing_invoice}</a>")

#     return nuevo_ncf

# def get_serie_for_(doc):
#     if not doc.tax_category:
#         frappe.throw("Favor seleccionar alguna categoria de impuestos")
    
#     return frappe.get_doc("Comprobantes Fiscales NCF", {
#         "company": doc.company,
#         "tax_category": doc.tax_category
#     })

# def fetch_print_heading_if_missing(doc, go_silently=False):
#     if doc.select_print_heading:
#         return False

#     try:
#         conf = get_serie_for_(doc)
#     except:
#         return False

#     if not conf.select_print_heading:
#         infomsg = translate("Print Heading was not specified on {doctype}: {name}")

#         if not go_silently:
#             frappe.msgprint(infomsg.format(**conf.as_dict()))

#         return False

#     doc.select_print_heading = conf.select_print_heading

#     doc.db_update()

# def validate_tax_category(doc):
#     conf = get_serie_for_(doc)
#     tipo_comprobante_fiscal = frappe.get_doc("Tipo Comprobante Fiscal", conf.document_type)
    
#     if doc.is_return:
#         if tipo_comprobante_fiscal.codigo != '04':
#             frappe.msgprint("Por favor, seleccione una categoría de impuestos adecuada para notas de crédito.")
#             raise frappe.ValidationError("Categoría de impuestos incorrecta para notas de crédito.")
#     else:
#         if tipo_comprobante_fiscal.codigo != '01':
#             frappe.msgprint("Por favor, seleccione una categoría de impuestos adecuada para facturas de crédito fiscal.")
#             raise frappe.ValidationError("Categoría de impuestos incorrecta para facturas de crédito fiscal.")




MAX_VALUE_AVALIABLE = 250000

def autoname(doc, event):
    doc.name = make_autoname(doc.naming_series)

def before_insert(doc, event):
    print(f"before_insert: doc.is_return = {doc.is_return}")
    print(f"before_insert: doc.return_against = {doc.return_against}")
    print(f"before_insert: doc.custom_ncf (before) = {doc.custom_ncf}")

    # Validar el monto total y el RNC o Cédula del cliente
    validate_customer_tax_id(doc)

    # Validar la categoría de impuestos
    validate_tax_category(doc)

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

    # Validar la categoría de impuestos
    validate_tax_category(doc)

    # Verificar y generar un NCF único
    if not doc.custom_ncf:
        doc.custom_ncf = generate_new(doc)
        print(f"before_submit: Se ha generado un nuevo NCF = {doc.custom_ncf}")

    print(f"before_submit: doc.custom_ncf (after) = {doc.custom_ncf}")

def on_change(doc, event):
    fetch_print_heading_if_missing(doc)

def get_document_type(doc):
    conf = get_serie_for_(doc)
    tipo_comprobante_fiscal = frappe.get_doc("Tipo Comprobante Fiscal", conf.document_type)
    doc.custom_tipo_de_factura = tipo_comprobante_fiscal.codigo + "-" + tipo_comprobante_fiscal.tipo_comprobante

def generate_new(doc):
    conf = get_serie_for_(doc)
    
    if not conf.serie or not conf.document_type:
        return ''
    
    # Obtener el tipo de comprobante fiscal
    tipo_comprobante_fiscal = frappe.get_doc("Tipo Comprobante Fiscal", conf.document_type)
    
    # Validar el código del tipo de comprobante fiscal
    validate_tax_category_code(doc, tipo_comprobante_fiscal)
    
    # Validar la vigencia de los comprobantes fiscales
    validate_fiscal_document_expiry(conf)
    
    if len(tipo_comprobante_fiscal.codigo) != 2:
        frappe.throw("El código del tipo de comprobante fiscal debe tener exactamente 2 dígitos.")

    current = cint(conf.secuencia_actual)

    if cint(conf.secuencia_final) and current >= cint(conf.secuencia_final):
        frappe.throw("Ha llegado al máximo establecido para esta serie de comprobantes!")

    current += 1

    conf.secuencia_actual = current
    conf.db_update()

    # Formato: Serie (parcial) + Código de tipo de comprobante (2 dígitos) + Secuencia (8 dígitos)
    nuevo_ncf = '{0}{1}{2:08d}'.format(conf.serie.split(".")[0], tipo_comprobante_fiscal.codigo, current)

    # Validar que el nuevo NCF no se haya usado con anterioridad
    validate_unique_ncf(nuevo_ncf)

    return nuevo_ncf

def get_serie_for_(doc):
    if not doc.tax_category:
        frappe.throw("Favor seleccionar alguna categoria de impuestos")
    
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

def validate_customer_tax_id(doc):
    if doc.base_total >= MAX_VALUE_AVALIABLE:
        ct = frappe.get_doc('Customer', doc.customer)
        if not ct.tax_id:
            frappe.throw('Para realizar ventas por un monto igual o mayor a los RD$250,000. El cliente debe de tener un RNC o Cédula asociado.')

def validate_tax_category(doc):
    conf = get_serie_for_(doc)
    tipo_comprobante_fiscal = frappe.get_doc("Tipo Comprobante Fiscal", conf.document_type)
    validate_tax_category_code(doc, tipo_comprobante_fiscal)

def validate_tax_category_code(doc, tipo_comprobante_fiscal):
    if doc.is_return:
        if tipo_comprobante_fiscal.codigo != '04':
            frappe.msgprint("Por favor, seleccione una categoría de impuestos adecuada para notas de crédito.")
            raise frappe.ValidationError("Categoría de impuestos incorrecta para notas de crédito.")
    else:
        if tipo_comprobante_fiscal.codigo != '01':
            frappe.msgprint("Por favor, seleccione una categoría de impuestos adecuada para facturas de crédito fiscal.")
            raise frappe.ValidationError("Categoría de impuestos incorrecta para facturas de crédito fiscal.")

def validate_fiscal_document_expiry(conf):
    if conf.expira_el and getdate(nowdate()) > getdate(conf.expira_el):
        frappe.msgprint("Los comprobantes fiscales seleccionados han expirado.")
        raise frappe.ValidationError("Comprobantes fiscales expirados.")

def validate_unique_ncf(nuevo_ncf):
    existing_invoice = frappe.db.get_value("Sales Invoice", {"custom_ncf": nuevo_ncf}, "name")
    if existing_invoice:
        invoice_link = frappe.utils.get_url_to_form("Sales Invoice", existing_invoice)
        frappe.throw(f"El NCF generado ({nuevo_ncf}) ya ha sido usado en otra factura de venta: <a href='{invoice_link}'>{existing_invoice}</a>")

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