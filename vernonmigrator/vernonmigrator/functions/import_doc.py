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
	"Territory",
	"Warehouse"
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
	"Price List",
	# "Asset Category",
	"Customer Group",
	"Supplier Group",
	# "Customer",
	"Supplier",
	"Warehouse"
	# "Journal Entry"
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
	"Warehouse"
]

# list field to import based on doctype
field_to_import = {
	"Purchase Order": [
		"naming_series",
		"supplier",
		"transaction_date",
		"required_by",
		"cost_center",
		"branch",
		"items",
		"apply_discount_on",
		"additional_discount_percentage",
		"discount_amount",
		"docstatus",
		"status"
	],
	"Purchase Receipt": [
		"naming_series",
		"supplier",
		"is_return",
		"posting_date",
		"posting_time", #kalau ada ini error is_internal_transfer not found
		"company",
		"set_posting_time",
		"items",
		"docstatus",
		"status"
	],
}

# list of Transaction Doctypes
transaction_doctypes = [
	"Sales Order",
	"Purchase Order",
	"Sales Invoice",
	"Purchase Invoice",
	"Delivery Note",
	"Purchase Receipt",
	"Stock Entry",
	"Payment Entry",
	"Journal Entry",
	"Expense Claim",
	"Payment Request",
	"Quotation",
]

# ------------------------------------------------------------
# DELETE ALL DATA
# ------------------------------------------------------------
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
	iteration_counter = 0
	while True:
		# increment iteration counter
		iteration_counter = iteration_counter + 1

		# Get all data here sort by lft desc if tree doctype, otherwise order by name
		if is_tree:
			# If iteration counter > 1, break while loop
			if iteration_counter > 1:
				break
			else:
				# Get all data from doctype
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
			frappe.msgprint(f"Deleting for {d.name} in {doctype}")
			can_delete, message = can_delete_data(doctype = doctype, docname = d.name)
			
			try:
				# VALIDATE IF DATA DELETABLE
				if can_delete == False:
					frappe.msgprint(f"😂Fail to delete for {d.name} in {doctype}")
				else:
					frappe.msgprint(f"😂Executing delete for {d.name} in {doctype}")
					frappe.delete_doc(doctype, d.name)

			except Exception as e:
				if continue_on_delete_error:
					counter_error = counter_error + 1
					error_list.append(f"{d.name}: {e}")
				else:
					frappe.throw(f"Gagal menghapus {doctype} '{d.name}'. Error: {e}")
			finally:
				counter_processed = counter_processed + 1
				progress_percentage = (counter_processed / len(data)) * 100
				frappe.publish_progress(progress_percentage, title=f"Deleting 🗑️ {doctype}", description=f"Deleting {counter_processed} data from {len(data)}")

	return counter_processed, error_list

