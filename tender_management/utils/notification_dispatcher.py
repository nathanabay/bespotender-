
import frappe
import uuid
from frappe import _

def dispatch(doc, category, subject=None, message=None):
    """
    Dispatches notifications based on hierarchical routing and user preferences.
    """
    recipients = set()
    
    # 1. Fetch recipients
    # Bid Manager
    bid_manager = doc.get("bid_manager") or doc.owner
    if bid_manager:
        recipients.add(bid_manager)
        
    # Team Members
    if hasattr(doc, "team_members"):
        for member in doc.team_members:
            if member.user:
                recipients.add(member.user)
                
    # Followers
    if hasattr(doc, "followers"):
        for follower in doc.followers:
            if follower.user:
                recipients.add(follower.user)
                
    # Global Recipients from Tender Settings
    settings = frappe.get_single("Tender Settings")
    if doc.workflow_state == "Lost" and settings.lost_tender_recipient:
        recipients.add(settings.lost_tender_recipient)
    elif category == "cpo_expiry" and settings.cpo_expiry_recipient:
        recipients.add(settings.cpo_expiry_recipient)
        
    # 2. Filter by preferences
    pref_field = f"receive_{category}_alerts"
    trace_id = str(uuid.uuid4())
    bespo_installed = "bespo_notifications" in frappe.get_installed_apps()
    
    for user_id in recipients:
        # Check User preferences and basic status
        user_info = frappe.db.get_value("User", user_id, ["enabled", "email", pref_field], as_dict=True)
        if not user_info or not user_info.enabled or not user_info.email:
            continue
            
        # Preference check (e.g., receive_workflow_state_alerts)
        if not user_info.get(pref_field):
            continue
            
        # 3. Create 'Notification Log' if Bespo is installed
        if bespo_installed:
            try:
                frappe.get_doc({
                    "doctype": "Notification Log",
                    "status": "Debounced",
                    "trace_id": trace_id,
                    "category": category,
                    "for_user": user_id,
                    "document_type": doc.doctype,
                    "document_name": doc.name,
                    "subject": subject or _("Tender Notification: {0}").format(doc.name),
                    "email_content": message or _("Notification triggered for {0}").format(doc.name)
                }).insert(ignore_permissions=True)
            except Exception as e:
                frappe.log_error(f"Bespo Notification Log creation failed: {str(e)}", "Notification Dispatcher")

        # 4. Fallback/Standard Email dispatch via frappe.sendmail
        try:
            frappe.sendmail(
                recipients=[user_info.email],
                subject=subject or _("Tender Notification: {0}").format(doc.name),
                message=message or _("Notification for {0} {1}").format(doc.doctype, doc.name)
            )
        except Exception as e:
            frappe.log_error(f"Email dispatch failed for {user_id}: {str(e)}", "Notification Dispatcher")

def handle_workflow_notification(doc, method=None):
    """
    Handle notifications triggered by workflow actions.
    """
    if doc.workflow_state in ["Plan", "Lost", "Approved", "Rejected"]:
        dispatch(
            doc=doc,
            category="workflow_state",
            subject=f"Tender Workflow Alert: {doc.workflow_state} - {doc.name}",
            message=f"The tender <b>{doc.title}</b> has moved to state: <b>{doc.workflow_state}</b> via workflow action."
        )

def handle_tender_update(doc, method=None):
    """
    Handle notifications triggered by document updates.
    """
    if doc.flags.is_new_doc:
        dispatch(
            doc=doc,
            category="workflow_state",
            subject=f"New Tender Created: {doc.name}",
            message=f"A new tender <b>{doc.title}</b> has been created by {doc.owner}."
        )
    elif doc.has_value_changed("workflow_state"):
        dispatch(
            doc=doc,
            category="workflow_state",
            subject=f"Tender Alert: {doc.workflow_state} - {doc.name}",
            message=f"The tender <b>{doc.title}</b> has been changed to state: <b>{doc.workflow_state}</b>."
        )
