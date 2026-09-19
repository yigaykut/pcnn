"""Verification suite.  Standard library only: `python -m unittest discover tests`.

The tests are written against the guarantees, not the implementation: a fact
never shrinks, weight never falls on its own, a bad mutation never lands, a
broken transcript never breaks a session.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pcnn import distill, ingest, merge, query, schema, weights  # noqa: E402
from pcnn.store import Network, Registry  # noqa: E402

TODAY = "2026-09-17"


def sample_neuron(nid: str = "T.DEC-001", **over) -> schema.Neuron:
    base = dict(
        id=nid, head="Cache the ranking per trading day",
        layer="DEC", project="t", status="active", confidence="verified",
        salience=0.90, signals=["caching", "ranking", "quote-api"],
        description="The ranking pipeline writes its scored output to a dated cache file "
                    "and reuses it for the rest of the trading day.",
        rationale="A full re-rank costs more in API calls than a day-old ranking costs "
                  "in accuracy.",
        anchors=["pipeline/rank.py:88-140"], evidence=["P1"],
        first_seen=TODAY, last_touched=TODAY, revision=1)
    base.update(over)
    return schema.Neuron(**base).canonical()


class TempWorkspace(unittest.TestCase):
    """Each test gets its own orchestrator root so nothing touches real data."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)
        (self.home / "networks").mkdir()
        reg = Registry(self.home)
        reg.add("t", self.home / "project")
        reg.save()
        (self.home / "project").mkdir()
        self.net = Network("t", self.home)
        self.net.init()
        self.net.load()

    def tearDown(self) -> None:
        self.tmp.cleanup()


# --------------------------------------------------------------------------

class TestSchema(unittest.TestCase):
    def test_round_trip_is_byte_identical(self):
        text = schema.dumps([sample_neuron()])
        again = schema.dumps(schema.loads(text))
        self.assertEqual(text, again)

    def test_round_trip_survives_edges_and_wrapping(self):
        n = sample_neuron(description="x " * 200)
        n.edges = [schema.Edge(n.id, "T.CON-002", "constrained_by", 1.0),
                   schema.Edge(n.id, "T.IMP-003", "implements", 0.9)]
        text = schema.dumps([n])
        self.assertEqual(text, schema.dumps(schema.loads(text)))
        parsed = schema.loads(text)[0]
        self.assertEqual(len(parsed.edges), 2)
        self.assertEqual(parsed.edges[0].type, "constrained_by")

    def test_stored_networks_round_trip(self):
        """The committed self-network must survive a parse/dump cycle exactly."""
        neurons = ROOT / "networks" / "pcnn" / "neurons"
        if not neurons.is_dir():
            self.skipTest("self-network not present")
        for path in sorted(neurons.glob("*.md")):
            text = path.read_text(encoding="utf-8")
            self.assertEqual(text, schema.dumps(schema.loads(text)), path.name)

    def test_validator_catches_every_planted_error(self):
        bad = schema.Neuron(
            id="T.DEC-002", head="A bad neuron", layer="DEC", project="wrong",
            status="maybe", confidence="guessed", salience=0.10,
            description="short", first_seen="17-09-2026", revision=0,
            edges=[schema.Edge("T.DEC-002", "T.ARC-009", "influences", 0.5),
                   schema.Edge("T.DEC-002", "T.ARC-010", "relates_to", 0.95)])
        codes = {f.code for f in schema.errors(schema.validate_neuron(bad))}
        for expected in ("E006",  # project disagrees with scope
                         "E007",  # unknown status
                         "E008",  # unknown confidence
                         "E010",  # salience below the DEC floor
                         "E013",  # DEC without rationale
                         "E014",  # unknown edge type
                         "E016",  # relates_to over its cap
                         "E018",  # malformed date
                         "E019"):  # revision below 1
            self.assertIn(expected, codes)

    def test_dangling_edge_is_a_graph_error(self):
        n = sample_neuron()
        n.edges = [schema.Edge(n.id, "T.ARC-404", "depends_on", 0.8)]
        codes = {f.code for f in schema.errors(schema.validate_graph([n]))}
        self.assertIn("E020", codes)

    def test_parser_rejects_broken_syntax(self):
        for text in ("head: orphan field\n",
                     "@neuron nope\nhead: x\n",
                     "@neuron T.DEC-001\nconnected.T.DEC-001 -> T.ARC-001\n",
                     "@neuron T.DEC-001\nbogus_field: x\n"):
            with self.assertRaises(schema.DSLError):
                schema.loads(text)

    def test_weak_edge_weight_is_capped_on_write(self):
        n = sample_neuron()
        n.edges = [schema.Edge(n.id, "T.ARC-001", "relates_to", 0.95)]
        codes = {f.code for f in schema.errors(schema.validate_neuron(n))}
        self.assertIn("E016", codes)


class TestWeightNeverFalls(TempWorkspace):
    def test_put_raises_a_neuron_to_its_floor(self):
        self.net.put(sample_neuron(salience=0.10))
        self.assertAlmostEqual(self.net.neurons["T.DEC-001"].salience,
                               schema.LAYERS["DEC"])

    def test_raise_salience_refuses_to_lower(self):
        self.net.put(sample_neuron(salience=0.95))
        self.assertFalse(weights.raise_salience(self.net, "T.DEC-001", 0.50,
                                                cause="test"))
        self.assertAlmostEqual(self.net.neurons["T.DEC-001"].salience, 0.95)

    def test_touch_boost_saturates_and_never_falls(self):
        self.net.put(sample_neuron(salience=0.90))
        for _ in range(40):
            weights.boost_on_touch(self.net, "T.DEC-001")
        n = self.net.neurons["T.DEC-001"]
        self.assertLessEqual(n.salience, weights.ceiling_for(n) + 1e-9)
        self.assertGreaterEqual(n.salience, 0.90)

    def test_demote_requires_a_reason_and_respects_the_floor(self):
        self.net.put(sample_neuron(salience=0.95))
        with self.assertRaises(ValueError):
            weights.demote(self.net, "T.DEC-001", 0.90, reason="  ")
        with self.assertRaises(ValueError):
            weights.demote(self.net, "T.DEC-001", 0.10, reason="no longer central")
        weights.demote(self.net, "T.DEC-001", 0.86, reason="no longer central")
        self.assertAlmostEqual(self.net.neurons["T.DEC-001"].salience, 0.86)
        ops = [e["op"] for e in self.net.read_changelog()]
        self.assertIn("demote", ops)


