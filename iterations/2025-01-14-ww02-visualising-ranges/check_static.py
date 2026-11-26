"""Run case-local mandatory static gates without changing shared indexes."""
import json,hashlib,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]))
from scripts.validate_iteration import validate_metadata, validate_source_lock, validate_builder_boundary, validate_workbook_schema
case=validate_metadata(HERE)
validate_source_lock(HERE,case)
validate_builder_boundary(HERE)
validate_workbook_schema(HERE,case)
print(json.dumps({'case_local_static':'pass','artifact_sha256':hashlib.sha256((HERE/'outputs/replicated-workbook.twbx').read_bytes()).hexdigest(),'catalogue':'parent-owned; run full validator after regenerating shared indexes'},indent=2))
