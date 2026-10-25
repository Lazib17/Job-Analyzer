"""Tests for deterministic skill ranking."""

from utils.learning_rank import RankedJobInput, canonical_skill, rank_learning_skills


def _job(job_id, skills, score, japanese=""):
    return RankedJobInput(
        job_id=job_id,
        missing_skills=skills,
        compatibility_score=score,
        japanese_level=japanese,
    )


def test_aliases_count_as_one_skill():
    jobs = [
        _job("1", ["JS", "Postgres"], 80),
        _job("2", ["JavaScript", "PostgreSQL"], 70),
    ]
    ranked = rank_learning_skills(jobs)
    names = [item.skill for item in ranked]
    assert names == ["JavaScript", "PostgreSQL"]
    assert ranked[0].jobs_missing_count == 2
    assert ranked[0].total_jobs == 2
    assert ranked[0].demand_percent == 100
    assert ranked[0].tier == "High"


def test_higher_match_score_outranks_more_frequent_low_scores():
    jobs = [
        _job("high", ["Kubernetes"], 100),
        _job("low-1", ["Excel"], 10),
        _job("low-2", ["Excel"], 10),
        _job("low-3", ["Excel"], 10),
    ]
    ranked = rank_learning_skills(jobs)
    assert ranked[0].skill == "Kubernetes"
    assert ranked[0].jobs_missing_count == 1
    assert ranked[1].skill == "Excel"
    assert ranked[1].jobs_missing_count == 3
    assert ranked[1].total_jobs == 4


def test_top_five_and_tiers():
    jobs = [
        _job(
            "1",
            ["Python", "SQL", "Docker", "AWS", "Git", "Figma"],
            90,
        )
    ]
    ranked = rank_learning_skills(jobs, top_n=5)
    assert len(ranked) == 5
    assert [item.rank for item in ranked] == [1, 2, 3, 4, 5]
    assert all(item.tier == "High" for item in ranked)
    assert all(item.demand_percent == 100 for item in ranked)


def test_medium_and_low_tiers():
    jobs = [_job(str(i), ["Python"] if i < 3 else ["Rust"], 50) for i in range(10)]
    ranked = {item.skill: item for item in rank_learning_skills(jobs)}
    assert ranked["Python"].jobs_missing_count == 3
    assert ranked["Python"].demand_percent == 30
    assert ranked["Python"].tier == "Medium"
    assert ranked["Rust"].jobs_missing_count == 7
    assert ranked["Rust"].tier == "High"


def test_unanalyzed_jobs_are_ignored():
    jobs = [
        _job("1", ["Python"], None),
        _job("2", ["Python"], 40),
    ]
    ranked = rank_learning_skills(jobs)
    assert len(ranked) == 1
    assert ranked[0].total_jobs == 1
    assert ranked[0].jobs_missing_count == 1


def test_duplicate_skill_on_one_job_counts_once():
    jobs = [_job("1", ["JS", "JavaScript", "js"], 80)]
    ranked = rank_learning_skills(jobs)
    assert len(ranked) == 1
    assert ranked[0].jobs_missing_count == 1


def test_japanese_added_when_jobs_require_more_than_the_user():
    jobs = [
        _job("1", ["Python"], 80, "N3"),
        _job("2", ["Python"], 70, "Conversational Japanese"),
        _job("3", ["Python"], 60, "Japanese not required"),
    ]
    ranked = rank_learning_skills(jobs, user_japanese_level="N5")
    japanese = next(item for item in ranked if item.skill.startswith("Japanese"))
    assert japanese.skill == "Japanese (target N3)"
    assert japanese.jobs_missing_count == 2
    assert japanese.total_jobs == 3


def test_japanese_hidden_when_user_already_meets_the_jobs():
    jobs = [
        _job("1", ["Python"], 80, "N3"),
        _job("2", ["SQL"], 70, "Business Japanese"),
    ]
    ranked = rank_learning_skills(jobs, user_japanese_level="N1")
    assert all(not item.skill.startswith("Japanese") for item in ranked)


def test_japanese_hidden_when_no_job_requires_it():
    jobs = [_job("1", ["Python"], 80, "Japanese not required")]
    ranked = rank_learning_skills(jobs, user_japanese_level="None")
    assert all(not item.skill.startswith("Japanese") for item in ranked)


def test_japanese_tie_prefers_the_higher_level():
    jobs = [
        _job("1", [], 80, "N3"),
        _job("2", [], 80, "N2"),
        _job("3", [], 80, "Conversational Japanese"),
        _job("4", [], 80, "Business Japanese"),
    ]
    ranked = rank_learning_skills(jobs, user_japanese_level="N5")
    assert ranked[0].skill == "Japanese (target N2)"


def test_free_text_japanese_does_not_create_a_second_skill():
    jobs = [_job("1", ["Japanese", "JLPT N2"], 90, "Japanese not required")]
    ranked = rank_learning_skills(jobs, user_japanese_level="N1")
    assert ranked == []


def test_not_sure_is_treated_as_not_yet_qualified():
    jobs = [_job("1", [], 50, "N2")]
    ranked = rank_learning_skills(jobs, user_japanese_level="Not sure")
    assert ranked[0].skill == "Japanese (target N2)"


def test_canonical_skill_keeps_java_separate_from_javascript():
    assert canonical_skill("Java") == "java"
    assert canonical_skill("JavaScript") == "javascript"
    assert canonical_skill("JS") == "javascript"
