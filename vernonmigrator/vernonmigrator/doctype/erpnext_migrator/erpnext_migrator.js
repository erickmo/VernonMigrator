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
	delete_item_group: function (frm) {
		// Confirm
		frappe.confirm("Are you sure you want to delete Item Group?", function () {
			new ERPNextMigratorController(frm).delete_now("Item Group");
		})
	},
	import_asset_category: function (frm) {
		frappe.confirm("Are you sure you want to import Asset Category?", function () {
			new ERPNextMigratorController(frm).import_now("Asset Category");
		});
	},
	delete_asset_category: function (frm) {
		// Confirm
		frappe.confirm("Are you sure you want to delete Asset Category?", function () {
			new ERPNextMigratorController(frm).delete_now("Asset Category");
		})
	},
	import_item: function (frm) { 
		frappe.confirm("Are you sure you want to import Item?", function () {
			new ERPNextMigratorController(frm).import_now("Item"); 
		});
	},
	delete_item: function (frm) {
		// Confirm
		frappe.confirm("Are you sure you want to delete Item?", function () {
			new ERPNextMigratorController(frm).delete_now("Item");
		})
	},
	import_address: function (frm) { 
		frappe.confirm("Are you sure you want to import Address?", function () {
			new ERPNextMigratorController(frm).import_now("Address"); 
		})
	},
	delete_address: function (frm) {
		// Confirm
		frappe.confirm("Are you sure you want to delete Address?", function () {
			new ERPNextMigratorController(frm).delete_now("Address");
		})
	},
	import_contact: function (frm) { 
		frappe.confirm("Are you sure you want to import Contact?", function () {
			new ERPNextMigratorController(frm).import_now("Contact"); 
		});
	},
	delete_contact: function (frm) {
		// Confirm
		frappe.confirm("Are you sure you want to delete Contact?", function () {
			new ERPNextMigratorController(frm).delete_now("Contact");
		})
	},
	import_customer_group: function (frm) { 
		frappe.confirm("Are you sure you want to import Customer Group?", function () {
			new ERPNextMigratorController(frm).import_now("Customer Group"); 
		});
	},
	delete_customer_group: function (frm) {
		// Confirm
		frappe.confirm("Are you sure you want to delete Customer Group?", function () {
			new ERPNextMigratorController(frm).delete_now("Customer Group");
		})
	},
	import_customer: function (frm) { 
		frappe.confirm("Are you sure you want to import Customer?", function () {
			new ERPNextMigratorController(frm).import_now("Customer"); 
		});
	},
	delete_customer: function (frm) {
		// Confirm
		frappe.confirm("Are you sure you want to delete Customer?", function () {
			new ERPNextMigratorController(frm).delete_now("Customer");
		})
	},
	import_supplier_group: function (frm) { 
		frappe.confirm("Are you sure you want to import Supplier Group?", function () {
			new ERPNextMigratorController(frm).import_now("Supplier Group"); 
		});
	},
	delete_supplier_group: function (frm) {
		// Confirm
		frappe.confirm("Are you sure you want to delete Supplier Group?", function () {
			new ERPNextMigratorController(frm).delete_now("Supplier Group");
		})
	},
	import_supplier: function (frm) { 
		frappe.confirm("Are you sure you want to import Supplier?", function () {
			new ERPNextMigratorController(frm).import_now("Supplier"); 
		});
	},
	delete_supplier: function (frm) {
		// Confirm
		frappe.confirm("Are you sure you want to delete Supplier?", function () {
			new ERPNextMigratorController(frm).delete_now("Supplier");
		})
	},
	import_account: function (frm) { 
		frappe.confirm("Are you sure you want to import Account?", function () {
			new ERPNextMigratorController(frm).import_now("Account"); 
		});
	},
	delete_account: function (frm) {
		// Confirm
		frappe.confirm("Are you sure you want to delete Account?", function () {
			new ERPNextMigratorController(frm).delete_now("Account");
		})
	},
	import_cost_center: function (frm) {
		frappe.confirm("Are you sure you want to import Cost Center?", function () {
			new ERPNextMigratorController(frm).import_now("Cost Center");
		});
	},
	delete_cost_center: function (frm) {
		// Confirm
		frappe.confirm("Are you sure you want to delete Cost Center?", function () {
			new ERPNextMigratorController(frm).delete_now("Cost Center");
		})
	},
	import_journal_entry: function (frm) { 
		frappe.confirm("Are you sure you want to import Journal Entry?", function () {
			new ERPNextMigratorController(frm).import_now("Journal Entry"); 
		});
	},
	delete_journal_entry: function (frm) {
		// Confirm
		frappe.confirm("Are you sure you want to delete Journal Entry?", function () {
			new ERPNextMigratorController(frm).delete_now("Journal Entry");
		})
	},
	import_journal_entry_template: function (frm) {
		frappe.confirm("Are you sure you want to import Journal Entry Template?", function () {
			new ERPNextMigratorController(frm).import_now("Journal Entry Template");
		});
	},
	delete_journal_entry_template: function (frm) {
		// Confirm
		frappe.confirm("Are you sure you want to delete Journal Entry Template?", function () {
			new ERPNextMigratorController(frm).delete_now("Journal Entry Template");
		})
	},
	import_purchase_order: function (frm) { 
		frappe.confirm("Are you sure you want to import Purchase Order?", function () {
			new ERPNextMigratorController(frm).import_now("Purchase Order"); 
		});
	},
	delete_purchase_order: function (frm) {
		frappe.confirm("Are you sure you want to delete Purchase Order?", function () {
			new ERPNextMigratorController(frm).delete_now("Purchase Order");
		});
	},
	import_purchase_invoice: function (frm) { 
		frappe.confirm("Are you sure you want to import Purchase Invoice?", function () {
			new ERPNextMigratorController(frm).import_now("Purchase Invoice"); 
		});		
	},
	delete_purchase_invoice: function (frm) {
		frappe.confirm("Are you sure you want to delete Purchase Invoice?", function () {
			new ERPNextMigratorController(frm).delete_now("Purchase Invoice");
		});
	},
	import_purchase_receipt: function (frm) { 
		frappe.confirm("Are you sure you want to import Purchase Receipt?", function () {
			new ERPNextMigratorController(frm).import_now("Purchase Receipt"); 
		});		
	},
	delete_purchase_receipt: function (frm) {
		frappe.confirm("Are you sure you want to delete Purchase Receipt?", function () {
			new ERPNextMigratorController(frm).delete_now("Purchase Receipt");
		});
	},
	import_sales_order: function (frm) { 
		frappe.confirm("Are you sure you want to import Sales Order?", function () {
			new ERPNextMigratorController(frm).import_now("Sales Order"); 
		});
	},
	delete_sales_order: function (frm) {
		frappe.confirm("Are you sure you want to delete Sales Order?", function () {
			new ERPNextMigratorController(frm).delete_now("Sales Order");
		});
	},
	import_sales_invoice: function (frm) { 
		frappe.confirm("Are you sure you want to import Sales Invoice?", function () {
			new ERPNextMigratorController(frm).import_now("Sales Invoice"); 
		});
	},
	delete_sales_invoice: function (frm) {
		frappe.confirm("Are you sure you want to delete Sales Invoice?", function () {
			new ERPNextMigratorController(frm).delete_now("Sales Invoice");
		});
	},
	import_payment_entry: function (frm) { 
		frappe.confirm("Are you sure you want to import Payment Entry?", function () {
			new ERPNextMigratorController(frm).import_now("Payment Entry"); 
		});
	},
	delete_payment_entry: function (frm) {
		frappe.confirm("Are you sure you want to delete Payment Entry?", function () {
			new ERPNextMigratorController(frm).delete_now("Payment Entry");
		});
	},
	import_stock_entry: function (frm) { 
		frappe.confirm("Are you sure you want to import Stock Entry?", function () {
			new ERPNextMigratorController(frm).import_now("Stock Entry"); 
		});
	},
	delete_stock_entry: function (frm) {
		frappe.confirm("Are you sure you want to delete Stock Entry?", function () {
			new ERPNextMigratorController(frm).delete_now("Stock Entry");
		});
	},
	import_delivery_note: function (frm) { 
		frappe.confirm("Are you sure you want to import Delivery Note?", function () {
			new ERPNextMigratorController(frm).import_now("Delivery Note"); 
		});
	},
	delete_delivery_note: function (frm) {
		frappe.confirm("Are you sure you want to delete Delivery Note?", function () {
			new ERPNextMigratorController(frm).delete_now("Delivery Note");
		});
	},
	import_subscription: function (frm) {
		frappe.confirm("Are you sure you want to import Subscription?", function () {
			new ERPNextMigratorController(frm).import_now("Subscription");
		});
	},
	delete_subscription: function (frm) {
		frappe.confirm("Are you sure you want to delete Subscription?", function () {
			new ERPNextMigratorController(frm).delete_now("Subscription");
		});
	},
});

