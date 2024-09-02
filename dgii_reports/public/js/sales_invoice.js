frappe.ui.form.on('Sales Invoice', {
    onload: function(frm) {
        // Buscar el botón de cancelar por su atributo data-label
        let cancel_button = cur_frm.page.btn_secondary.filter((index, btn) => $(btn).data('label') === 'Cancelar');
        if (cancel_button.length) {
            $(cancel_button).off('click').on('click', function() {
                prompt_for_cancellation_reason(frm);
            });
        }
    },
});

function prompt_for_cancellation_reason(frm) {
    frappe.prompt([
        {
            label: 'Tipo de Anulación',
            fieldname: 'tipo_de_anulacion',
            fieldtype: 'Link',
            options: 'Tipo de Anulacion',
            reqd: 1
        }
    ],
    function(values) {
        frappe.db.get_value('Tipo de Anulacion', values.tipo_de_anulacion, 'codigo', (r) => {
            if (r && r.codigo) {
                frm.set_value('custom_codigo_de_anulacion', r.codigo).then(() => {
                    // Proceder directamente a la cancelación sin intentar guardar
                    frappe.call({
                        method: 'frappe.client.cancel',
                        args: {
                            doctype: frm.doc.doctype,
                            name: frm.doc.name
                        },
                        callback: function(response) {
                            if (response.message) {
                                frm.reload_doc();
                            }
                        },
                        error: function(error) {
                            console.error("Error cancelling document:", error);
                        }
                    });
                }).catch((error) => {
                    console.error("Error setting value:", error);
                });
            }
        });
    },
    'Razón de Cancelación',
    'Cancelar');
}