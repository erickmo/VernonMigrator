// Copyright (c) 2025, VernonCorp and contributors
// For license information, please see license.txt

frappe.ui.form.on("ERPNext Migrator", {
	refresh(frm) {

	},
	import_item_group: function (frm) { new ERPNextMigratorController(frm).import_now("Item Group"); },
	import_item: function (frm) { new ERPNextMigratorController(frm).import_now("Item"); },,
	import_address: function (frm) { new ERPNextMigratorController(frm).import_now("Address"); },,
	import_contact: function (frm) { new ERPNextMigratorController(frm).import_now("Contact"); },,
	import_customer_group: function (frm) { new ERPNextMigratorController(frm).import_now("Customer Group"); },,
	import_customer: function (frm) { new ERPNextMigratorController(frm).import_now("Customer"); },,
	import_supplier_group: function (frm) { new ERPNextMigratorController(frm).import_now("Supplier Group"); },,
	import_supplier: function (frm) { new ERPNextMigratorController(frm).import_now("Supplier"); },,
	import_account: function (frm) { new ERPNextMigratorController(frm).import_now("Account"); },,
	import_journal_entry: function (frm) { new ERPNextMigratorController(frm).import_now("Journal Entry"); },,
	import_purchase_order: function (frm) { new ERPNextMigratorController(frm).import_now("Purchase Order"); },,
	import_purchase_invoice: function (frm) { new ERPNextMigratorController(frm).import_now("Purchase Invoice"); },,
	import_purchase_receipt: function (frm) { new ERPNextMigratorController(frm).import_now("Purchase Receipt"); },,
	import_sales_order: function (frm) { new ERPNextMigratorController(frm).import_now("Sales Order"); },
	import_sales_invoice: function (frm) { new ERPNextMigratorController(frm).import_now("Sales Invoice"); },,
	import_payment_entry: function (frm) { new ERPNextMigratorController(frm).import_now("Payment Entry"); },,
	import_stock_entry: function (frm) { new ERPNextMigratorController(frm).import_now("Stock Entry"); },,
	import_delivery_note: function (frm) { new ERPNextMigratorController(frm).import_now("Delivery Note"); },
});

class ERPNextMigratorController {
	constructor(frm) {
		this.frm = frm;
	}

	import_now(doctype_to_import) {
		alert("Processing")
		frappe.call({
			method: "vernonmigrator.vernonmigrator.functions.import_doc.import_doctype",
			args: {
				erpnext_migrator_name: this.frm.doc['name'],
				doctype_to_import: doctype_to_import
			},
			callback: function (response) {
				frappe.msgprint("Operasi berhasil!");
			}
		});
	}
}