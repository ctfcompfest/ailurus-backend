from ailurus.utils.svcmode import get_svcmode_module
import ailurus.svcmodes.sample

def test_get_svcmode_module_import_correct_module():
    assert get_svcmode_module("sample") == ailurus.svcmodes.sample