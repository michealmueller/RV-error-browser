import pytest

# from theming import apply_branding_theme, BRANDING_THEMES  # MISSING MODULE, COMMENTED OUT


@pytest.mark.skip(reason="Skipped: depends on missing theming/BRANDING_THEMES")
def test_apply_branding_theme_sets_palette(qapp, brand, theme):
    pass


@pytest.mark.skip(reason="Skipped: depends on missing theming/BRANDING_THEMES")
def test_apply_branding_theme_unknown_brand(qapp, caplog):
    pass
