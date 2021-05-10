# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from datetime import datetime
from frappe.model.document import Document
from frappe.utils import cint, flt, cstr
from frappe import _, msgprint, throw

class CashierClosing(Document):
	def before_save(self):
		self.get_sys_payments()
		self.get_custody()
		self.make_calculations()

	def get_sys_payments(self):
		filters = {
			"posting_date": self.date,
			"pos_profile": self.pos_profile
		}
		values = frappe.db.sql("""
			SELECT
				tmp.pos_profile,
				tmp.mode_of_payment,
				tmp.paid_amount
			FROM
				(
					select 
						`tabSales Invoice`.pos_profile,
						`tabSales Invoice Payment`.mode_of_payment,
						sum(`tabSales Invoice Payment`.amount) as paid_amount
					from 
						`tabSales Invoice`
					join
						`tabSales Invoice Payment`
					on
						`tabSales Invoice`.name = `tabSales Invoice Payment`.parent
					where 
						`tabSales Invoice`.posting_date = %(posting_date)s
					and 
						`tabSales Invoice`.pos_profile = %(pos_profile)s
					and 
						`tabSales Invoice`.docstatus = 1
					group by 
						`tabSales Invoice`.pos_profile, `tabSales Invoice Payment`.mode_of_payment

					UNION

					select 
						`tabPayment Entry`.pos_profile,
						`tabPayment Entry`.mode_of_payment,
						SUM(`tabPayment Entry Reference`.allocated_amount) paid_amount																
					from 
						`tabPayment Entry`
					join
						`tabPayment Entry Reference`
					on
						`tabPayment Entry`.name = `tabPayment Entry Reference`.parent
					where
						`tabPayment Entry`.docstatus = 1
					and 
						`tabPayment Entry`.payment_type = 'Receive'
					and
						`tabPayment Entry`.posting_date = %(posting_date)s 
					and
						`tabPayment Entry`.pos_profile = %(pos_profile)s 
					group by 
						`tabPayment Entry`.pos_profile, `tabPayment Entry`.mode_of_payment
				) as tmp
			GROUP BY tmp.pos_profile, tmp.mode_of_payment
		""", filters, debug=False, as_dict=True)
		
		for row in values:
			pymt = list(filter(lambda x, mop=row.mode_of_payment: x.mode_of_payment == mop, self.payments))
			if not pymt:
				continue
			pymt = pymt[0]
			pymt.sys_amount = flt(row.paid_amount)
			pymt.difference = flt(pymt.sys_amount) - flt(pymt.amount)

	def make_calculations(self):
		total = 0.00
		sys_total = 0.00
		for i in self.payments:
			total += flt(i.amount)

		self.net_amount = flt(total) - flt(self.expense) - flt(self.custody ) + flt(self.returns)
		self.registered_amount = flt(total) + flt(self.expense) - flt(self.sys_custody) + flt(self.returns)

	# def validate_time(self):

	# 	if self.from_time >= self.time:
	# 		frappe.throw(_("From Time {from_time} Should Be  Less Than To Time <b>{time}</b>".format(**self.as_dict())))

	@frappe.whitelist()
	def get_custody(self):
		values = frappe.db.sql("""
			select sum(net_total)
			from `tabSales Invoice`
			where posting_date=%s and posting_time>=%s and posting_time<=%s and pos_profile=%s
		""", (self.date, self.from_time, self.time, self.pos_profile))
		self.sys_custody = flt(values[0][0] if values else 0)

	def load_mode_of_payments(self):
		self.payments = []
		self.append("payments", {"mode_of_payment":"EFECTIVO"})