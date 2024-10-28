frappe.ui.form.on("Sales Invoice", {
    onload: function(frm) {
        // Limpiar campos bill_no y vencimiento_ncf si es una nota de débito y está en estado "Nuevo"
        if (frm.doc.is_return && frm.doc.docstatus == 0) {
            synchronize_is_return(frm);
            frm.trgger('is_return'); 
        }
        set_custom_tipo_comprobante_options(frm);

    },
    is_return: function(frm) {
        // Sincronizar con el campo custom_tipo_comprobante
        synchronize_is_return(frm);
    },
    custom_tipo_comprobante: function(frm) {
        if (!frm.doc.custom_tipo_comprobante) {
            // Si el valor es vacío, limpiar los campos custom_ncf
            frm.set_value('custom_ncf', '');
        } else {
            // Si el valor no es vacío, llamar a la función generate_new
            frappe.call({
                method: 'dgii_reports.hook.sales_invoice.generate_new',
                args: {
                    doc: frm.doc
                },
                callback: function(r) {
                    if (r.message) {
                        // Establecer los valores obtenidos en los campos custom_ncf 
                        frm.set_value('custom_ncf', r.message.custom_ncf);
                    }
                }
            });
        }
    }
});

function synchronize_is_return(frm) {
    if (frm.doc.is_return) {
        frm.set_value('custom_tipo_comprobante', 'Notas de Crédito').then(() => {
            frm.refresh_field('custom_tipo_comprobante');
        });
    } else if (frm.doc.custom_tipo_comprobante === 'Notas de Crédito') {
        frm.set_value('custom_tipo_comprobante', '').then(() => {
            frm.refresh_field('custom_tipo_comprobante');
        });
    }
}
frappe.ui.form.on('Sales Invoice', {
    onload: function(frm) {
        set_custom_tipo_comprobante_options(frm);
    }
});

function set_custom_tipo_comprobante_options(frm) {
    frappe.call({
        method: 'dgii_reports.hook.sales_invoice.get_custom_tipo_comprobante_options',
        callback: function(r) {
            if (r.message) {
                frm.set_df_property('custom_tipo_comprobante', 'options', r.message);
            }
        }
    });
}