frappe.ui.form.on("Purchase Invoice", {
    onload: function(frm) {
        // Recuperar el valor de isr del Doctype DGII Reports Settings
        frappe.db.get_single_value('DGII Reports Settings', 'isr')
            .then(value => {
                console.log("ISR value:", value);
                frm.doc.isr = value;
                check_retention_type_visibility(frm);
            });
    },
    refresh: function(frm) {
        check_retention_type_visibility(frm);
    },
    // Se ejecuta cuando se valida el formulario antes de guardar
    validate(frm) {
        // Llama a las funciones de validación y ajuste de campos específicos
        frm.trigger("bill_no");
        frm.trigger("validate_cost_center");
        frm.trigger("validate_ncf");
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

    // Ajusta la interfaz cuando se incluye la retención de ISR
    include_isr(frm) {
        frm.trigger("calculate_isr");  // Calcula el monto de ISR

        // Establece ciertos campos como obligatorios si include_isr está marcado
        $.map(["retention_rate", "retention_type"], field => {
            frm.set_df_property(field, 'reqd', frm.doc.include_isr);
        });
    },

    // Recalcula el ISR cuando cambia la tasa de ISR
    isr_rate(frm) {
        frm.trigger("calculate_isr");  // Calcula el monto de ISR basado en la nueva tasa
    },

    // Ajusta la interfaz cuando se incluye la retención
    include_retention(frm) {
        // Establece el campo retention_rate como obligatorio si include_retention está marcado
        frm.set_df_property("retention_rate", 'reqd', frm.doc.include_retention);
        frm.trigger("calculate_retention");  // Calcula el monto de retención
    },

    // Recalcula la retención cuando cambia la tasa de retención
    retention_rate(frm) {
        frm.trigger("calculate_retention");  // Calcula el monto de retención basado en la nueva tasa
    },

    // Calcula el monto de la retención basado en la tasa seleccionada
    calculate_retention(frm) {
        // Si no se incluye la retención, o si faltan otros valores clave, establece el monto en 0
        if (!frm.doc.include_retention || !frm.doc.total_taxes_and_charges || !frm.doc.retention_rate)
            frm.set_value("retention_amount", 0);

        let retention_rate = 0;
        if (frm.doc.retention_rate == '30%')
            retention_rate = 0.30;  // Tasa del 30%

        if (frm.doc.retention_rate == '100%')
            retention_rate = 1;  // Tasa del 100%
        
        // Calcula el monto de retención y lo asigna al campo retention_amount
        frm.set_value("retention_amount", frm.doc.total_taxes_and_charges * retention_rate);		
    },

    // Calcula el monto de ISR basado en la tasa y el total
    calculate_isr(frm) {
        // Si no se incluye ISR, o si faltan otros valores clave, establece el monto en 0
        if (!frm.doc.include_isr || !frm.doc.total || !frm.doc.isr_rate)
            frm.set_value("isr_amount", 0);
        
        // Calcula el monto de ISR y lo asigna al campo isr_amount
        let amount = frm.doc.total * (frm.doc.isr_rate / 100);
        frm.set_value("isr_amount", amount);
    }
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
    console.log("Checking retention type visibility");
    let show_retention_type = false;
    const isr = frm.doc.isr;

    frm.doc.taxes.forEach(function(tax) {
        console.log("Tax account head:", tax.account_head);
        if (tax.account_head === isr) {
            show_retention_type = true;
        }
    });

    frm.toggle_display('retention_type', show_retention_type);
    frm.toggle_reqd('retention_type', show_retention_type);
}