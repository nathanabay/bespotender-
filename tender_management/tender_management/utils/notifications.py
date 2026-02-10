
import frappe
import requests
import json

# CHATWOOT CREDENTIALS (Synced from chatwoot_integration app)
CW_URL = "https://support.bespo.et"
CW_TOKEN = "VXi81L2ep9zmDCueikdro2F2"
CW_ACCOUNT_ID = "1"
CW_DEFAULT_CONV_ID = "15" # Fallback if specific conv not specified

def get_headers():
    return {"api_access_token": CW_TOKEN}

@frappe.whitelist()
def notify_chatwoot(content, conversation_id=None):
    """
    Push a system notification to Chatwoot.
    """
    if not CW_TOKEN:
        return {"status": "error", "message": "Chatwoot Token not configured"}

    cid = conversation_id or CW_DEFAULT_CONV_ID
    url = f"{CW_URL}/api/v1/accounts/{CW_ACCOUNT_ID}/conversations/{cid}/messages"
    
    data = {
        "content": content,
        "message_type": "outgoing"
    }

    try:
        # Use json=data to automatically set Content-Type and dump JSON
        response = requests.post(url, headers=get_headers(), json=data, timeout=10)
        if response.status_code == 200:
            return {"status": "success", "id": response.json().get('id')}
        else:
            frappe.log_error(title="Chatwoot Notify Error", message=f"HTTP {response.status_code}: {response.text}")
            return {"status": "error", "message": response.text}
    except Exception as e:
        frappe.log_error(title="Chatwoot Notify Exception", message=str(e))
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def notify_email(subject, message, recipients=None):
    """
    Standardize email sending with consistent branding/footer.
    """
    if not recipients:
        # Optimized query to find users with "Tender Manager" role
        recipients = frappe.get_all(
            "Has Role", 
            filters={"role": "Tender Manager", "parenttype": "User"}, 
            fields=["parent"]
        )
        # Fetch emails for these users
        if recipients:
            user_names = [r.parent for r in recipients]
            recipients = [u.email for u in frappe.get_all("User", filters={"name": ["in", user_names], "enabled": 1}, fields=["email"])]

    if not recipients:
        return

    frappe.sendmail(
        recipients=recipients,
        subject=subject,
        message=message,
        delayed=False
    )
    
def notify_tender_update(doc, method=None):
    """
    Hook function for Tender Opportunity updates.
    """
    if doc.flags.is_new_doc:
        msg = f"🆕 *New Tender*: {doc.title} ({doc.name})\n📍 Sector: {doc.sector}\n📅 Deadline: {doc.submission_deadline}\n🔗 [View Tender](/app/tender-opportunity/{doc.name})"
        notify_chatwoot(msg)
    elif doc.has_value_changed("workflow_state"):
        msg = f"🔄 *Workflow Update*: {doc.name}\nState: *{doc.workflow_state}*\n🔗 [View Tender](/app/tender-opportunity/{doc.name})"
        notify_chatwoot(msg)
        
        # Email Alert for Critical States
        if doc.workflow_state in ["Plan", "Lost"]:
            notify_email(
                subject=f"Tender Alert: {doc.workflow_state} - {doc.name}",
                message=f"The tender <b>{doc.title}</b> has been changed to state: <b>{doc.workflow_state}</b>."
            )

def send_daily_deadline_reminders():
    """
    Scheduled job: Check for tenders closing in 2 days.
    """
    upcoming = frappe.get_all("Tender Opportunity", 
                             filters={
                                 "submission_deadline": ["between", [frappe.utils.nowdate(), frappe.utils.add_days(frappe.utils.nowdate(), 2)]],
                                 "workflow_state": ["not in", ["Submitted", "Negotiation", "Won", "Lost"]]
                             },
                             fields=["name", "title", "submission_deadline"])

    for t in upcoming:
        msg = f"⏰ *REMINDER*: Tender closing soon!\n📌 {t.title} ({t.name})\n🕒 Deadline: {t.submission_deadline}\n🔗 [View Tender](/app/tender-opportunity/{t.name})"
        notify_chatwoot(msg)
