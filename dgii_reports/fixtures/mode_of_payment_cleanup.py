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