class TestMutations(TempWorkspace):
    def seed(self) -> None:
        self.net.put(sample_neuron("T.CON-001", layer="CON", salience=1.0,
                                   head="The quote API rate-limits above 500 req/h",
                                   description="The upstream quote API returns HTTP 429 "
                                               "above 500 requests per hour.",
                                   rationale="Exceeding it stalls the whole pipeline."))
        self.net.put(sample_neuron())

    def test_placeholders_are_allocated_and_linked(self):
        self.seed()
        text = (
            "@mutation upsert $IMP-1\n"
            "head: rank.py writes the dated cache file\n"
            "layer: IMP\nproject: t\nsalience: 0.60\n"
            "signals: cache-writer, rank, persistence\n"
            "description: The rank module serialises the scored frame to a dated JSON "
            "file under cache/ and reads it back on the next run of the same day.\n"
            "anchors: pipeline/rank.py\nevidence: recap/x\n"
            f"first_seen: {TODAY}\n\n"
            "@mutation link $IMP-1 -> T.DEC-001 : implements w=0.90\n"
            "@mutation touch T.CON-001\n")
        result = distill.apply_mutations(self.net, text, cause="recap/test")
        self.assertEqual(result.rejected, [])
        new_id = result.allocated["$IMP-1"]
        self.assertEqual(new_id, "T.IMP-001")
        self.assertIn(new_id, self.net.neurons)
        self.assertEqual(self.net.neurons[new_id].edges[0].dst, "T.DEC-001")

    def test_shrinking_rewrite_is_quarantined(self):
        self.seed()
        text = ("@mutation upsert T.DEC-001\n"
                "head: Cache the ranking\nlayer: DEC\nproject: t\nsalience: 0.90\n"
                "signals: caching, ranking\n"
                "description: The ranking is cached for the day.\n"
                "rationale: cost\nevidence: recap/x\n"
                f"first_seen: {TODAY}\n")
        before = self.net.neurons["T.DEC-001"].description
        result = distill.apply_mutations(self.net, text, cause="recap/test")
        self.assertEqual(result.applied, [])
        self.assertEqual(len(result.rejected), 1)
        self.assertIn("supersede", result.rejected[0].reason)
        self.assertEqual(self.net.neurons["T.DEC-001"].description, before)

    def test_quarantine_file_is_written(self):
        self.seed()
        result = distill.apply_mutations(
            self.net, "@mutation link T.DEC-001 -> T.NOPE-001 : implements w=0.5\n",
            cause="recap/test")
        self.assertEqual(len(result.rejected), 1)
        path = distill.quarantine(self.net, result, cause="recap/test")
        self.assertTrue(path.exists())
        self.assertIn("rejected", json.loads(path.read_text(encoding="utf-8")))

    def test_unknown_edge_type_and_op_are_rejected(self):
        self.seed()
        result = distill.apply_mutations(
            self.net,
            "@mutation link T.DEC-001 -> T.CON-001 : influences w=0.5\n"
            "@mutation delete T.CON-001\n",
            cause="recap/test")
        self.assertEqual(len(result.rejected), 2)
        self.assertEqual(result.applied, [])

    def test_a_wrong_edge_can_be_taken_back(self):
        """Facts are permanent; a claim about how two of them relate is not."""
        self.seed()
        self.net.link("T.DEC-001", "T.CON-001", "supersedes", 1.0)
        result = distill.apply_mutations(
            self.net,
            "@mutation unlink T.DEC-001 -> T.CON-001 : supersedes\n"
            "@mutation link T.DEC-001 -> T.CON-001 : constrained_by w=0.90\n",
            cause="manual/fix")
        self.assertEqual(result.rejected, [])
        edges = self.net.neurons["T.DEC-001"].edges
        self.assertFalse(any(e.type == "supersedes" for e in edges))
        self.assertTrue(any(e.type == "constrained_by" and e.dst == "T.CON-001"
                            for e in edges))
        self.assertIn("unlink", [e["op"] for e in self.net.read_changelog()
                                 if "op" in e])

    def test_unlinking_an_edge_that_is_not_there_is_rejected(self):
        self.seed()
        result = distill.apply_mutations(
            self.net, "@mutation unlink T.DEC-001 -> T.CON-001 : blocks\n",
            cause="manual/fix")
        self.assertEqual(result.applied, [])
        self.assertEqual(len(result.rejected), 1)
        self.assertIn("no blocks edge", result.rejected[0].reason)

    def test_merge_keeps_everything_the_old_neuron_held(self):
        self.seed()
        self.net.link("T.DEC-001", "T.CON-001", "constrained_by", 1.0)
        text = ("@mutation upsert T.DEC-001\n"
                "head: Cache the ranking per trading day\nlayer: DEC\nproject: t\n"
                "salience: 0.85\nsignals: caching, ranking, quote-api, rate-limit\n"
                "description: The ranking pipeline writes its scored output to a dated "
                "cache file and reuses it for the rest of the trading day. The cache key "
                "is the exchange trading date, not the wall clock date.\n"
                "rationale: A full re-rank costs more in API calls than a day-old "
                "ranking costs in accuracy.\n"
                "anchors: pipeline/cache.py\nevidence: recap/y\n"
                f"first_seen: {TODAY}\n")
        result = distill.apply_mutations(self.net, text, cause="recap/test")
        self.assertEqual(result.rejected, [])
        n = self.net.neurons["T.DEC-001"]
        self.assertAlmostEqual(n.salience, 0.90)             # kept the higher value
        self.assertEqual(n.revision, 2)
        self.assertIn("rate-limit", n.signals)
        self.assertIn("caching", n.signals)                  # union, not replacement
        self.assertIn("pipeline/cache.py", n.anchors)
        self.assertIn("pipeline/rank.py:88-140", n.anchors)  # old anchor survives
        self.assertIn("P1", n.evidence)
        self.assertTrue(any(e.dst == "T.CON-001" for e in n.edges))

    def test_supersede_retires_without_deleting(self):
        self.seed()
        text = ("@mutation upsert $DEC-1\n"
                "head: Ranking is recomputed on demand behind a request budget\n"
                "layer: DEC\nproject: t\nsalience: 0.88\n"
                "signals: on-demand, budget, ranking\n"
                "description: The ranking is recomputed whenever requested, guarded by a "
                "per-hour request budget rather than a dated cache file.\n"
                "rationale: The budget guard covers the rate limit without serving stale "
                "rankings.\nevidence: recap/z\n"
                f"first_seen: {TODAY}\n\n"
                "@mutation link $DEC-1 -> T.CON-001 : constrained_by w=1.00\n"
                "@mutation supersede T.DEC-001 by $DEC-1\n")
        result = distill.apply_mutations(self.net, text, cause="recap/test")
        self.assertEqual(result.rejected, [])
        self.assertIn("T.DEC-001", self.net.neurons)                 # still on disk
        self.assertEqual(self.net.neurons["T.DEC-001"].status, "superseded")
        self.net.rebuild()
        invariants = self.net.invariants_path.read_text(encoding="utf-8")
        self.assertIn("RETIRED", invariants)
        self.assertIn("T.DEC-001", invariants)

    def test_ids_are_never_reused(self):
        self.seed()
        self.assertEqual(self.net.next_id("IMP"), "T.IMP-001")
        self.net.put(sample_neuron("T.IMP-001", layer="IMP", salience=0.6,
                                   head="a module", rationale=""))
        self.net.log("upsert", "T.IMP-001", cause="test")
        del self.net.neurons["T.IMP-001"]      # simulate a merge losing the live file
        self.assertEqual(self.net.next_id("IMP"), "T.IMP-002")


