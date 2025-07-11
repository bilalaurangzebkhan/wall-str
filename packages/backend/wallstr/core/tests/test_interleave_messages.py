from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from wallstr.core.llm import interleave_messages


def test_interleave_messages_empty_list() -> None:
    messages: list[BaseMessage] = []
    result = interleave_messages(messages)
    assert result == messages


def test_interleave_messages_single_message() -> None:
    messages = [HumanMessage(content="Hello")]
    result = interleave_messages(messages)
    assert result == messages


def test_interleave_messages_alternating() -> None:
    messages = [
        HumanMessage(content="Hello"),
        AIMessage(content="Hi"),
        HumanMessage(content="How are you?"),
        AIMessage(content="I'm good"),
    ]
    result = interleave_messages(messages)
    assert result == messages


def test_interleave_messages_same_type_sequential() -> None:
    messages = [
        HumanMessage(content="Hello"),
        HumanMessage(content="How are you?"),
        AIMessage(content="I'm good"),
    ]
    result = interleave_messages(messages)
    assert len(result) == 2
    assert isinstance(result[0], HumanMessage)
    assert result[0].content == "Hello\nHow are you?"
    assert isinstance(result[1], AIMessage)
    assert result[1].content == "I'm good"


def test_interleave_messages_multiple_same_type() -> None:
    messages = [
        HumanMessage(content="Message 1"),
        HumanMessage(content="Message 2"),
        HumanMessage(content="Message 3"),
        AIMessage(content="Response"),
    ]
    result = interleave_messages(messages)
    assert len(result) == 2
    assert isinstance(result[0], HumanMessage)
    assert result[0].content == "Message 1\nMessage 2\nMessage 3"
    assert isinstance(result[1], AIMessage)
    assert result[1].content == "Response"


def test_interleave_messages_with_system() -> None:
    """Test interleaving messages including system messages"""
    messages = [
        SystemMessage(content="System instruction"),
        HumanMessage(content="Hello"),
        AIMessage(content="Hi"),
        SystemMessage(content="Another instruction"),
        HumanMessage(content="Goodbye"),
    ]
    result = interleave_messages(messages)
    assert len(result) == 5
    assert [type(msg) for msg in result] == [
        SystemMessage,
        HumanMessage,
        AIMessage,
        SystemMessage,
        HumanMessage,
    ]