# ------------------------------------------------------------
# EXECUTE
# ------------------------------------------------------------
@frappe.whitelist()
def execute(*args,**kwargs):
	# disable throttle
	frappe.flags.disable_throttle = True

	# ambil kwargs[erpnext_migrator], kwargs[doctype], kwargs[start_date] kalau ada atau set None, kwargs[end_date] kalau ada atau set None
	erpnext_migrator_name = kwargs['erpnext_migrator_name']
	doctype = kwargs['doctype']
	action = kwargs['action']
	import_start_date = None
	import_end_date = None
	if 'start_date' in kwargs:
		import_start_date = kwargs['start_date']
	if 'end_date' in kwargs:
		import_end_date = kwargs['end_date']

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


	# Execute the action
	if action == "delete":
		success_count, error_list = delete_all_data(doctype=doctype)
	elif action == "close_purchasing_doc":
		# Close or cancel purchase docs
		close_or_cancel_purchase_docs(erpnext_migrator_name=erpnext_migrator_name, doctype=doctype, action=action)
		success_count = 1
		error_list = []
	elif action == "wipe":
		# if tree or transaction use delete_all_data
		if doctype in tree_doctypes or doctype in transaction_doctypes:
			success_count, error_list = delete_all_data(doctype=doctype)
		else:
			frappe.db.sql(f"DELETE FROM `tab{doctype}`")
		success_count = 1
		error_list = []
	elif action == "import":
		frappe.msgprint(f"Importing {doctype} from {erpnext_migrator_doc.source_url}")
		success_count, error_list = import_data(
			source_url= erpnext_migrator_doc.source_url,
			source_headers=source_headers,
			doctype=doctype,
			company=company,
			start_date=import_start_date,
			end_date=import_end_date
		)

	# Update last update field dengan nama field '{doctype}_last_update'
	try:
		last_update_field = f"{doctype.lower()}_last_update".replace(" ", "_")

		if hasattr(erpnext_migrator_doc, last_update_field):
			erpnext_migrator_doc.set(last_update_field, f"{action} {now.strftime('%d-%m-%Y %H:%M:%S')}")
			erpnext_migrator_doc.save()
		else:
			frappe.msgprint(f"Field {last_update_field} does not exist in ERPNext Migrator")
	except Exception as e:
		# show error message
		frappe.throw(f"Error updating last update field: {last_update_field} {action} {now.strftime('%Y-%m-%d %H:%M:%S')}", "Update Last Update Field")
		frappe.throw(f"Error updating last update field: {last_update_field} {action} {now.strftime('%Y-%m-%d %H:%M:%S')}")

	# Add comment to the erpnext_migrator_doc as the log of the import
	comment = f"Imported {doctype} on {now.strftime('%Y-%m-%d %H:%M:%S')}. Successfully imported: {success_count}. Errors: {len(error_list)}"
	if error_list:
		comment += f". <hr>Error details: {'<hr>'.join(error_list)}"
	erpnext_migrator_doc.add_comment('Comment', comment)
	erpnext_migrator_doc.save()

	frappe.msgprint(f"Import {doctype} selesai")