class TestRetrieval(TempWorkspace):
    def build(self) -> list[schema.Neuron]:
        con = sample_neuron("T.CON-001", layer="CON", salience=1.0,
                            head="The quote API rate-limits above 500 requests per hour",
                            signals=["rate-limit", "quota", "http-429"],
                            description="The upstream quote API returns HTTP 429 above "
                                        "500 requests per hour.",
                            rationale="Exceeding it stalls the pipeline.")
        dec = sample_neuron()
        dec.edges = [schema.Edge(dec.id, con.id, "constrained_by", 1.0)]
        far = sample_neuron("T.GLO-001", layer="GLO", salience=0.55,
                            head="Trading date means the exchange session date",
                            signals=["trading-date", "session", "calendar"],
                            description="A trading date is the exchange session date, "
                                        "which differs from the wall clock date.",
                            rationale="")
        return [con, dec, far]

    def test_query_reaches_a_cause_no_term_mentioned(self):
        hits = query.activate(self.build(), "why is the ranking cached")
        ids = [h.neuron.id for h in hits]
        self.assertEqual(ids[0], "T.DEC-001")
        self.assertIn("T.CON-001", ids)                      # surfaced by the edge
        con = next(h for h in hits if h.neuron.id == "T.CON-001")
        self.assertEqual(con.hops, 1)
        self.assertEqual(con.via, ["T.DEC-001", "T.CON-001"])

    def test_unrelated_neuron_stays_below_the_cutoff(self):
        hits = query.activate(self.build(), "rate limit quota")
        self.assertNotIn("T.GLO-001", [h.neuron.id for h in hits])

    def test_empty_query_returns_nothing(self):
        self.assertEqual(query.activate(self.build(), "the and of"), [])


