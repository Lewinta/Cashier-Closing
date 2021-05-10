// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.ui.form.on('Cashier Closing', {

	setup(frm){
		if (frm.doc.user == "" || frm.doc.user == null) {
			frm.doc.user = frappe.session.user;
		}
		if (frm.is_new())
			frm.call("load_mode_of_payments");
	},
	refresh(frm){
		if (!frappe.user.has_role("Auditor"))
			frm.set_df_property("date", "read_only", 1);
		
		if (frm.doc.user == "" || frm.doc.user == null) {
			if (!frm.doc.user)
				frm.doc.user = frappe.session.user;
		}
	},
	validate(frm){
		if (frm.doc.user == "" || frm.doc.user == null)
			frm.doc.user = frappe.session.user;
	},
	date(frm){
		frm.trigger("reset_payments_table");
	},
	pos_profile(frm){
		frm.trigger("reset_payments_table");
	},
	reset_payments_table(frm){
		frm.clear_table("payments");
		frm.add_child("payments", {"mode_of_payment": "EFECTIVO", "sys_amount": 0, "difference": 0});
		frm.refresh_field("payments");
	}


});
