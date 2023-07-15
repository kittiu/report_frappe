# Copyright 2023 Kitti U.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
import requests
import json
from odoo import _, api, models
from odoo.exceptions import ValidationError


class PushToFrappe(models.AbstractModel):
    _name = "push.to.frappe"

    @api.model
    def push(self, target_doctype, target_docs):
        # Connection to Frappe
        auth_token = self.env["ir.config_parameter"].sudo().get_param("frappe.auth.token")
        server_url = self.env["ir.config_parameter"].sudo().get_param("frappe.server.url")
        if not auth_token or not server_url:
            raise ValidationError(
                _("Cannot connect to Frappe Server.\n"
                  "System parameters frappe.server.url, frappe.auth.token not found")
            )
        headers = {"Authorization": "token %s" % auth_token}
        frappe_docs = self._create_frappe_docs(headers, server_url, target_doctype, target_docs)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'sticky': True,
                'title': _("Data pushed to %s") % server_url,
                'message': ", ".join(["%s => %s" % (x[0], x[1]) for x in frappe_docs]),
            }
        }

    @api.model
    def _create_frappe_docs(self, headers, server_url, target_doctype, target_docs):
        json_data = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        frappe_docs = []
        for doc in target_docs:
            url = "%s/api/resource/%s" % (server_url, target_doctype)
            res_json = requests.post(
                url=url, json=json_data, data=json.dumps(doc), headers=headers
            ).json()
            if not res_json.get("data"):
                raise ValidationError(res_json.get("_server_messages", res_json.get("exception")))
            # Success, return new doc
            frappe_docs.append((doc.get("custom_odoo_ref", "-"), res_json['data']['name']))
        return frappe_docs
