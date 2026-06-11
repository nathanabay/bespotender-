"""
tender_management/utils/file_utils.py

File utility hooks called by the Frappe doc-event system.
These are referenced in hooks.py under doc_events["File"].
"""
import frappe

# Frappe's database column for file_name is VARCHAR(255).
# Truncate proactively to avoid a Data Too Long error on save.
_MAX_FILE_NAME_LEN = 200


def truncate_file_name(doc, method=None):
	"""
	Ensure the file_name field does not exceed the database column limit.
	Preserves the file extension so the file remains openable.

	Called on: File.validate
	"""
	if not doc.file_name:
		return

	name = doc.file_name.strip()
	if len(name) <= _MAX_FILE_NAME_LEN:
		return

	# Split off the extension so it is always preserved.
	dot_idx = name.rfind(".")
	if dot_idx > 0:
		stem = name[:dot_idx]
		ext = name[dot_idx:]  # includes the leading dot
	else:
		stem = name
		ext = ""

	max_stem = _MAX_FILE_NAME_LEN - len(ext)
	truncated = stem[:max_stem] + ext
	frappe.logger().warning(
		f"File name truncated from {len(name)} to {len(truncated)} chars: {name!r}"
	)
	doc.file_name = truncated
