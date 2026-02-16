from frappe import _

def get_data(data=None):
    return {
        "fieldname": "tender",
        "transactions": [
            {
                "label": _("Activities"),
                "items": ["Tender Task", "Tender Comment"]
            },
            {
                "label": _("Decision & Planning"),
                "items": ["Bid Decision Matrix", "Cost Estimation"]
            },
            {
                "label": _("Contract Management"),
                "items": ["Performance Bond"]
            }
        ]
    }