class ERPNextMigratorController {
	constructor(frm) {
		this.frm = frm;
	}

	import_now(doctype) {
		frappe.call({
			method: "vernonmigrator.vernonmigrator.functions.import_doc.execute",
			args: {
				erpnext_migrator_name: this.frm.doc['name'],
				doctype: doctype,
				action: "import"
			},
			freeze: true,
			freeze_message: "Importing...",
			// async: true,
			success: function (response) {
				frappe.msgprint("Import Success!");
			},
			error: function (response) {
				// Tampilkan msg response error
				frappe.msgprint("Import Failed!");
				
				console.log(response.message);
			}
		});
	}

	delete_now(doctype) {
		frappe.call({
			method: "vernonmigrator.vernonmigrator.functions.import_doc.execute",
			args: {
				erpnext_migrator_name: this.frm.doc['name'],
				doctype: doctype,
				action: "wipe"
			},
			callback: function (response) {
				frappe.msgprint("Delete Berhasil!");
				// Confirm before reloading the page
				// frappe.confirm("Delete berhasil! Apakah Anda ingin memuat ulang halaman?", function () {
				// 	location.reload();
				// });
			}
		});
	}

	close_purchasing() {
		frappe.call({
			method: "vernonmigrator.vernonmigrator.functions.import_doc.execute",
			args: {
				erpnext_migrator_name: this.frm.doc['name'],
				action: "close_purchasing_doc"
			},
			callback: function (response) {
				frappe.msgprint("Close Purchasing Berhasil!");
			}
		});
	}
}