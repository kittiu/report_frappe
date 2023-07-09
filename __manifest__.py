# Copyright 2023 Ecosoft
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "Report with Frappe Server",
    "summary": "Base module to create PDF form using Frappe",
    "author": "Ecosoft, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/reporting-engine",
    "category": "Reporting",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["base", "web"],
    "data": ["views/ir_actions_report_view.xml"],
    "assets": {
        "web.assets_backend": [
            "report_frappe/static/src/js/report/qwebactionmanager.esm.js"
        ]
    },
    "installable": True,
}
