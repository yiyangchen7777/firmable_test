"""Part 3 — entity identification across sources.

Stored truth is the pairwise LINK TABLE (append-only, with retraction records);
clusters are derived from it by union-find and saved as a versioned snapshot
(a cache, not truth). See docs/DESIGN.md "Part 3" for the full reasoning.

Matchers, strict to loose:
  1. ABN equality (both checksum-valid)      → link, confidence 0.98
  2. ACN equality (both true ACN claims)     → link, confidence 0.95
  3. exact normalised name + same state      → link, confidence 0.75
  4. fuzzy name similarity in the grey zone  → UNLINKED QUEUE, never auto-linked
Confidences are heuristic scores, not calibrated probabilities; the 50-link
hand-check measures what they are worth.

Hairball defence: identifier links propagate freely (same valid ABN is the same
entity by definition). A name link may attach records to a cluster but may NOT
bridge two clusters that each already contain different ABNs — such links go to
the conflict queue instead. Clusters over 10 records are flagged for review.
"""

import csv
import hashlib
import json
import random
from datetime import datetime, timezone

from rapidfuzz import fuzz

from .config import OUTPUTS, ROOT
from .names import name_key

# 0.2: identifier links are refused when either record's own country claim is
# non-AU. Measured on matcher-0.1: 19 of 50 hand-checked links were foreign
# parent companies carrying a local subsidiary's ABN (source-asserted), all
# with country_code us/ch in the raw rows. An Australian identifier on a
# non-Australian party is evidence of agency, not identity.
MATCHER_VERSION = "matcher-0.2"
ABN_CONFIDENCE = 0.98
ACN_CONFIDENCE = 0.95
NAME_CONFIDENCE = 0.75
FUZZY_QUEUE_BAND = (85, 100)  # similarity scores that land in the queue
MIN_NAME_KEY_LEN = 6  # "SMITH" alone is too generic to link on
CLUSTER_SIZE_FLAG = 10

def load_records(drop_source: str | None = None) -> dict[str, dict]:
    """One summary per observation record: identifiers, name keys, state."""
    records: dict[str, dict] = {}
    for path in sorted((OUTPUTS / "observations").glob("*.jsonl")):
        if drop_source is not None and path.stem == drop_source:
            continue
        for line in path.read_text().splitlines():
            obs = json.loads(line)
            key = f"{obs['source_id']}::{obs['source_record_id']}"
            summary = {
                "key": key, "source": obs["source_id"],
                "abn": None, "acn": None, "names": [], "state": None, "country": None,
            }
            for claim in obs["claims"]:
                if claim["field"] == "entity.abn":
                    summary["abn"] = claim["value"]
                elif claim["field"] == "entity.acn":
                    summary["acn"] = claim["value"]
                elif claim["field"] in ("entity.legal_name", "entity.trading_name"):
                    summary["names"].append(claim["value"])
                elif claim["field"] == "address.state":
                    summary["state"] = claim["value"]
                elif claim["field"] == "address.country":
                    country = str(claim["value"]).upper()
                    if country == "AUSTRALIA":  # sources spell it both ways
                        country = "AU"
                    summary["country"] = country
            records[key] = summary
    return records


