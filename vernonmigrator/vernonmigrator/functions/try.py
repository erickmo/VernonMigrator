import frappe
import json
import requests
from datetime import datetime

@frappe.whitelist()
def execute_function(*args,**kwargs):
	"""
	This fonction will be executed when the Execute Action Button will be clicked
	"""
	# Konversi kwargs ke string JSON dengan indentasi agar lebih mudah dibaca
	# Get ERPNext Migrator Doc
	x = kwargs['doc']	
	doc_dict = json.loads(x)
	docname = doc_dict['name']
	doc = frappe.get_doc("ERPNext Migrator", docname)

	# Konfigurasi API
	source_headers = {
			"Authorization": f"token {doc.source_api_key}:{doc.source_api_secret}",
			"Content-Type": "application/json"
	}
	target_headers = {
			"Authorization": f"token {doc.target_api_key}:{doc.target_api_secret}",
			"Content-Type": "application/json"
	}

	# Get Company from target
	response = requests.get(f"{doc.target_url}/api/resource/Company", headers=target_headers)
	if response.status_code == 200:
		company = response.json().get("data", {})
	else:
		frappe.throw(f"Gagal mengambil data Company '{doc.target_company}' dari target. Error: {response.text}")
	
	# Take only the first company
	company = company[0]

	# dict urutan doctype yg akan diimport dan berikan info:
	# - tree atau bukan 
	# - hapus semua atau tidak
	# - ignore delete error atau tidak
	is_delete_all = True
	doctypes = {
		"Item Group": {"tree": True, "delete_all": is_delete_all, "continue_on_delete_error": False},
		# "Account": {"tree": True, "delete_all": is_delete_all, "continue_on_delete_error": True},
		"Cost Center": {"tree": True, "delete_all": is_delete_all, "continue_on_delete_error": True},
		"UOM": {"tree": False, "delete_all": is_delete_all, "continue_on_delete_error": False},
		"Warehouse": {"tree": False, "delete_all": is_delete_all, "continue_on_delete_error": False},
		"Brand": {"tree": False, "delete_all": is_delete_all, "continue_on_delete_error": False},
		"Item": {"tree": False, "delete_all": is_delete_all, "continue_on_delete_error": False},
		"Module Profile": {"tree": False, "delete_all": is_delete_all, "continue_on_delete_error": False},
		"Role": {"tree": False, "delete_all": is_delete_all, "continue_on_delete_error": False},
		"Role Profile": {"tree": False, "delete_all": is_delete_all, "continue_on_delete_error": False},
		"User": {"tree": False, "delete_all": is_delete_all, "continue_on_delete_error": False},
		"Price List": {"tree": False, "delete_all": is_delete_all, "continue_on_delete_error": False},
		"Payment Terms Template": {"tree": False, "delete_all": is_delete_all, "continue_on_delete_error": False},
		"Shipping Rule": {"tree": False, "delete_all": is_delete_all, "continue_on_delete_error": False},
		"Customer Group": {"tree": True, "delete_all": is_delete_all, "continue_on_delete_error": False},
		"Supplier Group": {"tree": True, "delete_all": is_delete_all, "continue_on_delete_error": False},
		"Territory": {"tree": True, "delete_all": is_delete_all, "continue_on_delete_error": False},
		"Address": {"tree": False, "delete_all": is_delete_all, "continue_on_delete_error": False},
		"Contact": {"tree": False, "delete_all": is_delete_all, "continue_on_delete_error": False},
		"Customer": {"tree": False, "delete_all": is_delete_all, "continue_on_delete_error": False},
		"Supplier": {"tree": False, "delete_all": is_delete_all, "continue_on_delete_error": False},
		"Sales Order": {"tree": False, "delete_all": is_delete_all, "continue_on_delete_error": False},
		"Purchase Order": {"tree": False, "delete_all": is_delete_all, "continue_on_delete_error": False},
		"Delivery Note": {"tree": False, "delete_all": is_delete_all, "continue_on_delete_error": False},
		"Purchase Receipt": {"tree": False, "delete_all": is_delete_all, "continue_on_delete_error": False},
		"Sales Invoice": {"tree": False, "delete_all": is_delete_all, "continue_on_delete_error": False},
		"Purchase Invoice": {"tree": False, "delete_all": is_delete_all, "continue_on_delete_error": False},
		"Stock Entry": {"tree": False, "delete_all": is_delete_all, "continue_on_delete_error": False},
		"Payment Entry": {"tree": False, "delete_all": is_delete_all, "continue_on_delete_error": False},
		"Journal Entry": {"tree": False, "delete_all": is_delete_all, "continue_on_delete_error": False}
	}

	# Process dictionary di atas untuk mengimpor data, jika delete_all == True, hapus data dulu sebelum import
	for doctype, config in doctypes.items():
		if config["delete_all"]:
			delete_all_data(doc.target_url, target_headers, doctype, config["tree"], config["continue_on_delete_error"])

		if config["tree"]:
			import_tree_data(doc.source_url, doc.target_url, source_headers, target_headers, doctype, doc, company)
		else:
			import_doctype(doc.source_url, doc.target_url, source_headers, target_headers, doctype, doc, company)