class TestHarvest(unittest.TestCase):
    def transcript(self, path: Path, *, broken: bool = False) -> Path:
        rows = [
            {"type": "user", "timestamp": "2026-09-17T09:00:00Z", "cwd": "/p",
             "gitBranch": "main", "sessionId": "s1", "version": "2.1.0",
             "message": {"role": "user", "content": "Add a PDF export step."}},
            {"type": "assistant", "timestamp": "2026-09-17T09:01:00Z", "sessionId": "s1",
             "message": {"role": "assistant", "content": [
                 {"type": "tool_use", "id": "t1", "name": "Write",
                  "input": {"file_path": "export.py", "content": "x" * 120}},
                 {"type": "tool_use", "id": "t2", "name": "Bash",
                  "input": {"command": "pip install fpdf2", "description": "install"}},
                 {"type": "tool_use", "id": "t3", "name": "Read",
                  "input": {"file_path": "app.py"}}]}},
            {"type": "user", "timestamp": "2026-09-17T09:02:00Z", "sessionId": "s1",
             "message": {"role": "user", "content": [
                 {"type": "tool_result", "tool_use_id": "t2", "is_error": True,
                  "content": "ModuleNotFoundError: reportlab"}]}},
            {"type": "user", "timestamp": "2026-09-17T09:03:00Z", "sessionId": "s1",
             "isMeta": True,
             "message": {"role": "user", "content": "<system reminder>"}},
            {"type": "assistant", "timestamp": "2026-09-17T09:04:00Z", "sessionId": "s1",
             "message": {"role": "assistant", "content": [
                 {"type": "text", "text": "Switched PDF generation to fpdf2."}]}},
        ]
        with path.open("w", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r) + "\n")
            if broken:
                fh.write('{"type": "assistant", "message": {"content": [{"typ\n')
                fh.write("not json at all\n")
        return path

    def test_delta_captures_the_facts_and_drops_the_noise(self):
        with tempfile.TemporaryDirectory() as tmp:
            t = self.transcript(Path(tmp) / "s1.jsonl")
            deltas, lines = ingest.parse_transcript(t)
            self.assertEqual(len(deltas), 1)
            d = deltas[0]
            self.assertEqual(d.day, "2026-09-17")
            self.assertEqual(lines, 5)
            self.assertEqual(d.session_id, "s1")
            self.assertEqual(d.git_branch, "main")
            self.assertEqual(d.counts["instructions"], 1)          # meta excluded
            self.assertEqual(d.user_instructions[0]["text"], "Add a PDF export step.")
            self.assertEqual([c["path"] for c in d.file_changes], ["export.py"])
            self.assertTrue(d.file_changes[0]["created"])
            self.assertEqual(d.file_changes[0]["churn"], 120)
            self.assertEqual(d.commands[0]["bucket"], "install")
            self.assertEqual(d.files_read, ["app.py"])
            self.assertEqual(len(d.failures), 1)
            self.assertEqual(d.failures[0]["tool"], "Bash")        # mapped by tool_use_id
            self.assertIn("reportlab", d.failures[0]["error"])
            self.assertIn("fpdf2", d.recap)

    def test_days_are_split_into_separate_deltas(self):
        with tempfile.TemporaryDirectory() as tmp:
            t = Path(tmp) / "s3.jsonl"
            rows = []
            for day in ("2026-09-15", "2026-09-16"):
                rows.append({"type": "user", "sessionId": "s3",
                             "timestamp": f"{day}T10:00:00Z", "cwd": "/p",
                             "message": {"content": f"work on {day}"}})
                rows.append({"type": "assistant", "sessionId": "s3",
                             "timestamp": f"{day}T10:05:00Z",
                             "message": {"content": [
                                 {"type": "tool_use", "id": "w" + day, "name": "Write",
                                  "input": {"file_path": f"{day}.py", "content": "x"}}]}})
            t.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
            deltas, _ = ingest.parse_transcript(t)
            self.assertEqual([d.day for d in deltas], ["2026-09-15", "2026-09-16"])
            self.assertEqual(deltas[0].file_changes[0]["path"], "2026-09-15.py")

    def test_repeated_commands_fold_with_a_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            t = Path(tmp) / "s4.jsonl"
            rows = [{"type": "assistant", "sessionId": "s4",
                     "timestamp": "2026-09-17T10:00:0%dZ" % i,
                     "message": {"content": [
                         {"type": "tool_use", "id": f"c{i}", "name": "Bash",
                          "input": {"command": "pytest -q"}}]}} for i in range(9)]
            t.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
            d = ingest.parse_transcript(t)[0][0]
            self.assertEqual(d.counts["commands"], 9)
            self.assertEqual(d.counts["unique_commands"], 1)
            self.assertEqual(d.commands[0]["repeats"], 9)

    def test_corrupt_transcript_is_survivable(self):
        with tempfile.TemporaryDirectory() as tmp:
            t = self.transcript(Path(tmp) / "s1.jsonl", broken=True)
            deltas, _ = ingest.parse_transcript(t)
            self.assertEqual(len(deltas[0].file_changes), 1)        # bad lines skipped

    def test_read_only_session_writes_no_delta(self):
        with tempfile.TemporaryDirectory() as tmp:
            t = Path(tmp) / "s2.jsonl"
            t.write_text(json.dumps(
                {"type": "assistant", "sessionId": "s2",
                 "timestamp": "2026-09-17T10:00:00Z", "message": {"content": [
                     {"type": "tool_use", "id": "r", "name": "Read",
                      "input": {"file_path": "a.py"}}]}}) + "\n", encoding="utf-8")
            net_dir = Path(tmp) / "net"
            net_dir.mkdir()
            self.assertEqual(ingest.harvest(t, "t", net_dir), [])

    def test_harvest_is_incremental_and_never_re_emits_a_day(self):
        with tempfile.TemporaryDirectory() as tmp:
            t = self.transcript(Path(tmp) / "s1.jsonl")
            net_dir = Path(tmp) / "net"
            net_dir.mkdir()
            first = ingest.harvest(t, "t", net_dir)
            self.assertEqual(len(first), 1)
            self.assertEqual(ingest.harvest(t, "t", net_dir), [])   # cursor holds
            with t.open("a", encoding="utf-8") as fh:               # session continues
                fh.write(json.dumps(
                    {"type": "assistant", "sessionId": "s1",
                     "timestamp": "2026-09-18T09:00:00Z", "message": {"content": [
                         {"type": "tool_use", "id": "t9", "name": "Write",
                          "input": {"file_path": "b.py", "content": "y"}}]}}) + "\n")
            second = ingest.harvest(t, "t", net_dir)
            self.assertEqual(len(second), 1)
            self.assertIn("2026-09-18", str(second[0]))
            self.assertNotEqual(first[0], second[0])

    def test_a_distillation_run_is_not_harvested_as_project_work(self):
        """The pipeline must never feed itself: that loop spends tokens forever."""
        with tempfile.TemporaryDirectory() as tmp:
            t = Path(tmp) / "internal.jsonl"
            rows = [
                {"type": "user", "sessionId": "int", "timestamp": "2026-09-17T10:00:00Z",
                 "cwd": "/p", "message": {"content": "# TASK: distil one session delta"}},
                {"type": "assistant", "sessionId": "int",
                 "timestamp": "2026-09-17T10:01:00Z", "message": {"content": [
                     {"type": "text",
                      "text": "@mutation upsert $DEC-1\nhead: something"}]}},
            ]
            t.write_text("\n".join(json.dumps(r) for r in rows) + "\n",
                         encoding="utf-8")
            delta = ingest.parse_transcript(t)[0][0]
            self.assertTrue(ingest.is_pipeline_output(delta))
            net_dir = Path(tmp) / "net"
            net_dir.mkdir()
            self.assertEqual(ingest.harvest(t, "t", net_dir), [])

    def test_real_work_is_never_mistaken_for_pipeline_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            t = self.transcript(Path(tmp) / "s1.jsonl")
            delta = ingest.parse_transcript(t)[0][0]
            self.assertFalse(ingest.is_pipeline_output(delta))

    def test_a_session_that_reports_itself_needs_no_model(self):
        """The zero-token path: parse what the session already wrote."""
        from pcnn import reap
        block = (
            "done.\n\n@pcnn\n"
            "@mutation upsert $GOT-1\n"
            "head: The PDF writer must be flushed before the temp file is read\n"
            "layer: GOT\nproject: t\nsalience: 0.85\n"
            "signals: pdf, flush, temp-file\n"
            "description: The writer buffers, so reading the temp file before a "
            "flush yields a truncated document that opens without any error.\n"
            "rationale: The failure is silent, which is what made it expensive.\n"
            "anchors: src/export.py:120-150\n"
            "@end\n")
        self.assertTrue(reap.has_block(block))
        body = reap.extract(block)
        self.assertTrue(body.startswith("@mutation"))
        self.assertNotIn("@end", body)
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            (home / "networks").mkdir()
            net = Network("t", home)
            net.init()
            net.load()
            result = distill.apply_mutations(net, body, cause="self/test")
            self.assertEqual(result.rejected, [])
            self.assertEqual(len(result.applied), 1)
            self.assertIn("T.GOT-001", net.neurons)

    def test_a_report_survives_a_long_tail_of_later_messages(self):
        """The block is often written before the session's last few messages."""
        with tempfile.TemporaryDirectory() as tmp:
            t = Path(tmp) / "tail.jsonl"
            rows = [
                {"type": "assistant", "sessionId": "tl",
                 "timestamp": "2026-09-17T10:00:00Z", "message": {"content": [
                     {"type": "tool_use", "id": "w", "name": "Write",
                      "input": {"file_path": "a.py", "content": "x"}}]}},
                {"type": "assistant", "sessionId": "tl",
                 "timestamp": "2026-09-17T10:01:00Z", "message": {"content": [
                     {"type": "text",
                      "text": "@pcnn\n@mutation touch T.DEC-001\n@end"}]}},
            ]
            for i in range(4):          # four more messages push it out of the recap
                rows.append({"type": "assistant", "sessionId": "tl",
                             "timestamp": f"2026-09-17T10:0{i + 2}:00Z",
                             "message": {"content": [
                                 {"type": "text", "text": f"more work {i}"}]}})
            t.write_text("\n".join(json.dumps(r) for r in rows) + "\n",
                         encoding="utf-8")
            d = ingest.parse_transcript(t)[0][0]
            self.assertNotIn("@pcnn", d.recap)      # gone from the recap window
            self.assertEqual(d.self_report, "@mutation touch T.DEC-001")

    def test_a_fenced_self_report_is_not_mistaken_for_the_distiller(self):
        from pcnn import reap
        reported = ingest.Delta(recap="@pcnn\n@mutation touch T.DEC-001\n@end")
        self.assertTrue(reap.has_block(reported.recap))
        self.assertFalse(ingest.is_pipeline_output(reported))
        bare = ingest.Delta(recap="@mutation upsert $DEC-1\nhead: x")
        self.assertTrue(ingest.is_pipeline_output(bare))

    def test_only_the_last_block_counts(self):
        from pcnn import reap
        text = ("@pcnn\n@mutation touch A.DEC-001\n@end\n"
                "then more work happened\n"
                "@pcnn\n@mutation touch A.DEC-002\n@end\n")
        self.assertEqual(reap.extract(text), "@mutation touch A.DEC-002")

    def test_no_block_means_no_update(self):
        from pcnn import reap
        self.assertIsNone(reap.extract("just a normal closing message"))
        self.assertIsNone(reap.extract("@pcnn without a close"))
        self.assertIsNone(reap.extract(""))

    def test_the_cursor_ignores_how_the_path_was_spelled(self):
        """The CLI passes forward slashes, the hook passes backslashes."""
        with tempfile.TemporaryDirectory() as tmp:
            t = self.transcript(Path(tmp) / "s1.jsonl")
            net_dir = Path(tmp) / "net"
            net_dir.mkdir()
            first = ingest.harvest(t, "t", net_dir)
            self.assertEqual(len(first), 1)
            other_spelling = str(t).replace("\\", "/")
            self.assertEqual(ingest.read_cursor(net_dir, other_spelling),
                             ingest.read_cursor(net_dir, t))
            # harvesting again under the other spelling must find nothing new
            self.assertEqual(ingest.harvest(other_spelling, "t", net_dir), [])

    def test_pending_tracks_undistilled_deltas(self):
        with tempfile.TemporaryDirectory() as tmp:
            t = self.transcript(Path(tmp) / "s1.jsonl")
            net_dir = Path(tmp) / "net"
            net_dir.mkdir()
            raw = ingest.harvest(t, "t", net_dir)
            self.assertEqual(ingest.pending(net_dir), raw)
            ingest.mark_applied(raw[0], {"applied": []})
            self.assertEqual(ingest.pending(net_dir), [])


