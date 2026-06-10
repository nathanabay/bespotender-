import json

with open("tender_management/tender_management/doctype/scraped_tender/scraped_tender.json", "r") as f:
    data = json.load(f)

has_days = any(f["fieldname"] == "days_remaining" for f in data["fields"])
if not has_days:
    # insert after closing_date
    idx = next((i for i, f in enumerate(data["fields"]) if f["fieldname"] == "closing_date"), -1)
    if idx != -1:
        data["fields"].insert(idx + 1, {
            "fieldname": "days_remaining",
            "fieldtype": "Int",
            "label": "Days Remaining",
            "in_list_view": 1,
            "read_only": 1
        })
        
        # update field_order
        fo_idx = data["field_order"].index("closing_date")
        data["field_order"].insert(fo_idx + 1, "days_remaining")

with open("tender_management/tender_management/doctype/scraped_tender/scraped_tender.json", "w") as f:
    json.dump(data, f, indent=1)

print("Days remaining added to schema.")
