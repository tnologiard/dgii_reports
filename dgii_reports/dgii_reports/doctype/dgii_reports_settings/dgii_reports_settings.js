frappe.ui.form.on('DGII Reports Settings', {
    refresh: function(frm) {
        // Agregar botón en el footer de la tabla purchase_ncf_list_settings
        frm.fields_dict['purchase_ncf_list_settings'].grid.add_custom_button(__('Cargar todos los comprobantes'), function() {
            cargar_todos_los_comprobantes(frm, 'purchase_ncf_list_settings');
        });

        // Agregar botón en el footer de la tabla sales_ncf_list_settings
        frm.fields_dict['sales_ncf_list_settings'].grid.add_custom_button(__('Cargar todos los comprobantes'), function() {
            cargar_todos_los_comprobantes(frm, 'sales_ncf_list_settings');
        });
    }
});

function cargar_todos_los_comprobantes(frm, table_fieldname) {
    frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: 'Tipo Comprobante Fiscal',
            fields: ['name', 'codigo']
        },
        callback: function(response) {
            let comprobantes = response.message;
            if (comprobantes) {
                // Separar los códigos que se pueden convertir a número y los que no
                let numeric_comprobantes = comprobantes.filter(c => !isNaN(c.codigo)).sort((a, b) => parseFloat(a.codigo) - parseFloat(b.codigo));
                let non_numeric_comprobantes = comprobantes.filter(c => isNaN(c.codigo)).sort((a, b) => a.codigo.localeCompare(b.codigo));

                // Concatenar las listas ordenadas
                let sorted_comprobantes = numeric_comprobantes.concat(non_numeric_comprobantes);

                sorted_comprobantes.forEach(comprobante => {
                    let new_row = frm.add_child(table_fieldname);
                    frappe.model.set_value(new_row.doctype, new_row.name, 'tipo_comprobante_fiscal', comprobante.name);
                    frappe.model.set_value(new_row.doctype, new_row.name, 'code', comprobante.codigo);
                    frappe.model.set_value(new_row.doctype, new_row.name, 'visible_en_factura', 1);
                    frappe.model.set_value(new_row.doctype, new_row.name, 'visible_en_factura', 0);
                });
                frm.refresh_field(table_fieldname);
            }
        }
    });
}