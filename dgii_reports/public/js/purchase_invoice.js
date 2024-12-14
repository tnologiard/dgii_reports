frappe.ui.form.on('Purchase Invoice', {
    onload_post_render: function(frm) {        
        // Ajustar la altura del campo custom_notes
        $(frm.fields_dict.custom_notes.wrapper).find('textarea').css('height', '75px');

    },
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

        // Limpiar campos bill_no y vencimiento_ncf si es una nota de débito y está en estado "Nuevo"
        if (frm.doc.is_return && frm.doc.docstatus == 0) {
            frm.set_value('bill_no', '');
            frm.set_value('vencimiento_ncf', '');
            synchronize_is_return(frm);
            frm.trgger('is_return'); 
        }
        update_bill_no_label(frm);

        set_custom_tipo_comprobante_options(frm);

        $(frm.fields_dict.custom_notes.wrapper).find('textarea').css('height', '75px');

    },
    // Se ejecuta cuando se valida el formulario antes de guardar
    validate(frm) {
        console.log("iniciando la validación frm.doc.tax_id", frm.doc.tax_id);
        if (!frm.doc.custom_rnc) {
            const tipo_comprobante = frm.get_field('custom_tipo_comprobante').get_value();
            if (tipo_comprobante === "Comprobante para Gastos Menores") {
                // Obtener el tax_id de la compañía y asignarlo al documento
                frappe.db.get_value("Company", frm.doc.company, "tax_id", (r) => {
                    if (r && r.tax_id) {
                        frm.set_value("tax_id", r.tax_id);
                    }
                });
            } else {
                // Validación adicional para proveedores en DGII Reports Settings
                frappe.call({
                    method: 'frappe.client.get',
                    args: {
                        doctype: 'DGII Reports Settings',
                        name: 'DGII Reports Settings'
                    },
                    callback: function(r) {
                        if (r.message) {
                            const pretty_cash_suppliers = r.message.pretty_cash || [];
                            const supplier_names = pretty_cash_suppliers.map(supplier => supplier.supplier);
    
                            // Comparar el proveedor seleccionado con los proveedores en pretty_cash y verificar si tax_id está vacío
                            if (!supplier_names.includes(frm.doc.supplier)) {
                                // Solicitar el RNC / Cédula del proveedor y actualizar el proveedor
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
                                        frappe.validated = true; // Continuar con la validación
                                    },
                                    'Favor proporcionar el RNC / Cédula del proveedor',
                                    'Actualizar'
                                );
                                frappe.validated = false; // Detener el flujo hasta que se proporcione el tax_id
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
                                        // Actualizar el campo tax_id del documento
                                        frm.set_value("tax_id", values.tax_id);
                                        frappe.validated = true; // Continuar con la validación
                                    },
                                    'Favor proporcionar el RNC / Cédula del proveedor',
                                    'Actualizar'
                                );
                                frappe.validated = false; // Detener el flujo hasta que se proporcione el tax_id
                            }
                        }
                    }
                });
            }
        }
        console.log("terminando la validación frm.doc.tax_id", frm.doc.tax_id);
        if (frm.doc.custom_rnc) {
            // sólo para saltar la validación en caso de que el campo custom_rnc tenga un valor
            // y sea proveedor de caja chica, se guardara como campo vacío
            frm.set_value("tax_id", frm.doc.custom_rnc);
        }
    },
    refresh: function(frm) {
        // Verificar si los elementos necesarios existen antes de llamar a las funciones
        if (frm.retention_link_values && frm.isr_account) {
            check_retention_type_visibility(frm);
        }
        if (frm.isr_account) {
            // handle_checkbox_state(frm);
        }
    
        // Eliminar cualquier evento de clic previo en el campo tax_id
        frm.get_field('custom_rnc').$wrapper.off('click');

        // Agregar evento de clic al campo tax_id si el proveedor cumple la condición
        frappe.call({
            method: 'frappe.client.get',
            args: {
                doctype: 'DGII Reports Settings',
                name: 'DGII Reports Settings'
            },
            callback: function(r) {
                if (r.message) {
                    const pretty_cash_suppliers = r.message.pretty_cash || [];
                    const supplier_names = pretty_cash_suppliers.map(supplier => supplier.supplier);
                    console.log(supplier_names);
                    console.log(frm.doc.supplier);
                    // Comparar el proveedor seleccionado con los proveedores en pretty_cash
                    if (supplier_names.includes(frm.doc.supplier)) {
                        // Hacer que el campo tax_id sea clicable
                        frm.get_field('custom_rnc').$wrapper.on('click', function() {
                            // Solicitar el RNC / Cédula del proveedor
                            frappe.prompt(
                                [
                                    {
                                        'fieldname': 'tax_id',
                                        'fieldtype': 'Data',
                                        'label': 'RNC / Cédula del proveedor',
                                        'reqd': 1,
                                        'default': frm.doc.custom_rnc
                                    }
                                ],
                                function(values){
                                    console.log(values);
                                    console.log(values.tax_id);
                                    // Actualizar el campo tax_id del documento sin disparar el evento supplier nuevamente
                                    frm.set_value("custom_rnc", values.tax_id);
                                },
                                'Favor proporcionar el RNC / Cédula del proveedor',
                                'Actualizar'
                            );
                        });
                    }
                }
            }
        });
        $(frm.fields_dict.custom_notes.wrapper).find('textarea').css('height', '75px');
    },
    custom_tipo_comprobante: function(frm) {
        if (!frm.doc.supplier) {
            // Si el campo supplier no está seleccionado, mostrar un mensaje de error y rechazar el cambio
            frappe.msgprint(__('Seleccione un suplidor'));
            frm.set_value('custom_tipo_comprobante', '');
            return;
        }

        if (!frm.doc.custom_tipo_comprobante) {
            // Si el valor es vacío, limpiar los campos bill_no y vencimiento_ncf
            frm.set_value('bill_no', '');
            frm.set_value('vencimiento_ncf', '');
        } else {
            // Si el valor no es vacío, llamar a la función generate_new
            frappe.call({
                method: 'dgii_reports.hook.purchase_invoice.generate_new',
                args: {
                    doc: frm.doc
                },
                callback: function(r) {
                    if (r.message) {
                        // Establecer los valores obtenidos en los campos bill_no y vencimiento_ncf
                        frm.set_value('bill_no', r.message.bill_no);
                        frm.set_value('vencimiento_ncf', r.message.vencimiento_ncf);
                    }
                },
                error: function(r) {
                    // Limpiar los campos custom_ncf si hubo un error
                    frm.set_value('bill_no', '');
                    frm.set_value('vencimiento_ncf', '');
                }
            });
        }

        // Sincronizar con el campo is_return
        if (frm.doc.custom_tipo_comprobante === "Notas de Crédito") {
            frm.set_value('is_return', 1);
        } else if (frm.doc.custom_tipo_comprobante !== "") {
            frm.set_value('is_return', 0);
        }
        update_bill_no_label(frm);
    },
    supplier: function(frm) {
        // Agregar una bandera para evitar que el evento se dispare dos veces
        if (frm.supplier_event_triggered) {
            return;
        }
        frm.supplier_event_triggered = true;
    
        // Limpiar los campos
        frm.set_value('bill_no', '');
        frm.set_value('vencimiento_ncf', '');
        frm.set_value('custom_tipo_comprobante', '');
        frm.set_value("custom_rnc", '');
    
        // Recuperar el campo pretty_cash del doctype DGII Reports Settings
        frappe.call({
            method: 'frappe.client.get',
            args: {
                doctype: 'DGII Reports Settings',
                name: 'DGII Reports Settings'
            },
            callback: function(r) {
                if (r.message) {
                    const pretty_cash_suppliers = r.message.pretty_cash || [];
                    const supplier_names = pretty_cash_suppliers.map(supplier => supplier.supplier);
    
                    // Comparar el proveedor seleccionado con los proveedores en pretty_cash
                    if (supplier_names.includes(frm.doc.supplier)) {
                        frm.set_value('tax_id', '');
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
                                // Actualizar el campo tax_id del documento sin disparar el evento supplier nuevamente
                                frm.set_value("tax_id", values.tax_id);
                                frm.supplier_event_triggered = false; // Restablecer la bandera
                            },
                            'Favor proporcionar el RNC / Cédula del proveedor',
                            'Actualizar'
                        );
    
                        // Establecer el campo tax_id como requerido
                        frm.set_df_property('tax_id', 'reqd', 1);
    
                        // Manejar el caso en que el prompt se cierra sin proporcionar un valor
                        $(document).on('hidden.bs.modal', '.modal', function () {
                            if (!$('.modal').hasClass('show')) {
                                console.log('Modal cerrado');
                                frm.supplier_event_triggered = false;
                            }
                        });
                        } else {
                        // Quitar las condiciones si no se cumple la condición
                        frm.set_df_property('tax_id', 'reqd', 0);
                        frm.supplier_event_triggered = false; // Restablecer la bandera
                    }
                } else {
                    frm.supplier_event_triggered = false; // Restablecer la bandera en caso de error
                }
            },
            error: function() {
                frm.supplier_event_triggered = false; // Restablecer la bandera en caso de error
            }
        });
    },
    is_return: function(frm) {
        // Sincronizar con el campo custom_tipo_comprobante
        synchronize_is_return(frm);
        update_bill_no_label(frm);
    },
    bill_no: function(frm) {
        if ([1].includes(frm.doc.bill_no.length)) {

            const tipo_comprobante = frm.doc.custom_tipo_comprobante;
            if (!tipo_comprobante) {
                frappe.msgprint(__('Seleccione un tipo de comprobante.'));
                return;
            }    
        }
        // Validar el RNC al cambiar el campo bill_no
        if ([11, 13, 19].includes(frm.doc.bill_no.length)) {
            validate_ncf(frm);
        }
    },
    tax_id: function(frm) {
        if (frm.doc.tax_id) {
            setTimeout(() => {
                frm.set_value("custom_rnc", frm.doc.tax_id).then(() => {
                    frm.refresh_field('custom_rnc');
                    frm.set_df_property('custom_rnc', 'read_only', 1); 
                }).catch(err => {
                    console.error("Error al establecer custom_rnc:", err);
                });
            }, 100); // Ajusta el tiempo de espera según sea necesario
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


function validate_ncf(frm) {
    console.log("iniciando validate_ncf");
    const supplier = frm.doc.supplier;
    const bill_no = frm.doc.bill_no.trim().toUpperCase();
    const custom_rnc = frm.doc.custom_rnc;
    const tipo_comprobante = frm.doc.custom_tipo_comprobante;

    if (!tipo_comprobante) {
        frappe.msgprint(__('Seleccione un tipo de comprobante.'));
        return;
    }
    
    frm.set_value("bill_no", bill_no.trim().toUpperCase());

    // Validación previa
    if (bill_no.length === 11 && !bill_no.startsWith('B')) {
        frappe.msgprint(__('El NCF de 11 caracteres debe iniciar con la letra B.'));
        return;
    }
    if (bill_no.length === 13 && !bill_no.startsWith('E')) {
        frappe.msgprint(__('El NCF de 13 caracteres debe iniciar con la letra E.'));
        return;
    }

    // Validaciones adicionales basadas en custom_tipo_comprobante
    if (tipo_comprobante === 'Factura de Crédito Fiscal' && !bill_no.startsWith('B01')) {
        frappe.msgprint(__('El NCF para Factura de Crédito Fiscal debe iniciar con B01.'));
        frm.set_value('bill_no', '');
        return;
    }
    // Validaciones adicionales basadas en custom_tipo_comprobante
    if (tipo_comprobante === 'Factura de Consumo' && !bill_no.startsWith('B02')) {
        frappe.msgprint(__('El NCF para Factura de Consumo debe iniciar con B02.'));
        frm.set_value('bill_no', '');
        return;
    }
    
    if (tipo_comprobante === 'Notas de Crédito' && !bill_no.startsWith('B04')) {
        frappe.msgprint(__('El NCF para Notas de Crédito debe iniciar con B04.'));
        frm.set_value('bill_no', '');
        return;
    }
    if (tipo_comprobante === 'Comprobante Fiscal Electrónico' && !bill_no.startsWith('E31')) {
        frappe.msgprint(__('El NCF para Comprobante Fiscal Electrónico debe iniciar con E31.'));
        frm.set_value('bill_no', '');
        return;
    }


    frappe.call({
        method: 'dgii_reports.hook.purchase_invoice.validate_ncf',
        args: {
            ncf_number: bill_no,
            supplier: supplier,
            custom_rnc: custom_rnc
        },
        callback: function(r) {
            if (r.message) {
                // Si el NCF es válido y cumple con las condiciones, hacer visible el campo custom_security_code
                if (bill_no.startsWith('E') && bill_no.length === 13) {
                    frm.set_df_property('custom_security_code', 'hidden', 0);
                    frm.set_df_property('custom_security_code', 'reqd', 1);
                    frm.set_value('custom_require_security_code', true);
                } else {
                    // Si el NCF no cumple con las condiciones, ocultar el campo custom_security_code
                    frm.set_df_property('custom_security_code', 'hidden', 1);
                    frm.set_df_property('custom_security_code', 'reqd', 0);
                    frm.set_value('custom_require_security_code', false);
                }
            } else {
                // Si el NCF no es válido, ocultar el campo custom_security_code, marcarlo como no requerido y establecer custom_require_security_code a false
                frappe.msgprint(__('El NCF ingresado no es válido.'));
                frm.set_df_property('custom_security_code', 'hidden', 1);
                frm.set_df_property('custom_security_code', 'reqd', 0);
                frm.set_value('custom_require_security_code', false);
            }
        }
    });
}
function update_bill_no_label(frm) {
    const tipo_comprobante = frm.get_field('custom_tipo_comprobante').get_value();
    if (tipo_comprobante === "Comprobante de Compras" || tipo_comprobante === "Comprobante para Gastos Menores") {
        frm.set_df_property('bill_no', 'label', 'NCF');
        frm.set_df_property('bill_date', 'label', 'Fecha de Comprobante');
        if(frm.is_new())
            {
                frm.set_value('bill_date', frm.doc.posting_date); 
            }
        frm.set_df_property('vencimiento_ncf', 'reqd', 0);
        frm.set_df_property('bill_no', 'read_only', 1); 
        frm.set_df_property('vencimiento_ncf', 'read_only', 1); 
    } else {
        frm.set_df_property('bill_no', 'label', 'NCF Suplidor');
        frm.set_df_property('bill_date', 'label', 'Fecha de Factura del Suplidor');
        if(frm.is_new())
            {
                frm.set_value('bill_date', ''); 
            }
        frm.set_df_property('vencimiento_ncf', 'reqd', 1); 
        frm.set_df_property('bill_no', 'read_only', 0); 
        frm.set_df_property('vencimiento_ncf', 'read_only', 0); 
    }
}

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

function set_custom_tipo_comprobante_options(frm) {
    frappe.call({
        method: 'dgii_reports.hook.purchase_invoice.get_custom_tipo_comprobante_options',
        callback: function(r) {
            if (r.message) {
                frm.set_df_property('custom_tipo_comprobante', 'options', r.message);
            }
        }
    });
}