class TestConsolidation(TempWorkspace):
    def test_near_duplicates_merge_without_losing_a_field(self):
        a = sample_neuron("T.IMP-001", layer="IMP", salience=0.55,
                          head="rank module writes the dated cache file",
                          signals=["cache-writer", "rank"],
                          description="The rank module writes the dated cache file.",
                          rationale="", anchors=["pipeline/rank.py"], evidence=["P1"],
                          first_seen="2026-09-01")
        b = sample_neuron("T.IMP-002", layer="IMP", salience=0.70,
                          head="rank module writes the dated cache file",
                          signals=["cache-writer", "rank", "json"],
                          description="Serialisation uses JSON with a date-stamped name.",
                          rationale="", anchors=["pipeline/rank.py"], evidence=["P9"],
                          first_seen="2026-09-05")
        self.net.put(a)
        self.net.put(b)
        report = merge.consolidate(self.net)
        self.assertEqual(report.merged, [("T.IMP-001", "T.IMP-002")])
        keeper = self.net.neurons["T.IMP-001"]
        self.assertAlmostEqual(keeper.salience, 0.70)
        self.assertIn("json", keeper.signals)
        self.assertIn("P9", keeper.evidence)
        self.assertIn("JSON", keeper.description)
        self.assertEqual(self.net.neurons["T.IMP-002"].status, "superseded")

    def test_distinct_neurons_are_only_reported(self):
        self.net.put(sample_neuron("T.IMP-001", layer="IMP", salience=0.5,
                                   head="rank module writes the cache", rationale=""))
        self.net.put(sample_neuron("T.IMP-002", layer="IMP", salience=0.5,
                                   head="dashboard renders the ranking table",
                                   signals=["dashboard", "html", "table"],
                                   rationale=""))
        report = merge.consolidate(self.net)
        self.assertEqual(report.merged, [])

    def test_same_fact_in_different_words_is_still_flagged(self):
        """Lexical similarity alone misses a re-worded duplicate."""
        a = sample_neuron("T.GOT-001", layer="GOT", salience=0.85,
                          head="Repeated distillation mints duplicate neurons",
                          signals=["duplicate", "placeholder", "upsert"],
                          description="Running the same delta twice creates a second "
                                      "neuron because a placeholder always allocates.",
                          rationale="Placeholder ids cannot match an existing neuron.",
                          anchors=["pcnn/distill.py", "pcnn/store.py"])
        b = sample_neuron("T.GOT-002", layer="GOT", salience=0.85,
                          head="Re-distilling a delta cannot be idempotent",
                          signals=["duplicate neurons", "idempotence", "placeholder id"],
                          description="A rerun of one delta yields a fresh id each time, "
                                      "so the same fact lands twice.",
                          rationale="Allocation happens before any comparison.",
                          anchors=["pcnn/distill.py", "pcnn/schema.py"])
        self.assertLess(merge.similarity(a, b), merge.REPORT_FROM)
        self.assertTrue(merge.overlaps(a, b))
        self.net.put(a)
        self.net.put(b)
        report = merge.consolidate(self.net)
        self.assertEqual(report.merged, [])          # never merged on evidence alone
        self.assertTrue(any({x, y} == {"T.GOT-001", "T.GOT-002"}
                            for x, y, _ in report.candidates))

    def test_edges_are_reinforced_only_for_co_changing_pairs(self):
        self.net.put(sample_neuron("T.CON-001", layer="CON", salience=1.0,
                                   head="rate limit", rationale="because"))
        self.net.put(sample_neuron())
        self.net.link("T.DEC-001", "T.CON-001", "constrained_by", 0.50)
        for i in range(3):
            self.net.log("upsert", "T.DEC-001", cause=f"recap/2026-09-0{i}/a.json")
            self.net.log("upsert", "T.CON-001", cause=f"recap/2026-09-0{i}/a.json")
        weights.reinforce_edges(self.net)
        edge = next(e for e in self.net.neurons["T.DEC-001"].edges
                    if e.dst == "T.CON-001")
        self.assertGreater(edge.weight, 0.50)

    def test_suggestions_never_invent_edges(self):
        self.net.put(sample_neuron("T.CON-001", layer="CON", salience=1.0,
                                   head="rate limit", rationale="because"))
        self.net.put(sample_neuron())
        for i in range(4):
            self.net.log("upsert", "T.DEC-001", cause=f"recap/2026-09-0{i}/a.json")
            self.net.log("upsert", "T.CON-001", cause=f"recap/2026-09-0{i}/a.json")
        self.assertTrue(weights.unlinked_co_changes(self.net))
        self.assertEqual(self.net.neurons["T.DEC-001"].edges, [])


