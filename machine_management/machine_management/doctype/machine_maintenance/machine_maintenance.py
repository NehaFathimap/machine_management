# Copyright (c) 2025, Neha Fathima and contributors
# For license information, please see license.txt

# import frappe
import frappe
from frappe.model.document import Document
from frappe.utils import  now
from frappe import _
from frappe.utils import flt
from frappe.utils import get_url_to_form


class MachineMaintenance(Document):
	

	def on_submit(self):
		"""
		Actions to perform when a Machine Maintenance document is submitted.
		"""
		self.validate_technician()
		self.create_journal_entry_from_machine_maintenance()
		

	def validate_technician(self):
		"""
		Ensure a technician is assigned.
		"""
		if not self.technician:
			frappe.throw("Technician must be assigned before submitting Machine Maintenance.")

	@frappe.whitelist()
	def add_note(docname, note):
		"""
		Add a note to the 'notes' child table of a Machine Maintenance document.

		Args:
			docname (str): Name of the Machine Maintenance document.
			note (str): Note content to add.
		"""
		if not note:
			return
		maintenance_doc = frappe.get_doc("Machine Maintenance", docname)
		maintenance_doc.append("notes", {
			"note": note,
			"added_by": frappe.session.user,
			"added_on": now()
		})
		maintenance_doc.save(ignore_permissions=True)
		return "Note added successfully"

	def create_journal_entry_from_machine_maintenance(self):
		'''
		Create Journal Entry on submission of Machine Maintenance
		'''
		if not self.cost or self.cost <= 0:
			return
		maintenance_expense_account = frappe.db.get_single_value(
			"Maintenance Account Settings", "maintenance_expense_account"
		)
		payment_account = frappe.db.get_single_value(
			"Maintenance Account Settings", "payment_account"
		)
		if not maintenance_expense_account:
			frappe.throw(_("Maintenance Expense Account is not configured in Maintenance Account Settings"))
		if not payment_account:
			frappe.throw(_("Payment (Cash/Bank) Account is not configured in Maintenance Account Settings"))
		company =frappe.db.get_single_value(
				"Global Defaults", "default_company"
			)
		company_currency = frappe.db.get_value(
			"Company", company, "default_currency"
		)
		amount_company_currency = flt(self.cost, 2)
		journal_entry = frappe.new_doc("Journal Entry")
		journal_entry.posting_date = self.maintenance_date
		journal_entry.company = company
		journal_entry.currency = company_currency
		journal_entry.user_remark = f"Maintenance cost for Machine {self.machine_name}"
		journal_entry.machine_maintenance_reference = self.name
		journal_entry.append("accounts", {
			"account": maintenance_expense_account,
			"debit_in_account_currency": amount_company_currency,
			"credit_in_account_currency": 0,
		})
		journal_entry.append("accounts", {
			"account": payment_account,
			"debit_in_account_currency": 0,
			"credit_in_account_currency": amount_company_currency,
		})
		journal_entry.insert(ignore_permissions=True)
		journal_entry.submit()
		frappe.msgprint(
			f" Journal Entry {journal_entry.name} created successfully.",
			alert=True,
			indicator="green"
		)
	
	def on_update(self):
		"""
		Triggered after document update.
		Sends mail ONLY when workflow_state changes to Closed.
		"""
		old_doc = self.get_doc_before_save()
		print("dilshan",old_doc)
		if (
			old_doc
			and old_doc.workflow_state != self.workflow_state
			and self.workflow_state == "Closed"
			and not self.mail_sent
		):print("neha")
		self.send_mail_on_close()

	def send_mail_on_close(self):
		subject = f"Machine Maintenance Closed - {self.name}"
		print("neha",subject)
		message = f"""
		<p>Hello,</p>
		<p>The following Machine Maintenance has been <b>Closed</b>:</p>
		<ul>
			<li><b>ID:</b> {self.name}</li>
			<li><b>Completion Date:</b> {self.completion_date}</li>
		</ul>
		<p>
			<a href="{get_url_to_form(self.doctype, self.name)}">
				View Document
			</a>
		</p>
		"""

		recipients = frappe.get_all(
			"Has Role",
			filters={"role": "Operation Manager"},
			pluck="parent"
		)
		if recipients:
			frappe.sendmail(
				recipients=recipients,
				subject=subject,
				message=message
		)
		print("diluu")
		