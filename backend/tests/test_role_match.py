from utils.role_match import arrangement_fits, experience_fits, title_matches


def test_sales_title_does_not_match_software():
    assert title_matches("戸建住宅の法人営業", ["Sales Representative"])
    assert not title_matches("戸建住宅の法人営業", ["Software Engineer"])


def test_software_title_does_not_match_sales():
    assert title_matches("Webエンジニア", ["Software Engineer"])
    assert not title_matches("Webエンジニア", ["Sales Representative"])


def test_ai_title_is_not_treated_as_generic_software():
    assert title_matches("AIエンジニア", ["AI / Machine Learning Engineer"])
    assert not title_matches("AIエンジニア", ["Software Engineer"])


def test_multiple_positions_match_either_title():
    selected = ["Sales Representative", "Teacher / English Instructor"]
    assert title_matches("法人営業", selected)
    assert title_matches("英語講師", selected)
    assert not title_matches("物流管理", selected)


def test_entry_search_drops_manager_titles():
    assert experience_fits("未経験歓迎の営業", "entry")
    assert not experience_fits("営業マネージャー", "entry")


def test_any_work_style_keeps_office_jobs():
    assert arrangement_fits("東京都", False, "Any")
    assert not arrangement_fits("東京都", False, "Remote")
    assert arrangement_fits("フルリモート", True, "Remote")


def test_city_filter_uses_city_and_prefecture_names():
    from utils.city_match import city_fits

    assert city_fits("東京都", "Tokyo")
    assert city_fits("Kanagawa", "Yokohama")
    assert city_fits("Hokkaido", "Sapporo")
    assert city_fits("京都府", "Kyoto")
    assert not city_fits("東京都", "Kyoto")
    assert city_fits("大阪", "Any")
    assert not city_fits("日本", "Osaka")