def import_data(source_url, source_headers, doctype, company, start_date=None, end_date=None):

	# Konfigurasi continue_on_input_data_error_list
	is_continue_on_input_data_error = doctype in continue_on_input_data_error_list

	# Set pagination, page_length = 10 kalau has_child_tables, 100 kalau bukan tree doctype, 1000 kalau tree doctype
	page_length = 50 if doctype in has_child_tables else 200
	if doctype in tree_doctypes:
		page_length = 1000

	limit_start = 0

	# Set counter
	counter_processed = 0 # Starts at 0
	error_counter = 0 # Starts at 0
	iteration_counter = 0 # Starts at 1
	error_list = []

	# While more data
	while True:
		iteration_counter = iteration_counter + 1
		limit_start = (iteration_counter - 1) * page_length
		frappe.msgprint(f"Importing {doctype} Iterasi #{iteration_counter}")

		# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
		# Get data from source
		# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
		# Create filters for start_date and end_date if provided
		filters = ""
		if start_date:
			if filters:
				filters = f"{filters}, "
			# set start_date fields base on doc
			if doctype in ["Sales Order", "Purchase Order", "Delivery Note"]:
				# if filters is not empty, add , before adding new filter and set the start_date field
				filters = f"{filters} [\"transaction_date\", \">=\", \"{start_date}\"]"
			elif doctype in ["Stock Entry", "Payment Entry", "Journal Entry", "Expense Claim", "Payment Request", "Purchase Receipt", "Purchase Invoice", "Sales Invoice"]:
				filters = f"{filters} [\"posting_date\", \">=\", \"{start_date}\"]"
			elif doctype in ["Quotation"]:
				filters = f"{filters} [\"transaction_date\", \">=\", \"{start_date}\"]"
			elif doctype in ["Contact", "Customer", "Supplier"]:
				filters = f"{filters} [\"modified\", \">=\", \"{start_date}\"]"
			elif doctype in ["Item", "Item Group", "Warehouse", "Cost Center", "Account", "Customer Group", "Supplier Group", "Territory"]:
				filters = f"{filters} [\"modified\", \">=\", \"{start_date}\"]"
		if end_date:
			if filters:
				filters = f"{filters}, "
			# set end_date fields base on doc
			if doctype in ["Sales Order", "Purchase Order", "Delivery Note"]:
				filters = f"{filters} [\"transaction_date\", \"<=\", \"{end_date}\"]"
			elif doctype in ["Stock Entry", "Payment Entry", "Journal Entry", "Expense Claim", "Payment Request", "Purchase Receipt", "Purchase Invoice", "Sales Invoice"]:
				filters = f"{filters} [\"posting_date\", \"<=\", \"{end_date}\"]"
			elif doctype in ["Quotation"]:
				filters = f"{filters} [\"transaction_date\", \"<=\", \"{end_date}\"]"
			elif doctype in ["Contact", "Customer", "Supplier"]:
				filters = f"{filters} [\"modified\", \"<=\", \"{end_date}\"]"
			elif doctype in ["Item", "Item Group", "Warehouse", "Cost Center", "Account", "Customer Group", "Supplier Group", "Territory"]:
				filters = f"{filters} [\"modified\", \"<=\", \"{end_date}\"]"
			
		data_list = get_source_data_list(doctype = doctype, source_url = source_url, source_headers = source_headers, limit_start=limit_start, limit_page_length=page_length, filters=filters)

		# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
		# Process Data
		# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
		if data_list == None or len(data_list) == 0:
			break
		else:
			# -----------------------------------
			# Kalau doctype adalah tree doctype, sort data by lft
			if doctype in tree_doctypes:
				data_list = sorted(data_list, key=lambda x: x['lft'], reverse=False)

			# loop through data
			for data in data_list:
				# --------------------------- Update source data if necessary (has child tables)
				if doctype in has_child_tables:
					data = get_source_doc(doctype=doctype, source_url=source_url, source_headers=source_headers, name=data['name'])
					# debug data
					# frappe.msgprint(f"Data {doctype} {data['name']} : {json.dumps(data, indent=4)}")

				# --------------------------- Create Doc
				doc = create_doc(doctype=doctype, data=data, company=company)
				doc = modify_doc(doctype=doctype, doc=doc, data=data)

				try:
					# update progress
					counter_processed = counter_processed + 1

					# Update progress
					update_progress(counter_processed, limit_start, data_list, iteration_counter, data, doc, error_counter, doctype)

					# Save doc
					doc = save_doc(doc, data, doctype)

				except Exception as e:
					if is_continue_on_input_data_error:
						frappe.msgprint(f"Gagal mengimport {doctype} '{data['name']}', tapi tetap lanjut'. Error: {e}")
						error_counter = error_counter + 1
						error_list.append(f"{data['name']}: {e}")
						continue
					else:
						# raise error with doc (pretty print)
						do = json.loads(doc.as_json())
						frappe.throw(f"Gagal mengimport {doctype} '{data['name']}'. Error: {e}. Data: {json.dumps(do, indent=4)}")

		#update limit_start
		limit_start = limit_start + page_length

	return counter_processed, error_list

# ------------------------------------ UTILITY FUNCTIONS
#  Get Source Data List
def get_source_data_list(doctype, source_url, source_headers, limit_start, limit_page_length, filters=None):
	# get data from source order by created add pagination 
	# if filters is not None, add to url
	if filters:
		# debug if this is executed
		# frappe.throw(f"executing: {source_url}/api/resource/{doctype}?limit_start={limit_start}&limit_page_length={limit_page_length}&fields=[\"*\"]&order_by=creation asc&filters=[{filters}]")
		response = requests.get(f"{source_url}/api/resource/{doctype}?limit_start={limit_start}&limit_page_length={limit_page_length}&fields=[\"*\"]&order_by=creation asc&filters=[{filters}]", headers=source_headers)
	else:
		# debug if this is executed
		# frappe.throw(f"Not Executed")
		response = requests.get(f"{source_url}/api/resource/{doctype}?limit_start={limit_start}&limit_page_length={limit_page_length}&fields=[\"*\"]&order_by=creation asc", headers=source_headers)

	if response.status_code == 200:
		# if data is empty, break
		data_list = response.json().get("data", [])
		if len(data_list) == 0:
			# frappe.msgprint(f"Data {doctype} tidak ditemukan di source")
			return None

		# return data list
		return data_list
	else:
			# if response is not 200, raise error
		frappe.throw(f"Gagal mengambil data {doctype} dari source. Error: {response.text}")

