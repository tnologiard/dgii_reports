def execute():
    from dgii_reports.fixtures.mode_of_payment_cleanup import delete_modes_if_not_custom
    delete_modes_if_not_custom()