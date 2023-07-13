# Copyright 2023 Kitti U.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
import requests
import json
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval


class ReportAction(models.Model):
    _inherit = "ir.actions.report"

    report_type = fields.Selection(
        selection_add=[("frappe", "PDF (Frappe Server)")], ondelete={"frappe": "set default"}
    )
    frappe_doctype = fields.Char(string="Doctype")
    frappe_printformat = fields.Char(string="Print Format")
    frappe_letterhead = fields.Char(string="Letter Head")
    frappe_doctype_mapper = fields.Text(string="Doctype Data Mapper")
    frappe_delete = fields.Boolean(
        string="Delete printed data",
        help="Delete data from frappe server after print"
    )

    @api.model
    def _render_frappe(self, docids, data):
        # Get authorization token
        auth_token = self.env["ir.config_parameter"].sudo().get_param("frappe.auth.token")
        server_url = self.env["ir.config_parameter"].sudo().get_param("frappe.server.url")
        if not auth_token or not server_url:
            raise ValidationError(
                _("Cannot connect to Frappe Server.\n"
                  "System parameters frappe.server.url, frappe.auth.token not found")
            )
        headers = {"Authorization": "token %s" % auth_token}
        # Get report action
        report_sudo = self
        # Prepare print URL, based on print format type
        designer, method, printformat, letterhead = self._prepare_print_params(docids, report_sudo, server_url, headers)
        frappe_docs = self._create_frappe_docs(docids, report_sudo, server_url, headers)
        print_url = self._prepare_print_url(frappe_docs, report_sudo.frappe_doctype, server_url, designer, method, printformat, letterhead)
        # Render PDF
        response = requests.request("GET", print_url, headers=headers)
        self._delete_frappe_data(frappe_docs, report_sudo, server_url, headers)
        return response.content, "pdf"

    @api.model
    def _get_report_from_name(self, report_name):
        res = super(ReportAction, self)._get_report_from_name(report_name)
        if res:
            return res
        report_obj = self.env["ir.actions.report"]
        qwebtypes = ["frappe"]
        conditions = [
            ("report_type", "in", qwebtypes),
            ("report_name", "=", report_name),
        ]
        context = self.env["res.users"].context_get()
        return report_obj.with_context(**context).search(conditions, limit=1)

    @api.model
    def _create_frappe_docs(self, docids, report_sudo, server_url, headers):
        json_data = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        frappe_docs = []
        objects = self.env[report_sudo.model].browse(docids)
        for object in objects:
            doc = safe_eval(report_sudo.frappe_doctype_mapper, {'object': object})
            url = "%s/api/resource/%s" % (server_url, report_sudo.frappe_doctype)
            response = requests.post(url=url, json=json_data, data=json.dumps(doc), headers=headers)
            if response.json().get("exception"):
                raise ValidationError(response.json()["exception"])
            frappe_docs.append(response.json()['data']['name'])
        return frappe_docs

    @api.model
    def _prepare_print_params(self, docids, report_sudo, server_url, headers):
        designer = "print_format"
        if report_sudo.frappe_printformat:
            url = (
                '%s/api/resource/Print Format?'
                'fields=["print_format_builder_beta"]'
                '&filters=[["Print Format","name","=","%s"],["Print Format","doc_type","=","%s"]]'
                % (server_url, report_sudo.frappe_printformat, report_sudo.frappe_doctype)
            )
            response = requests.request("GET", url, headers=headers)
            if response.json().get("exception"):
                raise ValidationError(response.json()["exception"])
            result = response.json()["data"]
            if result and result[0]["print_format_builder_beta"]:
                designer = "weasyprint"
        if designer == "weasyprint" and len(docids) > 1:
            raise ValidationError(
                _("Selected form use frappe's print format builder (beta) which does not support multi forms")
            )
        printformat = "format=%s" % (report_sudo.frappe_printformat or "Standard")
        if designer == "weasyprint":
            printformat = "print_format=%s" % report_sudo.frappe_printformat
        letterhead = report_sudo.frappe_letterhead or ""
        method = "download_multi_pdf"
        return (designer, method, printformat, letterhead)

    @api.model
    def _prepare_print_url(self, frappe_docs, frappe_doctype, server_url, designer, method, printformat, letterhead):
        if len(frappe_docs) == 1:
            method = "download_pdf"
            frappe_docs = frappe_docs[0]
        url = (
            "%s/api/method/frappe.utils.%s.%s?"
            "doctype=%s&name=%s&%s&letterhead=%s" % (
                server_url, designer, method, frappe_doctype, frappe_docs, printformat, letterhead
            )
        )
        return url.replace("'", '"')

    @api.model
    def _delete_frappe_data(self, frappe_docs, report_sudo, server_url, headers):
        if report_sudo.frappe_delete:
            for doc in frappe_docs:
                url = "%s/api/resource/%s/%s" % (server_url, report_sudo.frappe_doctype, doc)
                response = requests.delete(url=url, headers=headers)
                if response.json().get("exception"):
                    raise ValidationError(response.json()["exception"])