#  Get Source Doc
def get_source_doc(doctype, source_url, source_headers, name):
	# get data from source order by created
	response = requests.get(f"{source_url}/api/resource/{doctype}/{name}?fields=[\"*\"]&", headers=source_headers)
	if response.status_code == 200:
		# if data is empty, break
		data = response.json().get("data", {})
		if not data:
			frappe.msgprint(f"Data {doctype} '{name}' tidak ditemukan di source")
			return None

		# return data list
		return data
	else:
			# if response is not 200, raise error
		frappe.throw(f"Gagal mengambil data {doctype} '{name}' dari source. Error: {response.text}")

# Create Doc
def create_doc(doctype, data, company):
	# create doc
	doc = frappe.get_doc({
		"doctype": doctype,
		"__unsaved": 1,
	})

	# update data based on field_to_import
	if doctype in field_to_import:
		for field in field_to_import[doctype]:
			doc.set(field, data.get(field))
	else:
		doc.update(data) # update data from source to doc object (doc)

	# Update company
	if "company" in data:
		doc.company = company['name']

	return doc

# Save Doc
def save_doc(doc, data, doctype):
	# --------------------------- Reset Settings per Data
	is_cancelled = False
	is_closed = False

	if doc == None:
		return None

	# ----------------------------------- Check if doc already exists
	if doctype in transaction_doctypes:
		existing_doc = frappe.get_all(doctype, filters={"custom_previous_id": data['name']})
		if existing_doc:
			doc = None

	if doc == None:
		return None

	# ----------------------------------- Link Target Doc to Source Doc
	doc.custom_previous_id = data['name']

	# ----------------------------------- Update Amended (from source to target)
	# If amended_from exists, get the new name
	if doc.get("amended_from"):
		doc.amended_from = frappe.db.get_value(doctype, {"custom_previous_id": doc.amended_from}, "name")

	# ========================================
	# Docstatus Management (Need to insert before close / cancel)
	# ========================================
	# Flag Submittable but cancelled / closed
	if doc.docstatus == 2:
		doc.docstatus = 1
		is_cancelled = data.get("status") == "Cancelled" or False
		is_closed = data.get("status") == "Closed" or False

	# ========================================
	# Insert Doc (Autosubmit if submittable)
	# ========================================
	doc.insert(ignore_permissions=True)

	# ========================================
	# If Flagged cancelled, cancel the doc
	# ========================================
	if is_cancelled or is_closed:
		# Reload doc
		doc = frappe.get_doc(doctype, doc.name)

		if is_cancelled:
			doc.cancel()
		elif is_closed:
			doc.close()

	# commit DB
	frappe.db.commit()

	return doc

# Update Progress
def update_progress(counter_processed, limit_start, data_list, iteration_counter, data, doc, error_counter, doctype):
	# update progress
	progress_percentage = (counter_processed / (limit_start + len(data_list))) * 100
	frappe.publish_progress(
		progress_percentage, 
		title=f"Importing 🍏 {doctype}", 
		description=(f"Importing Iterasi #{iteration_counter}: {counter_processed} / {len(data_list) * iteration_counter}. \n Document: {data.get('name')} \n Skip Import: {True if doc else False} \n Error: {error_counter} / {len(data_list)}")
	)

# ------------------------------------ CUSTOM DOC PER DOCTYPE
def modify_doc(doctype, doc, data):
	if doctype == "Contact":
		doc = modify_doc_contact(doc, data)
	elif doctype == "Account":
		doc = modify_doc_account(doc, data)
	elif doctype == "Customer":
		doc = modify_doc_customer(doc, data)
	elif doctype == "Purchase Order":
		doc = modify_doc_purchase_order(doc, data)
	elif doctype == "Purchase Invoice":
		doc = modify_doc_purchase_invoice(doc, data)
	elif doctype == "Purchase Receipt":
		doc = modify_doc_purchase_receipt(doc, data)
	elif doctype == "Sales Invoice":
		doc = modify_doc_sales_invoice(doc, data)

	# Tambahkan modify doc lainnya sesuai kebutuhan
	return doc

