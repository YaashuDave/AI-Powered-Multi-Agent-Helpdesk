from a2a.a2a_protocol import A2ABus, A2AMessage


def msg(receiver, type="ping", **payload):
    return A2AMessage(sender="tester", receiver=receiver, type=type, payload=payload)


def test_send_and_receive():
    bus = A2ABus()
    bus.register("agent")
    bus.send(msg("agent", ticket_id="T1"))

    got = bus.receive("agent", timeout=1)
    assert got.payload == {"ticket_id": "T1"}
    assert bus.receive("agent", timeout=0.01) is None


def test_message_to_unstarted_agent_is_kept():
    bus = A2ABus()
    bus.send(msg("late_agent"))
    assert bus.receive("late_agent", timeout=1).type == "ping"


def test_subscriber_gets_copies_of_its_types():
    bus = A2ABus()
    bus.register("agent")
    bus.subscribe("observer", {"retrieval_ready"})

    bus.send(msg("agent", type="retrieval_ready"))
    bus.send(msg("agent", type="other"))

    assert bus.receive("observer", timeout=1).type == "retrieval_ready"
    assert bus.receive("observer", timeout=0.01) is None
    assert bus.receive("agent", timeout=1).type == "retrieval_ready"
    assert bus.receive("agent", timeout=1).type == "other"


def test_subscriber_is_not_sent_duplicates():
    bus = A2ABus()
    bus.subscribe("observer", {"ping"})
    bus.send(msg("observer"))

    assert bus.receive("observer", timeout=1) is not None
    assert bus.receive("observer", timeout=0.01) is None
