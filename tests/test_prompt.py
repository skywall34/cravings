"""Tests for prompt construction."""

from tagging.prompt import build_tagging_prompt, FEW_SHOT_EXAMPLES, SYSTEM_PROMPT


class TestBuildTaggingPrompt:
    def test_has_system_message(self):
        messages = build_tagging_prompt("Test Item")
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == SYSTEM_PROMPT

    def test_has_few_shot_examples(self):
        messages = build_tagging_prompt("Test Item")
        # system + (user+assistant) * num_examples + final user
        expected_len = 1 + len(FEW_SHOT_EXAMPLES) * 2 + 1
        assert len(messages) == expected_len

    def test_user_input_name_only(self):
        messages = build_tagging_prompt("Pizza")
        last = messages[-1]
        assert last["role"] == "user"
        assert last["content"] == "Pizza"

    def test_user_input_with_description(self):
        messages = build_tagging_prompt("Pizza", "Wood-fired with mozzarella")
        last = messages[-1]
        assert last["content"] == "Pizza - Wood-fired with mozzarella"

    def test_few_shot_alternates_roles(self):
        messages = build_tagging_prompt("Test")
        for i in range(1, len(messages) - 1, 2):
            assert messages[i]["role"] == "user"
            assert messages[i + 1]["role"] == "assistant"