def propose_links(records: dict[str, dict]) -> tuple[list[dict], list[dict]]:
    """Build candidate links (tiers 1-3) and the fuzzy queue (tier 4).

    Pairs are generated inside buckets (same ABN / ACN / name key), never by
    comparing everything with everything. Cross-source pairs only: linking two
    rows of the same source tells Part 3 nothing.
    """
    links: list[dict] = []
    queue: list[dict] = []
    seen_pairs: set[tuple[str, str]] = set()
    queued_pairs: set[tuple[str, str]] = set()

    def is_australian(rec: dict) -> bool:
        # no country claim counts as Australian (every source here is an AU register)
        return rec["country"] is None or rec["country"] == "AU"

    def add_to_queue(a: dict, b: dict, reason: str, evidence: str) -> None:
        pair = tuple(sorted([a["key"], b["key"]]))
        if pair in seen_pairs or pair in queued_pairs:
            return  # never queue a pair that is already linked, or queued twice
        queued_pairs.add(pair)
        queue.append({"record_a": pair[0], "record_b": pair[1], "reason": reason, "evidence": evidence})

    def add_link(a: dict, b: dict, confidence: float, evidence: str, tier: str) -> None:
        pair = tuple(sorted([a["key"], b["key"]]))
        if pair in seen_pairs or a["source"] == b["source"]:
            return
        if not is_australian(a) or not is_australian(b):
            # all tiers: a non-AU party record must not link into AU entities —
            # gating only the identifier tier would let the name tier relink
            # the same pair at lower confidence
            add_to_queue(
                a, b,
                "matcher-0.2 country gate: record belongs to a non-AU party "
                "(agency or parent, not identity); refused",
                f"{evidence} | countries {a['country']},{b['country']}",
            )
            return
        seen_pairs.add(pair)
        links.append(
            {"record_a": pair[0], "record_b": pair[1], "link_confidence": confidence,
             "evidence": evidence, "tier": tier}
        )

    # tier 1 + 2: identifier buckets
    by_abn: dict[str, list[dict]] = {}
    by_acn: dict[str, list[dict]] = {}
    for rec in records.values():
        if rec["abn"]:
            by_abn.setdefault(rec["abn"], []).append(rec)
        if rec["acn"]:
            by_acn.setdefault(rec["acn"], []).append(rec)
    for abn, bucket in by_abn.items():
        for i in range(len(bucket)):
            for j in range(i + 1, len(bucket)):
                add_link(bucket[i], bucket[j], ABN_CONFIDENCE, f"abn_exact:{abn}", "id")
    for acn, bucket in by_acn.items():
        for i in range(len(bucket)):
            for j in range(i + 1, len(bucket)):
                add_link(bucket[i], bucket[j], ACN_CONFIDENCE, f"acn_exact:{acn}", "id")

    # tier 3: exact name key + same state
    by_name: dict[str, list[dict]] = {}
    for rec in records.values():
        for name in rec["names"]:
            key = name_key(name)
            if len(key) >= MIN_NAME_KEY_LEN:
                by_name.setdefault(key, []).append(rec)
    for key, bucket in by_name.items():
        for i in range(len(bucket)):
            for j in range(i + 1, len(bucket)):
                a, b = bucket[i], bucket[j]
                if a["state"] and b["state"] and a["state"] == b["state"]:
                    add_link(a, b, NAME_CONFIDENCE, f"name_exact+state:{key}|{a['state']}", "name")
                elif a["key"] != b["key"] and a["source"] != b["source"]:
                    add_to_queue(
                        a, b,
                        "name matches but state missing or different; refused to link",
                        f"name_exact:{key} states={a['state']},{b['state']}",
                    )

    # tier 4: fuzzy names → queue only. Blocked by state + first letter to keep
    # the comparison count sane; this tier never links, it only shows our line.
    blocks: dict[tuple, list[tuple[str, dict]]] = {}
    for rec in records.values():
        for name in rec["names"]:
            key = name_key(name)
            if len(key) >= MIN_NAME_KEY_LEN and rec["state"]:
                blocks.setdefault((rec["state"], key[0]), []).append((key, rec))
    low, high = FUZZY_QUEUE_BAND
    for block in blocks.values():
        if len(block) > 400:  # a block this big is all-against-all noise; skip
            continue
        for i in range(len(block)):
            for j in range(i + 1, len(block)):
                key_a, rec_a = block[i]
                key_b, rec_b = block[j]
                if key_a == key_b or rec_a["source"] == rec_b["source"]:
                    continue
                score = fuzz.token_sort_ratio(key_a, key_b)
                if low <= score < high:
                    add_to_queue(
                        rec_a, rec_b,
                        f"fuzzy name similarity {score:.0f} in grey zone [{low},{high}); deliberately not linked",
                        f"fuzzy:{key_a!r} vs {key_b!r}",
                    )
    return links, queue


class UnionFind:
    """Textbook union-find: find the group's root, merge two groups."""

    def __init__(self) -> None:
        self.parent: dict[str, str] = {}

    def find(self, key: str) -> str:
        self.parent.setdefault(key, key)
        root = key
        while self.parent[root] != root:
            root = self.parent[root]
        while self.parent[key] != root:  # path compression, one plain loop
            self.parent[key], key = root, self.parent[key]
        return root

    def union(self, a: str, b: str) -> None:
        self.parent[self.find(a)] = self.find(b)


def derive_clusters(records: dict[str, dict], links: list[dict]) -> tuple[list[dict], list[dict], list[dict]]:
    """Union-find with the bridge defence. Returns (accepted, conflicts, clusters)."""
    uf = UnionFind()
    cluster_abns: dict[str, set[str]] = {}  # root -> ABNs inside that cluster

    def abns_of(root: str) -> set[str]:
        return cluster_abns.setdefault(root, set())

    for rec in records.values():
        root = uf.find(rec["key"])
        if rec["abn"]:
            abns_of(root).add(rec["abn"])

    accepted: list[dict] = []
    conflicts: list[dict] = []
    ordered = sorted(links, key=lambda l: -l["link_confidence"])  # ids first
    for link in ordered:
        root_a = uf.find(link["record_a"])
        root_b = uf.find(link["record_b"])
        if root_a == root_b:
            accepted.append(link)
            continue
        abns_a, abns_b = abns_of(root_a), abns_of(root_b)
        if abns_a and abns_b and not (abns_a & abns_b):
            # NO link may weld two clusters anchored to different ABNs — not a
            # name match, and not a shared ACN either (a reused or mistyped
            # secondary identifier must surface as a conflict, not a merge)
            conflicts.append(
                {"record_a": link["record_a"], "record_b": link["record_b"],
                 "reason": f"{link['tier']} link would bridge clusters with conflicting ABNs; refused",
                 "evidence": f"{link['evidence']} | abns {sorted(abns_a)[:3]} vs {sorted(abns_b)[:3]}"}
            )
            continue
        merged = abns_a | abns_b
        uf.union(link["record_a"], link["record_b"])
        cluster_abns[uf.find(link["record_a"])] = merged
        accepted.append(link)

    members: dict[str, list[str]] = {}
    for rec in records.values():
        members.setdefault(uf.find(rec["key"]), []).append(rec["key"])
    link_conf: dict[tuple[str, str], float] = {}
    for link in accepted:
        link_conf[(link["record_a"], link["record_b"])] = link["link_confidence"]

    clusters = []
    for group in members.values():
        if len(group) < 2:
            continue  # singletons are not entities we linked
        group.sort()
        support = min(
            (l["link_confidence"] for l in accepted
             if l["record_a"] in group and l["record_b"] in group),
            default=None,
        )
        clusters.append(
            {"entity_id": group[0],  # a label for THIS run only, not a durable id
             "members": group,
             "sources": sorted({m.split("::")[0] for m in group}),
             "cluster_support": support,
             "flag_large": len(group) > CLUSTER_SIZE_FLAG}
        )
    clusters.sort(key=lambda c: c["entity_id"])
    return accepted, conflicts, clusters


