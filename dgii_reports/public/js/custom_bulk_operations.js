frappe.provide('dgii_reports.bulk_operations');

// Implementación de submit_or_cancel
dgii_reports.bulk_operations.submit_or_cancel = function(docnames, action = "submit", done = null) {
    action = action.toLowerCase();
    const task_id = Math.random().toString(36).slice(-5);
    frappe.realtime.task_subscribe(task_id);

    if (action === "cancel" && (this.doctype === "Purchase Invoice" || this.doctype === "Sales Invoice")) {
        const field = this.doctype === "Purchase Invoice" ? "bill_no" : "custom_ncf";
        const prefix = this.doctype === "Purchase Invoice" ? ["B11", "B13"] : ["B01", "B04", "B14", "B15","B16"];
        
        frappe.call({
            method: "frappe.client.get_list",
            args: {
                doctype: this.doctype,
                filters: { name: ["in", docnames] },
                fields: ["name", field, "docstatus"]
            },
            callback: (r) => {
                const docs_to_cancel = r.message.filter(doc => {
                    return doc.docstatus !== 2 && prefix.some(p => doc[field] && doc[field].startsWith(p));
                });

                if (docs_to_cancel.length > 0) {
                    const doc_links = docs_to_cancel.map(doc => `<a href="/app/${this.doctype}/${doc.name}" target="_blank">${doc.name}</a>`).join(", ");
                    const dialog = new frappe.ui.Dialog({
                        title: __("Indique la razón de cancelación"),
                        fields: [
                            {
                                fieldtype: "HTML",
                                options: `<p>${__("Para los Documentos:")} ${doc_links}</p>`
                            },
                            {
                                fieldtype: "Link",
                                label: __("Tipo de Anulación"),
                                fieldname: "tipo_de_anulacion",
                                options: "Tipo de Anulacion",
                                reqd: 1
                            }
                        ],
                        primary_action: (values) => {
                            // Actualizar el campo custom_codigo_de_anulacion antes de cancelar los documentos
                            dgii_reports.bulk_operations.update_custom_codigo_de_anulacion.call(this, docs_to_cancel, values.tipo_de_anulacion)
                                .then(() => {
                                    dgii_reports.bulk_operations.proceed_with_cancellation.call(this, docnames, action, values.tipo_de_anulacion, docs_to_cancel, done);
                                })
                                .catch((error) => {
                                    console.error("Error updating custom_codigo_de_anulacion:", error);
                                });
                            dialog.hide();
                        }
                    });
                    dialog.show();
                } else {
                    dgii_reports.bulk_operations.proceed_with_cancellation.call(this, docnames, action, null, [], done);
                }
            }
        });
    } else {
        dgii_reports.bulk_operations.proceed_with_cancellation.call(this, docnames, action, null, [], done);
    }
}

dgii_reports.bulk_operations.update_custom_codigo_de_anulacion = function(docs_to_cancel, tipo_de_anulacion) {
    return new Promise((resolve, reject) => {
        frappe.call({
            method: "frappe.client.get",
            args: {
                doctype: "Tipo de Anulacion",
                name: tipo_de_anulacion
            },
            callback: (r) => {
                const codigo = r.message.codigo;
                const update_promises = docs_to_cancel.map(doc => {
                    return frappe.db.set_value(this.doctype, doc.name, 'custom_codigo_de_anulacion', codigo);
                });

                Promise.all(update_promises)
                    .then(() => {
                        resolve();
                    })
                    .catch((error) => {
                        reject(error);
                    });
            }
        });
    });
}

dgii_reports.bulk_operations.proceed_with_cancellation = function(docnames, action, tipo_de_anulacion, docs_to_cancel, done) {
    const task_id = Math.random().toString(36).slice(-5);
    frappe.realtime.task_subscribe(task_id);

    return frappe
        .xcall("frappe.desk.doctype.bulk_update.bulk_update.submit_cancel_or_update_docs", {
            doctype: this.doctype,
            action: action,
            docnames: docnames,
            task_id: task_id,
        })
        .then((failed_docnames) => {
            const successful_docnames = docnames.filter(docname => !failed_docnames.includes(docname));
            
            // Manejar documentos fallidos
            if (failed_docnames?.length) {
                const comma_separated_records = frappe.utils.comma_and(failed_docnames);
                frappe.msgprint({
                    title: __('Error'),
                    indicator: 'red',
                    message: __("Cannot cancel {0}.", [comma_separated_records])
                });
            }
            
            // Manejar documentos exitosos
            if (successful_docnames.length) {
                frappe.utils.play_sound(action);
                if (done) done.call(this);  // Asegurarse de que `this` se refiere al contexto correcto
            }
        })
        .finally(() => {
            frappe.realtime.task_unsubscribe(task_id);
        });
}