class TestGeneratedViews(TempWorkspace):
    def test_invariants_holds_every_pinned_and_heavy_neuron_in_full(self):
        self.net.put(sample_neuron("T.CON-001", layer="CON", salience=1.0, pin=True,
                                   head="never call the quote API more than 500 times/h",
                                   description="The pipeline must not exceed 500 quote "
                                               "API calls per hour under any code path.",
                                   rationale="Above it the API returns HTTP 429."))
        self.net.put(sample_neuron("T.IMP-001", layer="IMP", salience=0.50,
                                   head="a minor helper", rationale=""))
        self.net.rebuild()
        text = self.net.invariants_path.read_text(encoding="utf-8")
        self.assertIn("T.CON-001", text)
        self.assertIn("must not exceed 500 quote API calls", text)   # full, not clipped
        self.assertNotIn("T.IMP-001", text)

    def test_map_lists_every_neuron_with_decodable_edges(self):
        self.net.put(sample_neuron("T.CON-001", layer="CON", salience=1.0,
                                   head="rate limit", rationale="because"))
        self.net.put(sample_neuron())
        self.net.link("T.DEC-001", "T.CON-001", "constrained_by", 1.0)
        self.net.rebuild()
        text = self.net.map_path.read_text(encoding="utf-8")
        self.assertIn("T.DEC-001", text)
        self.assertIn("con>CON-001", text)
        self.assertIn("con=constrained_by", text)                    # decoder included

    def test_rebuild_refuses_to_shrink_the_map_from_a_stale_instance(self):
        """A caller that forgot to load must not overwrite the whole map."""
        self.net.put(sample_neuron("T.CON-001", layer="CON", salience=1.0,
                                   head="a rule", rationale="because"))
        self.net.put(sample_neuron())
        self.net.rebuild()
        self.assertEqual(self.net.map_path.read_text(encoding="utf-8").count("T."),
                         self.net.map_path.read_text(encoding="utf-8").count("T."))

        stale = Network("t", self.home)      # never loaded: knows nothing
        stale.init()
        self.assertEqual(len(stale.neurons), 0)
        stale.rebuild()
        text = stale.map_path.read_text(encoding="utf-8")
        self.assertIn("T.DEC-001", text)
        self.assertIn("T.CON-001", text)

    def test_graph_json_matches_the_neurons(self):
        self.net.put(sample_neuron())
        self.net.rebuild()
        g = json.loads(self.net.graph_path.read_text(encoding="utf-8"))
        self.assertEqual(len(g["nodes"]), 1)
        self.assertEqual(g["nodes"][0]["id"], "T.DEC-001")
        self.assertEqual(g["project"], "t")


