"""Tableau Desktop load verification.

Tableau Desktop's own log is the only reliable oracle for "does this workbook
open". The XSD gate in ``scripts/validate_iteration.py`` catches schema-order
defects but cannot see manifest-flag and element-placement defects, so a
workbook can pass validation and still be rejected by Desktop (error code
``d2e8da72``).

These tools classify a packaged workbook by reading Tableau's log:

* ``verdict``       - the classifier and process control
* ``check``         - one workbook, with retries
* ``check_batch``   - several workbooks
* ``verify_corpus`` - the 50-case regression baseline
* ``build_and_check`` - rebuild a case with a chosen SDK, then check it
* ``sdk_source``    - resolve which ``cwtwb`` checkout a build imports

See ``docs/cross-repo-desktop-workflow.md`` for the workflow these support.
"""