def modify_doc_contact(doc, data):
	doc.user = None
	return doc

def modify_doc_account(doc, data):
	# bagian terakhir parent akan ada "- [NAMA COMPANY]" dari source data, ubah menjadi "- company['abbr']"
	# if doc.parent_account:
	# 	# hapus dari "-" terakhir hingga ke belakang
	# 	doc.parent_account = doc.parent_account.rsplit("-", 1)[0]

	# 	# tambahkan company['abbr'] di akhir
	# 	doc.parent_account = doc.parent_account + f"- {company['abbr']}"

	return doc

def modify_doc_customer(doc, data):
	if not doc.customer_primary_address:
		doc.customer_primary_address = "Unknown Address-Billing"
	
	if not doc.customer_primary_contact:
		doc.customer_primary_contact = "Unknown Contact"

	return doc

def modify_doc_purchase_order(doc, data):
	# if closed, keep it as submitted
	if data.get("status") == "Closed" or data.get("status") == "Cancelled":
		doc.status = None
		doc.docstatus = 1

	return doc

def modify_doc_purchase_invoice(doc, data):
	# If status is cancelled, skip import
	if data.get("status") == "Cancelled":
		return None
	else:
		# ----------------------------------------------------- Init Data
		# variable to hold PO & PR in target (because numbering is not the same from source) { "source_id": "target_id" }
		new_po_no_list = {}
		new_pr_no_list = {}

		# ----------------------------------------------------- Init Data
		doc.amended_from = None # Karena yg cancelled skip_import, set amended to none
		doc.set_posting_time = 1

		# ----------------------------------------------------- Update Return Against if exists
		if data.get("is_return"):
			return_against_doc = frappe.get_doc("Purchase Invoice", {"custom_previous_id": data['return_against']})
			doc.return_against = return_against_doc.name

		# ----------------------------------------------------- Modify Child Table (source id to target id)
		for item in doc.items:
			# -------------------------------------- Modify Source Item's Purchase Order to Purchase Order in target
			if hasattr(item, "purchase_order") and item.purchase_order != None:
				if item.purchase_order in new_po_no_list:
					item.purchase_order = new_po_no_list[item.purchase_order]
					item.po_detail = None
					item.purchase_order_item = None
				else:
					# Get PO Doc with custom_previous_id = item.purchase_order
					po = frappe.get_doc("Purchase Order", {"custom_previous_id": item.purchase_order})
					new_po_no_list[item.purchase_order] = po.name
					
					item.purchase_order = po.name
					item.po_detail = None
					item.purchase_order_item = None

			# -------------------------------------- Modify Source Item's Purchase Receipt to Purchase Receipt in target
			if hasattr(item, "purchase_receipt") and item.purchase_receipt != None:
				if item.purchase_receipt in new_pr_no_list:
					item.purchase_receipt = new_pr_no_list[item.purchase_receipt]
					item.pr_detail = None
				else:
					# Get Purchase Receipt with custom_previous_id = item.purchase_receipt
					pr = frappe.get_doc("Purchase Receipt", {"custom_previous_id": item.purchase_receipt})
					new_pr_no_list[item.purchase_receipt] = pr.name
					
					item.purchase_receipt = pr.name
					item.pr_detail = None
		# -------------------------------------- End Modify Child Table

		# -------------------------------------- Dont close / cancel the doc here. It will be done in separate function
		if data.get("status") == "Closed" or data.get("status") == "Cancelled":
			doc.status = None
			doc.docstatus = 1

		return doc

