import frappe

def run():
    print("--- 🧮 FIXING BID SCORE CALCULATION BUG ---")

    script_name = "calculate_bid_score"
    
    # We replace the script with a robust version that converts strings to floats safely
    new_logic = """
total_score = 0.0
total_weight = 0.0

if doc.decision_matrix:
    for row in doc.decision_matrix:
        # SAFETY FIX: Force convert to float, default to 0 if empty
        w = flt(row.weight)
        s = flt(row.score)
        
        # Calculate score contribution: (Score / 5) * Weight
        contribution = (s / 5.0) * w
        
        total_score += contribution
        total_weight += w

    # Update the parent field
    doc.bid_probability_score = total_score
    
    # Optional: Warn if weights don't add up to 100 (for user guidance only)
    if total_weight != 100.0:
        frappe.msgprint(f"Note: Decision Matrix weights sum to {total_weight}%, ideally should be 100%.", alert=True)
"""

    if frappe.db.exists("Server Script", script_name):
        server_script = frappe.get_doc("Server Script", script_name)
        server_script.script = new_logic
        server_script.save(ignore_permissions=True)
        print(f"✔ Updated Server Script: {script_name}")
    else:
        # Create if missing (rare case)
        frappe.get_doc({
            "doctype": "Server Script",
            "name": script_name,
            "script": new_logic,
            "event": "Before Save",
            "docstatus": 0,
            "dt": "Tender Opportunity"
        }).insert(ignore_permissions=True)
        print(f"✔ Created Server Script: {script_name}")

    print("--- ✅ CALCULATION LOGIC FIXED ---")

if __name__ == "__main__":
    run()
