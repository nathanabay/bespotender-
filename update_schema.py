import json

with open("tender_management/tender_management/doctype/scraped_tender/scraped_tender.json", "r") as f:
    data = json.load(f)

# Add company to field_order
if "company" not in data["field_order"]:
    data["field_order"].insert(2, "company")

# Add company to fields
has_company = any(f["fieldname"] == "company" for f in data["fields"])
if not has_company:
    data["fields"].insert(2, {
        "fieldname": "company",
        "fieldtype": "Data",
        "label": "Company / Organization"
    })

with open("tender_management/tender_management/doctype/scraped_tender/scraped_tender.json", "w") as f:
    json.dump(data, f, indent=1)

print("Schema updated.")
