# import frappe
# from frappe import _
# from frappe.utils import cint
# from dgii_reports.servicios.consultas_web_dgii import ServicioConsultasWebDgii

# def validate(doc, event):
# 	set_taxes(doc)
# 	calculate_totals(doc)
# 	validate_duplicate_ncf(doc)

# def before_submit(doc, event):
# 	generate_new(doc)
# 	validate_against_dgii(doc)

# def calculate_totals(doc):
# 	total_bienes = total_servicios = 0.0

# 	for item in doc.items:
# 		item_type = frappe.db.get_value("Item", item.item_code, "item_type")
# 		if item_type == "Bienes":
# 			total_bienes += item.amount
# 		elif item_type == "Servicios":
# 			total_servicios += item.amount
	
# 	doc.monto_facturado_bienes = total_bienes
# 	doc.monto_facturado_servicios = total_servicios

# def generate_new(doc):
# 	tax_category = frappe.db.get_value("Supplier", doc.supplier, "tax_category")
# 	if doc.bill_no or not tax_category:
# 		return

# 	conf = get_serie_for_(doc)
# 	current = cint(conf.current)

# 	if cint(conf.top) and current >= cint(conf.top):
# 		frappe.throw("Ha llegado al máximo establecido para esta serie de comprobantes!")

# 	current += 1
# 	conf.current = current
# 	conf.db_update()

# 	doc.bill_no = f'{conf.serie.split(".")[0]}{current:08d}'
# 	doc.vencimiento_ncf = conf.expiration
# 	doc.db_update()
# 	frappe.db.commit()

# def get_serie_for_(doc):
# 	supplier_category = frappe.get_value("Supplier", doc.supplier, "tax_category")
# 	if not supplier_category:
# 		frappe.throw(f"Favor seleccionar una categoría de impuestos para el suplidor <a href='/desk#Form/Supplier/{doc.supplier_name}'>{doc.supplier_name}</a>")
	
# 	filters = {
# 		"company": doc.company,
# 		"tax_category": supplier_category,
# 	}
# 	if not frappe.db.exists("Comprobantes Fiscales NCF", filters):
# 		frappe.throw(f"No existe una secuencia de NCF para el tipo {supplier_category}")

# 	return frappe.get_doc("Comprobantes Fiscales NCF", filters)

# def set_taxes(doc):	
# 	conf = frappe.get_single("DGII Settings")
# 	total_itbis = total_legal_tip = total_excise = 0.0

# 	tax_fields = [
# 		(conf.itbis_account, "total_itbis"),
# 		(conf.legal_tip_account, "legal_tip"),
# 		(conf.excise_tax, "excise_tax")
# 	]

# 	for account, field in tax_fields:
# 		if account:
# 			total_amount = sum(row.base_tax_amount_after_discount_amount for row in doc.taxes if row.account_head == account)
# 			doc.set(field, total_amount)

# 	if conf.other_taxes:
# 		for tax in conf.other_taxes:
# 			total_amount = sum(row.base_tax_amount_after_discount_amount for row in doc.taxes if row.account_head == tax.account)
# 			doc.set(tax.tax_type, total_amount)

# def validate_duplicate_ncf(doc):
# 	if not doc.bill_no:
# 		return 

# 	filters = {
# 		"tax_id": doc.tax_id,
# 		"bill_no": doc.bill_no,
# 		"docstatus": 1,
# 		"name": ["!=", doc.name],
# 	}
# 	if frappe.db.exists("Purchase Invoice", filters):
# 		frappe.throw(f"Ya existe una factura registrada a nombre de <b>{doc.supplier_name}</b> con el mismo NCF <b>{doc.bill_no}</b>, favor verificar!")

# def validate_unique_ncf_by_supplier(supplier, ncf):
# 	filters = {
# 		"bill_no": ncf,
# 		"supplier": supplier,
# 		"docstatus": 1
# 	}
# 	purchase_invoice = frappe.db.exists("Purchase Invoice", filters)
# 	if purchase_invoice:
# 		purchase_invoice_link = f'<a class="bold" href="/app/purchase-invoice/{purchase_invoice}">{purchase_invoice}</a>'
# 		frappe.throw(_("NCF must be unique by Supplier. There is another Purchase Invoice with this bill no.: " + purchase_invoice_link))

# def validate_ncf_with_dgii(rnc, ncf, my_rnc=None, sec_code=None, req_sec_code=False):
# 	try:
# 		servicio = ServicioConsultasWebDgii()
# 		respuesta = servicio.consultar_ncf(ncf, rnc, my_rnc=my_rnc, sec_code=sec_code, req_sec_code=req_sec_code)
# 		return respuesta.success and respuesta.estado in ["VIGENTE", "VENCIDO", "Aceptado"]
# 	except Exception as e:
# 		frappe.log_error(message=str(e), title="Error en validate_ncf_with_dgii")
# 		return False

# def validate_against_dgii(doc):
# 	if not doc.tax_id:
# 		return

# 	if not doc.bill_no:
# 		frappe.throw("El número de comprobante fiscal es obligatorio.")