def modify_doc_purchase_receipt(doc, data):
	# If status is cancelled, skip import
	if data.get("status") == "Cancelled":
		return None
	else:
		# ----------------------------------------------------- Init Data
		# variable to hold PO & PR in target (because numbering is not the same from source) { "source_id": "target_id" }
		new_po_no_list = {}
		new_pr_no_list = {}

		# ----------------------------------------------------- Init Data
		doc.amended_from = None # Karena yg cancelled skip_import, set amended to none
		doc.set_posting_time = 1

		# ----------------------------------------------------- Update Return Against if exists
		if data.get("is_return"):
			return_against_doc = frappe.get_doc("Purchase Receipt", {"custom_previous_id": data['return_against']})
			doc.return_against = return_against_doc.name
			doc.posting_time = "23:59:59" # Set posting time to 23:59:59	

		# ----------------------------------------------------- Modify Child Table (source id to target id)
		items = []
		for item in doc.items:
			# -------------------------------------- Modify Source Item's Purchase Order to Purchase Order in target
			if hasattr(item, "purchase_order") and item.purchase_order != None:
				# Get New PO
				if not item.purchase_order in new_po_no_list:
					# Get PO Doc with custom_previous_id = item.purchase_order
					po = frappe.get_doc("Purchase Order", {"custom_previous_id": item.purchase_order})
					new_po_no_list[item.purchase_order] = po
				
				# Keep old PO Number
				old_po_no = item.purchase_order

				# Replace item in new doc
				item.purchase_order = new_po_no_list[item.purchase_order].name
				item.po_detail = None
				item.purchase_order_item = None

				# Remove rejected warehouse if exists
				if hasattr(item, "rejected_warehouse"):
					if item.rejected_warehouse:
						item.rejected_warehouse = None

				# Get item name from new_po_no_list[item.purchase_order] that has item_code = item.code
				for po_item in new_po_no_list[old_po_no].items:
					# If item_code matches (item_code, rate, and received_qty < qty), set purchase_order_item to po_item.name
					if po_item.item_code == item.item_code and po_item.rate == item.rate and po_item.received_qty + item.qty <= po_item.qty:
						item.purchase_order_item = po_item.name
						# Update received_qty to item.qty (in case ada item dengan > 1 line dan rate sama di source PO)
						po_item.received_qty = item.qty

			# -------------------------------------- Modify Source Item's Purchase Receipt to Purchase Receipt in target
			if hasattr(item, "purchase_receipt") and item.purchase_receipt != None:
				if item.purchase_receipt in new_pr_no_list:
					item.purchase_receipt = new_pr_no_list[item.purchase_receipt]
					item.pr_detail = None
				else:
					# Get Purchase Receipt with custom_previous_id = item.purchase_receipt
					pr = frappe.get_doc("Purchase Receipt", {"custom_previous_id": item.purchase_receipt})
					new_pr_no_list[item.purchase_receipt] = pr.name
					
					item.purchase_receipt = pr.name
					item.pr_detail = None

			# -------------------------------------- Hapus attr di item selain item_code, qty, rate, warehouse
			# Add data to items from item attr only ["item_code", "qty", "rate", "warehouse", "purchase_order", "purchase_receipt"]:
			# items.append({
			# 	"item_code": item.item_code,
			# 	"qty": item.qty,
			# 	"rate": item.rate,
			# 	"warehouse": item.warehouse,
			# 	"purchase_order": item.purchase_order
			# })
		
		# set items
		# doc.set("items", items)
		# -------------------------------------- End Modify Child Table

		# -------------------------------------- Dont close / cancel the doc here. It will be done in separate function
		if data.get("status") == "Closed" or data.get("status") == "Cancelled":
			doc.status = None
			doc.docstatus = 1

		return doc

