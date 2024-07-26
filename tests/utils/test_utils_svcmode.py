from ailurus.utils.svcmode import get_svcmode_module
import ailurus.svcmodes.sample

def test_get_svcmode_module_import_correct_module():
    svcmodule = get_svcmode_module("sample")
    assert ailurus.svcmodes.sample.generator_public_services_info(None, None, None) == svcmodule.generator_public_services_info(None, None, None)