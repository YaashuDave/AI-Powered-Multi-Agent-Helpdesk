import json

from monitor import FinalOutput, render_markdown, save


def make_final(**extra):
    return FinalOutput(ticket_id="TKT-1", troubleshoot={"success": True},
                       escalation={"escalate": False}, timestamp="2026-01-01T00:00:00", **extra)


def test_markdown_lists_validations_and_errors():
    final = make_final(
        validation=[{"source_type": "troubleshoot_done", "validation": {"passed": False}}],
        errors=[{"agent": "knowledge_agent", "error": "timeout"}],
    )
    md = render_markdown(final)
    assert "**Ticket ID:** TKT-1" in md
    assert "`troubleshoot_done`: **FAILED**" in md
    assert "`knowledge_agent`: timeout" in md


def test_save_writes_latest_and_per_ticket_reports(output_dir):
    save(make_final())
    for name in ("final.json", "final.md", "tickets/TKT-1.json", "tickets/TKT-1.md"):
        assert (output_dir / name).exists(), name
    assert json.loads((output_dir / "final.json").read_text(encoding="utf-8"))["ticket_id"] == "TKT-1"
