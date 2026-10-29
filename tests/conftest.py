import pytest


def pytest_configure(config):
    config.addinivalue_line("markers", "gemini: chama o Gemini de verdade e gasta cota (rode com: pytest -m gemini)")


def pytest_collection_modifyitems(config, items):
    """Pula os testes marcados com 'gemini', a menos que sejam pedidos com -m gemini."""
    if "gemini" in (config.option.markexpr or ""):
        return
    pular = pytest.mark.skip(reason="gasta cota do Gemini; rode com: pytest -m gemini")
    for item in items:
        if "gemini" in item.keywords:
            item.add_marker(pular)
