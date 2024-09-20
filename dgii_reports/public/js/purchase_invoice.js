frappe.ui.form.on("Purchase Invoice", {
    onload: function(frm) {
        // Obtener el documento DGII Reports Settings
        frappe.db.get_single_value('DGII Reports Settings', 'ret606_isr').then(value => {
            frm.isr_account = value;
        });

        frappe.call({
            method: 'frappe.client.get',
            args: {
                doctype: 'DGII Reports Settings',
                name: 'DGII Reports Settings'
            },
            callback: function(r) {
                if (r.message) {
                    const doc = r.message;
                    // Acceder a los valores de los campos con el prefijo 'ret606_'
                    const retention_link_values = Object.keys(doc)
                        .filter(key => key.startsWith('ret606_') && doc[key])
                        .map(key => doc[key]);

                        frm.retention_link_values = retention_link_values;
                    check_retention_type_visibility(frm);
                }
            },
            error: function(error) {
                console.error('Error al recuperar el documento DGII Reports Settings:', error);
            }
        });

        // Verificar el estado inicial de los checkboxes
        handle_checkbox_state(frm);

        // Limpiar campos bill_no y tax_category si es una nota de débito y está en estado "Nuevo"
        if (frm.doc.is_return && frm.doc.docstatus == 0) {
            frm.set_value('bill_no', '');
            frm.set_value('tax_category', '');
        }
    },
    refresh: function(frm) {
        // Verificar si los elementos necesarios existen antes de llamar a las funciones
        if (frm.retention_link_values && frm.isr_account) {
            check_retention_type_visibility(frm);
        }
        if (frm.isr_account) {
            handle_checkbox_state(frm);
        }
    },
    // Se ejecuta cuando se valida el formulario antes de guardar
    validate(frm) {
        // Llama a las funciones de validación y ajuste de campos específicos
        if (!frm.doc.custom_is_b13 == 1 || !frm.doc.custom_is_b11 == 1) {
            frm.trigger("bill_no");
            frm.trigger("validate_cost_center");
            frm.trigger("validate_ncf");
            }
            if (!frm.doc.tax_id) {
                if (frm.doc.custom_is_b13) {
                    // Obtener el tax_id de la compañía y asignarlo al documento
                    frappe.db.get_value("Company", frm.doc.company, "tax_id", (r) => {
                        if (r && r.tax_id) {
                            frm.set_value("tax_id", r.tax_id);
                        }
                    });
                } else {
                    // Solicitar el RNC / Cédula del proveedor
                    frappe.prompt(
                        [
                            {
                                'fieldname': 'tax_id',
                                'fieldtype': 'Data',
                                'label': 'RNC / Cédula del proveedor',
                                'reqd': 1
                            }
                        ],
                        function(values){
                            // Actualizar el proveedor y el campo tax_id del documento
                            frappe.db.set_value("Supplier", frm.doc.supplier, "tax_id", values.tax_id);
                            frm.set_value("tax_id", values.tax_id);
                        },
                        'Favor proporcionar el RNC / Cédula del proveedor',
                        'Actualizar'
                    );
                    frappe.validated = false; // Detener el flujo hasta que se proporcione el tax_id
                }
            }
    
    },

    // Ajusta el comportamiento del campo bill_no
    bill_no(frm) {
        let {bill_no} = frm.doc;  // Extrae el valor de bill_no del documento actual

        // Establece el campo vencimiento_ncf como requerido si hay un valor en bill_no
        frm.set_df_property("vencimiento_ncf", "reqd", !!bill_no);
        
        if (!bill_no)
            return;  // Si bill_no está vacío, no hace nada más
        
        // Formatea el valor de bill_no eliminando espacios y convirtiéndolo a mayúsculas
        frm.set_value("bill_no", bill_no.trim().toUpperCase());

        // Dispara la validación del NCF si la longitud es 11 o 13
        if ([11, 13].includes(bill_no.length)) {
            frm.trigger("validate_ncf");
        }
    },

    // Valida el número de comprobante fiscal (NCF)
    validate_ncf(frm) {
        let len = frm.doc.bill_no.length;  // Obtiene la longitud del bill_no
        let valid_prefix = ["B01", "B04", "B11", "B13", "B14", "B15", "E31", "E34"];  // Prefijos válidos

        // Verifica si la longitud de bill_no es 11 o 13 caracteres
        if (![11, 13].includes(len)) {
            // Muestra un mensaje de error si la longitud no es válida
            frappe.msgprint(`El número de comprobante tiene <b>${len}</b> caracteres, deben ser <b>11</b> o <b>13</b> para la serie E.`);
            frappe.validated = false;  // Detiene la validación y evita que se guarde el documento
            frm.set_df_property("custom_security_code", "hidden", 1);  // Oculta el campo custom_security_code
            frm.set_df_property("custom_security_code", "reqd", 0);  // Hace que custom_security_code no sea obligatorio
            frm.set_value("custom_require_security_code", false);  // Establece custom_require_security_code a false
            return;
        }

        // Verifica si el prefijo del bill_no es válido
        if (frm.doc.bill_no && !valid_prefix.includes(frm.doc.bill_no.substr(0, 3))) {
            // Muestra un mensaje de error si el prefijo no es válido
            frappe.msgprint(`El prefijo <b>${frm.doc.bill_no.substr(0, 3)}</b> del NCF ingresado no es válido.`);
            frappe.validated = false;  // Detiene la validación y evita que se guarde el documento
            frm.set_df_property("custom_security_code", "hidden", 1);  // Oculta el campo custom_security_code
            frm.set_df_property("custom_security_code", "reqd", 0);  // Hace que custom_security_code no sea obligatorio
            frm.set_value("custom_require_security_code", false);  // Establece custom_require_security_code a false
            return;
        }

        // Verifica si el prefijo del bill_no comienza con "E"
        if (frm.doc.bill_no && frm.doc.bill_no.startsWith("E")) {
            frm.set_df_property("custom_security_code", "hidden", 0);  // Muestra el campo custom_security_code
            frm.set_df_property("custom_security_code", "reqd", 1);  // Hace que custom_security_code sea obligatorio
            frm.set_value("custom_require_security_code", true);  // Establece custom_require_security_code a true
        } else {
            frm.set_df_property("custom_security_code", "hidden", 1);  // Oculta el campo custom_security_code
            frm.set_df_property("custom_security_code", "reqd", 0);  // Hace que custom_security_code no sea obligatorio
            frm.set_value("custom_require_security_code", false);  // Establece custom_require_security_code a false
        }
    },

    validate_ncf(frm) {
        let len = frm.doc.bill_no.length;  // Obtiene la longitud del bill_no
        let valid_prefix = ["B01", "B04", "B11", "B13", "B14", "B15", "E31", "E34"];  // Prefijos válidos
        
        // Verifica si los campos custom_is_b11 o custom_is_b13 no están seleccionados
        if (!frm.doc.custom_is_b11 && !frm.doc.custom_is_b13) {
            // Verifica si la longitud de bill_no es 11 o 13 caracteres
            if (![11, 13].includes(len)) {
                // Muestra un mensaje de error si la longitud no es válida
                frappe.msgprint(`El número de comprobante tiene <b>${len}</b> caracteres, deben ser <b>11</b> o <b>13</b> para la serie E.`);
                frappe.validated = false;  // Detiene la validación y evita que se guarde el documento
                frm.set_df_property("custom_security_code", "hidden", 1);  // Oculta el campo custom_security_code
                frm.set_df_property("custom_security_code", "reqd", 0);  // Hace que custom_security_code no sea obligatorio
                frm.set_value("custom_require_security_code", false);  // Establece custom_require_security_code a false
                return;
            }
        
            // Verifica si el prefijo del bill_no es válido
            if (frm.doc.bill_no && !valid_prefix.includes(frm.doc.bill_no.substr(0, 3))) {
                // Muestra un mensaje de error si el prefijo no es válido
                frappe.msgprint(`El prefijo <b>${frm.doc.bill_no.substr(0, 3)}</b> del NCF ingresado no es válido.`);
                frappe.validated = false;  // Detiene la validación y evita que se guarde el documento
                frm.set_df_property("custom_security_code", "hidden", 1);  // Oculta el campo custom_security_code
                frm.set_df_property("custom_security_code", "reqd", 0);  // Hace que custom_security_code no sea obligatorio
                frm.set_value("custom_require_security_code", false);  // Establece custom_require_security_code a false
                return;
            }
        
            // Verifica si el prefijo del bill_no comienza con "E"
            if (frm.doc.bill_no && frm.doc.bill_no.startsWith("E")) {
                frm.set_df_property("custom_security_code", "hidden", 0);  // Muestra el campo custom_security_code
                frm.set_df_property("custom_security_code", "reqd", 1);  // Hace que custom_security_code sea obligatorio
                frm.set_value("custom_require_security_code", true);  // Establece custom_require_security_code a true
            } else {
                frm.set_df_property("custom_security_code", "hidden", 1);  // Oculta el campo custom_security_code
                frm.set_df_property("custom_security_code", "reqd", 0);  // Hace que custom_security_code no sea obligatorio
                frm.set_value("custom_require_security_code", false);  // Establece custom_require_security_code a false
            }
        }
    },

    // Valida la longitud del número de identificación fiscal (RNC o cédula)
    validate_rnc(frm) {
        let len = frm.doc.tax_id.length;  // Obtiene la longitud del tax_id

        // Verifica si la longitud de tax_id es 9 o 11 caracteres
        if (![9, 11].includes(len)) {
            // Muestra un mensaje de error si la longitud no es válida
            frappe.msgprint(`El RNC/Cédula ingresados tiene <b>${len}</b> caracteres, favor verificar. Deben ser 9 u 11.`);
            frappe.validated = false;  // Detiene la validación y evita que se guarde el documento
            return;
        }
    },

    // Asigna el centro de costos si no está definido en impuestos o artículos
    validate_cost_center(frm) {
        if (!frm.doc.cost_center)
            return;  // Si no hay un centro de costos en el documento, no hace nada
        
        // Asigna el centro de costos del documento a cada impuesto que no tenga uno definido
        $.map(frm.doc.taxes, tax => {
            if (!tax.cost_center)
                tax.cost_center = frm.doc.cost_center;
        });

        // Asigna el centro de costos del documento a cada artículo que no tenga uno definido
        $.map(frm.doc.items, item => {
            if (!item.cost_center)
                item.cost_center = frm.doc.cost_center;
        });
    },

    // Elimina los guiones del tax_id y lo valida
    tax_id(frm) {
        if (!frm.doc.tax_id)
            return;  // Si no hay tax_id, no hace nada
        
        // Elimina los guiones del tax_id y lo valida
        frm.set_value("tax_id", replace_all(frm.doc.tax_id.trim(), "-", ""));
        frm.trigger("validate_rnc");
    },

});

