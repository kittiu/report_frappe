# Copyright 2023 Ecosoft
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "Push data to Frappe Server",
    "summary": "Base module to push data to frappe server",
    "author": "Ecosoft, Odoo Community Association (OCA)",
    "website": "https://github.com/kittiu/push_to_frappe",
    "license": "AGPL-3",
    "depends": ["base", "web"],
    "data": [
        "data/server_actions.xml",
    ],
    "installable": True,
}
