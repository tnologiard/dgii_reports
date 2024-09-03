frappe.ui.form.on('Sales Invoice', {
    onload: function(frm) {
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
                // Verificar si el doctype es Sales Invoice o Purchase Invoice
                if (me.doctype === 'Sales Invoice' || me.doctype === 'Purchase Invoice') {
                    prompt_for_cancellation_reason(me).then(() => {
                        cancel_doc();
                    }).catch(() => {
                        me.handle_save_fail(btn, on_error);
                    });
                } else {
                    // Si no es Sales Invoice o Purchase Invoice, proceder con la cancelación sin solicitar razón
                    cancel_doc();
                }
            };

            if (skip_confirm) {
                prompt_and_cancel();
            } else {
                frappe.confirm(
                    __("Permanently Cancel {0}?", [this.docname]),
                    prompt_and_cancel,
                    me.handle_save_fail(btn, on_error)
                );
            }
        };
    }
});

frappe.ui.form.on('Purchase Invoice', {
    onload: function(frm) {
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
                // Verificar si el doctype es Sales Invoice o Purchase Invoice
                if (me.doctype === 'Sales Invoice' || me.doctype === 'Purchase Invoice') {
                    prompt_for_cancellation_reason(me).then(() => {
                        cancel_doc();
                    }).catch(() => {
                        me.handle_save_fail(btn, on_error);
                    });
                } else {
                    // Si no es Sales Invoice o Purchase Invoice, proceder con la cancelación sin solicitar razón
                    cancel_doc();
                }
            };

            if (skip_confirm) {
                prompt_and_cancel();
            } else {
                frappe.confirm(
                    __("Permanently Cancel {0}?", [this.docname]),
                    prompt_and_cancel,
                    me.handle_save_fail(btn, on_error)
                );
            }
        };
    }
});