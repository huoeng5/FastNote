from DesktopAssistant.utils.hotkey_listener import normalize_shortcut_to_pynput


def test_normalize_shortcut_to_pynput():
    assert normalize_shortcut_to_pynput('Alt+F1') == '<alt>+<f1>'
    assert normalize_shortcut_to_pynput('Ctrl+Shift+A') == '<ctrl>+<shift>+a'
    assert normalize_shortcut_to_pynput('Win+F2') == '<cmd>+<f2>'
