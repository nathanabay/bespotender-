from frappe import _

def get_data(data=None):
    return {
        "fieldname": "tender",
        "transactions": [
            {
                "label": _("Activities"),
                "items": ["Tender Task"]
            },
            {
                "label": _("Bid Security"),
                "items": ["Bid Security", "Bid Security Request"]
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