def get_last_update(doc, doctype_name):
	"""
	Mengambil waktu terakhir update untuk doctype tertentu dari child table `update_log`.
	"""
	for log in doc.update_log:
		if log.doctype_name == doctype_name:
			return log.last_update
	return None

def update_last_update(doc, doctype_name, last_update):
	"""
	Memperbarui atau menambahkan entri di child table `update_log`.
	"""
	for log in doc.update_log:
		if log.doctype_name == doctype_name:
			log.last_update = last_update
			doc.save()
			frappe.db.commit()
			return

	# Jika belum ada entri, tambahkan baru
	doc.append("update_log", {
		"doctype_name": doctype_name,
		"last_update": last_update
	})
	doc.save()
	frappe.db.commit()

# merge delete_all_data and delete_all_tree_data. Receive parameter is tree or not
def delete_all_data(target_url, target_headers, doctype, is_tree, continue_on_delete_error=False):
	"""
	Delete all data in a doctype or tree doctype
	"""

	# progress counter
	counter_processed = 0

	# ignored error counter
	counter_error = 0

	# loop until no data left
	while True:
		# Get data from target
		response = requests.get(f"{target_url}/api/resource/{doctype}?limit_page_length=1000&fields=[\"*\"]", headers=target_headers)
		if response.status_code == 200:
			data_list = response.json().get("data", [])

			# if no data left (including error if continue on error), break
			if len(data_list) == 0:
				break
			elif len(data_list) == counter_error and continue_on_delete_error:
				break

			#if tree doctype, sort by largest lft
			if is_tree:
				data_list.sort(key=lambda x: x.get("lft", 0), reverse=True)

			for data in data_list:
				#show progress
				counter_processed = counter_processed + 1
				progress_percentage = (counter_processed / len(data_list)) * 100
				frappe.publish_progress(progress_percentage, title=f"Menghapus data 🍎 {doctype}", description=f"Menghapus {counter_processed} data")

				# Delete data
				response = requests.delete(f"{target_url}/api/resource/{doctype}/{data['name']}", headers=target_headers)
				if response.status_code == 200 or response.status_code == 202:
					continue
				else:
					if continue_on_delete_error:
						counter_error = counter_error + 1
						frappe.msgprint(f"Gagal menghapus {doctype} '{data['name']}'. Error: {response.status_code} {response.text}")
						continue
					else:
						frappe.throw(f"Gagal menghapus {doctype} '{data['name']}'. Error: {response.status_code} {response.text}")
		else:
			frappe.throw(f"Gagal mengambil data {doctype} dari target. Error: {response.text}")