frappe.ui.form.on('Purchase Taxes and Charges', {
    account_head: function(frm, cdt, cdn) {
        check_retention_type_visibility(frm);
    },
    taxes_remove: function(frm) {
        check_retention_type_visibility(frm);
    },
    taxes_add: function(frm) {
        check_retention_type_visibility(frm);
    }
});

function check_retention_type_visibility(frm) {
    let show_retention_type = false;
    frm.doc.taxes.forEach(function(tax) {
        frm.retention_link_values.forEach(value => {
            if (tax.account_head === value) {
                frappe.model.set_value(tax.doctype, tax.name, 'is_tax_withholding_account', 1);
                frappe.model.set_value(tax.doctype, tax.name, 'add_deduct_tax', "Deduct");
                if(tax.account_head == frm.isr_account) {
                    show_retention_type = true;
                }
            }
        });
    });

    frm.toggle_display('retention_type', show_retention_type);
    frm.toggle_reqd('retention_type', show_retention_type);
}

function handle_checkbox_state(frm) {
    // Verificar la existencia de los elementos antes de agregar eventos
    if (frm.fields_dict.is_return && frm.fields_dict.is_return.$input) {
        frm.fields_dict.is_return.$input.on('change', function() {
            if (frm.get_field('is_return').get_value()) {
                frm.set_value('custom_is_b11', 0);
                frm.set_value('custom_is_b13', 0);
                frm.toggle_enable('custom_is_b11', false);
                frm.toggle_enable('custom_is_b13', false);
            } else {
                frm.toggle_enable('custom_is_b11', true);
                frm.toggle_enable('custom_is_b13', true);
            }
            update_bill_no_label(frm);
        });
    }

    if (frm.fields_dict.custom_is_b11 && frm.fields_dict.custom_is_b11.$input) {
        frm.fields_dict.custom_is_b11.$input.on('change', function() {
            if (frm.get_field('custom_is_b11').get_value()) {
                frm.set_value('is_return', 0);
                frm.set_value('custom_is_b13', 0);
                frm.toggle_enable('is_return', false);
                frm.toggle_enable('custom_is_b13', false);
            } else {
                frm.toggle_enable('is_return', true);
                frm.toggle_enable('custom_is_b13', true);
            }
            update_bill_no_label(frm);
        });
    }

    if (frm.fields_dict.custom_is_b13 && frm.fields_dict.custom_is_b13.$input) {
        frm.fields_dict.custom_is_b13.$input.on('change', function() {
            if (frm.get_field('custom_is_b13').get_value()) {
                frm.set_value('is_return', 0);
                frm.set_value('custom_is_b11', 0);
                frm.toggle_enable('is_return', false);
                frm.toggle_enable('custom_is_b11', false);
            } else {
                frm.toggle_enable('is_return', true);
                frm.toggle_enable('custom_is_b11', true);
            }
            update_bill_no_label(frm);
        });
    }

    function update_bill_no_label(frm) {
        if (frm.get_field('custom_is_b11').get_value() || frm.get_field('custom_is_b13').get_value()) {
            frm.set_df_property('bill_no', 'label', 'NCF');
            frm.set_df_property('bill_date', 'label', 'Fecha de Comprobante');
            frm.set_value('bill_date', frm.doc.posting_date); 
            frm.set_df_property('vencimiento_ncf', 'reqd', 0);
            // frm.set_df_property('bill_no', 'read_only', 1); 
        } else {
            frm.set_df_property('bill_no', 'label', 'NCF Suplidor');
            frm.set_df_property('bill_date', 'label', 'Fecha de Factura del Suplidor');
            frm.set_value('bill_date', ''); 
            frm.set_df_property('vencimiento_ncf', 'reqd', 1); 
            // frm.set_df_property('bill_no', 'read_only', 0); 
        }
    }
}