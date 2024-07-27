from ailurus.utils.svcmode import get_svcmode_module
from unittest.mock import Mock
import ailurus.svcmodes.sample

def test_get_svcmode_module_import_correct_module():
    mock_team = Mock()
    mock_team.id.return_value = 3
    mock_chall = Mock()
    mock_chall.id.return_value = 4
    mock_svc = Mock()
    mock_svc.detail = '{"key":"value"}'

    svcmodule = get_svcmode_module("sample")
    assert ailurus.svcmodes.sample.generator_public_services_info(mock_team, mock_chall, [mock_svc]) == svcmodule.generator_public_services_info(mock_team, mock_chall, [mock_svc])