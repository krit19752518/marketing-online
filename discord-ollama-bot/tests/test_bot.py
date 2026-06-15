import pytest
from bot import split_message

def test_split_message_short():
    text = "Hello world"
    chunks = split_message(text, limit=20)
    assert chunks == ["Hello world"]

def test_split_message_long_newline():
    text = "First line\nSecond line\nThird line"
    chunks = split_message(text, limit=15)
    # Splits on newlines
    assert len(chunks) == 3
    assert chunks[0] == "First line"
    assert chunks[1] == "Second line"
    assert chunks[2] == "Third line"

def test_split_message_long_no_space():
    text = "abcdefghijklmnopqrstuvwxyz"
    chunks = split_message(text, limit=10)
    assert len(chunks) == 3
    assert chunks[0] == "abcdefghij"
    assert chunks[1] == "klmnopqrst"
    assert chunks[2] == "uvwxyz"

def test_memory_tag_parsing():
    import re
    reply = "Sure, I have updated the project timeline. [SAVE_MEMORY: category=WBS; summary=Updated project timeline to end in December]"
    
    memory_pattern = r"\[SAVE_MEMORY:\s*category=([^;]+);\s*summary=([^\]]+)\]"
    matches = re.findall(memory_pattern, reply)
    
    assert len(matches) == 1
    assert matches[0][0].strip() == "WBS"
    assert matches[0][1].strip() == "Updated project timeline to end in December"
    
    clean_reply = re.sub(memory_pattern, "", reply).strip()
    assert clean_reply == "Sure, I have updated the project timeline."

