import frappe
import json
import requests
from datetime import datetime

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

# delete all doctype dict
delete_all_doctypes = [
	"Item Group",
	"Item",
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
	"Account",
	"Cost Center",
	"Warehouse",
	"Customer Group",
	"Supplier Group",
	"Territory"
]

# Continue on input data error list
continue_on_input_data_error_list = [
]

@frappe.whitelist()
def import_doctype(*args,**kwargs):
	# ambil kwargs[erpnext_migrator] dan kwargs[doctype_to_import]
	erpnext_migrator_name = kwargs['erpnext_migrator_name']
	doctype_to_import = kwargs['doctype_to_import']
	
	# ambil kwargs[doc] dan kwargs[docname]
	erpnext_migrator_doc = frappe.get_doc('ERPNext Migrator', erpnext_migrator_name)

	# konfigurasi source API
	source_headers = {
		"Authorization": f"token {erpnext_migrator_doc.source_api_key}:{erpnext_migrator_doc.source_api_secret}",
		"Content-Type": "application/json"
	}

	# Get Company from target
	response = requests.get(f"{erpnext_migrator_doc.target_url}/api/resource/Company", headers=target_headers)
	if response.status_code == 200:
		company = response.json().get("data", {})
	else:
		frappe.throw(f"Gagal mengambil data Company '{erpnext_migrator_doc.target_company}' dari target. Error: {response.text}")
	
	company = company[0]

	frappe.msgprint(f"Importing {doctype_to_import} from {erpnext_migrator_doc.source_url} to {erpnext_migrator_doc.target_url}")
	
	# Kalau doctype ada di delete_all_doctypes, delete all data
	if doctype_to_import in delete_all_doctypes:
		delete_all_data(doctype_to_import=doctype_to_import)
	
	frappe.throw(f"Company2: {company}")
	
	# Import doctype
	import_data(
		source_url= erpnext_migrator_doc.source_url, 
		source_headers=source_headers,
		doctype_to_import=doctype_to_import, 
		continue_on_input_data_error_list=doctype_to_import in continue_on_input_data_error_list,
	)

	# Update last update field dengan nama field '{doctype_to_import}_last_update'
	erpnext_migrator_doc.set(f"{doctype_to_import}_last_update", datetime.now())
	erpnext_migrator_doc.save()

def delete_all_data(doctype_to_import):
	"""
	Delete all data in a doctype or tree doctype
	"""

	# Check if doctype is tree doctype
	is_tree = doctype_to_import in tree_doctypes

	# Set Continue on delete error
	continue_on_delete_error = doctype_to_import in continue_on_delete_error_list

	# progress counter
	counter_processed = 0

	# ignored error counter
	counter_error = 0

	# loop until no data left
	while True:
		# Get all data here sort by lft desc if tree doctype, otherwise order by name
		if is_tree:
			data = frappe.get_all(doctype_to_import, fields=["name", "lft"], order_by="lft desc")
		else:
			data = frappe.get_all(doctype_to_import, fields=["name"], order_by="name")

		# if no data left (including error if continue on error), break
		if len(data) == 0:
			break
		elif len(data) == counter_error and continue_on_delete_error:
			break

		frappe.msgprint(f"Deleting {len(data)} data from {doctype_to_import}")

		# loop through data and delete
		for d in data:
			try:
				frappe.delete_doc(doctype_to_import, d.name)
				counter_processed = counter_processed + 1
				progress_percentage = (counter_processed / len(data)) * 100
				frappe.publish_progress(progress_percentage, title=f"Deleting 🗑️ {doctype_to_import}", description=f"Deleting {counter_processed} data from {len(data)}")
			except Exception as e:
				if continue_on_delete_error:
					counter_error = counter_error + 1
					counter_processed = counter_processed + 1
					progress_percentage = (counter_processed / len(data)) * 100
					frappe.publish_progress(progress_percentage, title=f"Deleting 🗑️ {doctype_to_import}", description=f"Deleting {counter_processed} data from {len(data)}")
				else:
					frappe.throw(f"Gagal menghapus {doctype_to_import} '{d.name}'. Error: {e}")


def import_data(source_url, source_headers, doctype_to_import):

	# Konfigurasi continue_on_input_data_error_list
	continue_on_input_data_error_list = doctype_to_import in continue_on_input_data_error_list

	# Set pagination
	page_length = 40
	page_start = 0

	# Set counter
	counter_processed = 0
	error_counter = 0
	iteration_counter = 0

	# While more data
	while True:
		iteration_counter = iteration_counter + 1
		frappe.msgprint(f"Importing {doctype_to_import} Iterasi #{iteration_counter}")

		# get data from source order by created
		response = requests.get(f"{source_url}/api/resource/{doctype_to_import}?limit_page_length={page_length}&limit_start={page_start}&fields=[\"*\"]&order_by=creation", headers=source_headers)
		if response.status_code == 200:
			# if data is empty, break
			data_list = response.json().get("data", [])
			if len(data_list) == 0:
				break

			# loop through data
			for data in data_list:
				# Import data, if error and continue_on_input_data_error_list, ignore (use try except)
				try:
					# create doc
					doc = frappe.get_doc({
						"doctype": doctype_to_import,
						"__islocal": 1,
						"__unsaved": 1,
						"company": company['name']
					})
					doc.update(data) # update data from source to doc object (doc) 
					doc.save()

					# update progress
					counter_processed = counter_processed + 1
					progress_percentage = (counter_processed / len(data_list)) * 100
					frappe.publish_progress(progress_percentage, title=f"Importing 🍏 {doctype_to_import}", description=f"Importing Iterasi #{iteration_counter}: {counter_processed} data from {len(data_list)}")

				except Exception as e:
					if continue_on_input_data_error_list:
						frappe.msgprint(f"Gagal mengimport {doctype_to_import} '{data['name']}, tapi tetap lanjut'. Error: {e}")
						error_counter = error_counter + 1

						# update progress
						counter_processed = counter_processed + 1
						progress_percentage = (counter_processed / len(data_list)) * 100
						frappe.publish_progress(progress_percentage, title=f"Importing 🍏 {doctype_to_import}", description=f"Importing Iterasi #{iteration_counter}: {counter_processed} data from {len(data_list)}")
						continue
					else:
						frappe.throw(f"Gagal mengimport {doctype_to_import} '{data['name']}'. Error: {e}")
			#update page_start
			page_start = page_start + page_length