def modify_doc_sales_invoice(doc, data):
	# If status is cancelled, skip import
	if data.get("status") == "Cancelled":
		return None
	else:
		# ----------------------------------------------------- Init Data
		# variable to hold PO & PR in target (because numbering is not the same from source) { "source_id": "target_id" }
		new_so_no_list = {}
		new_sr_no_list = {}

		# ----------------------------------------------------- Init Data
		doc.amended_from = None # Karena yg cancelled skip_import, set amended to none
		doc.set_posting_time = 1

		# ----------------------------------------------------- Update Return Against if exists
		if data.get("is_return"):
			return_against_doc = frappe.get_doc("Purchase Receipt", {"custom_previous_id": data['return_against']})
			doc.return_against = return_against_doc.name
			doc.posting_time = "23:59:59" # Set posting time to 23:59:59	

		# ----------------------------------------------------- Modify Child Table (source id to target id)
		items = []
		for item in doc.items:
			# -------------------------------------- Modify Source Item's Purchase Order to Purchase Order in target
			if hasattr(item, "sales_order") and item.sales_order != None:
				if item.sales_order in new_so_no_list:
					item.sales_order = new_so_no_list[item.sales_order]
					item.po_detail = None
					item.sales_order_item = None
				else:
					# Get PO Doc with custom_previous_id = item.purchase_order
					po = frappe.get_doc("Sales Order", {"custom_previous_id": item.sales_order})
					new_so_no_list[item.sales_order] = po.name
					
					item.sales_order = po.name
					item.so_detail = None
					item.sales_order_item = None

			# -------------------------------------- Modify Source Item's Purchase Receipt to Purchase Receipt in target
			if hasattr(item, "sales_invoice") and item.sales_invoice != None:
				if item.sales_invoice in new_sr_no_list:
					item.sales_invoice = new_sr_no_list[item.sales_invoice]
					item.pr_detail = None
				else:
					# Get Purchase Receipt with custom_previous_id = item.sales_invoice
					pr = frappe.get_doc("Purchase Receipt", {"custom_previous_id": item.sales_invoice})
					new_sr_no_list[item.sales_invoice] = pr.name
					
					item.sales_invoice = pr.name
					item.pr_detail = None

			# -------------------------------------- Hapus attr di item selain item_code, qty, rate, warehouse
			# Add data to items from item attr only ["item_code", "qty", "rate", "warehouse", "purchase_order", "purchase_receipt"]:
			# items.append({
			# 	"item_code": item.item_code,
			# 	"qty": item.qty,
			# 	"rate": item.rate,
			# 	"warehouse": item.warehouse,
			# 	"purchase_order": item.purchase_order
			# })
		
		# set items
		# doc.set("items", items)
		# -------------------------------------- End Modify Child Table

		# -------------------------------------- Dont close / cancel the doc here. It will be done in separate function
		if data.get("status") == "Closed" or data.get("status") == "Cancelled":
			doc.status = None
			doc.docstatus = 1

		return doc

# ------------------------------------------------------------
# CLOSE OR CANCEL PURCHASE DOCS
# ------------------------------------------------------------
@frappe.whitelist()
def close_or_cancel_purchase_docs():
	# Create array of Purchase Document doctypes
	purchase_docs = [
		"Purchase Receipt"
		"Purchase Invoice",
		"Purchase Order",
	]

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

	# Loop purchase_docs
	for doc in purchase_docs:
		# Loop while True
		while True:
			# Get data from erpnext_migrator_doc.source_url yang docstatus = 2
			response = requests.get(f"{erpnext_migrator_doc.source_url}/api/resource/{doc}?docstatus=2&limit_page_length=1000", headers=source_headers)
			if response.status_code == 200:
				# if data is empty, break
				data_list = response.json().get("data", [])
				if len(data_list) == 0:
					break

				# loop through data
				for data in data_list:
					# Get doc from target
					target_doc = frappe.get_doc(doc, {"custom_previous_id": data['name']})

					if target_doc:
						# Kalau status cancelled, cancel doc. Kalau status closed, close doc

						if data.get("status") == "Cancelled":
							target_doc.cancel()
						elif data.get("status") == "Closed":
							target_doc.status = "Closed"
							target_doc.docstatus = 1
							target_doc.save()

						# Save the doc
						frappe.db.commit()

						# update progress
						frappe.publish_progress(0, title=f"Closing / Cancelling {doc}", description=f"Closing / Cancelling {doc} {data['name']}")



# ------------------------------------------------------------
# RULES 
# ------------------------------------------------------------
# Function to check if account can be deleted
def can_delete_data(doctype, docname):
	# Check if doctype is Account
	if doctype == "Account":
			# Check if account has no parent
			parent_account = frappe.get_value(doctype, docname, "parent_account")
			if not parent_account:
				return False, "Account has no parent account"

	return True, ""