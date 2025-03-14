import frappe
import json
import requests
from datetime import datetime
import pytz

# tree doctype dict
tree_doctypes = [
	"Item Group",
	"Account",
	"Cost Center",
	"Warehouse",
	"Customer Group",
	"Supplier Group",
	"Territory"
]

# Continue on delete error list (untuk tree dan transaction doctype)
continue_on_delete_error_list = [
	"Item Group",
	"Asset Category",
	"Account",
	"Cost Center",
	"Warehouse",
	"Customer Group",
	"Supplier Group",
	"Territory"
]

# Continue on input data error list
continue_on_input_data_error_list = [
	"Item Group",
	"Item",
	"Account",
	"Cost Center",
	# "Asset Category",
	"Customer Group",
	"Supplier Group",
	"Customer"
]

# List of has child tables doc 
has_child_tables = [
	"Journal Entry",
	"Asset Category",
	"Sales Order",
	"Purchase Order",
	"Sales Invoice",
	"Purchase Invoice",
	"Delivery Note",
	"Purchase Receipt",
	"Stock Entry",
	"Payment Entry",
	"Quotation",
]

@frappe.whitelist()
def execute(*args,**kwargs):
	# disable throttle
	frappe.flags.disable_throttle = True
	
	# ambil kwargs[erpnext_migrator] dan kwargs[doctype]
	erpnext_migrator_name = kwargs['erpnext_migrator_name']
	doctype = kwargs['doctype']
	action = kwargs['action']
	
	# ambil kwargs[doc] dan kwargs[docname]
	erpnext_migrator_doc = frappe.get_doc('ERPNext Migrator', erpnext_migrator_name)

	# konfigurasi source API
	source_headers = {
		"Authorization": f"token {erpnext_migrator_doc.source_api_key}:{erpnext_migrator_doc.source_api_secret}",
		"Content-Type": "application/json"
	}

	# Get system timezone
	system_timezone = frappe.utils.get_system_timezone()
	now = datetime.now(	pytz.timezone(system_timezone))

	# Get Company from target
	companies = frappe.get_all("Company", fields=["*"])
	company = companies[0]

	frappe.msgprint(f"Importing {doctype} from {erpnext_migrator_doc.source_url}")
	
	# Execute the action
	if action == "delete":
		success_count, error_list = delete_all_data(doctype=doctype)
	elif action == "wipe":
		# delete all data in doctype using database api
		frappe.db.sql(f"DELETE FROM `tab{doctype}`")
		success_count = 1
		error_list = []
	elif action == "import":
		success_count, error_list = import_data(
			source_url= erpnext_migrator_doc.source_url, 
			source_headers=source_headers,
			doctype=doctype, 
			company=company
		)

	# Update last update field dengan nama field '{doctype}_last_update' 
	try:
		last_update_field = f"{doctype.lower()}_last_update".replace(" ", "_")
		if hasattr(erpnext_migrator_doc, last_update_field):
			erpnext_migrator_doc.set(last_update_field, now.strftime('%Y-%m-%d %H:%M:%S'))
			erpnext_migrator_doc.save()
		else:
			frappe.msgprint(f"Field {last_update_field} does not exist in ERPNext Migrator")
	except Exception as e:
		# comment = f"Imported {doctype} on {now.strftime('%Y-%m-%d %H:%M:%S')}. Error updating last update field: {e}"
		# erpnext_migrator_doc.add_comment('Comment', comment)
		# erpnext_migrator_doc.save()
		frappe.throw(f"Error updating last update field: {e}")

	# Add comment to the erpnext_migrator_doc as the log of the import
	comment = f"Imported {doctype} on {now.strftime('%Y-%m-%d %H:%M:%S')}. Successfully imported: {success_count}. Errors: {len(error_list)}"
	if error_list:
		comment += f". <hr>Error details: {'<hr>'.join(error_list)}"
	erpnext_migrator_doc.add_comment('Comment', comment)
	erpnext_migrator_doc.save()

	frappe.msgprint(f"Import {doctype} selesai")

