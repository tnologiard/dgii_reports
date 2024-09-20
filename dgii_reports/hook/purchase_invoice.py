import frappe
from frappe import _
from frappe.utils import cint, getdate, nowdate
from dgii_reports.servicios.consultas_web_dgii import ServicioConsultasWebDgii

def common_validations(doc):
    """Función que realiza las validaciones comunes."""
    validate_tax_id(doc)
    # validate_bill_no_and_custom_flags(doc)
    validate_duplicate_ncf(doc)

def validate(doc, event):
    """Función para validar el documento antes de cualquier acción."""
    common_validations(doc)

def before_save(doc, event):
    """Función que se ejecuta antes de guardar el documento."""
    common_validations(doc)
    if (doc.custom_is_b11 or doc.custom_is_b13) and not doc.amended_from:
        generate_new(doc)
        print(f"before_save: Se ha generado un nuevo NCF = {doc.bill_no}")
    else:
        validate_tax_category(doc)
        validate_unique_ncf_by_supplier(doc)
        print(f"before_save: doc.bill_no (after) = {doc.bill_no}")
        validate_against_dgii(doc)

def before_submit(doc, event):
    """Función que se ejecuta antes de enviar el documento."""
    common_validations(doc)
    if (doc.custom_is_b11 or doc.custom_is_b13) and not doc.amended_from:
        generate_new(doc)
        print(f"before_submit: Se ha generado un nuevo NCF = {doc.bill_no}")
    else:
        validate_tax_category(doc)
        validate_unique_ncf_by_supplier(doc)
        print(f"before_submit: doc.bill_no (after) = {doc.bill_no}")
        validate_against_dgii(doc)

def generate_new(doc):
    """Genera un nuevo número de comprobante fiscal para el documento."""
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
        frappe.throw("¡Ha llegado al máximo establecido para esta serie de comprobantes!")

    current += 1
    conf.secuencia_actual = current
    conf.db_update()
    # Formato: Serie (parcial) + Código de tipo de comprobante (2 dígitos) + Secuencia (8 dígitos)
    doc.bill_no = '{0}{1}{2:08d}'.format(conf.serie.split(".")[0], tipo_comprobante_fiscal.codigo, current)
        # Validar que el nuevo NCF no se haya usado con anterioridad
    validate_unique_ncf(doc.bill_no)

    doc.vencimiento_ncf = conf.expira_el
    doc.db_update()
    frappe.db.commit()

def get_serie_for_(doc):
    if not doc.custom_is_b11 and not doc.custom_is_b13:
        return None

    if not doc.tax_category:
        frappe.throw("Favor seleccionar alguna categoría de impuestos")
    
    return frappe.get_doc("Comprobantes Fiscales NCF", {
        "company": doc.company,
        "tax_category": doc.tax_category
    })

def validate_tax_category(doc):
    if not doc.custom_is_b11 and not doc.custom_is_b13:
        return

    conf = get_serie_for_(doc)
    if conf:
        tipo_comprobante_fiscal = frappe.get_doc("Tipo Comprobante Fiscal", conf.document_type)
        validate_tax_category_code(doc, tipo_comprobante_fiscal)

def validate_tax_category_code(doc, tipo_comprobante_fiscal):
    print(f"validate_tax_category_code: doc.custom_is_b11 = {doc.custom_is_b11}, doc.custom_is_b13 = {doc.custom_is_b13}")
    if doc.custom_is_b11:
        if tipo_comprobante_fiscal.codigo != '11':
            frappe.msgprint("Por favor, seleccione una categoría de impuestos adecuada para facturas de Comprobante de Compras.")
            raise frappe.ValidationError("Categoría de impuestos incorrecta para facturas de Comprobante de Compras.")
    elif doc.custom_is_b13:
        if tipo_comprobante_fiscal.codigo != '13':
            frappe.msgprint("Por favor, seleccione una categoría de impuestos adecuada para facturas de Comprobante para Gastos Menores.")
            raise frappe.ValidationError("Categoría de impuestos incorrecta para facturas de Comprobante para Gastos Menores.")
    validate_bill_no_and_custom_flags(doc)

def validate_bill_no_and_custom_flags(doc):
    if doc.bill_no:
        if doc.bill_no.startswith('B13') and not doc.custom_is_b13:
            frappe.msgprint("Parece que está intentando registrar un Comprobante para Gastos Menores (B13). Por favor, seleccione la casilla correspondiente.")
            raise frappe.ValidationError("Casilla 'Comprobante para Gastos Menores (B13)' no seleccionada.")
        elif doc.bill_no.startswith('B14') and not doc.custom_is_b11:
            frappe.msgprint("Parece que está intentando registrar un Comprobante de Compras (B14). Por favor, seleccione la casilla correspondiente.")
            raise frappe.ValidationError("Casilla 'Comprobante de Compras (B14)' no seleccionada.")

def validate_fiscal_document_expiry(conf):
    if conf.expira_el and getdate(nowdate()) > getdate(conf.expira_el):
        frappe.msgprint("Los comprobantes fiscales seleccionados han expirado.")
        raise frappe.ValidationError("Comprobantes fiscales expirados.")

def validate_duplicate_ncf(doc):
    """Valida si el NCF ya existe para el suplidor en una factura activa."""
    if not doc.bill_no:
        return 

    # Verificar si es una nota de débito y que el NCF del suplidor tenga el prefijo B04
    if doc.is_return and not doc.bill_no.startswith("B04"):
        frappe.throw("El NCF de una nota de crédito del suplidor debe tener el prefijo 'B04'.")

    if doc.custom_is_b11 and not doc.bill_no.startswith("B11"):
        frappe.throw("El NCF de un Comprobante de Compras, debe tener el prefijo 'B11'.")

    if doc.custom_is_b13 and not doc.bill_no.startswith("B13"):
        frappe.throw("El NCF de un Comprobante para Gastos Menores, debe tener el prefijo 'B13'.")

    filters = {
        "tax_id": doc.tax_id, # rnc
        "bill_no": doc.bill_no, # ncf
        "docstatus": 1,
        "name": ["!=", doc.name],
    }
    if frappe.db.exists("Purchase Invoice", filters):
        frappe.throw(f"Ya existe una factura registrada a nombre de <b>{doc.supplier_name}</b> con el mismo NCF <b>{doc.bill_no}</b>, ¡favor verificar!")

def validate_unique_ncf(nuevo_ncf):
    existing_invoice = frappe.db.get_value("Purchase Invoice", {"bill_no": nuevo_ncf}, "name")
    if existing_invoice:
        invoice_link = frappe.utils.get_url_to_form("Purchase Invoice", existing_invoice)
        frappe.throw(f"El NCF generado ({nuevo_ncf}) ya ha sido usado en otra factura de venta: <a href='{invoice_link}'>{existing_invoice}</a>")

def validate_tax_id(doc):
    """Valida que el campo tax_id no sea vacío."""
    if not doc.tax_id:
        if doc.custom_is_b13:
            # Obtener el tax_id de la compañía y asignarlo al documento
            my_tax_id = frappe.get_value("Company", doc.company, "tax_id")
            doc.tax_id = my_tax_id
        else:
            # Detener el flujo y lanzar una excepción
            frappe.throw("El campo RNC / Cédula del proveedor es obligatorio. Favor proporcionar el RNC / Cédula del proveedor.")

# def validate_unique_ncf_by_supplier(supplier, ncf):
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