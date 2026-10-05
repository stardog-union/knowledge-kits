"""A/B test: ask every question in questions.json to Voicebox against the kit database and,
optionally, a baseline database without BFO/CCO, several runs each, and score the answers.

Usage:
    VOICEBOX_TOKEN=<Stardog JWT> python3 voicebox_eval.py OUT.jsonl [--runs 3]
        [--voicebox-url http://localhost:8000] [--stardog-for-voicebox http://localhost:5820]
        [--named-graph urn:fleet:kg] [--db kit-bfo-cco-fleet --db BASELINE_DB]

Targets the self-hosted Voicebox service's v4 API (POST /voicebox/v4/{conversation}/ask-sync),
which queries Stardog as the user in the JWT (mint one with `stardog-admin user token`).
--stardog-for-voicebox is the Stardog URL as seen from the Voicebox service, for example
http://stardog:5820 when both run in the same Docker network. Install the kit first
(`kits install examples/bfo_cco_fleet`). For a baseline, create a Voicebox-enabled database and
load ../../data/fleet_ontology.ttl into tag:stardog:api:context:schema and urn:fleet:kg,
fleet_data.ttl into urn:fleet:kg and incoming_batch.ttl into urn:fleet:incoming.

Every call uses a fresh conversation. Runs are interleaved (run 1 of every question on every
database, then run 2, and so on), and the databases are asked concurrently. An answer counts
as correct when every expected value appears in it; review the saved answers and generated
SPARQL too. Summarize with analyze_results.py.
"""
import argparse, json, os, re, time, uuid, urllib.error, urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("out")
ap.add_argument("--runs", type=int, default=3)
ap.add_argument("--voicebox-url", default="http://localhost:8000")
ap.add_argument("--stardog-for-voicebox", default="http://localhost:5820")
ap.add_argument("--named-graph", default="urn:fleet:kg")
ap.add_argument("--db", action="append", help="database to ask (repeatable)")
args = ap.parse_args()
DBS = args.db or ["kit-bfo-cco-fleet"]
TOKEN = os.environ["VOICEBOX_TOKEN"]
QUESTIONS = json.loads((Path(__file__).parent / "questions.json").read_text())


def normalize(text):
    return re.sub(r"(?<=\d),(?=\d{3})", "", text or "")


def score(answer, expect_all):
    a = normalize(answer).lower()

    def hit(e):
        if re.fullmatch(r"[\d.]+", e):
            return re.search(rf"(?<![\d.]){re.escape(e)}(?:\.0+)?(?![\d])", a) is not None
        return e.lower() in a
    missing = [e for e in expect_all if not hit(e)]
    return not missing, missing


def ask(db, q):
    body = json.dumps({"endpoint": args.stardog_for_voicebox, "database": db, "model": "default", "question": q["q"],
                       "reasoning": True, "named_graphs": [args.named_graph]}).encode()
    req = urllib.request.Request(f"{args.voicebox_url.rstrip('/')}/voicebox/v4/{uuid.uuid4()}/ask-sync", data=body,
                                 method="POST", headers={"Content-Type": "application/json", "Authorization": f"Bearer {TOKEN}"})
    t0 = time.time()
    rec = {"db": db, "id": q["id"], "kind": q["kind"], "question": q["q"]}
    try:
        with urllib.request.urlopen(req, timeout=240) as r:
            data = json.loads(r.read().decode())
        rec["status"] = "ok" if data.get("type") != "error" else "vbx_error"
        rec["answer"] = data.get("answer") or data.get("error")
        acts = [a for a in data.get("actions") or [] if isinstance(a, dict)]
        rec["sparql"] = [a["value"] for a in acts if a.get("type") == "sparql"]
        rec["csv"] = [a["value"][:2000] for a in acts if a.get("type") == "csv"]
    except urllib.error.HTTPError as e:
        rec["status"] = f"http_{e.code}"; rec["answer"] = e.read().decode()[:500]
    except Exception as e:  # noqa: BLE001
        rec["status"] = "exception"; rec["answer"] = repr(e)[:500]
    rec["latency_s"] = round(time.time() - t0, 1)
    rec["correct"], rec["missing"] = score(rec["answer"], q["expect_all"]) if rec["status"] == "ok" else (False, q["expect_all"])
    return rec


def main():
    with Path(args.out).open("a") as f, ThreadPoolExecutor(max_workers=len(DBS)) as pool:
        for run in range(1, args.runs + 1):
            for q in QUESTIONS:
                for rec in pool.map(lambda db: ask(db, q), DBS):
                    rec["run"] = run
                    f.write(json.dumps(rec) + "\n"); f.flush()
                    print(f"run{run} {rec['id']:3} {rec['db']:24} {rec['status']:9} {'OK ' if rec['correct'] else 'BAD'} "
                          f"{rec['latency_s']:6}s  missing={rec['missing']}", flush=True)


if __name__ == "__main__":
    main()
