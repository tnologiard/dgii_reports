import frappe
        
def delete_modes_if_not_custom():
    print("Eliminando modos de pago standard de ErpNext...")
    frappe.db.sql("DELETE FROM `tabMode of Payment`")
    frappe.db.commit()
    print("Modos de pago eliminados con éxito.")
