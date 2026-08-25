"""Influence network with as_of snapshot support."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from .models import Person, RoleEvent, InfluenceEdge, NetworkSnapshot, Evidence


class InfluenceNetwork:
    """In-memory + file-backed influence network.

    Always query through snapshot(as_of=...) so historical analysis
    cannot see future roles or edges.
    """

    def __init__(self) -> None:
        self.persons: dict[str, Person] = {}
        self.roles: list[RoleEvent] = []
        self.edges: list[InfluenceEdge] = []
        self.evidence: dict[str, Evidence] = {}

    def add_person(self, person: Person) -> None:
        self.persons[person.person_id] = person

    def add_role(self, role: RoleEvent) -> None:
        self.roles.append(role)

    def add_edge(self, edge: InfluenceEdge) -> None:
        self.edges.append(edge)

    def add_evidence(self, evidence: Evidence) -> None:
        self.evidence[evidence.evidence_id] = evidence

    def snapshot(self, as_of: str, snapshot_id: str | None = None) -> NetworkSnapshot:
        active_roles = [r for r in self.roles if r.is_active_as_of(as_of)]
        active_person_ids = {r.person_id for r in active_roles}
        persons = [self.persons[pid] for pid in active_person_ids if pid in self.persons]
        for p in self.persons.values():
            if p.person_id not in active_person_ids:
                pass
        active_edges = [
            e for e in self.edges
            if e.is_valid_as_of(as_of)
            and e.from_person_id in active_person_ids
            and e.to_person_id in active_person_ids
        ]
        evidence_ids = sorted({
            *(eid for e in active_edges for eid in e.evidence_ids),
        })
        sid = snapshot_id or f"net-{as_of}"
        return NetworkSnapshot(
            snapshot_id=sid,
            as_of=as_of,
            persons=persons,
            roles=active_roles,
            edges=active_edges,
            evidence_ids=evidence_ids,
        )

    def load_from_json(self, path: str | Path) -> None:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        for p in data.get("persons", []):
            self.add_person(Person(**p))
        for r in data.get("roles", []):
            self.add_role(RoleEvent(**r))
        for e in data.get("edges", []):
            self.add_edge(InfluenceEdge(**e))
        for ev in data.get("evidence", []):
            self.add_evidence(Evidence(**ev))

    def save_to_json(self, path: str | Path) -> None:
        payload = {
            "persons": [p.as_dict() for p in self.persons.values()],
            "roles": [r.as_dict() for r in self.roles],
            "edges": [e.as_dict() for e in self.edges],
            "evidence": [e.as_dict() for e in self.evidence.values()],
        }
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