# 	my_tax_id = frappe.get_value("Company", doc.company, "tax_id")
# 	if not my_tax_id:
# 		frappe.throw("Favor ingresar el RNC en la compañía (sin guiones).")

# 	validate_unique_ncf_by_supplier(doc.supplier, doc.bill_no)

# 	if not validate_ncf_with_dgii(doc.tax_id, doc.bill_no, my_rnc=my_tax_id, sec_code=doc.security_code, req_sec_code=doc.require_security_code):
# 		frappe.throw(_("Número de Comprobante Fiscal <b>NO VÁLIDO</b>."))


import frappe
from frappe import _
from frappe.utils import cint
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
    generate_new(doc)
    validate_against_dgii(doc)

def calculate_totals(doc):
    """Calcula los totales de bienes y servicios en el documento."""
    total_bienes = total_servicios = 0.0

    for item in doc.items:
        item_type = frappe.db.get_value("Item", item.item_code, "item_type")
        if item_type == "Bienes":
            total_bienes += item.amount
        elif item_type == "Servicios":
            total_servicios += item.amount
    
    doc.monto_facturado_bienes = total_bienes
    doc.monto_facturado_servicios = total_servicios

def generate_new(doc):
    """Genera un nuevo número de comprobante fiscal para el documento."""
    tax_category = frappe.db.get_value("Supplier", doc.supplier, "tax_category")
    if doc.bill_no or not tax_category:
        return

    conf = get_serie_for_(doc)
    current = cint(conf.current)

    if cint(conf.top) and current >= cint(conf.top):
        frappe.throw("¡Ha llegado al máximo establecido para esta serie de comprobantes!")

    current += 1
    conf.current = current
    conf.db_update()

    doc.bill_no = f'{conf.serie.split(".")[0]}{current:08d}'
    doc.vencimiento_ncf = conf.expiration
    doc.db_update()
    frappe.db.commit()

def get_serie_for_(doc):
    """Obtiene la serie de comprobantes fiscales para el suplidor."""
    supplier_category = frappe.get_value("Supplier", doc.supplier, "tax_category")
    if not supplier_category:
        frappe.throw(f"Favor seleccionar una categoría de impuestos para el suplidor <a href='/desk#Form/Supplier/{doc.supplier_name}'>{doc.supplier_name}</a>")
    
    filters = {
        "company": doc.company,
        "tax_category": supplier_category,
    }
    if not frappe.db.exists("Comprobantes Fiscales NCF", filters):
        frappe.throw(f"No existe una secuencia de NCF para el tipo {supplier_category}")

    return frappe.get_doc("Comprobantes Fiscales NCF", filters)

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

def validate_duplicate_ncf(doc):
    """Valida si el NCF ya existe para el proveedor en una factura activa."""
    if not doc.bill_no:
        return 

    filters = {
        "tax_id": doc.tax_id,
        "bill_no": doc.bill_no,
        "docstatus": 1,
        "name": ["!=", doc.name],
    }
    if frappe.db.exists("Purchase Invoice", filters):
        frappe.throw(f"Ya existe una factura registrada a nombre de <b>{doc.supplier_name}</b> con el mismo NCF <b>{doc.bill_no}</b>, ¡favor verificar!")

def validate_unique_ncf_by_supplier(supplier, ncf):
    """Valida que el NCF sea único por proveedor."""
    filters = {
        "bill_no": ncf,
        "supplier": supplier,
        "docstatus": 1
    }
    purchase_invoice = frappe.db.exists("Purchase Invoice", filters)
    if purchase_invoice:
        purchase_invoice_link = f'<a class="bold" href="/app/purchase-invoice/{purchase_invoice}">{purchase_invoice}</a>'
        frappe.throw(_("El NCF debe ser único por proveedor. Existe otra factura con este número de comprobante: " + purchase_invoice_link))

def validate_ncf_with_dgii(rnc, ncf, my_rnc=None, sec_code=None, req_sec_code=False):
    """Valida el NCF con la DGII."""
    try:
        servicio = ServicioConsultasWebDgii()
        respuesta = servicio.consultar_ncf(ncf, rnc, my_rnc=my_rnc, sec_code=sec_code, req_sec_code=req_sec_code)
        return respuesta.success and respuesta.estado in ["VIGENTE", "VENCIDO", "Aceptado"]
    except Exception as e:
        frappe.log_error(message=str(e), title="Error en validate_ncf_with_dgii")
        return False

def validate_against_dgii(doc):
    """Valida el NCF contra la DGII y verifica su validez."""
    if not doc.tax_id:
        return

    if not doc.bill_no:
        frappe.throw("El número de comprobante fiscal es obligatorio.")

    my_tax_id = frappe.get_value("Company", doc.company, "tax_id")
    if not my_tax_id:
        frappe.throw("Favor ingresar el RNC en la compañía (sin guiones).")

    validate_unique_ncf_by_supplier(doc.supplier, doc.bill_no)

    if not validate_ncf_with_dgii(doc.tax_id, doc.bill_no, my_rnc=my_tax_id, sec_code=doc.security_code, req_sec_code=doc.require_security_code):
        frappe.throw(_("Número de Comprobante Fiscal <b>NO VÁLIDO</b>."))
