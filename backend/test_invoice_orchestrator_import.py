def test_invoice_orchestrator_imports_without_forward_reference_crash():
    import services.invoice_orchestrator as invoice_orchestrator

    assert callable(invoice_orchestrator.scan_invoice)
