import frappe
        
def delete_modes_if_not_custom():
    print("Eliminando modos de pago standard de ErpNext...")
    frappe.db.sql("DELETE FROM `tabMode of Payment`")
    frappe.db.commit()
    print("Modos de pago eliminados con éxito.")


def delete_old_custom_fields_purchase_invoice():
    print("Eliminando old custom fields from Purchase Invoice...")

    if frappe.db.exists("Custom Field", "Purchase Invoice-include_retention"):
        frappe.delete_doc("Custom Field", "Purchase Invoice-include_retention")

    if frappe.db.exists("Custom Field", "Purchase Invoice-retention_rate"):
        frappe.delete_doc("Custom Field", "Purchase Invoice-retention_rate")

    if frappe.db.exists("Custom Field", "Purchase Invoice-retention_amount"):
        frappe.delete_doc("Custom Field", "Purchase Invoice-retention_amount")

    if frappe.db.exists("Custom Field", "Purchase Invoice-include_isr"):
        frappe.delete_doc("Custom Field", "Purchase Invoice-include_isr")

    if frappe.db.exists("Custom Field", "Purchase Invoice-isr_rate"):
        frappe.delete_doc("Custom Field", "Purchase Invoice-isr_rate")

    if frappe.db.exists("Custom Field", "Purchase Invoice-isr_amount"):
        frappe.delete_doc("Custom Field", "Purchase Invoice-isr_amount")

    if frappe.db.exists("Custom Field", "Purchase Invoice-total_itbis"):
        frappe.delete_doc("Custom Field", "Purchase Invoice-total_itbis")

    if frappe.db.exists("Custom Field", "Purchase Invoice-supplier_invoice_no"):
        frappe.delete_doc("Custom Field", "Purchase Invoice-supplier_invoice_no")

    print("Se eliminaron los custom fields obsoletos de la Factura de Compra.")


def delete_old_custom_fields_purchase_invoice_I():
    print("Eliminando old custom fields from Purchase Invoice...")

    if frappe.db.exists("Custom Field", "Purchase Invoice-custom_is_b11"):
        frappe.delete_doc("Custom Field", "Purchase Invoice-custom_is_b11")

    if frappe.db.exists("Custom Field", "Purchase Invoice-custom_is_b13"):
        frappe.delete_doc("Custom Field", "Purchase Invoice-custom_is_b13")

    print("Se eliminaron los custom fields obsoletos de la Factura de Compra (2).")


def delete_old_custom_fields_comprobantes_fiscales_ncf():
    print("Eliminando old custom fields from Comprobantes Fiscales NCF...")

    if frappe.db.exists("Custom Field", "Reports Settings-tax_category"):
        frappe.delete_doc("Custom Field", "Reports Settings-tax_category")

    print("Se eliminaron los custom fields obsoletos de Comprobantes Fiscales NCF.")

def delete_old_custom_fields_sales_invoice():
    print("Eliminando old custom fields from Sales Invoice...")

    if frappe.db.exists("Custom Field", "Sales Invoice-custom_is_b14"):
        frappe.delete_doc("Custom Field", "Sales Invoice-custom_is_b14")

    if frappe.db.exists("Custom Field", "Sales Invoice-custom_is_b15"):
        frappe.delete_doc("Custom Field", "Sales Invoice-custom_is_b15")

    if frappe.db.exists("Custom Field", "Sales Invoice-custom_is_b16"):
        frappe.delete_doc("Custom Field", "Sales Invoice-custom_is_b16")

    print("Se eliminaron los custom fields obsoletos de la Factura de Venta.")