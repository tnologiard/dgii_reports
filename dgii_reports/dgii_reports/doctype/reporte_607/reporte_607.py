# Copyright (c) 2024, TnologiaRD and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import cstr, cint, flt, formatdate, format_datetime
from frappe.model.document import Document
from frappe.utils.csvutils import UnicodeWriter
import time
from datetime import datetime

class Reporte607(Document):
	pass


@frappe.whitelist()
def validate_pending_invoices(from_date, to_date):
    draft_invoices = frappe.db.sql("""
        SELECT 
            COUNT(*) 
        FROM 
            `tabSales Invoice` 
        WHERE 
            docstatus = 0 AND posting_date BETWEEN '%s' AND '%s'
    """ % (from_date, to_date))

    if draft_invoices[0][0] > 0:
        frappe.log_error("Facturas pendientes encontradas", "validate_pending_invoices")
        return {"message": "Hay facturas de venta pendientes de procesar. Por favor, complete las facturas pendientes antes de generar el reporte."}
    
    frappe.log_error("No hay facturas pendientes", "validate_pending_invoices")
    return {"message": ""}

@frappe.whitelist()
def get_file_address(from_date, to_date, decimal_places=2):
    # Obtener el tax_id del doctype Company
    company = frappe.get_doc("Company", frappe.defaults.get_user_default("Company"))
    rnc = company.tax_id.replace("-", "") if company.tax_id else ""

    # Calcular el periodo
    from_date_obj = datetime.strptime(from_date, "%Y-%m-%d")
    to_date_obj = datetime.strptime(to_date, "%Y-%m-%d")
    periodo = f"{from_date_obj.year}{min(from_date_obj.month, to_date_obj.month):02d}"

    # Consulta SQL para obtener los datos necesarios
    query = """
    SELECT 
        cust.tax_id, 
        cust.custom_tipo_rnc as tipo_identificacion,
        sinv.custom_ncf as ncf, 
        sinv.custom_return_against_ncf as ncf_modificado,
        tipo_ing.codigo as tipo_de_ingreso,  -- Recuperar la columna codigo de la tabla tabTipo de Ingreso
        sinv.posting_date as fecha_comprobante, 
        sinv.due_date as fecha_retencion,
        sinv.base_total as monto_facturado, 
        sinv.base_total_taxes_and_charges as itbis_facturado,
        '' as itbis_retenido_terceros,  -- No disponible en la tabla
        '' as itbis_percibido,  -- No disponible en la tabla
        '' as retencion_renta_terceros,  -- No disponible en la tabla
        '' as isr_percibido,  -- No disponible en la tabla
        '' as impuesto_selectivo_consumo,  -- No disponible en la tabla
        '' as otros_impuestos_tasas,  -- No disponible en la tabla
        '' as monto_propina_legal,  -- No disponible en la tabla
        CASE WHEN COALESCE(SUM(CASE WHEN pe.mode_of_payment = 'Efectivo' THEN pe.paid_amount ELSE 0 END), 0) = 0 THEN '' ELSE COALESCE(SUM(CASE WHEN pe.mode_of_payment = 'Efectivo' THEN pe.paid_amount ELSE 0 END), 0) END as efectivo,  -- Calcular el total de pagos con Modo de Pago Efectivo
        CASE WHEN COALESCE(SUM(CASE WHEN pe.mode_of_payment = 'Transferencia bancaria' THEN pe.paid_amount ELSE 0 END), 0) = 0 THEN '' ELSE COALESCE(SUM(CASE WHEN pe.mode_of_payment = 'Transferencia bancaria' THEN pe.paid_amount ELSE 0 END), 0) END as cheque_transferencia_deposito,  -- Calcular el total de pagos con Modo de Pago Transferencia bancaria
        CASE WHEN COALESCE(SUM(CASE WHEN pe.mode_of_payment = 'Tarjetas de credito' THEN pe.paid_amount ELSE 0 END), 0) = 0 THEN '' ELSE COALESCE(SUM(CASE WHEN pe.mode_of_payment = 'Tarjetas de credito' THEN pe.paid_amount ELSE 0 END), 0) END as tarjeta_debito_credito,  -- Calcular el total de pagos con Modo de Pago Tarjetas de credito
        '' as venta_credito,  -- No disponible en la tabla
        '' as bonos_certificados_regalo,  -- No disponible en la tabla
        '' as permuta,  -- No disponible en la tabla
        '' as otras_formas_ventas  -- No disponible en la tabla
    FROM 
        `tabSales Invoice` AS sinv 
    JOIN 
        tabCustomer AS cust on sinv.customer = cust.name 
    LEFT JOIN 
        `tabPayment Entry Reference` AS per ON per.reference_name = sinv.name
    LEFT JOIN 
        `tabPayment Entry` AS pe ON pe.name = per.parent
    LEFT JOIN 
        `tabTipo de Ingreso` AS tipo_ing ON sinv.custom_tipo_de_ingreso = tipo_ing.tipo_de_ingreso
    WHERE 
        sinv.custom_ncf NOT LIKE 'SINV-%%' AND sinv.docstatus = 1 AND sinv.posting_date BETWEEN %(from_date)s AND %(to_date)s
    GROUP BY 
        sinv.name
    """

    # Ejecutar la consulta
    result = frappe.db.sql(query, {"from_date": from_date, "to_date": to_date}, as_dict=True)

    # Número de registros
    numero_registros = len(result)

    # Crear el archivo en memoria usando UnicodeWriter
    w = UnicodeWriter()

    # Agregar la primera línea
    w.writerow([
        "607", 
        rnc, 
        periodo, 
        numero_registros
    ])

    def format_amount(amount):
        if amount == '':
            return amount
        try:
            amount = abs(float(amount))  # Convertir a valor absoluto
        except ValueError:
            return amount
        if amount == int(amount):
            return str(int(amount))
        else:
            return f"{amount:.{decimal_places}f}"
        
    for row in result:
        if row.tipo_identificacion == "RNC":
            tipo_identificacion = "1"
        elif row.tipo_identificacion == "Cédula":
            tipo_identificacion = "2"
        elif row.tipo_identificacion == "Pasaporte":
            tipo_identificacion = "3"
        else:
            tipo_identificacion = "2"  # Valor por defecto si no coincide con ninguno

        fecha_retencion = row.fecha_retencion.strftime("%Y%m%d") if row.fecha_retencion and row.retencion_renta_terceros not in ["", 0] else ""
        w.writerow([
            row.tax_id.replace("-", "") if row.tax_id else "", 
            tipo_identificacion, 
            row.ncf, 
            row.ncf_modificado, 
            int(row.tipo_de_ingreso),  # Convertir tipo_de_ingreso a entero
            row.fecha_comprobante.strftime("%Y%m%d") if row.fecha_comprobante else "", 
            fecha_retencion, 
            format_amount(row.monto_facturado), 
            format_amount(row.itbis_facturado), 
            row.itbis_retenido_terceros, 
            row.itbis_percibido, 
            row.retencion_renta_terceros, 
            row.isr_percibido, 
            row.impuesto_selectivo_consumo, 
            row.otros_impuestos_tasas, 
            row.monto_propina_legal, 
            format_amount(row.efectivo) if row.efectivo != 0 else "", 
            format_amount(row.cheque_transferencia_deposito) if row.cheque_transferencia_deposito != 0 else "", 
            format_amount(row.tarjeta_debito_credito) if row.tarjeta_debito_credito != 0 else "",
            row.venta_credito, 
            row.bonos_certificados_regalo, 
            row.permuta, 
            row.otras_formas_ventas
        ])

    # Convertir el contenido a texto con delimitador de pipes
    content = w.getvalue().replace(",", "|").replace('"', '')

    # Devolver el contenido del archivo de texto como descarga
    frappe.response['filename'] = "Reporte_607_%s.txt" % time.strftime("%Y%m%d_%H%M%S")
    frappe.response['filecontent'] = content
    frappe.response['type'] = 'download'



