// Copyright (c) 2025, Neha Fathima and contributors
// For license information, please see license.txt

frappe.ui.form.on('Machine Maintenance', {
	refresh(frm) {
		const crm_notes = new erpnext.utils.CRMNotes({
			frm: frm,
			notes_wrapper: $(frm.fields_dict.notes_html.wrapper),
		});
		crm_notes.refresh();
    toggle_notes_field(frm);
	update_overdue_status(frm);
	if(frm.doc.status !== "Completed") {
			frm.add_custom_button(__('Mark Completed'), function() {
				frm.set_value('status', 'Completed');
				frm.set_value('completion_date', frappe.datetime.get_today());
				frm.save();
				frappe.show_alert({
					message: __('Maintenance marked as Completed'),
					indicator: 'green'
				});
			});
		}
	},
	onload(frm) {
		if(frm.is_new() && !frm.doc.maintenance_date) {
            frm.set_value("maintenance_date", frappe.datetime.get_today());
        }
	},
    status(frm) {
        toggle_notes_field(frm);
    }       


});



frappe.ui.form.on('Parts Used', {
	quandity(frm, cdt, cdn) {
        calculate_amount(cdt, cdn, frm);
    },
    rate(frm, cdt, cdn) {
        calculate_amount(cdt, cdn, frm);
    },
	parts_used_add(frm) {
        compute_total_cost(frm);
    },
    parts_used_remove(frm) {
        compute_total_cost(frm);
    }

});


function calculate_amount(cdt, cdn, frm) {
    let row = locals[cdt][cdn];
    row.amount = (row.quandity || 0) * (row.rate || 0);
    frappe.model.set_value(cdt, cdn, "amount", row.amount);
    compute_total_cost(frm);
}

function compute_total_cost(frm) {
    let total = 0;
    (frm.doc.parts_used || []).forEach(d => {
        total += d.amount || 0;
    });
    frm.set_value("cost", total);
    frm.refresh_field("cost");
}


function update_overdue_status(frm) {
    if(frm.doc.status !== "Completed") {
        let today = frappe.datetime.get_today();
        if(frm.doc.maintenance_date && frm.doc.maintenance_date < today) {
            frm.set_value('status', 'Overdue');
        }
    }
}

function toggle_notes_field(frm) {
    if (frm.doc.status === "Scheduled") {
        frm.toggle_display('notes_tab', false);
    } else {
        frm.toggle_display('notes_tab', true);
    }
}



