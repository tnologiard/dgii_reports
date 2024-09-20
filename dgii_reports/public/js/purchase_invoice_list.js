frappe.provide('dgii_reports.bulk_operations');
// frappe.require('/assets/dgii_reports/js/custom_bulk_operations.js'); 

// Verificar si frappe.views.ListView y get_actions_menu_items están definidos
if (typeof frappe.views.ListView !== 'undefined' && typeof frappe.views.ListView.prototype.get_actions_menu_items !== 'undefined') {
    const original_get_actions_menu_items = frappe.views.ListView.prototype.get_actions_menu_items;

    frappe.views.ListView.prototype.get_actions_menu_items = function() {
        const actions_menu_items = original_get_actions_menu_items.apply(this, arguments);

        // Iterar sobre los elementos de actions_menu_items
        actions_menu_items.forEach((item, index) => {
            // Identificar la acción de Cancelar
            if (item.label === 'Cancelar') {
                // Sobrescribir la acción de Cancelar
                item.action = () => {
                    // Invocar la función submit_or_cancel con confirmación
                    const docnames = this.get_checked_items().map(doc => doc.name);
                    if (docnames.length > 0) {
                        frappe.confirm(
                            __("Cancel {0} documents?", [docnames.length]),
                            () => {
                                this.disable_list_update = true;
                                dgii_reports.bulk_operations.submit_or_cancel.call(this, docnames, 'cancel', () => {
                                    this.disable_list_update = false;
                                    this.clear_checked_items();
                                    this.refresh();
                                });
                            }
                        );
                    }
                };
            }
        });

        return actions_menu_items;
    };
}
