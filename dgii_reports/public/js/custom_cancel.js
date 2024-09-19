console.log("custom_cancel.js is loaded");

frappe.ui.form.on('Sales Invoice', {
    onload: function(frm) {
        console.log("Sales Invoice form loaded");
        frm._cancel = function(btn, callback, on_error, skip_confirm) {
            const me = this;

            const prompt_for_cancellation_reason = (frm) => {
                return new Promise((resolve, reject) => {
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
                                frappe.db.set_value(frm.doctype, frm.docname, 'custom_codigo_de_anulacion', r.codigo)
                                    .then(() => {
                                        resolve();
                                    })
                                    .catch((error) => {
                                        console.error("Error setting value:", error);
                                        reject();
                                    });
                            } else {
                                reject();
                            }
                        });
                    },
                    'Razón de Cancelación',
                    'Cancelar');
                });
            };

            const cancel_doc = () => {
                frappe.validated = true;
                me.script_manager.trigger("before_cancel").then(() => {
                    if (!frappe.validated) {
                        return me.handle_save_fail(btn, on_error);
                    }

                    var after_cancel = function (r) {
                        if (r.exc) {
                            me.handle_save_fail(btn, on_error);
                        } else {
                            frappe.utils.play_sound("cancel");
                            me.refresh();
                            callback && callback();
                            me.script_manager.trigger("after_cancel");
                        }
                    };
                    frappe.ui.form.save(me, "cancel", after_cancel, btn);
                });
            };

            const prompt_and_cancel = () => {
                console.log("prompt_and_cancel called");
                // Verificar si el doctype es Sales Invoice o Purchase Invoice
                if (frm.doc.doctype === 'Sales Invoice') {
                    const ncf = frm.doc.custom_ncf || '';
                    console.log("Sales Invoice NCF:", ncf);
                    if (ncf && ['B01', 'B04', 'B14', 'B15', 'B16'].some(prefix => ncf.startsWith(prefix))) {
                        console.log("Prompting for cancellation reason for Sales Invoice");
                        prompt_for_cancellation_reason(frm).then(() => {
                            cancel_doc();
                        }).catch(() => {
                            me.handle_save_fail(btn, on_error);
                        });
                    } else {
                        cancel_doc();
                    }
                } else if (frm.doc.doctype === 'Purchase Invoice') {
                    const ncf = frm.doc.bill_no || '';
                    console.log("Purchase Invoice NCF:", ncf);
                    if (ncf && ['B11', 'B13'].some(prefix => ncf.startsWith(prefix))) {
                        console.log("Prompting for cancellation reason for Purchase Invoice");
                        prompt_for_cancellation_reason(frm).then(() => {
                            cancel_doc();
                        }).catch(() => {
                            me.handle_save_fail(btn, on_error);
                        });
                    } else {
                        cancel_doc();
                    }
                } else {
                    // Si no es Sales Invoice o Purchase Invoice, proceder con la cancelación sin solicitar razón
                    cancel_doc();
                }
            };

            if (skip_confirm) {
                prompt_and_cancel();
            } else {
                frappe.confirm(
                    __("Permanently Cancel {0}?", [frm.docname]),
                    function() {
                        console.log("User confirmed cancellation");
                        prompt_and_cancel();
                    },
                    function() {
                        console.log("User cancelled the confirmation dialog");
                        me.handle_save_fail(btn, on_error);
                    }
                );
            }
        };
    }
});

frappe.ui.form.on('Purchase Invoice', {
    onload: function(frm) {
        console.log("Purchase Invoice form loaded");
        frm._cancel = function(btn, callback, on_error, skip_confirm) {
            const me = this;

            const prompt_for_cancellation_reason = (frm) => {
                return new Promise((resolve, reject) => {
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
                                frappe.db.set_value(frm.doctype, frm.docname, 'custom_codigo_de_anulacion', r.codigo)
                                    .then(() => {
                                        resolve();
                                    })
                                    .catch((error) => {
                                        console.error("Error setting value:", error);
                                        reject();
                                    });
                            } else {
                                reject();
                            }
                        });
                    },
                    'Razón de Cancelación',
                    'Cancelar');
                });
            };

            const cancel_doc = () => {
                frappe.validated = true;
                me.script_manager.trigger("before_cancel").then(() => {
                    if (!frappe.validated) {
                        return me.handle_save_fail(btn, on_error);
                    }

                    var after_cancel = function (r) {
                        if (r.exc) {
                            me.handle_save_fail(btn, on_error);
                        } else {
                            frappe.utils.play_sound("cancel");
                            me.refresh();
                            callback && callback();
                            me.script_manager.trigger("after_cancel");
                        }
                    };
                    frappe.ui.form.save(me, "cancel", after_cancel, btn);
                });
            };

            const prompt_and_cancel = () => {
                console.log("prompt_and_cancel called");
                // Verificar si el doctype es Sales Invoice o Purchase Invoice
                if (frm.doc.doctype === 'Sales Invoice') {
                    const ncf = frm.doc.custom_ncf || '';
                    console.log("Sales Invoice NCF:", ncf);
                    if (ncf && ['B01', 'B04', 'B14', 'B15', 'B16'].some(prefix => ncf.startsWith(prefix))) {
                        console.log("Prompting for cancellation reason for Sales Invoice");
                        prompt_for_cancellation_reason(frm).then(() => {
                            cancel_doc();
                        }).catch(() => {
                            me.handle_save_fail(btn, on_error);
                        });
                    } else {
                        cancel_doc();
                    }
                } else if (frm.doc.doctype === 'Purchase Invoice') {
                    const ncf = frm.doc.bill_no || '';
                    console.log("Purchase Invoice NCF:", ncf);
                    if (ncf && ['B11', 'B13'].some(prefix => ncf.startsWith(prefix))) {
                        console.log("Prompting for cancellation reason for Purchase Invoice");
                        prompt_for_cancellation_reason(frm).then(() => {
                            cancel_doc();
                        }).catch(() => {
                            me.handle_save_fail(btn, on_error);
                        });
                    } else {
                        cancel_doc();
                    }
                } else {
                    // Si no es Sales Invoice o Purchase Invoice, proceder con la cancelación sin solicitar razón
                    cancel_doc();
                }
            };

            if (skip_confirm) {
                prompt_and_cancel();
            } else {
                frappe.confirm(
                    __("Permanently Cancel {0}?", [frm.docname]),
                    function() {
                        console.log("User confirmed cancellation");
                        prompt_and_cancel();
                    },
                    function() {
                        console.log("User cancelled the confirmation dialog");
                        me.handle_save_fail(btn, on_error);
                    }
                );
            }
        };
    }
});