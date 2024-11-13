import frappe
import json
from frappe import _
from frappe.utils import cint, getdate, nowdate
from dgii_reports.servicios.consultas_web_dgii import ServicioConsultasWebDgii
from stdnum.do import rnc
from stdnum.do import ncf


def validate_unique_ncf_by_supplier(doc):
    """Valida que el NCF sea único por suplidor."""
    if not doc.bill_no:
        frappe.throw("El número de comprobante fiscal es obligatorio.++")

    filters = {
        "bill_no": doc.bill_no,
        "supplier": doc.supplier,
        "docstatus": 1
    }
    purchase_invoice = frappe.db.exists("Purchase Invoice", filters)
    if purchase_invoice:
        purchase_invoice_link = f'<a class="bold" href="/app/purchase-invoice/{purchase_invoice}">{purchase_invoice}</a>'
        frappe.throw(_("El NCF debe ser único por suplidor. Existe otra factura con este número de comprobante: " + purchase_invoice_link))


@frappe.whitelist()
def generate_new(doc):
    # Convertir el JSON recibido en un diccionario de Python
    if isinstance(doc, str):
        doc = json.loads(doc)

    conf = get_serie_for_(doc)

    if not conf or not conf.serie or not conf.document_type:
        return {
            'bill_no': '',
            'vencimiento_ncf': ''
        }

    tipo_comprobante_fiscal = frappe.get_doc("Tipo Comprobante Fiscal", conf.document_type)
    validate_fiscal_document_expiry(conf)

    if len(tipo_comprobante_fiscal.codigo) != 2:
        frappe.throw("El código del tipo de comprobante fiscal debe tener exactamente 2 dígitos.")

    current = cint(conf.secuencia_actual) + 1
    bill_no = '{0}{1}{2:08d}'.format(conf.serie.split(".")[0], tipo_comprobante_fiscal.codigo, current)
    validate_unique_ncf(bill_no)

    vencimiento_ncf = conf.expira_el

    return {
        'bill_no': bill_no,
        'vencimiento_ncf': vencimiento_ncf
    }

def get_serie_for_(doc):
    if isinstance(doc, str):
        doc = json.loads(doc)

    if doc.get('custom_tipo_comprobante') not in ["Comprobante de Compras", "Comprobante para Gastos Menores"]:
        return None

    if not doc.get('custom_tipo_comprobante'):
        frappe.throw("Favor seleccionar un tipo de comprobante")

    # Obtener el name del Tipo Comprobante Fiscal
    tipo_comprobante = frappe.db.get_value("Tipo Comprobante Fiscal", {"tipo_comprobante": doc.get('custom_tipo_comprobante')}, "name")
    if not tipo_comprobante:
        frappe.throw(f"Tipo de comprobante fiscal '{doc.get('custom_tipo_comprobante')}' no encontrado")

    return frappe.get_doc("Comprobantes Fiscales NCF", {
        "company": doc.get('company'),
        "document_type": tipo_comprobante
    })

def validate_fiscal_document_expiry(conf):
    if conf.expira_el and getdate(nowdate()) > getdate(conf.expira_el):
        frappe.msgprint("Los comprobantes fiscales seleccionados han expirado.")
        raise frappe.ValidationError("Comprobantes fiscales expirados.")


def validate_unique_ncf(nuevo_ncf):
    existing_invoice = frappe.db.get_value(
        "Purchase Invoice", 
        {"bill_no": nuevo_ncf, "docstatus": ["!=", 0]},  # Excluir facturas en estado "Draft"
        "name"
    )
    if existing_invoice:
        invoice_link = frappe.utils.get_url_to_form("Purchase Invoice", existing_invoice)
        frappe.throw(f"El NCF generado ({nuevo_ncf}) ya ha sido usado en otra factura de venta: <a href='{invoice_link}'>{existing_invoice}</a>")
    

@frappe.whitelist()
def validate_ncf(ncf_number, supplier):
    try:
        temp_doc = frappe._dict({
            "bill_no": ncf_number,
            "supplier": supplier
        })
        # validate_unique_ncf(ncf_number)
        validate_unique_ncf_by_supplier(temp_doc)
        return ncf.is_valid(ncf_number)
    except Exception as e:
        frappe.log_error(message=str(e), title="Error en validate_ncf")
        return False
    
