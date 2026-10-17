"""Crosswalk between two cluster snapshots (old matcher run → new one).

For every old entity, where did its member records land under the new run?
Supports one-to-many (splits) and many-to-one (merges) by listing every new
entity that holds at least one of the old members.

Usage: uv run python scripts/crosswalk.py outputs/history/clusters.matcher-0.1.json outputs/clusters.json
"""

import json
import sys
from pathlib import Path


def main(old_path: str, new_path: str) -> None:
    old = json.loads(Path(old_path).read_text())
    new = json.loads(Path(new_path).read_text())

    member_to_new: dict[str, str] = {}
    for cluster in new["clusters"]:
        for member in cluster["members"]:
            member_to_new[member] = cluster["entity_id"]

    crosswalk = []
    splits, intact, shrunk = 0, 0, 0
    for cluster in old["clusters"]:
        landed: dict[str, list[str]] = {}
        orphans = []
        for member in cluster["members"]:
            target = member_to_new.get(member)
            if target is None:
                orphans.append(member)  # record no longer in any multi-record entity
            else:
                landed.setdefault(target, []).append(member)
        entry = {
            "old_entity_id": cluster["entity_id"],
            "new_entity_ids": sorted(landed.keys()),
            "orphaned_records": orphans,
        }
        crosswalk.append(entry)
        if len(landed) == 1 and not orphans:
            intact += 1
        elif len(landed) > 1:
            splits += 1
        else:
            shrunk += 1

    out = {
        "from_run": old["meta"]["run_id"],
        "to_run": new["meta"]["run_id"],
        "old_entities": len(old["clusters"]),
        "new_entities": len(new["clusters"]),
        "intact": intact,
        "split": splits,
        "shrunk_or_dissolved": shrunk,
        "entries": crosswalk,
    }
    out_path = Path("outputs") / "crosswalk.json"
    out_path.write_text(json.dumps(out, indent=1))
    print(f"{out['from_run']} → {out['to_run']}: {intact} intact, {splits} split, "
          f"{shrunk} shrunk/dissolved → {out_path}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
