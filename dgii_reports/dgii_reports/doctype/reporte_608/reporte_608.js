// Copyright (c) 2024, TnologiaRD and contributors
// For license information, please see license.txt

frappe.ui.form.on("Reporte 608", {
    onload: function(frm) {
        frm.set_value("from_date", frappe.datetime.month_start());
        frm.set_value("to_date", frappe.datetime.month_end());
        frm.disable_save();
    },
    run_report: function(frm) {
        frappe.call({
            method: "dgii_reports.dgii_reports.doctype.reporte_608.reporte_608.validate_pending_invoices",
            args: {
                from_date: frm.doc.from_date,
                to_date: frm.doc.to_date
            },
            callback: function(response) {
                console.log("Respuesta del servidor:", response);
                if (response.message && response.message.message !== "") {
                    // Si hay un mensaje de advertencia, mostrarlo al usuario
                    frappe.msgprint(response.message.message);
                } else {
                    // Si no hay advertencia, abrir el archivo
                    var file_url = __("/api/method/dgii_reports.dgii_reports.doctype.reporte_608.reporte_608.get_file_address?from_date={0}&to_date={1}", 
                        [frm.doc.from_date, frm.doc.to_date]);
                    window.open(file_url);
                }
            }
        });
    }

});