class TestLayout(unittest.TestCase):
    """The ring order is solved when the page is written, not when it is opened."""

    def ring(self, n=12):
        ids = [f"T.DEC-{i:03d}" for i in range(n)]
        sal = {k: 1.0 - i * 0.01 for i, k in enumerate(ids)}
        return ids, sal

    def test_it_untangles_a_deliberately_tangled_ring(self):
        from pcnn import layout
        ids, sal = self.ring(12)
        # every neuron tied to the one opposite: maximally crossed to begin with
        ties = [(ids[i], ids[(i + 6) % 12]) for i in range(6)]
        kin = {k: set() for k in ids}
        for a, b in ties:
            kin[a].add(b)
            kin[b].add(a)
        plan = layout.solve(ids, ties, sal, kin)
        self.assertLess(plan.crossings, plan.seeded_crossings)
        self.assertEqual(layout.count_crossings(plan.order, ties), plan.crossings)

    def test_a_ring_of_neighbours_can_be_drawn_with_no_crossings_at_all(self):
        from pcnn import layout
        ids, sal = self.ring(10)
        ties = [(ids[i], ids[(i + 1) % 10]) for i in range(10)]
        kin = {k: set() for k in ids}
        for a, b in ties:
            kin[a].add(b)
            kin[b].add(a)
        plan = layout.solve(ids, ties, sal, kin)
        self.assertEqual(plan.crossings, 0)

    def test_every_neuron_is_placed_exactly_once(self):
        from pcnn import layout
        ids, sal = self.ring(15)
        ties = [(ids[i], ids[(i * 5 + 3) % 15]) for i in range(15)]
        ties = [(a, b) for a, b in ties if a != b]
        kin = {k: set() for k in ids}
        for a, b in ties:
            kin[a].add(b)
            kin[b].add(a)
        plan = layout.solve(ids, ties, sal, kin)
        self.assertEqual(sorted(plan.order), sorted(ids))
        self.assertEqual(len(set(plan.order)), len(ids))

    def test_the_same_network_always_draws_the_same_picture(self):
        from pcnn import layout
        ids, sal = self.ring(14)
        ties = [(ids[i], ids[(i * 3 + 1) % 14]) for i in range(14)]
        ties = [(a, b) for a, b in ties if a != b]
        kin = {k: set() for k in ids}
        for a, b in ties:
            kin[a].add(b)
            kin[b].add(a)
        first = layout.solve(ids, ties, sal, kin).order
        shuffled = list(reversed(ids))
        again = layout.solve(shuffled, ties, sal, kin).order
        self.assertEqual(first, again)

    def test_the_renderer_uses_the_even_ring_by_default(self):
        from pcnn import layout
        ids, sal = self.ring(12)
        ties = [(ids[i], ids[(i + 6) % 12]) for i in range(6)]
        kin = {k: set() for k in ids}
        for a, b in ties:
            kin[a].add(b)
            kin[b].add(a)
        os.environ.pop("PCNN_LAYOUT", None)
        even = layout.settle(ids, ties, sal, kin)
        seed = sorted(ids, key=lambda k: (-sal[k], k))
        self.assertEqual(even.order, layout.barycentre(seed, kin))

    def test_the_crossing_minimiser_is_one_env_var_away(self):
        from pcnn import layout
        ids, sal = self.ring(12)
        ties = [(ids[i], ids[(i + 6) % 12]) for i in range(6)]
        kin = {k: set() for k in ids}
        for a, b in ties:
            kin[a].add(b)
            kin[b].add(a)
        os.environ["PCNN_LAYOUT"] = "crossings"
        try:
            tight = layout.settle(ids, ties, sal, kin)
        finally:
            os.environ.pop("PCNN_LAYOUT", None)
        even = layout.settle(ids, ties, sal, kin)
        self.assertLessEqual(tight.crossings, even.crossings)

    def test_radius_still_follows_weight_rank(self):
        from pcnn import layout
        desc = [1.0, 0.9, 0.8, 0.7]
        radii = [layout.rank_radius(s, desc) for s in desc]
        self.assertEqual(radii, sorted(radii))          # heavier sits nearer the core
        self.assertAlmostEqual(radii[0], layout.R_IN)
        self.assertAlmostEqual(radii[-1], layout.R_OUT)

    def test_a_network_too_small_to_tangle_is_left_alone(self):
        from pcnn import layout
        plan = layout.solve(["A.DEC-001"], [], {"A.DEC-001": 0.9}, {})
        self.assertEqual(plan.order, ["A.DEC-001"])


