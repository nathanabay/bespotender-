import frappe

def run():
    doc = frappe.get_doc("Document Template", "Technical Proposal Cover Letter")
    # Using border-left instead of position:absolute for the red stripe.
    # wkhtmltopdf (the PDF engine) often struggles with absolute positioning,
    # which can cause layout breaks or blank pages.
    doc.content = """
<div style='font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; padding: 20px; background-color: #ffffff; color: #000000;'>
    
    <div style="border-left: 20px solid #C62828; padding-left: 40px; margin-top: 40px; min-height: 450px;">
        <!-- Company Name Header -->
        <div style="font-size: 16px; font-weight: bold; margin-bottom: 40px; text-transform: uppercase; letter-spacing: 2px; color: #333333;">
            {{company_name}}
        </div>
        
        <!-- Main Title -->
        <div style="font-size: 48px; font-weight: 900; color: #C62828; margin-bottom: 50px; line-height: 1.1; text-transform: uppercase; letter-spacing: -1px;">
            TECHNICAL<br>PROPOSAL
        </div>
        
        <!-- Project &amp; Contact Details -->
        <div style="font-size: 14px; text-transform: uppercase; letter-spacing: 1px;">
            <div style="margin-bottom: 10px; font-weight: bold; color: #000000;">
                PROJECT: {{tender_title}}
            </div>
            <div style="margin-bottom: 40px; color: #555555;">
                PREPARED FOR: {{organization}}
            </div>
            
            <div style="margin-top: 100px; font-size: 12px; line-height: 1.6; color: #444444;">
                <strong>{{company_name}}</strong><br>
                ADDIS ABABA, ETHIOPIA<br>
                DATE: {{submission_deadline}}
            </div>
        </div>
    </div>
</div>
"""
    doc.save()
    frappe.db.commit()

if __name__ == "__main__":
    run()