def common_validations(doc):
    """Función que realiza las validaciones comunes."""
    if not doc.custom_tipo_comprobante:
        frappe.throw("Favor seleccionar un tipo de comprobante")
    if not doc.supplier:
        frappe.throw("Favor seleccionar un suplidor")


def validate(doc, event):
    """Función para validar el documento antes de cualquier acción."""
    common_validations(doc)

def before_save(doc, event):
    """Función que se ejecuta antes de guardar el documento."""
    common_validations(doc)

def before_submit(doc, event):
    """Función que se ejecuta antes de enviar el documento."""
    common_validations(doc)
    if doc.custom_tipo_comprobante in ["Comprobante de Compras", "Comprobante para Gastos Menores"]  and not doc.amended_from:
        conf = get_serie_for_(doc)
        current = cint(conf.secuencia_actual) + 1
        conf.secuencia_actual = current
        conf.db_update()
        doc.bill_no = '{0}{1}{2:08d}'.format(conf.serie.split(".")[0], frappe.get_doc("Tipo Comprobante Fiscal", conf.document_type).codigo, current)
        doc.vencimiento_ncf = conf.expira_el
        print(f"before_save: Se ha generado un nuevo NCF = {doc.bill_no}")
    else:
        print(f"before_save: doc.bill_no (after) = {doc.bill_no}")
        validate_against_dgii(doc)

def validate_ncf_with_dgii(rnc, ncf, my_rnc=None, sec_code=None, req_sec_code=False):
    """Valida el NCF con la DGII."""
    no_validar_ncf = frappe.db.get_single_value('DGII Reports Settings', 'no_validar_ncf')
    
    if no_validar_ncf:
        return True
    
    try:
        servicio = ServicioConsultasWebDgii()
        respuesta = servicio.consultar_ncf(ncf, rnc, my_rnc=my_rnc, sec_code=sec_code, req_sec_code=req_sec_code)
        print(f"respuesta: {respuesta.success}, {respuesta.estado}, {respuesta.message}")
        return respuesta.success and (respuesta.estado in ["VIGENTE", "VENCIDO", "Aceptado"] or respuesta.valido_hasta in ["N/A"])
    except Exception as e:
        frappe.log_error(message=str(e), title="Error en validate_ncf_with_dgii")
        return False

def validate_against_dgii(doc):
    """Valida el NCF contra la DGII y verifica su validez."""
    if not doc.tax_id:
        return

    my_tax_id = frappe.get_value("Company", doc.company, "tax_id")
    if not my_tax_id:
        frappe.throw("Favor ingresar el RNC en la compañía (sin guiones).")

    if not validate_ncf_with_dgii(doc.tax_id, doc.bill_no, my_rnc=my_tax_id, sec_code=doc.custom_security_code, req_sec_code=doc.custom_require_security_code):
        print(f"doc.tax_id: {doc.tax_id}, doc.bill_no: {doc.bill_no}, my_rnc: {my_tax_id}, sec_code: {doc.custom_security_code}, req_sec_code: {doc.custom_require_security_code}")
        frappe.throw(_("Número de Comprobante Fiscal <b>NO VÁLIDO</b>."))


@frappe.whitelist()
def get_custom_tipo_comprobante_options():
    options = []

    # Obtener el doctype single del tipo 'DGII Reports Settings'
    dgii_reports_settings = frappe.get_single('DGII Reports Settings')

    # Obtener los valores del campo 'purchase_ncf_list_settings'
    purchase_ncf_list_settings = dgii_reports_settings.get('purchase_ncf_list_settings')

    for setting in purchase_ncf_list_settings:
        # Obtener el valor del campo 'tipo_comprobante' del documento enlazado 'Comprobantes Fiscales Settings'
        tipo_comprobante = frappe.get_value('Tipo Comprobante Fiscal', setting.tipo_comprobante_fiscal, 'tipo_comprobante')
        # Verificar si el campo 'visible_en_factura' es verdadero
        if setting.visible_en_factura:
            options.append(tipo_comprobante)

    # Devolver una lista de opciones únicas manteniendo el orden de la tabla
    return list(dict.fromkeys(options))