def delete_all_data(doctype):
	"""
	Delete all data in a doctype or tree doctype
	"""

	# Check if doctype is tree doctype
	is_tree = doctype in tree_doctypes

	# Set Continue on delete error
	continue_on_delete_error = doctype in continue_on_delete_error_list

	# progress counter
	counter_processed = 0

	# ignored error counter
	counter_error = 0

	# error list
	error_list = []

	# loop until no data left
	while True:
		# Get all data here sort by lft desc if tree doctype, otherwise order by name
		if is_tree:
			data = frappe.get_all(doctype, fields=["name", "lft"], order_by="lft desc")

			# sort data by lft desc
			data = sorted(data, key=lambda x: x['lft'], reverse=True)
		else:
			data = frappe.get_all(doctype, fields=["name"], order_by="name")

		# if no data left (including error if continue on error), break
		if len(data) == 0:
			break
		elif len(data) == counter_error and continue_on_delete_error:
			break

		frappe.msgprint(f"Deleting {len(data)} data from {doctype}")

		# loop through data and delete
		for d in data:
			try:
				frappe.delete_doc(doctype, d.name)
				counter_processed = counter_processed + 1
				progress_percentage = (counter_processed / len(data)) * 100
				frappe.publish_progress(progress_percentage, title=f"Deleting 🗑️ {doctype}", description=f"Deleting {counter_processed} data from {len(data)}")
			except Exception as e:
				if continue_on_delete_error:
					counter_error = counter_error + 1
					counter_processed = counter_processed + 1
					error_list.append(f"{d.name}: {e}")
					progress_percentage = (counter_processed / len(data)) * 100
					frappe.publish_progress(progress_percentage, title=f"Deleting 🗑️ {doctype}", description=f"Deleting {counter_processed} data from {len(data)}")
				else:
					frappe.throw(f"Gagal menghapus {doctype} '{d.name}'. Error: {e}")

	return counter_processed, error_list