# MariaDB [_de303899e9a722d8]> show columns from `tabSales Invoice`;
# +--------------------------------------------+---------------+------+-----+---------------------------->
# | Field                                      | Type          | Null | Key | Default                    >
# +--------------------------------------------+---------------+------+-----+---------------------------->
# | name                                       | varchar(140)  | NO   | PRI | NULL                       >
# | creation                                   | datetime(6)   | YES  |     | NULL                       >
# | modified                                   | datetime(6)   | YES  | MUL | NULL                       >
# | modified_by                                | varchar(140)  | YES  |     | NULL                       >
# | owner                                      | varchar(140)  | YES  |     | NULL                       >
# | docstatus                                  | int(1)        | NO   |     | 0                          >
# | idx                                        | int(8)        | NO   |     | 0                          >
# | title                                      | varchar(140)  | YES  |     | {customer_name}            >
# | naming_series                              | varchar(140)  | YES  |     | NULL                       >
# | customer                                   | varchar(140)  | YES  | MUL | NULL                       >
# | customer_name                              | text          | YES  |     | NULL                       >
# | tax_id                                     | varchar(140)  | YES  |     | NULL                       >
# | company                                    | varchar(140)  | YES  |     | NULL                       >
# | company_tax_id                             | varchar(140)  | YES  |     | NULL                       >
# | posting_date                               | date          | YES  | MUL | NULL                       >
# | posting_time                               | time(6)       | YES  |     | NULL                       >
# | set_posting_time                           | int(1)        | NO   |     | 0                          >
# | due_date                                   | date          | YES  |     | NULL                       >
# | is_pos                                     | int(1)        | NO   |     | 0                          >
# | pos_profile                                | varchar(140)  | YES  |     | NULL                       >
# | is_consolidated                            | int(1)        | NO   |     | 0                          >
# | is_return                                  | int(1)        | NO   |     | 0                          >
# | return_against                             | varchar(140)  | YES  | MUL | NULL                       >
# | update_outstanding_for_self                | int(1)        | NO   |     | 1                          >
# | update_billed_amount_in_sales_order        | int(1)        | NO   |     | 0                          >
# | update_billed_amount_in_delivery_note      | int(1)        | NO   |     | 1                          >
# | is_debit_note                              | int(1)        | NO   |     | 0                          >
# | amended_from                               | varchar(140)  | YES  |     | NULL                       >
# | cost_center                                | varchar(140)  | YES  |     | NULL                       >
# | project                                    | varchar(140)  | YES  |     | NULL                       >
# | currency                                   | varchar(140)  | YES  |     | NULL                       >
# | conversion_rate                            | decimal(21,9) | NO   |     | 0.000000000                >
# | selling_price_list                         | varchar(140)  | YES  |     | NULL                       >
# | price_list_currency                        | varchar(140)  | YES  |     | NULL                       >
# | plc_conversion_rate                        | decimal(21,9) | NO   |     | 0.000000000                >
# | ignore_pricing_rule                        | int(1)        | NO   |     | 0                          >
# | scan_barcode                               | varchar(140)  | YES  |     | NULL                       >
# | update_stock                               | int(1)        | NO   |     | 0                          >
# | set_warehouse                              | varchar(140)  | YES  |     | NULL                       >
# | set_target_warehouse                       | varchar(140)  | YES  |     | NULL                       >
# | total_qty                                  | decimal(21,9) | NO   |     | 0.000000000                >
# | total_net_weight                           | decimal(21,9) | NO   |     | 0.000000000                >
# | base_total                                 | decimal(21,9) | NO   |     | 0.000000000                >
# | base_net_total                             | decimal(21,9) | NO   |     | 0.000000000                >
# | total                                      | decimal(21,9) | NO   |     | 0.000000000                >
# | net_total                                  | decimal(21,9) | NO   |     | 0.000000000                >
# | tax_category                               | varchar(140)  | YES  |     | NULL                       >
# | taxes_and_charges                          | varchar(140)  | YES  |     | NULL                       >
# | shipping_rule                              | varchar(140)  | YES  |     | NULL                       >
# | incoterm                                   | varchar(140)  | YES  |     | NULL                       >
# | named_place                                | varchar(140)  | YES  |     | NULL                       >
# | base_total_taxes_and_charges               | decimal(21,9) | NO   |     | 0.000000000                >
# | total_taxes_and_charges                    | decimal(21,9) | NO   |     | 0.000000000                >
# | base_grand_total                           | decimal(21,9) | NO   |     | 0.000000000                >
# | base_rounding_adjustment                   | decimal(21,9) | NO   |     | 0.000000000                >
# | base_rounded_total                         | decimal(21,9) | NO   |     | 0.000000000                >
# | base_in_words                              | text          | YES  |     | NULL                       >
# | grand_total                                | decimal(21,9) | NO   |     | 0.000000000                >
# | rounding_adjustment                        | decimal(21,9) | NO   |     | 0.000000000                >
# | use_company_roundoff_cost_center           | int(1)        | NO   |     | 0                          >
# | rounded_total                              | decimal(21,9) | NO   |     | 0.000000000                >
# | in_words                                   | text          | YES  |     | NULL                       >
# | total_advance                              | decimal(21,9) | NO   |     | 0.000000000                >
# | outstanding_amount                         | decimal(21,9) | NO   |     | 0.000000000                >
# | disable_rounded_total                      | int(1)        | NO   |     | 0                          >
# | apply_discount_on                          | varchar(15)   | YES  |     | Grand Total                >
# | base_discount_amount                       | decimal(21,9) | NO   |     | 0.000000000                >
# | is_cash_or_non_trade_discount              | int(1)        | NO   |     | 0                          >
# | additional_discount_account                | varchar(140)  | YES  |     | NULL                       >
# | additional_discount_percentage             | decimal(21,9) | NO   |     | 0.000000000                >
# | discount_amount                            | decimal(21,9) | NO   |     | 0.000000000                >
# | other_charges_calculation                  | longtext      | YES  |     | NULL                       >
# | total_billing_hours                        | decimal(21,9) | NO   |     | 0.000000000                >
# | total_billing_amount                       | decimal(21,9) | NO   |     | 0.000000000                >
# | cash_bank_account                          | varchar(140)  | YES  |     | NULL                       >
# | base_paid_amount                           | decimal(21,9) | NO   |     | 0.000000000                >
# | paid_amount                                | decimal(21,9) | NO   |     | 0.000000000                >
# | base_change_amount                         | decimal(21,9) | NO   |     | 0.000000000                >
# | change_amount                              | decimal(21,9) | NO   |     | 0.000000000                >
# | account_for_change_amount                  | varchar(140)  | YES  |     | NULL                       >
# | allocate_advances_automatically            | int(1)        | NO   |     | 0                          >
# | only_include_allocated_payments            | int(1)        | NO   |     | 0                          >
# | write_off_amount                           | decimal(21,9) | NO   |     | 0.000000000                >
# | base_write_off_amount                      | decimal(21,9) | NO   |     | 0.000000000                >
# | write_off_outstanding_amount_automatically | int(1)        | NO   |     | 0                          >
# | write_off_account                          | varchar(140)  | YES  |     | NULL                       >
# | write_off_cost_center                      | varchar(140)  | YES  |     | NULL                       >
# | redeem_loyalty_points                      | int(1)        | NO   |     | 0                          >
# | loyalty_points                             | int(11)       | NO   |     | 0                          >
# | loyalty_amount                             | decimal(21,9) | NO   |     | 0.000000000                >
# | loyalty_program                            | varchar(140)  | YES  |     | NULL                       >
# | loyalty_redemption_account                 | varchar(140)  | YES  |     | NULL                       >
# | loyalty_redemption_cost_center             | varchar(140)  | YES  |     | NULL                       >
# | customer_address                           | varchar(140)  | YES  |     | NULL                       >
# | address_display                            | text          | YES  |     | NULL                       >
# | contact_person                             | varchar(140)  | YES  |     | NULL                       >
# | contact_display                            | text          | YES  |     | NULL                       >
# | contact_mobile                             | text          | YES  |     | NULL                       >
# | contact_email                              | varchar(140)  | YES  |     | NULL                       >
# | territory                                  | varchar(140)  | YES  |     | NULL                       >
# | shipping_address_name                      | varchar(140)  | YES  |     | NULL                       >
# | shipping_address                           | text          | YES  |     | NULL                       >
# | dispatch_address_name                      | varchar(140)  | YES  |     | NULL                       >
# | dispatch_address                           | text          | YES  |     | NULL                       >
# | company_address                            | varchar(140)  | YES  |     | NULL                       >
# | company_address_display                    | text          | YES  |     | NULL                       >
# | ignore_default_payment_terms_template      | int(1)        | NO   |     | 0                          >
# | payment_terms_template                     | varchar(140)  | YES  |     | NULL                       >
# | tc_name                                    | varchar(140)  | YES  |     | NULL                       >
# | terms                                      | longtext      | YES  |     | NULL                       >
# | po_no                                      | varchar(140)  | YES  |     | NULL                       >
# | po_date                                    | date          | YES  |     | NULL                       >
# | debit_to                                   | varchar(140)  | YES  | MUL | NULL                       >
# | party_account_currency                     | varchar(140)  | YES  |     | NULL                       >
# | is_opening                                 | varchar(4)    | YES  |     | No                         >
# | unrealized_profit_loss_account             | varchar(140)  | YES  |     | NULL                       >
# | against_income_account                     | text          | YES  |     | NULL                       >
# | sales_partner                              | varchar(140)  | YES  |     | NULL                       >
# | amount_eligible_for_commission             | decimal(21,9) | NO   |     | 0.000000000                >
# | commission_rate                            | decimal(21,9) | NO   |     | 0.000000000                >
# | total_commission                           | decimal(21,9) | NO   |     | 0.000000000                >
# | letter_head                                | varchar(140)  | YES  |     | NULL                       >
# | group_same_items                           | int(1)        | NO   |     | 0                          >
# | select_print_heading                       | varchar(140)  | YES  |     | NULL                       >
# | language                                   | varchar(6)    | YES  |     | NULL                       >
# | subscription                               | varchar(140)  | YES  |     | NULL                       >
# | from_date                                  | date          | YES  |     | NULL                       >
# | auto_repeat                                | varchar(140)  | YES  |     | NULL                       >
# | to_date                                    | date          | YES  |     | NULL                       >
# | status                                     | varchar(30)   | YES  |     | Draft                      >
# | inter_company_invoice_reference            | varchar(140)  | YES  | MUL | NULL                       >
# | campaign                                   | varchar(140)  | YES  |     | NULL                       >
# | represents_company                         | varchar(140)  | YES  |     | NULL                       >
# | source                                     | varchar(140)  | YES  |     | NULL                       >
# | customer_group                             | varchar(140)  | YES  |     | NULL                       >
# | is_internal_customer                       | int(1)        | NO   |     | 0                          >
# | is_discounted                              | int(1)        | NO   |     | 0                          >
# | remarks                                    | text          | YES  |     | NULL                       >
# | _user_tags                                 | text          | YES  |     | NULL                       >
# | _comments                                  | text          | YES  |     | NULL                       >
# | _assign                                    | text          | YES  |     | NULL                       >
# | _liked_by                                  | text          | YES  |     | NULL                       >
# | _seen                                      | text          | YES  |     | NULL                       >
# | custom_tipo_de_factura                     | varchar(140)  | YES  |     | NULL                       >
# | custom_ncf                                 | varchar(140)  | YES  |     | NULL                       >
# | custom_return_against_ncf                  | varchar(140)  | YES  |     | NULL                       >
# | custom_tipo_de_ingreso                     | varchar(140)  | YES  |     | Ingresos por Operaciones (N>
# +--------------------------------------------+---------------+------+-----+---------------------------->
# (END)


