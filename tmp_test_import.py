import sys
import os
sys.path.append(os.path.abspath('backend'))
import traceback

import importlib
def test_import(module_name):
    try:
        print(f"Importing {module_name}...")
        importlib.import_module(module_name)
        print(f"Successfully imported {module_name}")
    except Exception:
        print(f"Failed to import {module_name}")
        traceback.print_exc()

test_import('app.config')
test_import('app.models.document')
test_import('app.services.s3_service')
test_import('app.services.ocr_service')
test_import('app.agents.classifier_agent')
test_import('app.agents.extraction_agent')
test_import('app.agents.voice_agent')
test_import('app.agents.nemoclaw_orchestrator')
