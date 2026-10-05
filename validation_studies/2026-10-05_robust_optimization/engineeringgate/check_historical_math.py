"""Run the seven historical math tests with an isolated, unambiguous module name.

The archived test log's import collision is preserved. This loader resolves the
two same-named report modules without editing either historical directory.
"""
from pathlib import Path
import importlib.util
import sys
import unittest

follow=Path(__file__).resolve().parent.parent/'convergence_followup'
sys.path.insert(0,str(follow))
spec=importlib.util.spec_from_file_location('build_report',follow/'build_report.py')
module=importlib.util.module_from_spec(spec);sys.modules['build_report']=module;spec.loader.exec_module(module)
spec=importlib.util.spec_from_file_location('historical_followup_tests',follow/'test_followup.py')
tests=importlib.util.module_from_spec(spec);spec.loader.exec_module(tests)
suite=unittest.defaultTestLoader.loadTestsFromModule(tests)
out=unittest.TextTestRunner(verbosity=2).run(suite)
if not out.wasSuccessful():raise SystemExit(1)