def import_tree_data(source_url, target_url, source_headers, target_headers, doctype, doc, company):
	"""
	Mengimpor semua data tree tanpa memperhatikan field `modified`.
	Memastikan parent diimpor sebelum child dan tidak ada duplikasi.
	"""
	# Get data from source sampai semua data terimpor
	response = requests.get(f"{source_url}/api/resource/{doctype}?limit_page_length=1000", headers=source_headers)

	if response.status_code == 200:
		data_list = response.json().get("data", [])
		data_list.sort(key=lambda x: x.get("lft", 0))

		# Counter remaining data
		counter_processed = 0

		for data in data_list:
			# Update counter processed
			counter_processed = counter_processed + 1
			progress_percentage = (counter_processed / len(data_list)) * 100
			frappe.publish_progress(progress_percentage, title=f"Mengimpor data tree 🍎 {doctype}", description=f"Memproses {counter_processed} dari {len(data_list)}")	
			
			# Check if data exists in target. If exists, skip
			exists_response = requests.get(
				f"{target_url}/api/resource/{doctype}/{data['name']}",
				headers=target_headers
			)
			if response.status_code == 200 or response.status_code == 202:
				# frappe.msgprint(f"{doctype} '{data['name']}' sudah ada di target. Melewati...")
				continue

			# Get full data
			source_doc = requests.get(f"{source_url}/api/resource/{doctype}/{data['name']}", headers=source_headers)
			if source_doc.status_code == 200:
				data = source_doc.json().get("data", {})

				# --------------------------------------------------------
				# MODIFY DATA IF NECESSARY
				# --------------------------------------------------------
				# Replace company field with target company
				if "company" in data:
					data["company"] = company["name"]
				# --------------------------------------------------------
			else:
				frappe.throw(f"Gagal mengambil data {doctype} '{data['name']}' dari source. Error: {source_doc.text}")
			

			# Post data to Target URL
			response = requests.post(f"{target_url}/api/resource/{doctype}", headers=target_headers, json=data)
			if response.status_code == 200:
				# frappe.msgprint(f"{doctype} '{data['name']}' berhasil diimpor.")
				continue
			else:
				frappe.throw(f"Gagal mengimpor {doctype} '{json.dumps(data)}'. Error: {response.text}")

		# Update last update di child table ERPNext Migrator untuk doctype ini
		modified = datetime.now()
		update_last_update(doc, doctype, modified)

	else:
		frappe.throw(f"Gagal mengambil data {doctype} dari source. Error: {response.text}")

def import_doctype(source_url, target_url, source_headers, target_headers, doctype, doc, company):
	"""
	Mengimpor data doctype non-tree.
	Memastikan tidak ada duplikasi data.
	"""
	modified = get_last_update(doc, doctype)
	# modified_filter = f"?filters=[['modified','>', '{modified}']]" if modified else ""
	modified_filter = ""
	response = requests.get(f"{source_url}/api/resource/{doctype}?limit_page_length=1000", headers=source_headers)

	# Counter remaining data
	counter_processed = 0

	if response.status_code == 200:
		data_list = response.json().get("data", [])

		for data in data_list:
			# Update counter processed
			counter_processed = counter_processed + 1
			progress_percentage = (counter_processed / len(data_list)) * 100
			frappe.publish_progress(progress_percentage, title=f"Mengimpor data 🍎 {doctype}", description=f"Memproses {counter_processed} dari {len(data_list)}")	

			exists_response = requests.get(
				f"{target_url}/api/resource/{doctype}/{data['name']}",
				headers=target_headers
			)
			if exists_response.status_code == 200:
				# frappe.msgprint(f"{doctype} '{data['name']}' sudah ada di target. Melewati...")
				continue

			# Get full data
			source_doc = requests.get(f"{source_url}/api/resource/{doctype}/{data['name']}", headers=source_headers)
			if source_doc.status_code == 200:
				data = source_doc.json().get("data", {})
				
				# -------------------------------------------------------------
				# Modify data if necessary
				# -------------------------------------------------------------
				if doctype == "Address":
					if data['is_your_company_address'] == 1:
						# replace the company in the links with the target company
						data["links"] = [{"link_doctype": "Company", "link_name": company["name"]}]
					else:
						data["links"] = None
			
				# Replace company field with target company
				if "company" in data:
					data["company"] = company["name"]
				# -------------------------------------------------------------
			else:
				frappe.throw(f"Gagal mengambil data {doctype} '{data['name']}' dari source. Error: {source_doc.text}")


			response = requests.post(f"{target_url}/api/resource/{doctype}", headers=target_headers, json=data)
			if response.status_code == 200:
				# frappe.msgprint(f"{doctype} '{data['name']}' berhasil diimpor.")
				continue
			else:
				frappe.throw(f"Gagal mengimpor {doctype} '{data['name']}'. Error: {response.text}")

		modified = datetime.now()
		update_last_update(doc, doctype, modified)
		
	else:
		frappe.throw(f"Gagal mengambil data {doctype} dari source. Error: {response.text}")