class TestActivityGate(unittest.TestCase):
    """The nightly pass stands down on a day nobody opened a session."""

    def test_the_slug_matches_claude_codes_own_naming(self):
        from pcnn import activity
        # the folder name replaces every non-alphanumeric character, including
        # the drive colon, both separators, the space, and a non-ASCII letter
        path = Path("C:/Users/Ren" + chr(0xE9) + "e/OneDrive/Desktop/project orchestrator")
        self.assertEqual(activity._slug_for(path),
                         "C--Users-Ren-e-OneDrive-Desktop-project-orchestrator")

    def test_a_day_with_no_session_reports_nothing_happened(self):
        from pcnn import activity
        self.assertFalse(activity.anything_happened(day="1999-01-01"))

    def test_a_transcript_written_today_counts_as_activity(self):
        from pcnn import activity
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            (home / "networks").mkdir()
            project = home / "a project"
            project.mkdir()
            reg = Registry(home)
            reg.add("p", project)
            reg.save()

            fake = home / "claude" / "projects" / activity._slug_for(project.resolve())
            fake.mkdir(parents=True)
            (fake / "s.jsonl").write_text("{}\n", encoding="utf-8")

            os.environ["CLAUDE_CONFIG_DIR"] = str(home / "claude")
            try:
                self.assertTrue(activity.anything_happened(home))
                self.assertFalse(activity.anything_happened(home, day="1999-01-01"))
            finally:
                os.environ.pop("CLAUDE_CONFIG_DIR", None)

    def test_an_unregistered_project_does_not_count(self):
        from pcnn import activity
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            (home / "networks").mkdir()
            Registry(home).save()          # nothing registered
            fake = home / "claude" / "projects" / "C--somewhere-else"
            fake.mkdir(parents=True)
            (fake / "s.jsonl").write_text("{}\n", encoding="utf-8")
            os.environ["CLAUDE_CONFIG_DIR"] = str(home / "claude")
            try:
                self.assertFalse(activity.anything_happened(home))
            finally:
                os.environ.pop("CLAUDE_CONFIG_DIR", None)


class TestHookSafety(unittest.TestCase):
    def run_hook(self, name: str, payload: dict) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(ROOT / "hooks" / name)],
            input=json.dumps(payload), capture_output=True, text=True,
            encoding="utf-8", errors="replace",
            env=dict(os.environ, PCNN_NO_DISTILL="1"), timeout=60)

    def test_session_end_exits_zero_on_a_missing_transcript(self):
        p = self.run_hook("session_end.py", {"transcript_path": "/nope/x.jsonl",
                                             "cwd": "/nope", "session_id": "s"})
        self.assertEqual(p.returncode, 0)

    def test_session_end_exits_zero_on_garbage_stdin(self):
        p = subprocess.run(
            [sys.executable, str(ROOT / "hooks" / "session_end.py")],
            input="not json", capture_output=True, text=True,
            env=dict(os.environ, PCNN_NO_DISTILL="1"), timeout=60)
        self.assertEqual(p.returncode, 0)

    def test_hooks_decode_stdin_as_utf8(self):
        """A non-ASCII path must survive stdin on a non-UTF-8 console codepage."""
        payload = json.dumps({"cwd": str(ROOT), "session_id": "s"}).encode("utf-8")
        proc = subprocess.run(
            [sys.executable, str(ROOT / "hooks" / "session_start.py")],
            input=payload, capture_output=True,
            env=dict(os.environ, PCNN_NO_DISTILL="1"), timeout=60)
        self.assertEqual(proc.returncode, 0)
        if "İ" not in str(ROOT):
            self.skipTest("orchestrator path has no non-ASCII character to exercise")
        self.assertTrue(proc.stdout.strip(),
                        "non-ASCII cwd did not resolve to a project")

    def test_session_end_stands_down_inside_a_pipeline_session(self):
        proc = subprocess.run(
            [sys.executable, str(ROOT / "hooks" / "session_end.py")],
            input=json.dumps({"transcript_path": str(ROOT / "tests" / "test_pcnn.py"),
                              "cwd": str(ROOT), "session_id": "x"}),
            capture_output=True, text=True, timeout=60,
            env=dict(os.environ, PCNN_INTERNAL="1"))
        self.assertEqual(proc.returncode, 0)
        log = (ROOT / "hooks" / "hook.log")
        if log.exists():
            self.assertIn("standing down", log.read_text(encoding="utf-8")[-4000:])

    def test_session_start_is_silent_for_an_unregistered_cwd(self):
        p = self.run_hook("session_start.py", {"cwd": str(Path(tempfile.gettempdir()))})
        self.assertEqual(p.returncode, 0)
        self.assertEqual(p.stdout.strip(), "")

    def test_session_start_emits_valid_hook_json_for_a_known_project(self):
        p = self.run_hook("session_start.py", {"cwd": str(ROOT)})
        self.assertEqual(p.returncode, 0)
        if not p.stdout.strip():
            self.skipTest("orchestrator not registered in the live registry")
        payload = json.loads(p.stdout)
        out = payload["hookSpecificOutput"]
        self.assertEqual(out["hookEventName"], "SessionStart")
        self.assertIn("INVARIANTS", out["additionalContext"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