# SELECT GROUP_CONCAT(COLUMN_NAME ORDER BY ORDINAL_POSITION) AS columnas
# FROM INFORMATION_SCHEMA.COLUMNS
# WHERE TABLE_NAME = 'tabSales Invoice';

# other_charges_calculation

# SELECT name,creation,modified,modified_by,owner,docstatus,idx,title,naming_series,customer,customer_name,tax_id,company,company_tax_id,posting_date,posting_time,set_posting_time,due_date,is_pos,pos_profile,is_consolidated,is_return,return_against,update_outstanding_for_self,update_billed_amount_in_sales_order,update_billed_amount_in_delivery_note,is_debit_note,amended_from,cost_center,project,currency,conversion_rate,selling_price_list,price_list_currency,plc_conversion_rate,ignore_pricing_rule,scan_barcode,update_stock,set_warehouse,set_target_warehouse,total_qty,total_net_weight,base_total,base_net_total,total,net_total,tax_category,taxes_and_charges,shipping_rule,incoterm,named_place,base_total_taxes_and_charges,total_taxes_and_charges,base_grand_total,base_rounding_adjustment,base_rounded_total,base_in_words,grand_total,rounding_adjustment,use_company_roundoff_cost_center,rounded_total,in_words,total_advance,outstanding_amount,disable_rounded_total,apply_discount_on,base_discount_amount,is_cash_or_non_trade_discount,additional_discount_account,additional_discount_percentage,discount_amount,total_billing_hours,total_billing_amount,cash_bank_account,base_paid_amount,paid_amount,base_change_amount,change_amount,account_for_change_amount,allocate_advances_automatically,only_include_allocated_payments,write_off_amount,base_write_off_amount,write_off_outstanding_amount_automatically,write_off_account,write_off_cost_center,redeem_loyalty_points,loyalty_points,loyalty_amount,loyalty_program,loyalty_redemption_account,loyalty_redemption_cost_center,customer_address,address_display,contact_person,contact_display,contact_mobile,contact_email,territory,shipping_address_name,shipping_address,dispatch_address_name,dispatch_address,company_address,company_address_display,ignore_default_payment_terms_template,payment_terms_template,tc_name,terms,po_no,po_date,debit_to,party_account_currency,is_opening,unrealized_profit_loss_account,against_income_account,sales_partner,amount_eligible_for_commission,commission_rate,total_commission,letter_head,group_same_items,select_print_heading,language,subscription,from_date,auto_repeat,to_date,status,inter_company_invoice_reference,campaign,represents_company,source,customer_group,is_internal_customer,is_discounted,remarks,_user_tags,_comments,_assign,_liked_by,_seen,custom_tipo_de_factura,custom_ncf,custom_return_against_ncf,custom_tipo_de_ingreso FROM `tabSales Invoice`;


