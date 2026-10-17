"""Resolver tests: name normalisation, matching tiers, the bridge defence."""

from firm.resolve import UnionFind, derive_clusters, name_key, propose_links


def rec(key, source, abn=None, acn=None, names=(), state=None):
    return {"key": key, "source": source, "abn": abn, "acn": acn,
            "names": list(names), "state": state}


def test_name_key_strips_suffixes_and_punctuation():
    assert name_key("Example Charity Ltd.") == "EXAMPLE CHARITY"
    assert name_key("J & M HOLDINGS PTY LTD") == "J M HOLDINGS"
    assert name_key("ACME   Proprietary Limited") == "ACME"


def test_abn_links_and_same_source_excluded():
    records = {r["key"]: r for r in [
        rec("a::1", "a", abn="51824753556", names=["Example Charity Ltd"]),
        rec("b::1", "b", abn="51824753556", names=["EXAMPLE CHARITY LIMITED"]),
        rec("a::2", "a", abn="51824753556"),  # same source as a::1 → no link
    ]}
    links, queue = propose_links(records)
    pairs = {(l["record_a"], l["record_b"]) for l in links}
    assert ("a::1", "b::1") in pairs
    assert all("a::2" not in p or "a::1" not in p for p in pairs)


def test_exact_name_needs_same_state_else_queued():
    records = {r["key"]: r for r in [
        rec("a::1", "a", names=["Sunrise Bakery Pty Ltd"], state="VIC"),
        rec("b::1", "b", names=["SUNRISE BAKERY"], state="VIC"),
        rec("c::1", "c", names=["Sunrise Bakery"], state="QLD"),
    ]}
    links, queue = propose_links(records)
    assert any(l["tier"] == "name" and {"a::1", "b::1"} == {l["record_a"], l["record_b"]} for l in links)
    # the QLD one matches by name but not state → refused into the queue
    assert any("c::1" in (q["record_a"], q["record_b"]) for q in queue)
    assert not any("c::1" in (l["record_a"], l["record_b"]) for l in links)


def test_bridge_defence_blocks_conflicting_abns():
    # two clusters anchored on different ABNs + a name link trying to weld them
    records = {r["key"]: r for r in [
        rec("a::1", "a", abn="51824753556", names=["Smith Plumbing"], state="NSW"),
        rec("b::1", "b", abn="51824753556", names=["Smith Plumbing Pty Ltd"], state="NSW"),
        rec("c::1", "c", abn="53004085616", names=["Smith Plumbing"], state="NSW"),
    ]}
    links, _ = propose_links(records)
    accepted, conflicts, clusters = derive_clusters(records, links)
    # the name link a::1↔c::1 (or b::1↔c::1) must be refused
    assert len(conflicts) >= 1
    assert "conflicting ABNs" in conflicts[0]["reason"]
    # c::1 stays outside the 51824753556 cluster
    for cluster in clusters:
        if "a::1" in cluster["members"]:
            assert "c::1" not in cluster["members"]


def test_name_link_attaches_record_without_abn():
    records = {r["key"]: r for r in [
        rec("a::1", "a", abn="51824753556", names=["Sunrise Bakery"], state="VIC"),
        rec("b::1", "b", names=["SUNRISE BAKERY PTY LTD"], state="VIC"),  # no ABN
    ]}
    links, _ = propose_links(records)
    accepted, conflicts, clusters = derive_clusters(records, links)
    assert conflicts == []
    assert any(set(c["members"]) == {"a::1", "b::1"} for c in clusters)


def test_union_find_basics():
    uf = UnionFind()
    uf.union("x", "y")
    uf.union("y", "z")
    assert uf.find("x") == uf.find("z")
    assert uf.find("w") == "w"
