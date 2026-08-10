"""Narrator prompt-builder tests (deterministic; no model calls)."""

import json
import os

import pytest
from conftest import FIXTURES
from dispatch import narrator


def _facts():
    with open(os.path.join(FIXTURES, "facts", "fixture-day.json")) as f:
        return json.load(f)


def test_prompt_carries_the_facts_verbatim():
    doc = _facts()
    prompt = narrator.build_prompt(doc, "operator")
    assert json.dumps(doc, indent=2, sort_keys=True) in prompt
    assert doc["date"] in prompt


def test_prompt_states_the_contract_and_voice():
    prompt = narrator.build_prompt(_facts(), "brief")
    assert "only source of truth" in prompt.lower()
    assert "[F0007]" in prompt  # citation syntax is shown
    assert narrator.VOICES["brief"]["label"] in prompt


def test_prompt_is_facts_only_no_repo():
    # The fence: the narrator is told not to use tools / reach the repo.
    prompt = narrator.build_prompt(_facts(), "changelog")
    assert "do not use any tool" in prompt.lower()


def test_prompt_is_pure():
    doc = _facts()
    assert narrator.build_prompt(doc, "operator") == narrator.build_prompt(doc, "operator")


def test_unknown_voice_rejected():
    with pytest.raises(KeyError):
        narrator.build_prompt(_facts(), "nope")


def test_all_voices_build():
    doc = _facts()
    for key in narrator.VOICES:
        assert narrator.build_prompt(doc, key)