def run_resolve(drop_source: str | None = None, handcheck_seed: int = 99) -> dict:
    records = load_records(drop_source)
    links, queue = propose_links(records)
    accepted, conflicts, clusters = derive_clusters(records, links)

    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    # a fingerprint of WHICH records went in (keys, not contents) — enough to
    # tell two runs apart, honestly named
    input_keys_hash = hashlib.sha256(
        "".join(sorted(records.keys())).encode()
    ).hexdigest()[:12]
    run_id = f"resolve-{created_at.replace(':', '').replace('-', '')[:15]}-{input_keys_hash}"
    meta = {
        "run_id": run_id, "matcher_version": MATCHER_VERSION, "created_at": created_at,
        "input_records": len(records), "input_keys_hash": input_keys_hash,
        "thresholds": {"abn": ABN_CONFIDENCE, "acn": ACN_CONFIDENCE, "name_exact_state": NAME_CONFIDENCE,
                       "fuzzy_queue_band": list(FUZZY_QUEUE_BAND)},
        "drop_source": drop_source,
    }

    suffix = f".without-{drop_source}" if drop_source else ""
    out = OUTPUTS

    # the brief's link tuple includes the canonical entity key: stamp each link
    # with the entity its records land in under THIS run (a per-run label —
    # the cluster snapshot is the cache it comes from)
    entity_of: dict[str, str] = {}
    for cluster in clusters:
        for member in cluster["members"]:
            entity_of[member] = cluster["entity_id"]
    with (out / f"links{suffix}.jsonl").open("w") as fh:
        for link in accepted:
            fh.write(json.dumps(link | {
                "canonical_entity_key": entity_of.get(link["record_a"], link["record_a"]),
                "run_id": run_id, "matcher_version": MATCHER_VERSION,
                "created_at": created_at,
            }, sort_keys=True) + "\n")
    with (out / f"unlinked{suffix}.jsonl").open("w") as fh:
        for item in queue + conflicts:
            fh.write(json.dumps(item | {"run_id": run_id}, sort_keys=True) + "\n")
    (out / f"clusters{suffix}.json").write_text(
        json.dumps({"meta": meta, "note": "derived cache, not truth; recompute from links",
                    "clusters": clusters}, indent=1)
    )

    handcheck_path = ROOT / "review" / "part3_handcheck.csv"
    if drop_source is None and not handcheck_path.exists():
        # hand-check sheet only for the main run — and never overwrite one that
        # may already carry human verdicts (delete the file to resample)
        review_dir = ROOT / "review"
        review_dir.mkdir(exist_ok=True)
        sample = random.Random(handcheck_seed).sample(accepted, min(50, len(accepted)))
        with (review_dir / "part3_handcheck.csv").open("w", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=[
                "record_a", "record_b", "link_confidence", "tier", "evidence", "correct", "note"])
            writer.writeheader()
            for link in sample:
                writer.writerow({k: link[k] for k in ("record_a", "record_b", "link_confidence", "tier", "evidence")}
                                | {"correct": "", "note": ""})

    multi_source = [c for c in clusters if len(c["sources"]) > 1]
    print(f"records: {len(records)} | links accepted: {len(accepted)} "
          f"(queue: {len(queue)}, conflicts: {len(conflicts)})")
    print(f"clusters: {len(clusters)} | spanning >1 source: {len(multi_source)} "
          f"| flagged large: {sum(1 for c in clusters if c['flag_large'])}")
    return {"records": len(records), "links": len(accepted), "queue": len(queue),
            "conflicts": len(conflicts), "clusters": len(clusters),
            "multi_source_clusters": len(multi_source)}
