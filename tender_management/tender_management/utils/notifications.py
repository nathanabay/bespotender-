
import frappe

@frappe.whitelist()
def notify_email(subject, message, recipients=None):
    """
    Standardize email sending with consistent branding/footer.
    """
    if not recipients:
        # Optimized query to find users with "Tender Manager" role
        role_recipients = frappe.get_all(
            "Has Role", 
            filters={"role": "Tender Manager", "parenttype": "User"}, 
            fields=["parent"]
        )
        # Fetch emails for these users
        if role_recipients:
            user_names = [r.parent for r in role_recipients]
            recipients = [u.email for u in frappe.get_all("User", filters={"name": ["in", user_names], "enabled": 1}, fields=["email"])]

    if not recipients:
        return

    frappe.sendmail(
        recipients=recipients,
        subject=subject,
        message=message,
        delayed=False
    )
