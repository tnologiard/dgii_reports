// Copyright (c) 2024, TnologiaRD and contributors
// For license information, please see license.txt

frappe.ui.form.on('Comprobantes Fiscales NCF', {
    refresh: function(frm) {
        // Validar al cargar el formulario
        frm.trigger('validate_sequences');
        frm.trigger('validate_dates');
    },
    secuencia_actual: function(frm) {
        // Validar cuando se cambia la secuencia actual
        frm.trigger('validate_sequences');
    },
    secuencia_final: function(frm) {
        // Validar cuando se cambia la secuencia final
        frm.trigger('validate_sequences');
    },
    expira_el: function(frm) {
        // Validar cuando se cambia la fecha de vencimiento
        frm.trigger('validate_dates');
    },
    validate_sequences: function(frm) {
        // Verificar que los campos no estén vacíos
        if (frm.doc.secuencia_actual != null && frm.doc.secuencia_final != null) {
            if (frm.doc.secuencia_actual == frm.doc.secuencia_final) {
                frappe.msgprint({
                    title: __('Advertencia'),
                    indicator: 'orange',
                    message: __('La secuencia actual coincide con la secuencia final.')
                });
            }
        }
    },
    validate_dates: function(frm) {
        const today = frappe.datetime.get_today();
        // Verificar que la fecha de vencimiento no esté vacía
        if (frm.doc.expira_el) {
            if (frm.doc.expira_el == today) {
                frappe.msgprint({
                    title: __('Advertencia'),
                    indicator: 'orange',
                    message: __('La fecha actual coincide con la fecha de vencimiento.')
                });
            }
        }
    }
});