# | tabPayment Entry                                  |
# | tabPayment Entry Deduction                        |
# | tabPayment Entry Reference                        |
# | tabPayment Gateway Account                        |
# | tabPayment Ledger Entry                           |
# | tabPayment Order                                  |
# | tabPayment Order Reference                        |
# | tabPayment Request                                |
# | tabPayment Schedule                               |
# | tabPayment Term                                   |
# | tabPayment Terms Template                         |
# | tabPayment Terms Template Detail                  |



# MariaDB [_de303899e9a722d8]> show columns from `tabPayment Entry Reference`;
# +--------------------+---------------+------+-----+-------------+-------+
# | Field              | Type          | Null | Key | Default     | Extra |
# +--------------------+---------------+------+-----+-------------+-------+
# | name               | varchar(140)  | NO   | PRI | NULL        |       |
# | creation           | datetime(6)   | YES  |     | NULL        |       |
# | modified           | datetime(6)   | YES  |     | NULL        |       |
# | modified_by        | varchar(140)  | YES  |     | NULL        |       |
# | owner              | varchar(140)  | YES  |     | NULL        |       |
# | docstatus          | int(1)        | NO   |     | 0           |       |
# | idx                | int(8)        | NO   |     | 0           |       |
# | reference_doctype  | varchar(140)  | YES  | MUL | NULL        |       |
# | reference_name     | varchar(140)  | YES  | MUL | NULL        |       |
# | due_date           | date          | YES  |     | NULL        |       |
# | bill_no            | varchar(140)  | YES  |     | NULL        |       |
# | payment_term       | varchar(140)  | YES  |     | NULL        |       |
# | account_type       | varchar(140)  | YES  |     | NULL        |       |
# | payment_type       | varchar(140)  | YES  |     | NULL        |       |
# | total_amount       | decimal(21,9) | NO   |     | 0.000000000 |       |
# | outstanding_amount | decimal(21,9) | NO   |     | 0.000000000 |       |
# | allocated_amount   | decimal(21,9) | NO   |     | 0.000000000 |       |
# | exchange_rate      | decimal(21,9) | NO   |     | 0.000000000 |       |
# | exchange_gain_loss | decimal(21,9) | NO   |     | 0.000000000 |       |
# | account            | varchar(140)  | YES  |     | NULL        |       |
# | parent             | varchar(140)  | YES  | MUL | NULL        |       |
# | parentfield        | varchar(140)  | YES  |     | NULL        |       |
# | parenttype         | varchar(140)  | YES  |     | NULL        |       |
# +--------------------+---------------+------+-----+-------------+-------+
# 23 rows in set (0.024 sec)

