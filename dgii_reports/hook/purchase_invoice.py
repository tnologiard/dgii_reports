import frappe
from frappe import _
from frappe.utils import cint, getdate, nowdate
from dgii_reports.servicios.consultas_web_dgii import ServicioConsultasWebDgii
from dgii_reports.servicios.rnc import validate as validate_rnc  # Importar la función de validación RNC
from dgii_reports.servicios.cedula import validate as validate_cedula  # Importar la función de validación Cédula
from dgii_reports.servicios.ncf import validate as validate_ncf  # Importar la función de validación NCF

def validate(doc, event):
    """Función para validar el documento antes de cualquier acción."""
    set_taxes(doc)
    calculate_totals(doc)
    validate_duplicate_ncf(doc)

def before_submit(doc, event):
    """Función que se ejecuta antes de enviar el documento."""
    validate_tax_category(doc)

    # Verificar y generar un NCF único
    # todo cambiar el nombre de este campo: supplier_invoice_no
    if not doc.supplier_invoice_no:
        generate_new(doc)
        print(f"before_submit: Se ha generado un nuevo NCF = {doc.supplier_invoice_no}")
    validate_unique_ncf_by_supplier(doc.supplier, doc.supplier_invoice_no)

    print(f"before_submit: doc.supplier_invoice_no (after) = {doc.supplier_invoice_no}")

    validate_against_dgii(doc)

def calculate_totals(doc):
    """Calcula los totales de bienes y servicios en el documento."""
    total_bienes = total_servicios = 0.0

    # Imprimir los valores de doc.items
    print("-----doc.items:")
    for item in doc.items:
        print(f"Item: {item.item_code}, Amount: {item.amount}")

    for item in doc.items:
        item_type = frappe.db.get_value("Item", item.item_code, "item_type")
        # Imprimir los valores de item_type y item.amount
        print(f"Item Code: {item.item_code}, Item Type: {item_type}, Amount: {item.amount}")
        if item_type == "Bienes":
            total_bienes += item.amount
        elif item_type == "Servicios":
            total_servicios += item.amount
    
    # Imprimir los valores de total_bienes y total_servicios antes de asignarlos
    print(f"Total Bienes: {total_bienes}, Total Servicios: {total_servicios}")

    doc.monto_facturado_bienes = total_bienes
    doc.monto_facturado_servicios = total_servicios

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
    print("\n\n\n")
    print(tipo_comprobante_fiscal.codigo)
    # Formato: Serie (parcial) + Código de tipo de comprobante (2 dígitos) + Secuencia (8 dígitos)
    doc.supplier_invoice_no = '{0}{1}{2:08d}'.format(conf.serie.split(".")[0], tipo_comprobante_fiscal.codigo, current)
        # Validar que el nuevo NCF no se haya usado con anterioridad
    validate_unique_ncf(doc.supplier_invoice_no)

    doc.vencimiento_ncf = conf.expira_el
    doc.db_update()
    frappe.db.commit()

def get_serie_for_(doc):
    if not doc.tax_category:
        frappe.throw("Favor seleccionar alguna categoria de impuestos")
    
    return frappe.get_doc("Comprobantes Fiscales NCF", {
        "company": doc.company,
        "tax_category": doc.tax_category
    })

def set_taxes(doc):
    """Configura los impuestos en el documento basado en la configuración en el dt DGII Reports Settings."""
    conf = frappe.get_single("DGII Reports Settings")
    total_itbis = total_legal_tip = total_excise = 0.0

    tax_fields = [
        (conf.itbis_account, "total_itbis"),
        (conf.legal_tip_account, "legal_tip"),
        (conf.excise_tax, "excise_tax")
    ]

    for account, field in tax_fields:
        if account:
            total_amount = sum(row.base_tax_amount_after_discount_amount for row in doc.taxes if row.account_head == account)
            doc.set(field, total_amount)

    if conf.other_taxes:
        for tax in conf.other_taxes:
            total_amount = sum(row.base_tax_amount_after_discount_amount for row in doc.taxes if row.account_head == tax.account)
            doc.set(tax.tax_type, total_amount)

