frappe.ui.form.on("Sales Invoice", {
    onload: function(frm) {
        // Limpiar campos bill_no y vencimiento_ncf si es una nota de débito y está en estado "Nuevo"
        if (frm.doc.is_return && frm.doc.docstatus == 0) {
            synchronize_is_return(frm);
            // frm.trigger('is_return'); 
        }
        set_custom_tipo_comprobante_options(frm);
        
        // Verificar si es un documento nuevo y el cliente está establecido
        if (frm.is_new() && frm.doc.customer && !frm.doc.is_return && !frm.doc.amended_from) {
            frm.trigger('customer');
        }
    },
    onload_post_render: function(frm) {        
        // Ajustar la altura del campo custom_notes
        adjustTextAreaHeight(frm, ['custom_notes'], '75px');

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
                        frm.set_value('custom_ncf_valido_hasta', r.message.vencimiento_ncf);
                    }
                },
                error: function(r) {
                    // Limpiar los campos custom_ncf si hubo un error
                    frm.set_value('custom_ncf', '');
                    frm.set_value('custom_ncf_valido_hasta', '');
                }
            });
        }
        // Sincronizar con el campo is_return
        if (frm.doc.custom_tipo_comprobante === "Notas de Crédito") {
            frm.set_value('is_return', 1);
        } else if (frm.doc.custom_tipo_comprobante !== "") {
            frm.set_value('is_return', 0);
            frm.set_value('custom_is_internal', 0);
        }
    },
    customer: function(frm) {
        if (frm.doc.customer) {
            // Recuperar el valor del campo custom_default_fiscal_voucher del Customer
            frappe.db.get_value('Customer', frm.doc.customer, 'custom_default_fiscal_voucher', function(value) {
                if (value && value.custom_default_fiscal_voucher) {
                    const default_fiscal_voucher = value.custom_default_fiscal_voucher;

                    // Recuperar la propiedad tipo_comprobante del Tipo Comprobante Fiscal
                    frappe.db.get_value('Tipo Comprobante Fiscal', default_fiscal_voucher, 'tipo_comprobante', function(voucher) {
                        if (voucher && voucher.tipo_comprobante) {
                            const tipo_comprobante = voucher.tipo_comprobante;

                            // Verificar si el valor existe en el campo select custom_tipo_comprobante
                            const options = frm.fields_dict.custom_tipo_comprobante.df.options || [];
                            if (options.includes(tipo_comprobante)) {
                                // Establecer el valor como seleccionado
                                frm.set_value('custom_tipo_comprobante', tipo_comprobante);
                                frappe.show_alert({
                                    message: __('Se estableció el comprobante fiscal predeterminado del cliente: {0}', [tipo_comprobante]),
                                    indicator: 'green'
                                });
                            } else {
                                // Lanzar un mensaje de que el comprobante fiscal predeterminado no está configurado
                                frappe.msgprint(__('El comprobante fiscal predeterminado del cliente es {0}, pero no se ha configurado en DGII Settings para que aparezca en la lista.', [tipo_comprobante]));
                                frm.set_value('custom_tipo_comprobante', '');
                            }
                        } else {
                            // Reinicializar el campo select custom_tipo_comprobante
                            frm.set_value('custom_tipo_comprobante', '');
                            // frappe.msgprint(__('No se encontraron datos para establecer el tipo de comprobante fiscal.'));
                        }
                    });
                } else {
                    // Reinicializar el campo select custom_tipo_comprobante
                    frm.set_value('custom_tipo_comprobante', '');
                    // frappe.msgprint(__('No se encontraron datos para establecer el tipo de comprobante fiscal.'));
                }
            });
        } else {
            // Reinicializar el campo select custom_tipo_comprobante
            frm.set_value('custom_tipo_comprobante', '');
        }
    },
    custom_is_internal: function(frm) {
        if (frm.doc.custom_is_internal) {
            // Limpiar los campos custom_ncf y custom_ncf_valido_hasta
            frm.set_value('custom_ncf', '');
            frm.set_value('custom_ncf_valido_hasta', '');
        } else {
            // Disparar la rutina de custom_tipo_comprobante
            frm.trigger('custom_tipo_comprobante');
        }
    }
});

function synchronize_is_return(frm) {
    if (frm.doc.is_return) {
        frm.set_value('custom_tipo_comprobante', 'Notas de Crédito').then(() => {
            frm.refresh_field('custom_tipo_comprobante');
        });
    } else if (frm.doc.custom_tipo_comprobante === 'Notas de Crédito') {
        frm.set_value('is_return', 1).then(() => {
            frm.refresh_field('custom_tipo_comprobante');
        });
    }
}

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

function adjustTextAreaHeight(frm, fieldNames, height) {
    fieldNames.forEach(fieldName => {
        if (frm.fields_dict[fieldName]) {
            $(frm.fields_dict[fieldName].wrapper).find('textarea').css('height', height);
        }
    });
}