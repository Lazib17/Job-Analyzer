from utils.japanese_search import job_fits_japanese_level


def test_no_japanese_keeps_unstated_and_drops_business():
    assert job_fits_japanese_level("", "No Japanese")
    assert job_fits_japanese_level("Japanese not required", "No Japanese")
    assert not job_fits_japanese_level("Business Japanese", "No Japanese")
    assert not job_fits_japanese_level("Conversational Japanese", "No Japanese")


def test_daily_conversation_stops_before_business():
    assert job_fits_japanese_level("Conversational Japanese", "Daily conversation level")
    assert job_fits_japanese_level("N3", "Daily conversation level")
    assert not job_fits_japanese_level("N2", "Daily conversation level")
    assert not job_fits_japanese_level("Business Japanese", "Daily conversation level")


def test_intermediate_includes_n2_and_excludes_business():
    assert job_fits_japanese_level("N2", "Intermediate")
    assert not job_fits_japanese_level("Business Japanese", "Intermediate")


def test_business_excludes_native_and_fluent():
    assert job_fits_japanese_level("Business Japanese", "Business level")
    assert not job_fits_japanese_level("Fluent Japanese", "Business level")
    assert not job_fits_japanese_level("N1", "Business level")


def test_native_includes_every_stated_level():
    assert job_fits_japanese_level("Native", "Native")
    assert job_fits_japanese_level("Fluent Japanese", "Native")
    assert job_fits_japanese_level("Business Japanese", "Native")
