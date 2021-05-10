frappe.ui.form.on("Help Article", {
	refresh: frm => {
		frm.trigger("add_custom_buttons");
		frm.toggle_display("route", frappe.user.has_role("System Manager"));
	},
	add_custom_buttons: frm => {
		if (!!frm.is_new())
			return
		frm.add_custom_button(__("View Tutorial"), function () {
			window.open(frm.doc.route, '_blank');
		});
	}
});