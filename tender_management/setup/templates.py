"""
tender_management/tender_management/setup/templates.py

Seed professional default templates for document generation.
"""
import frappe


def create_default_document_templates():
	print("📄 Seeding default Document Templates...")
	
	templates = [
		{
			"template_name": "Technical Proposal Cover Letter", "doc_type": "Letter",
			"category": "Cover Letter",
			"content": """
<div style="font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; height: 900px; position: relative; padding: 120px 80px; background-color: #ffffff; color: #000000;">
    <!-- Red Vertical Accent Stripe -->
    <div style="position: absolute; left: 0; top: 400px; bottom: 80px; width: 35px; background-color: #C62828;"></div>
    
    <div style="margin-left: 60px;">
        <!-- Company Name Header -->
        <div style="font-size: 22px; font-weight: 500; margin-bottom: 60px; text-transform: uppercase; letter-spacing: 3px; color: #333333;">
            {{company_name}}
        </div>
        
        <!-- Main Title -->
        <div style="font-size: 84px; font-weight: 900; color: #C62828; margin-bottom: 80px; line-height: 0.95; text-transform: uppercase; letter-spacing: -2px;">
            TECHNICAL<br>PROPOSAL
        </div>
        
        <!-- Project & Contact Details -->
        <div style="font-size: 16px; text-transform: uppercase; letter-spacing: 2px;">
            <div style="margin-bottom: 15px; font-weight: bold; color: #000000;">
                PROJECT: {{tender_title}}
            </div>
            <div style="margin-bottom: 60px; color: #555555;">
                PREPARED FOR: {{organization}}
            </div>
            
            <div style="margin-top: 200px; font-size: 14px; line-height: 1.8; color: #444444;">
                <strong>{{company_name}}</strong><br>
                ADDIS ABABA, ETHIOPIA<br>
                DATE: {{submission_deadline}}
            </div>
        </div>
    </div>
</div>
            """
		},
		{
			"template_name": "Financial Proposal Cover Letter", "doc_type": "Letter",
			"category": "Cover Letter",
			"content": """
<div style="font-family: Arial, sans-serif; line-height: 1.6;">
    <p>To: <strong>{{organization}}</strong></p>
    <p>Subject: <strong>Financial Proposal for {{tender_title}} (Ref: {{tender_number}})</strong></p>
    <br>
    <p>Dear Sir/Madam,</p>
    <p>We are pleased to submit our Financial Proposal for <strong>{{tender_title}}</strong>. Having analyzed the technical requirements, we have prepared a competitive pricing structure that ensures maximum value for investment.</p>
    <p>Our total bid price is <strong>{{final_bid_price}}</strong>, which includes all applicable taxes and costs as detailed in the BOQ.</p>
    <p>This financial proposal remains valid until <strong>{{submission_deadline}}</strong>.</p>
    <br>
    <p>Sincerely,</p>
    <p>Finance Department<br><strong>{{company_name}}</strong></p>
</div>
            """
		},
		{
			"template_name": "Standard Executive Summary", "doc_type": "Letter",
			"category": "Executive Summary",
			"content": """
<div style="font-family: Arial, sans-serif; line-height: 1.6;">
    <h2>Executive Summary: {{tender_title}}</h2>
    <hr>
    <p><strong>{{company_name}}</strong> is proud to submit this bid for the <strong>{{tender_title}}</strong>. With extensive experience in the <strong>{{sector}}</strong> sector, we bring a unique combination of innovation, efficiency, and proven performance.</p>
    <h3>Key Value Propositions:</h3>
    <ul>
        <li><strong>Proven Track Record:</strong> Successfully delivered similar projects in {{sector}}.</li>
        <li><strong>Technical Excellence:</strong> Utilization of state-of-the-art methodologies and expert personnel.</li>
        <li><strong>Cost Efficiency:</strong> Strategic resource allocation to ensure competitive pricing.</li>
    </ul>
    <p>Our goal is to assist <strong>{{organization}}</strong> in achieving its project milestones with zero compromise on quality.</p>
</div>
            """
		},
		{
			"template_name": "Technical Methodology Template", "doc_type": "Letter",
			"category": "Methodology",
			"content": """
<div style="font-family: Arial, sans-serif; line-height: 1.6;">
    <h2>Proposed Methodology for {{tender_title}}</h2>
    <p>Our execution plan for <strong>{{tender_title}}</strong> is divided into four critical phases:</p>
    <ol>
        <li><strong>Initiation & Planning:</strong> Risk assessment, resource mobilization, and detailed scheduling.</li>
        <li><strong>Execution Phase:</strong> Deployment of technical teams and implementation of core modules.</li>
        <li><strong>Quality Assurance:</strong> Rigorous testing and compliance verification against {{organization}} standards.</li>
        <li><strong>Closure & Handover:</strong> Final reporting, documentation, and knowledge transfer.</li>
    </ol>
    <p>Our methodology ensures that every deliverable meets the highest professional standards.</p>
</div>
            """
		}
	]

	for template_data in templates:
		if not frappe.db.exists("Document Template", template_data["template_name"]):
			try:
				template_data["doctype"] = "Document Template"
				template_data["is_active"] = 1
				frappe.get_doc(template_data).insert(ignore_permissions=True)
				print(f"  ✔ Created Template: {template_data['template_name']}")
			except Exception as e:
				print(f"  ⚠ Error seeding template {template_data['template_name']}: {str(e)}")
		else:
			# Update content for default templates to ensure the latest design is applied
			doc = frappe.get_doc("Document Template", template_data["template_name"])
			updated = False
			if not doc.doc_type:
				doc.doc_type = template_data.get("doc_type", "Letter")
				updated = True
			if doc.content != template_data["content"]:
				doc.content = template_data["content"]
				updated = True
			if updated:
				doc.save(ignore_permissions=True)
				print(f"  ✔ Updated Template content: {template_data['template_name']}")
			else:
				print(f"  ✔ Template already exists: {template_data['template_name']}")
