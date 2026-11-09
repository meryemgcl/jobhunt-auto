import json

import pytest

from services.memory import add_seen_jobs, load_seen_jobs


def test_memory_migrates_legacy_url_list_and_dedupes(tmp_path):
    memory_path = tmp_path / "seen_jobs.json"
    memory_path.write_text(
        json.dumps(
            [
                "https://example.com/job?utm_source=email)",
                "https://example.com/job",
            ]
        ),
        encoding="utf-8",
    )

    records = load_seen_jobs(memory_path)

    assert len(records) == 1
    assert records[0]["canonical_url"] == "https://example.com/job"
    assert set(records[0]) == {
        "url",
        "canonical_url",
        "title",
        "company",
        "source",
        "first_seen_at",
        "last_seen_at",
        "score",
    }


def test_add_seen_jobs_writes_structured_records_atomically(tmp_path):
    memory_path = tmp_path / "seen_jobs.json"

    added_count = add_seen_jobs(
        [
            {
                "title": "Junior Python Developer",
                "company": "Example",
                "url": "https://example.com/job?utm_campaign=test",
                "source": "Test",
                "score": 72,
            },
            "https://example.com/job",
        ],
        memory_path,
    )

    records = json.loads(memory_path.read_text(encoding="utf-8"))
    assert added_count == 1
    assert len(records) == 1
    assert records[0]["canonical_url"] == "https://example.com/job"
    assert records[0]["score"] == 72


def test_memory_uses_real_url_instead_of_legacy_hash(tmp_path):
    memory_path = tmp_path / "seen_jobs.json"
    memory_path.write_text(
        json.dumps(
            [
                {
                    "url": "https://example.com/job?utm_source=mail",
                    "canonical_url": "legacy-content-hash",
                    "title": "Junior Python Developer",
                }
            ]
        ),
        encoding="utf-8",
    )

    [record] = load_seen_jobs(memory_path)

    assert record["canonical_url"] == "https://example.com/job"


def test_memory_rejects_corrupt_json_instead_of_treating_everything_as_new(tmp_path):
    memory_path = tmp_path / "seen_jobs.json"
    memory_path.write_text("{broken json", encoding="utf-8")

    with pytest.raises(ValueError, match="invalid JSON"):
        load_seen_jobs(memory_path)
