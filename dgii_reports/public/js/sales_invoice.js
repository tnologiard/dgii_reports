frappe.ui.form.on("Sales Invoice", {
    onload: function(frm) {
        // Función para manejar la lógica de habilitar/deshabilitar checkboxes
        function toggle_checkboxes(selected_field) {
            const fields = ["is_return", "custom_is_b14", "custom_is_b15", "custom_is_b16"];
            fields.forEach(field => {
                if (field !== selected_field) {
                    frm.set_value(field, 0); // Deseleccionar
                    frm.set_df_property(field, "read_only", frm.doc[selected_field] ? 1 : 0); // Deshabilitar si el seleccionado está marcado
                }
            });
        }

        // Función para habilitar todos los checkboxes
        function enable_all_checkboxes() {
            const fields = ["is_return", "custom_is_b14", "custom_is_b15", "custom_is_b16"];
            fields.forEach(field => {
                frm.set_df_property(field, "read_only", 0); // Habilitar todos
            });
        }

        // Agregar controladores de eventos para cada checkbox
        frm.fields_dict.is_return.$input.on("change", function() {
            setTimeout(function() {
                if (frm.doc.is_return) {
                    toggle_checkboxes("is_return");
                } else {
                    enable_all_checkboxes();
                }
            }, 100); // Pequeño retraso para asegurar que el valor se haya actualizado
        });

        frm.fields_dict.custom_is_b14.$input.on("change", function() {
            setTimeout(function() {
                if (frm.doc.custom_is_b14) {
                    toggle_checkboxes("custom_is_b14");
                } else {
                    enable_all_checkboxes();
                }
            }, 100); // Pequeño retraso para asegurar que el valor se haya actualizado
        });

        frm.fields_dict.custom_is_b15.$input.on("change", function() {
            setTimeout(function() {
                if (frm.doc.custom_is_b15) {
                    toggle_checkboxes("custom_is_b15");
                } else {
                    enable_all_checkboxes();
                }
            }, 100); // Pequeño retraso para asegurar que el valor se haya actualizado
        });

        frm.fields_dict.custom_is_b16.$input.on("change", function() {
            setTimeout(function() {
                if (frm.doc.custom_is_b16) {
                    toggle_checkboxes("custom_is_b16");
                } else {
                    enable_all_checkboxes();
                }
            }, 100); // Pequeño retraso para asegurar que el valor se haya actualizado
        });
    }
});