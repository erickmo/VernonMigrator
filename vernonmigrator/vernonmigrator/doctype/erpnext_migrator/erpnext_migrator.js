// Copyright (c) 2025, VernonCorp and contributors
// For license information, please see license.txt

frappe.ui.form.on("ERPNext Migrator", {
	refresh(frm) {

	},
	import_item_group: function (frm) { 
		// Confirm
		frappe.confirm("Are you sure you want to import Item Group?", function () {
			new ERPNextMigratorController(frm).import_now("Item Group"); 
		})
	},
	import_item: function (frm) { 
		frappe.confirm("Are you sure you want to import Item?", function () {
			new ERPNextMigratorController(frm).import_now("Item"); 
		});
	},
	import_address: function (frm) { 
		frappe.confirm("Are you sure you want to import Address?", function () {
			new ERPNextMigratorController(frm).import_now("Address"); 
		})
	},
	import_contact: function (frm) { 
		frappe.confirm("Are you sure you want to import Contact?", function () {
			new ERPNextMigratorController(frm).import_now("Contact"); 
		});
	},
	import_customer_group: function (frm) { 
		frappe.confirm("Are you sure you want to import Customer Group?", function () {
			new ERPNextMigratorController(frm).import_now("Customer Group"); 
		});
	},
	import_customer: function (frm) { 
		frappe.confirm("Are you sure you want to import Customer?", function () {
			new ERPNextMigratorController(frm).import_now("Customer"); 
		});
	},
	import_supplier_group: function (frm) { 
		frappe.confirm("Are you sure you want to import Supplier Group?", function () {
			new ERPNextMigratorController(frm).import_now("Supplier Group"); 
		});
	},
	import_supplier: function (frm) { 
		frappe.confirm("Are you sure you want to import Supplier?", function () {
			new ERPNextMigratorController(frm).import_now("Supplier"); 
		});
	},
	import_account: function (frm) { 
		frappe.confirm("Are you sure you want to import Account?", function () {
			new ERPNextMigratorController(frm).import_now("Account"); 
		});
	},
	import_journal_entry: function (frm) { 
		frappe.confirm("Are you sure you want to import Journal Entry?", function () {
			new ERPNextMigratorController(frm).import_now("Journal Entry"); 
		});
	},
	import_purchase_order: function (frm) { 
		frappe.confirm("Are you sure you want to import Purchase Order?", function () {
			new ERPNextMigratorController(frm).import_now("Purchase Order"); 
		});
	},
	import_purchase_invoice: function (frm) { 
		frappe.confirm("Are you sure you want to import Purchase Invoice?", function () {
			new ERPNextMigratorController(frm).import_now("Purchase Invoice"); 
		});		
	},
	import_purchase_receipt: function (frm) { 
		frappe.confirm("Are you sure you want to import Purchase Receipt?", function () {
			new ERPNextMigratorController(frm).import_now("Purchase Receipt"); 
		});		
	},
	import_sales_order: function (frm) { 
		frappe.confirm("Are you sure you want to import Sales Order?", function () {
			new ERPNextMigratorController(frm).import_now("Sales Order"); 
		});
	},
	import_sales_invoice: function (frm) { 
		frappe.confirm("Are you sure you want to import Sales Invoice?", function () {
			new ERPNextMigratorController(frm).import_now("Sales Invoice"); 
		});
	},
	import_payment_entry: function (frm) { 
		frappe.confirm("Are you sure you want to import Payment Entry?", function () {
			new ERPNextMigratorController(frm).import_now("Payment Entry"); 
		});
	},
	import_stock_entry: function (frm) { 
		frappe.confirm("Are you sure you want to import Stock Entry?", function () {
			new ERPNextMigratorController(frm).import_now("Stock Entry"); 
		});
	},
	import_delivery_note: function (frm) { 
		frappe.confirm("Are you sure you want to import Delivery Note?", function () {
			new ERPNextMigratorController(frm).import_now("Delivery Note"); 
		});
	},
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