def validate_tax_category(doc):
    conf = get_serie_for_(doc)
    tipo_comprobante_fiscal = frappe.get_doc("Tipo Comprobante Fiscal", conf.document_type)
    validate_tax_category_code(doc, tipo_comprobante_fiscal)

def validate_tax_category_code(doc, tipo_comprobante_fiscal):
    if doc.is_return:
        if tipo_comprobante_fiscal.codigo != '03':
            frappe.msgprint("Por favor, seleccione una categoría de impuestos adecuada para notas de débito.")
            raise frappe.ValidationError("Categoría de impuestos incorrecta para notas de débito.")
    else:
        if tipo_comprobante_fiscal.codigo != '01':
            frappe.msgprint("Por favor, seleccione una categoría de impuestos adecuada para facturas de crédito fiscal.")
            raise frappe.ValidationError("Categoría de impuestos incorrecta para facturas de crédito fiscal.")

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

    filters = {
        "tax_id": doc.tax_id, # rnc
        "bill_no": doc.bill_no, # ncf
        "docstatus": 1,
        "name": ["!=", doc.name],
    }
    if frappe.db.exists("Purchase Invoice", filters):
        frappe.throw(f"Ya existe una factura registrada a nombre de <b>{doc.supplier_name}</b> con el mismo NCF <b>{doc.bill_no}</b>, ¡favor verificar!")

def validate_unique_ncf(nuevo_ncf):
    existing_invoice = frappe.db.get_value("Purchase Invoice", {"supplier_invoice_no": nuevo_ncf}, "name")
    if existing_invoice:
        invoice_link = frappe.utils.get_url_to_form("Purchase Invoice", existing_invoice)
        frappe.throw(f"El NCF generado ({nuevo_ncf}) ya ha sido usado en otra factura de venta: <a href='{invoice_link}'>{existing_invoice}</a>")


def validate_unique_ncf_by_supplier(supplier, ncf):
    """Valida que el NCF sea único por suplidor."""
    filters = {
        "bill_no": ncf,
        # "supplier": supplier,
        "docstatus": 1
    }
    purchase_invoice = frappe.db.exists("Purchase Invoice", filters)
    if purchase_invoice:
        purchase_invoice_link = f'<a class="bold" href="/app/purchase-invoice/{purchase_invoice}">{purchase_invoice}</a>'
        frappe.throw(_("El NCF debe ser único por suplidor. Existe otra factura con este número de comprobante: " + purchase_invoice_link))

def validate_ncf_with_dgii(rnc, ncf, my_rnc=None, sec_code=None, req_sec_code=False):
    """Valida el NCF con la DGII."""
    # return True
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

    if not doc.bill_no:
        frappe.throw("El número de comprobante fiscal es obligatorio.")

    # Verificar si es una nota de débito y que el NCF del suplidor tenga el prefijo B04
    if doc.is_return and not doc.bill_no.startswith("B04"):
        frappe.throw("El NCF de una nota de crédito del suplidor, debe tener el prefijo 'B04'.")

    my_tax_id = frappe.get_value("Company", doc.company, "tax_id")
    if not my_tax_id:
        frappe.throw("Favor ingresar el RNC en la compañía (sin guiones).")

    # validate_unique_ncf_by_supplier(doc.supplier, doc.bill_no)

    if not validate_ncf_with_dgii(doc.tax_id, doc.bill_no, my_rnc=my_tax_id, sec_code=doc.custom_security_code, req_sec_code=doc.custom_require_security_code):
        print(f"doc.tax_id: {doc.tax_id}, doc.bill_no: {doc.bill_no}, my_rnc: {my_tax_id}, sec_code: {doc.custom_security_code}, req_sec_code: {doc.custom_require_security_code}")
        frappe.throw(_("Número de Comprobante Fiscal <b>NO VÁLIDO</b>."))