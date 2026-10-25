from utils.job_translation import merge_translation, page_payload, payload_has_text


def test_page_payload_uses_analysis_text_and_skill_lists():
    payload = page_payload(
        {"job_title": "営業", "company": "株式会社", "description": "仕事内容", "requirements": ["必須"]},
        {
            "ai_reasoning": "Strong match",
            "improvement_suggestions": "Learn SQL",
            "matching_skills": ["Excel"],
            "missing_skills": "SQL",
        },
    )
    assert payload["job_title"] == "営業"
    assert payload["requirements"] == "必須"
    assert payload["ai_reasoning"] == "Strong match"
    assert payload["missing_skills"] == ["SQL"]
    assert payload_has_text(payload)


def test_merge_keeps_original_when_translation_drops_a_field():
    source = {
        "job_title": "営業",
        "company": "Acme",
        "location": "東京",
        "salary": "",
        "description": "本文",
        "requirements": "",
        "ai_reasoning": "理由",
        "improvement_suggestions": "",
        "matching_skills": ["Excel"],
        "missing_skills": [],
    }
    merged = merge_translation(source, {"job_title": "Sales", "matching_skills": []})
    assert merged["job_title"] == "Sales"
    assert merged["description"] == "本文"
    assert merged["matching_skills"] == ["Excel"]
