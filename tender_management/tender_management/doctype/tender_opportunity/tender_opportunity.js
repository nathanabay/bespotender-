frappe.ui.form.on('Tender Opportunity', {
    refresh: function (frm) {
        // Add custom buttons for new features

        // Team Management button
        if (!frm.is_new()) {
            frm.add_custom_button(__('Team & Tasks'), function () {
                show_team_dialog(frm);
            }, __('Collaborate'));

            frm.add_custom_button(__('Add Comment'), function () {
                add_comment(frm);
            }, __('Collaborate'));

            frm.add_custom_button(__('Create Default Tasks'), function () {
                frm.call('create_standard_tasks').then(() => {
                    frm.reload_doc();
                });
            }, __('Collaborate'));

            // Document Generation button
            frm.add_custom_button(__('Generate Document'), function () {
                generate_document_dialog(frm);
            }, __('Documents'));

            // Cost Estimation button
            frm.add_custom_button(__('Create Cost Estimation'), function () {
                create_cost_estimation(frm);
            }, __('Costing'));

            frm.add_custom_button(__('View All Estimations'), function () {
                frappe.set_route('List', 'Cost Estimation', { 'tender': frm.doc.name });
            }, __('Costing'));

            // Bid Decision Matrix button
            frm.add_custom_button(__('Create Decision Matrix'), function () {
                create_bid_decision(frm);
            }, __('Decision'));

            frm.add_custom_button(__('View Decision Matrix'), function () {
                frappe.set_route('List', 'Bid Decision Matrix', { 'tender': frm.doc.name });
            }, __('Decision'));

            // Performance Bond button (only for Won tenders)
            if (frm.doc.workflow_state === 'Won') {
                frm.add_custom_button(__('Create Performance Bond'), function () {
                    create_performance_bond(frm);
                }, __('Contract'));

                frm.add_custom_button(__('Manage Milestones'), function () {
                    manage_milestones(frm);
                }, __('Contract'));
            }

            // Calendar View button
            frm.add_custom_button(__('View Calendar'), function () {
                frappe.set_route('tender-calendar');
            });
        }
    }
});

function show_team_dialog(frm) {
    let d = new frappe.ui.Dialog({
        title: 'Team Management',
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'team_html'
            }
        ],
        primary_action_label: __('Close')
    });

    // Build team HTML from actual child table
    let html = `
		<div class="team-management">
			<h4>Team Members</h4>
			<table class="table table-bordered">
				<thead>
					<tr>
						<th>Member</th>
						<th>Role</th>
						<th>Assigned Date</th>
					</tr>
				</thead>
				<tbody>
	`;

    if (frm.doc.team_members && frm.doc.team_members.length > 0) {
        frm.doc.team_members.forEach(m => {
            html += `<tr>
                <td>${m.user}</td>
                <td>${m.role}</td>
                <td>${frappe.datetime.str_to_user(m.assigned_date)}</td>
            </tr>`;
        });
    } else {
        html += `<tr><td colspan="3" class="text-muted">No team members assigned yet. Add them in the 'Collaborate' tab.</td></tr>`;
    }

    html += `
				</tbody>
			</table>
			<hr>
			<h4>Tasks</h4>
			<button class="btn btn-primary btn-sm btn-create-task">Create New Task</button>
		</div>
	`;

    d.fields_dict.team_html.$wrapper.html(html);

    // Bind event for task creation using delegates to avoid scope issues
    d.fields_dict.team_html.$wrapper.on('click', '.btn-create-task', function () {
        create_tender_task(frm.doc.name);
        d.hide(); // Optional: hide dialog after opening new task form
    });

    d.show();
}

function create_tender_task(tender_name) {
    frappe.new_doc('Tender Task', {
        tender: tender_name
    });
}

function add_comment(frm) {
    let d = new frappe.ui.Dialog({
        title: 'Add Discussion Comment',
        fields: [
            {
                fieldname: 'comment_text',
                fieldtype: 'Text Editor',
                label: 'Comment',
                reqd: 1
            },
            {
                fieldname: 'is_private',
                fieldtype: 'Check',
                label: 'Private Comment'
            }
        ],
        primary_action_label: __('Post Comment'),
        primary_action: function (values) {
            let row = frm.add_child('comments');
            row.comment_text = values.comment_text;
            row.is_private = values.is_private;
            row.user = frappe.session.user;
            row.timestamp = frappe.datetime.now_datetime();

            frm.refresh_field('comments');
            frm.save().then(() => {
                frappe.show_alert({
                    message: __('Comment added and tender saved'),
                    indicator: 'green'
                });
            });
            d.hide();
        }
    });
    d.show();
}

function generate_document_dialog(frm) {
    frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: 'Document Template',
            filters: { is_active: 1 },
            fields: ['name', 'category']
        },
        callback: function (r) {
            if (r.message && r.message.length > 0) {
                let template_options = r.message.map(t => t.name).join('\\n');

                let d = new frappe.ui.Dialog({
                    title: 'Generate Document from Template',
                    fields: [
                        {
                            fieldname: 'template',
                            fieldtype: 'Link',
                            label: 'Select Template',
                            options: 'Document Template',
                            reqd: 1
                        }
                    ],
                    primary_action_label: __('Generate'),
                    primary_action: function (values) {
                        frappe.call({
                            method: 'tender_management.tender_management.doctype.document_template.document_template.generate_from_template',
                            args: {
                                template_name: values.template,
                                tender_name: frm.doc.name
                            },
                            callback: function (r) {
                                if (r.message) {
                                    // Show generated content in a dialog
                                    show_generated_document(r.message);
                                }
                            }
                        });
                        d.hide();
                    }
                });
                d.show();
            } else {
                frappe.msgprint(__('No active templates found. Please create a Document Template first.'));
            }
        }
    });
}

function show_generated_document(content) {
    let d = new frappe.ui.Dialog({
        title: 'Generated Document',
        size: 'large',
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'doc_html'
            }
        ],
        primary_action_label: __('Download PDF'),
        primary_action: function () {
            // In real implementation, this would convert to PDF
            frappe.show_alert({
                message: __('PDF generation feature coming soon'),
                indicator: 'blue'
            });
        }
    });

    d.fields_dict.doc_html.$wrapper.html(content);
    d.show();
}

function create_cost_estimation(frm) {
    frappe.new_doc('Cost Estimation', {
        tender: frm.doc.name
    });
}

function create_bid_decision(frm) {
    frappe.new_doc('Bid Decision Matrix', {
        tender: frm.doc.name
    });
}

function create_performance_bond(frm) {
    frappe.new_doc('Performance Bond', {
        tender: frm.doc.name,
        amount: frm.doc.final_contract_value * 0.10 // Default to 10% of contract value
    });
}

function manage_milestones(frm) {
    frappe.msgprint(__('Milestone management will be added as a child table in the Tender Opportunity form.'));
}
