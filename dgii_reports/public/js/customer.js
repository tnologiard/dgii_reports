frappe.ui.form.on("Customer", {
    refresh(frm) {
        const events = [
            "add_custom_button",
            "set_properties",
        ]
        $.map(events, (event) => {
            frm.trigger(event);
        });
    },
    add_custom_button(frm) {
        frm.trigger("add_consult_rnc_button");
    },
    set_properties(frm) {
        frm.set_df_property('tipo_rnc', 'options', [
            { "value": "1", "label": "RNC" },
            { "value": "2", "label": "CEDULA" },
            { "value": "3", "label": "PASAPORTE" },
        ]);
    },
    add_consult_rnc_button(frm) {
        frappe.db.get_single_value('DGII Reports Settings', 'no_validar_ncf').then(no_validar_ncf => {
            if (no_validar_ncf) {
                return true;
            }
            if (!frm.is_new()) return;
            frm.add_custom_button(__('Consultar RNC'), () => {
                frm.trigger("get_rnc_details");
            }).addClass("btn-primary");
        });
    },
    get_rnc_details(frm) {
        const method = "dgii_reports.api.get_rnc_details"
        const fields = [
            {
                "fieldname": "tax_id",
                "label": __("RNC/Cedula"),
                "fieldtype": "Data",
                "reqd": 1,
                "onchange": function() {
                    const values = d.get_values();
                    if (values.tax_id.match(/-| /)) {
                        d.set_value("tax_id", values.tax_id.replace(/-| /g, ""));
                    }
                }
            },
            {
                "fieldname": "status",
                "label": __("Status"),
                "fieldtype": "Read Only",
                "read_only": 1,
            },
            { 
                "fieldtype": "Button", 
                "label": "Consultar",
                "click": function() {
                    console.log("Consultar");
                    const values = d.get_values();
					console.log('values:');
					console.log(values);
                    frappe.call({
                        method: method,
                        args: { tax_id: values.tax_id },
                        callback: function(r) {
							console.log(r);
                            if (r.message) {
                                d.set_value("status", r.message.status);
                                d.set_value("brand_name", r.message.brand_name);
                                d.set_value("company_name", r.message.company_name);
                                if (r.message.status === "ACTIVO") {
                                    d.$wrapper.find('.btn-default').removeClass('btn-primary');
                                    d.$wrapper.find('.btn-primary').show();
                                }
                            }else{
								console.log('......No hay resultados........');
							}
                        },
                        freeze: true,
                        freeze_message: __("Consultando RNC...")
                    })
                }
            },
            { "fieldtype": "Column Break" },
            {
                "fieldname": "brand_name",
                "label": __("Razon Social"),
                "fieldtype": "Read Only",
                "read_only": 1,
            },
            {
                "fieldname": "company_name",
                "label": __("Nombre Comercial"),
                "fieldtype": "Read Only",
                "read_only": 1,
            },
        ]

        const primary_action_label = __("Consultar RNC")
        const action = __("Guardar")
        const primary_action = (values) => {
            frm.set_value("tax_id", values.tax_id);
            // frm.set_value("brand_name", values.brand_name);
            frm.set_value("customer_name", values.company_name);
        }

        let d = frappe.prompt(fields, primary_action, primary_action_label, action);
        d.show();
        d.$wrapper.find('.btn-primary').hide();
        d.$wrapper.find('.btn-default').addClass('btn-primary');
    }
})