# MariaDB [_de303899e9a722d8]> show columns from `tabPayment Entry`;
# +-------------------------------------------------+---------------+------+-----+-------------+-------+
# | Field                                           | Type          | Null | Key | Default     | Extra |
# +-------------------------------------------------+---------------+------+-----+-------------+-------+
# | name                                            | varchar(140)  | NO   | PRI | NULL        |       |
# | creation                                        | datetime(6)   | YES  |     | NULL        |       |
# | modified                                        | datetime(6)   | YES  | MUL | NULL        |       |
# | modified_by                                     | varchar(140)  | YES  |     | NULL        |       |
# | owner                                           | varchar(140)  | YES  |     | NULL        |       |
# | docstatus                                       | int(1)        | NO   |     | 0           |       |
# | idx                                             | int(8)        | NO   |     | 0           |       |
# | naming_series                                   | varchar(140)  | YES  |     | NULL        |       |
# | payment_type                                    | varchar(140)  | YES  |     | NULL        |       |
# | payment_order_status                            | varchar(140)  | YES  |     | NULL        |       |
# | posting_date                                    | date          | YES  |     | NULL        |       |
# | company                                         | varchar(140)  | YES  |     | NULL        |       |
# | mode_of_payment                                 | varchar(140)  | YES  |     | NULL        |       |
# | party_type                                      | varchar(140)  | YES  | MUL | NULL        |       |
# | party                                           | varchar(140)  | YES  |     | NULL        |       |
# | party_name                                      | varchar(140)  | YES  |     | NULL        |       |
# | book_advance_payments_in_separate_party_account | int(1)        | NO   |     | 0           |       |
# | reconcile_on_advance_payment_date               | int(1)        | NO   |     | 0           |       |
# | bank_account                                    | varchar(140)  | YES  |     | NULL        |       |
# | party_bank_account                              | varchar(140)  | YES  |     | NULL        |       |
# | contact_person                                  | varchar(140)  | YES  |     | NULL        |       |
# | contact_email                                   | varchar(140)  | YES  |     | NULL        |       |
# | party_balance                                   | decimal(21,9) | NO   |     | 0.000000000 |       |
# | paid_from                                       | varchar(140)  | YES  |     | NULL        |       |
# | paid_from_account_type                          | varchar(140)  | YES  |     | NULL        |       |
# | paid_from_account_currency                      | varchar(140)  | YES  |     | NULL        |       |
# | paid_from_account_balance                       | decimal(21,9) | NO   |     | 0.000000000 |       |
# | paid_to                                         | varchar(140)  | YES  |     | NULL        |       |
# | paid_to_account_type                            | varchar(140)  | YES  |     | NULL        |       |
# | paid_to_account_currency                        | varchar(140)  | YES  |     | NULL        |       |
# | paid_to_account_balance                         | decimal(21,9) | NO   |     | 0.000000000 |       |
# | paid_amount                                     | decimal(21,9) | NO   |     | 0.000000000 |       |
# | paid_amount_after_tax                           | decimal(21,9) | NO   |     | 0.000000000 |       |
# | source_exchange_rate                            | decimal(21,9) | NO   |     | 0.000000000 |       |
# | base_paid_amount                                | decimal(21,9) | NO   |     | 0.000000000 |       |
# | base_paid_amount_after_tax                      | decimal(21,9) | NO   |     | 0.000000000 |       |
# | received_amount                                 | decimal(21,9) | NO   |     | 0.000000000 |       |
# | received_amount_after_tax                       | decimal(21,9) | NO   |     | 0.000000000 |       |
# | target_exchange_rate                            | decimal(21,9) | NO   |     | 0.000000000 |       |
# | base_received_amount                            | decimal(21,9) | NO   |     | 0.000000000 |       |
# | base_received_amount_after_tax                  | decimal(21,9) | NO   |     | 0.000000000 |       |
# | total_allocated_amount                          | decimal(21,9) | NO   |     | 0.000000000 |       |
# | base_total_allocated_amount                     | decimal(21,9) | NO   |     | 0.000000000 |       |
# | unallocated_amount                              | decimal(21,9) | NO   |     | 0.000000000 |       |
# | difference_amount                               | decimal(21,9) | NO   |     | 0.000000000 |       |
# | purchase_taxes_and_charges_template             | varchar(140)  | YES  |     | NULL        |       |
# | sales_taxes_and_charges_template                | varchar(140)  | YES  |     | NULL        |       |
# | apply_tax_withholding_amount                    | int(1)        | NO   |     | 0           |       |
# | tax_withholding_category                        | varchar(140)  | YES  |     | NULL        |       |
# | base_total_taxes_and_charges                    | decimal(21,9) | NO   |     | 0.000000000 |       |
# | total_taxes_and_charges                         | decimal(21,9) | NO   |     | 0.000000000 |       |
# | reference_no                                    | varchar(140)  | YES  |     | NULL        |       |
# | reference_date                                  | date          | YES  | MUL | NULL        |       |
# | clearance_date                                  | date          | YES  |     | NULL        |       |
# | project                                         | varchar(140)  | YES  |     | NULL        |       |
# | cost_center                                     | varchar(140)  | YES  |     | NULL        |       |
# | status                                          | varchar(140)  | YES  |     | Draft       |       |
# | custom_remarks                                  | int(1)        | NO   |     | 0           |       |
# | remarks                                         | text          | YES  |     | NULL        |       |
# | base_in_words                                   | text          | YES  |     | NULL        |       |
# | is_opening                                      | varchar(140)  | YES  | MUL | No          |       |
# | letter_head                                     | varchar(140)  | YES  |     | NULL        |       |
# | print_heading                                   | varchar(140)  | YES  |     | NULL        |       |
# | bank                                            | varchar(140)  | YES  |     | NULL        |       |
# | bank_account_no                                 | varchar(140)  | YES  |     | NULL        |       |
# | payment_order                                   | varchar(140)  | YES  |     | NULL        |       |
# | in_words                                        | text          | YES  |     | NULL        |       |
# | auto_repeat                                     | varchar(140)  | YES  |     | NULL        |       |
# | amended_from                                    | varchar(140)  | YES  |     | NULL        |       |
# | title                                           | varchar(140)  | YES  |     | NULL        |       |
# | _user_tags                                      | text          | YES  |     | NULL        |       |
# | _comments                                       | text          | YES  |     | NULL        |       |
# | _assign                                         | text          | YES  |     | NULL        |       |
# | _liked_by                                       | text          | YES  |     | NULL        |       |
# +-------------------------------------------------+---------------+------+-----+-------------+-------+
# 74 rows in set (0.010 sec)