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

	# 1. Import tree data
	import_tree_data(doc.source_url, doc.target_url, source_headers, target_headers, "Item Group", doc)
	import_tree_data(doc.source_url, doc.target_url, source_headers, target_headers, "Account", doc)
	import_tree_data(doc.source_url, doc.target_url, source_headers, target_headers, "Cost Center", doc)

	# 2. Import master data lainnya
	import_doctype(doc.source_url, doc.target_url, source_headers, target_headers, "UOM", doc)
	import_doctype(doc.source_url, doc.target_url, source_headers, target_headers, "Warehouse", doc)
	import_doctype(doc.source_url, doc.target_url, source_headers, target_headers, "Brand", doc)
	import_doctype(doc.source_url, doc.target_url, source_headers, target_headers, "Item", doc)

	# 3. Import setup data
	import_doctype(doc.source_url, doc.target_url, source_headers, target_headers, "Price List", doc)
	import_doctype(doc.source_url, doc.target_url, source_headers, target_headers, "Tax Template", doc)
	import_doctype(doc.source_url, doc.target_url, source_headers, target_headers, "Payment Terms Template", doc)
	import_doctype(doc.source_url, doc.target_url, source_headers, target_headers, "Shipping Rule", doc)

	# 4. Import customer dan supplier
	import_doctype(doc.source_url, doc.target_url, source_headers, target_headers, "Customer Group", doc)
	import_doctype(doc.source_url, doc.target_url, source_headers, target_headers, "Supplier Group", doc)
	import_doctype(doc.source_url, doc.target_url, source_headers, target_headers, "Territory", doc)
	import_doctype(doc.source_url, doc.target_url, source_headers, target_headers, "Customer", doc)
	import_doctype(doc.source_url, doc.target_url, source_headers, target_headers, "Supplier", doc)

	# 5. Import transaksi
	import_doctype(doc.source_url, doc.target_url, source_headers, target_headers, "Sales Order", doc)
	import_doctype(doc.source_url, doc.target_url, source_headers, target_headers, "Purchase Order", doc)
	import_doctype(doc.source_url, doc.target_url, source_headers, target_headers, "Delivery Note", doc)
	import_doctype(doc.source_url, doc.target_url, source_headers, target_headers, "Purchase Receipt", doc)
	import_doctype(doc.source_url, doc.target_url, source_headers, target_headers, "Sales Invoice", doc)
	import_doctype(doc.source_url, doc.target_url, source_headers, target_headers, "Purchase Invoice", doc)
	import_doctype(doc.source_url, doc.target_url, source_headers, target_headers, "Stock Entry", doc)
	import_doctype(doc.source_url, doc.target_url, source_headers, target_headers, "Journal Entry", doc)


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
			return
	# Jika belum ada entri, tambahkan baru
	doc.append("update_log", {
		"doctype_name": doctype_name,
		"last_update": last_update
	})
	doc.save()
	# Commit changes immediately
	frappe.db.commit()

def import_tree_data(source_url, target_url, source_headers, target_headers, doctype, doc):
	"""
	Mengimpor semua data tree tanpa memperhatikan field `modified`.
	Memastikan parent diimpor sebelum child dan tidak ada duplikasi.
	"""
	response = requests.get(f"{source_url}/api/resource/{doctype}", headers=source_headers)
	if response.status_code == 200:
		data_list = response.json().get("data", [])
		data_list.sort(key=lambda x: x.get("lft", 0))

		# Counter remaining data
		counter_processed = 0

		for data in data_list:
			# frappe.show_alert(f"Mengimpor data tree {doctype}", counter_processed, data_list.length, "Please wait")
			# frappe.show_progress(f"Mengimpor data tree {doctype}", counter_processed, data_list.length, "Please wait")
			
			# Check if data exists in target. If exists, skip
			exists_response = requests.get(
				f"{target_url}/api/resource/{doctype}/{data['name']}",
				headers=target_headers
			)
			if exists_response.status_code == 200:
				frappe.msgprint(f"{doctype} '{data['name']}' sudah ada di target. Melewati...")
				continue

			# Get full data
			source_doc = requests.get(f"{source_url}/api/resource/{doctype}/{data['name']}", headers=source_headers)
			if source_doc.status_code == 200:
				data = source_doc.json().get("data", {})
			else:
				frappe.throw(f"Gagal mengambil data {doctype} '{data['name']}' dari source. Error: {source_doc.text}")
			
			# Post data to Target URL
			response = requests.post(f"{target_url}/api/resource/{doctype}", headers=target_headers, json=data)
			if response.status_code == 200:
				frappe.msgprint(f"{doctype} '{data['name']}' berhasil diimpor.")
			else:
				frappe.throw(f"Gagal mengimpor {doctype} '{json.dumps(data)}'. Error: {response.text}")

		# Update last update di child table ERPNext Migrator untuk doctype ini
		modified = max(data.get("modified") for data in data_list) if data_list else datetime.now()
		update_last_update(doc, doctype, modified)

		# Update counter processed
		counter_processed = counter_processed + 1
	else:
		frappe.throw(f"Gagal mengambil data {doctype} dari source. Error: {response.text}")


def import_doctype(source_url, target_url, source_headers, target_headers, doctype, doc):
	"""
	Mengimpor data doctype non-tree.
	Memastikan tidak ada duplikasi data.
	"""
	modified = get_modified(doc, doctype)
	modified_filter = f"?filters=[['modified','>', '{modified}']]" if modified else ""
	response = requests.get(f"{source_url}/api/resource/{doctype}{modified_filter}", headers=source_headers)
	if response.status_code == 200:
		data_list = response.json().get("data", [])

		for data in data_list:
			exists_response = requests.get(
				f"{target_url}/api/resource/{doctype}/{data['name']}",
				headers=target_headers
			)
			if exists_response.status_code == 200:
				frappe.msgprint(f"{doctype} '{data['name']}' sudah ada di target. Melewati...")
				continue

			response = requests.post(f"{target_url}/api/resource/{doctype}", headers=target_headers, json=data)
			if response.status_code == 200:
				frappe.msgprint(f"{doctype} '{data['name']}' berhasil diimpor.")
			else:
				frappe.throw(f"Gagal mengimpor {doctype} '{data['name']}'. Error: {response.text}")

		modified = max(data.get("modified") for data in data_list) if data_list else datetime.now()
		update_last_update(doc, doctype, modified)
		
	else:
		frappe.throw(f"Gagal mengambil data {doctype} dari source. Error: {response.text}")