def import_data(source_url, source_headers, doctype, company):

	# Konfigurasi continue_on_input_data_error_list
	continue_on_input_data_error = doctype in continue_on_input_data_error_list

	# Set pagination, page_length = 10 kalau has_child_tables, 100 kalau bukan tree doctype, 1000 kalau tree doctype
	page_length = 50 if doctype in has_child_tables else 200
	if doctype in tree_doctypes:
		page_length = 1000

	limit_start = 0

	# Set counter
	counter_processed = 0
	error_counter = 0
	iteration_counter = 0
	error_list = []

	# While more data
	while True:
		iteration_counter = iteration_counter + 1
		limit_start = (iteration_counter - 1) * page_length
		frappe.msgprint(f"Importing {doctype} Iterasi #{iteration_counter}")

		# get data from source order by created
		response = requests.get(f"{source_url}/api/resource/{doctype}?order_by=creation asc&limit_page_length={page_length}&limit_start={limit_start}&fields=[\"*\"]&", headers=source_headers)
		if response.status_code == 200:
			# if data is empty, break
			data_list = response.json().get("data", [])
			if len(data_list) == 0:
				break

			# -----------------------------------
			# Kalau doctype adalah tree doctype, sort data by lft
			if doctype in tree_doctypes:
				data_list = sorted(data_list, key=lambda x: x['lft'], reverse=False)

			# loop through data
			for data in data_list:
				# Flag skip_import
				skip_import = False

				# Import data, if error and continue_on_input_data_error_list, ignore (use try except)
				try:
					# Kalau ada child table, get doc from source
					if doctype in has_child_tables:
						response = requests.get(f"{source_url}/api/resource/{doctype}/{data['name']}", headers=source_headers)
						if response.status_code == 200:
							data = response.json().get("data", {})
						else:
							frappe.throw(f"Gagal mengambil data {doctype} '{data['name']}' dari source. Error: {response.text}")

					# create doc
					doc = frappe.get_doc({
						"doctype": doctype,
						"__islocal": 1,
						"__unsaved": 1,
						"company": company['name']
					})
					doc.update(data) # update data from source to doc object (doc) 

					# -----------------------------------
					# Custom code here (pre insert)
					# -----------------------------------
					# Kalau ada company, replace dengan company yang ada di target
					if "company" in data:
						doc.company = company['name']
					
					if doctype == "Contact":
						doc.user = None
					elif doctype == "Account":
						# bagian terakhir parent akan ada "- [NAMA COMPANY]" dari source data, ubah menjadi "- company['abbr']"
						if doc.parent_account:
							# hapus dari "-" terakhir hingga ke belakang
							doc.parent_account = doc.parent_account.rsplit("-", 1)[0]
							# tambahkan company['abbr'] di akhir
							doc.parent_account = doc.parent_account + f"- {company['abbr']}"
					elif doctype == "Customer":
						if not doc.customer_primary_address:
							doc.customer_primary_address = "Unknown Address-Billing"
						if not doc.customer_primary_contact:
							doc.customer_primary_contact = "Unknown Contact"
					# elif doctype Purchase Invoice or Purchase Recepit
					elif doctype == "Purchase Invoice" or doctype == "Purchase Receipt":
						new_po_no_list = {}

						# Untuk setiap Purchase Invoice Item, kalau ada Purchase Order, set Purchase Order dari previous_id
						for item in doc.items:
							if item.purchase_order:
								# Check kalau query purchase order ini sudah pernah, jadi tidak perlu query lagi. Simpan di dict
								if item.purchase_order in new_po_no_list:
									new_purchase_order_no = new_po_no_list[item.purchase_order]
								else:
									# Get PO Doc with custom_previous_id = item.purchase_order
									po = frappe.get_doc("Purchase Order", {"custom_previous_id": item.purchase_order})

									# Kalau po cancelled, skip import
									if po.docstatus == 2:
										skip_import = True
									else:
										new_purchase_order_no = po.name
										new_po_no_list[item.purchase_order] = new_purchase_order_no
	
								if new_purchase_order_no:
									item.purchase_order = new_purchase_order_no
									item.purchase_order_item = None
								else:
									frappe.throw(f"Purchase Order '{item.purchase_order}' tidak ditemukan")
					

					# ----------------------------------- End Custom code here -----------------------------------

					# Ensure doc is set before saving
					if doc and skip_import == False:
						# ========================================
						# Final doc modification
						# ========================================
						# Flag Submittable but cancelled
						is_cancelled = False
						if doc.docstatus == 2:
							doc.docstatus = 1
							is_cancelled = True

						# Set prev ID
						doc.custom_previous_id = data['name']

						# If ammended_from exists, get the new name
						if doc.get("amended_from"):
							amended_from = frappe.db.get_value(doctype, {"custom_previous_id": doc.amended_from}, "name")
							if amended_from:
								doc.amended_from = amended_from

						# ========================================
						# Insert Doc
						# ========================================
						doc.insert(ignore_permissions=True)

						# ========================================
						# If Flagged cancelled, cancel the doc
						# ========================================
						if is_cancelled:
							# Reload doc
							doc = frappe.get_doc(doctype, doc.name)
							doc.cancel()
					else:
						frappe.throw(f"Doc is not set for {doctype} '{data['name']}'")

					# -----------------------------------
					# Custom code here (post insert)
					# -----------------------------------
					# ----------------------------------- End Custom code here -----------------------------------

					# update progress
					counter_processed = counter_processed + 1
					progress_percentage = (counter_processed / (limit_start + len(data_list))) * 100
					frappe.publish_progress(progress_percentage, title=f"Importing 🍏 {doctype}", description=f"Importing Iterasi #{iteration_counter}: {counter_processed} data from {len(data_list)}")

				except Exception as e:
					if continue_on_input_data_error:
						frappe.msgprint(f"Gagal mengimport {doctype} '{data['name']}', tapi tetap lanjut'. Error: {e}")
						error_counter = error_counter + 1
						error_list.append(f"{data['name']}: {e}")

						# update progress
						counter_processed = counter_processed + 1
						progress_percentage = (counter_processed / (limit_start + len(data_list))) * 100
						frappe.publish_progress(progress_percentage, title=f"Importing 🍏 {doctype}", description=f"Importing Iterasi #{iteration_counter}: {counter_processed} data from {len(data_list)}")
						continue
					else:
						frappe.throw(f"Gagal mengimport {doctype} '{data['name']}'. Error: {e}")
			#update limit_start
			limit_start = limit_start + page_length
		
		# commit DB
		frappe.db.commit()

	return counter_processed, error_list