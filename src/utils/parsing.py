import json
import re
import uuid
from collections import defaultdict
from datetime import datetime
from functools import cache, cached_property
from operator import itemgetter
from typing import TypeVar, cast

from stix2 import (
    TLP_WHITE,
    AttackPattern,
    Bundle,
    CourseOfAction,
    Identity,
    MarkingDefinition,
    Note,
    Relationship,
    StatementMarking,
    Tool,
)
from stix2.base import SCO_DET_ID_NAMESPACE, _STIXBase
from stix2.canonicalization.Canonicalize import canonicalize

from ..models import Individual, Manifest, Organization
from .config import VERSION, get_settings
from .functions import to_kebab_case, to_snake_case
from .sdo import MitreDataComponent, MitreDataSource, MitreMatrix, MitreTactic
from .vocabularies import IDENTITY_CLASS_ORGANIZATION

T = TypeVar("T", bound=_STIXBase, covariant=True)


class Stix:

    def __init__(self, manifest: Manifest):
        self.manifest = manifest
        self.X_SOURCE_ID = to_snake_case(f"x_{get_settings().project_name}_id")
        self.DEFAULT_AUTHOR = Identity(
            id=self.generate_id(
                Identity,
                name=get_settings().author.name,
                **{self.X_SOURCE_ID: get_settings().author.alias},
            ),
            name=get_settings().author.name,
            contact_information=get_settings().author.email,
            identity_class=IDENTITY_CLASS_ORGANIZATION,
            confidence=100,
            created=self.manifest.created,
            modified=self.manifest.modified,
        )

    @staticmethod
    def generate_id(tp: type[T], *, name: str | None = None, **kwargs):
        """Generates an ID based on the given type and key attributes."""
        if name:
            kwargs.setdefault("name", name.lower().strip())
        return f"{tp._type}--{uuid.uuid5(SCO_DET_ID_NAMESPACE, canonicalize(kwargs, utf8=False))}"

    @cached_property
    def marking_definitions(self):
        """Custom Marking references, including TLP and our Copyright."""
        now_year = datetime.now().year
        start_year = min(
            (
                ts.year
                for ts in {
                    self.manifest.created,
                    self.manifest.modified,
                }
                if ts
            ),
            default=now_year,
        )
        end_year = max(
            (
                ts.year
                for ts in {
                    self.manifest.created,
                    self.manifest.modified,
                }
                if ts
            ),
            default=now_year,
        )
        return [
            # [TRAFFIC LIGHT PROTOCOL (TLP)](https://www.first.org/tlp)
            TLP_WHITE,
            # Copyright / License
            MarkingDefinition(
                id=self.generate_id(
                    MarkingDefinition,
                    definition=(
                        # Contain the complete legal language
                        definition := StatementMarking(
                            statement=(
                                f"Copyright © {start_year if start_year == end_year else f"{start_year}-{end_year}"}"
                                f" {self.DEFAULT_AUTHOR["name"]}"
                            )
                        )
                    ).serialize(),
                    definition_type=(definition_type := "statement"),
                ),
                definition=definition,
                definition_type=definition_type,
                # Do not use `self._get_created_by_ref` which will cause an infinite loop.
                created_by_ref=self.DEFAULT_AUTHOR["id"],
                created=self.manifest.created,
            ),
        ]

    @cached_property
    def identities(self):
        """Individual and organizational contributors' identities."""
        return [
            Identity(
                id=self.generate_id(
                    Identity,
                    name=contributor.name,
                    **{self.X_SOURCE_ID: contributor.id},
                ),
                name=contributor.name,
                description=contributor.description,
                external_references=contributor.model_dump(
                    mode="json", include=(field := "external_references")
                )[field],
                identity_class=contributor.identity_class,
                roles=contributor.roles,
                sectors=contributor.sectors,
                contact_information=contributor.contact_information,
                object_marking_refs=self.marking_definitions,
                # Do not use `self._get_created_by_ref` which will cause an infinite loop.
                created_by_ref=self.DEFAULT_AUTHOR["id"],
                created=contributor.created,
                modified=contributor.modified,
                revoked=contributor.revoked,
                confidence=100,
                custom_properties={
                    "x_opencti_aliases": [contributor.id],
                    **(
                        {
                            "x_opencti_firstname": contributor.firstname,
                            "x_opencti_lastname": contributor.lastname,
                        }
                        if isinstance(contributor, Individual)
                        else {"x_opencti_reliability": contributor.organization_type}
                    ),
                    "x_opencti_reliability": contributor.reliability,
                    self.X_SOURCE_ID: contributor.id,
                },
            )
            for contributor in self.manifest.contributors
        ]

    @cached_property
    def attack_patterns(self):
        kill_chain_name = to_kebab_case(get_settings().project_name)
        return [
            AttackPattern(
                allow_custom=True,
                id=self.generate_id(
                    AttackPattern,
                    **{self.X_SOURCE_ID: technique.id},
                ),
                name=technique.name,
                description=technique.description,
                external_references=technique.model_dump(
                    mode="json", include=(field := "external_references")
                )[field],
                aliases=[technique.id],
                object_marking_refs=self.marking_definitions,
                created_by_ref=self._get_created_by_ref(*technique.contributors),
                created=technique.created,
                modified=technique.modified,
                confidence=100,
                kill_chain_phases=[
                    {
                        "kill_chain_name": kill_chain_name,
                        "phase_name": (
                            tactic.name
                            if (tactic := self.manifest.get_tactic(technique.tactic_id))
                            else technique.tactic_id
                        ),
                        "x_opencti_order": tactic.order,
                    }
                ],
                revoked=technique.revoked,
                custom_properties={
                    "x_mitre_contributors": list(
                        set(
                            self._get_contributor_name(contributor)
                            for contributor in technique.external_contributors
                        )
                    ),
                    "x_mitre_detection": technique.detection.description,
                    "x_mitre_id": technique.id,
                    "x_mitre_is_subtechnique": bool(technique.parent_id),
                    "x_mitre_permissions_required": technique.permissions,
                    "x_mitre_platforms": technique.platforms,
                    self.X_SOURCE_ID: technique.id,
                },
            )
            for technique in self.manifest.techniques
        ]

    @cached_property
    def course_of_actions(self):
        return [
            CourseOfAction(
                id=self.generate_id(
                    CourseOfAction,
                    **{self.X_SOURCE_ID: mitigation.id},
                ),
                name=mitigation.name,
                description=mitigation.description,
                external_references=mitigation.model_dump(
                    mode="json", include=(field := "external_references")
                )[field],
                object_marking_refs=self.marking_definitions,
                confidence=100,
                created_by_ref=self._get_created_by_ref(*mitigation.contributors),
                created=mitigation.created,
                modified=mitigation.modified,
                revoked=mitigation.revoked,
                custom_properties={
                    "x_mitre_contributors": list(
                        set(
                            self._get_contributor_name(contributor)
                            for contributor in mitigation.external_contributors
                        )
                    ),
                    self.X_SOURCE_ID: mitigation.id,
                },
            )
            for mitigation in self.manifest.mitigations
        ]

    @cached_property
    def tools(self):
        kill_chain_name = to_kebab_case(get_settings().project_name)
        return [
            Tool(
                allow_custom=True,
                id=self.generate_id(
                    Tool,
                    **{self.X_SOURCE_ID: tool.id},
                ),
                name=tool.name,
                description=tool.description,
                external_references=tool.model_dump(
                    mode="json", include=(field := "external_references")
                )[field],
                object_marking_refs=self.marking_definitions,
                confidence=100,
                created_by_ref=self._get_created_by_ref(*tool.contributors),
                created=tool.created,
                modified=tool.modified,
                tool_types=tool.tool_types,
                tool_version=tool.tool_version,
                kill_chain_phases=[
                    {
                        "kill_chain_name": kill_chain_name,
                        "phase_name": (
                            tactic.name
                            if (tactic := self.manifest.get_tactic(technique.tactic_id))
                            else technique.tactic_id
                        ),
                        "x_opencti_order": tactic.order,
                    }
                    for technique in self.manifest.get_techniques(
                        tool_id=tool.id, include_meta=False
                    )
                ],
                revoked=tool.revoked,
                custom_properties={
                    "x_mitre_contributors": list(
                        set(
                            self._get_contributor_name(contributor)
                            for contributor in tool.external_contributors
                        )
                    ),
                    "x_mitre_platforms": tool.platforms,
                    self.X_SOURCE_ID: tool.id,
                },
            )
            for tool in self.manifest.tools
        ]

    @cached_property
    def notes(self):
        return [
            Note(
                allow_custom=True,
                id=self.generate_id(
                    Note,
                    **{self.X_SOURCE_ID: note.id},
                ),
                abstract=note.name,
                content=note.description,
                note_types=note.note_types,
                authors=[
                    author_ref
                    for contributor in note.contributors
                    if (author_ref := self._get_contributor_ref(contributor))
                ],
                object_refs=[
                    object_ref
                    for related_id in note.related_ids
                    if (object_ref := self._get_object_ref(related_id))
                ],
                external_references=note.model_dump(
                    mode="json", include=(field := "external_references")
                )[field],
                object_marking_refs=self.marking_definitions,
                confidence=100,
                created_by_ref=self._get_created_by_ref(*note.contributors),
                created=note.created,
                modified=note.modified,
                revoked=note.revoked,
                custom_properties={
                    "x_mitre_contributors": list(
                        set(
                            self._get_contributor_name(contributor)
                            for contributor in note.external_contributors
                        )
                    ),
                    self.X_SOURCE_ID: note.id,
                },
            )
            for note in self.manifest.notes
        ]

    @cached_property
    def mitre_data_components(self):
        return [
            MitreDataComponent(
                id=self.generate_id(
                    MitreDataComponent,
                    **{self.X_SOURCE_ID: component.id},
                ),
                name=component.name,
                description=component.description,
                external_references=component.model_dump(
                    mode="json", include=(field := "external_references")
                )[field],
                object_marking_refs=self.marking_definitions,
                confidence=100,
                created_by_ref=self._get_created_by_ref(*component.contributors),
                created=component.created,
                modified=component.modified,
                revoked=component.revoked,
                custom_properties={
                    "x_mitre_contributors": list(
                        set(
                            self._get_contributor_name(contributor)
                            for contributor in component.external_contributors
                        )
                    ),
                    "x_mitre_data_source_ref": self._get_source_ref(
                        component.parent_id
                    ),
                    self.X_SOURCE_ID: component.id,
                },
            )
            for component in self.manifest.detection_components
        ]

    @cached_property
    def mitre_data_sources(self):
        return [
            MitreDataSource(
                id=self.generate_id(
                    MitreDataSource,
                    **{self.X_SOURCE_ID: source.id},
                ),
                name=source.name,
                description=source.description,
                external_references=source.model_dump(
                    mode="json", include=(field := "external_references")
                )[field],
                object_marking_refs=self.marking_definitions,
                confidence=100,
                created_by_ref=self._get_created_by_ref(*source.contributors),
                created=source.created,
                modified=source.modified,
                revoked=source.revoked,
                custom_properties={
                    "x_mitre_collection_layers": source.collection_layers,
                    "x_mitre_contributors": list(
                        set(
                            self._get_contributor_name(contributor)
                            for contributor in source.external_contributors
                        )
                    ),
                    "x_mitre_platforms": source.platforms,
                    self.X_SOURCE_ID: source.id,
                },
            )
            for source in self.manifest.detection_sources
        ]

    @cached_property
    def mitre_tactics(self):
        return [
            MitreTactic(
                id=self.generate_id(
                    MitreTactic,
                    **{self.X_SOURCE_ID: tactic.id},
                ),
                name=tactic.name,
                description=tactic.description,
                external_references=tactic.model_dump(
                    mode="json", include=(field := "external_references")
                )[field],
                object_marking_refs=self.marking_definitions,
                confidence=100,
                created_by_ref=self._get_created_by_ref(*tactic.contributors),
                created=tactic.created,
                modified=tactic.modified,
                revoked=tactic.revoked,
                custom_properties={
                    "x_mitre_contributors": list(
                        set(
                            self._get_contributor_name(contributor)
                            for contributor in tactic.external_contributors
                        )
                    ),
                    "x_mitre_shortname": tactic.name,
                    self.X_SOURCE_ID: tactic.id,
                },
            )
            for tactic in self.manifest.tactics
        ]

    @cached_property
    def mitre_matrix(self):
        kill_chain_name = to_kebab_case(get_settings().project_name)
        return [
            MitreMatrix(
                allow_custom=True,
                id=self.generate_id(
                    MitreMatrix,
                    **{self.X_SOURCE_ID: kill_chain_name},
                ),
                name=get_settings().project_name,
                description=self.manifest.description,
                tactic_refs=self.mitre_tactics,
                object_marking_refs=self.marking_definitions,
                confidence=100,
                # Do not use `self._get_created_by_ref` which will cause an infinite loop.
                created_by_ref=self.DEFAULT_AUTHOR["id"],
                created=self.manifest.created,
                modified=self.manifest.modified,
                custom_properties={
                    to_snake_case(f"x_{get_settings().project_name}_version"): VERSION,
                    self.X_SOURCE_ID: kill_chain_name,
                },
            )
        ] + [
            MitreMatrix(
                allow_custom=True,
                id=self.generate_id(
                    MitreMatrix,
                    **{self.X_SOURCE_ID: phase.id},
                ),
                name=phase.name,
                description=phase.description,
                tactic_refs=[
                    tactic_ref
                    for tactic in self.manifest.get_tactics(phase.id)
                    if (tactic_ref := self._get_tactic_ref(tactic.id))
                ],
                object_marking_refs=self.marking_definitions,
                confidence=100,
                created_by_ref=self._get_created_by_ref(*phase.contributors),
                created=phase.created,
                modified=phase.modified,
                custom_properties={
                    "x_mitre_contributors": list(
                        set(
                            self._get_contributor_name(contributor)
                            for contributor in phase.external_contributors
                        )
                    ),
                    self.X_SOURCE_ID: phase.id,
                },
            )
            for phase in self.manifest.phases
        ]

    @cached_property
    def relationships(self):
        relationships: list[Relationship] = []  # type: ignore[annotation-unchecked]
        for technique in self.manifest.techniques:
            if attack_pattern_ref := self._get_technique_ref(technique.id):
                relationships.extend(
                    Relationship(
                        id=self.generate_id(
                            Relationship,
                            relationship_type=(relationship_type := "uses"),
                            source_ref=tool_id,
                            target_ref=attack_pattern_ref,
                        ),
                        source_ref=tool_id,
                        target_ref=attack_pattern_ref,
                        description=e.description,
                        relationship_type=relationship_type,
                        created_by_ref=self._get_created_by_ref(
                            *technique.contributors
                        ),
                        created=technique.created,
                        modified=technique.modified,
                        revoked=technique.revoked,
                        object_marking_refs=self.marking_definitions,
                    )
                    for e in technique.tools
                    if (tool_id := self._get_tool_ref(e.id))
                )
                relationships.extend(
                    Relationship(
                        id=self.generate_id(
                            Relationship,
                            relationship_type=(relationship_type := "mitigates"),
                            source_ref=course_of_action_ref,
                            target_ref=attack_pattern_ref,
                        ),
                        source_ref=course_of_action_ref,
                        target_ref=attack_pattern_ref,
                        description=e.description,
                        relationship_type=relationship_type,
                        created_by_ref=self._get_created_by_ref(
                            *technique.contributors
                        ),
                        created=technique.created,
                        modified=technique.modified,
                        revoked=technique.revoked,
                        object_marking_refs=self.marking_definitions,
                    )
                    for e in technique.mitigations
                    if (course_of_action_ref := self._get_mitigation_ref(e.id))
                )
                if technique.detection:
                    relationships.extend(
                        Relationship(
                            allow_custom=True,
                            id=self.generate_id(
                                Relationship,
                                relationship_type=(relationship_type := "detects"),
                                source_ref=data_component_ref,
                                target_ref=attack_pattern_ref,
                            ),
                            source_ref=data_component_ref,
                            target_ref=attack_pattern_ref,
                            relationship_type=relationship_type,
                            description=e.description,
                            created_by_ref=self._get_created_by_ref(
                                *technique.contributors
                            ),
                            created=technique.created,
                            modified=technique.modified,
                            revoked=technique.revoked,
                            object_marking_refs=self.marking_definitions,
                        )
                        for e in technique.detection.items
                        if (data_component_ref := self._get_component_ref(e.id))
                    )
                if technique.parent_id and (
                    parent_attack_pattern_ref := self._get_technique_ref(
                        technique.parent_id
                    )
                ):
                    relationships.append(
                        Relationship(
                            id=self.generate_id(
                                Relationship,
                                relationship_type=(
                                    relationship_type := "subtechnique-of"
                                ),
                                source_ref=attack_pattern_ref,
                                target_ref=parent_attack_pattern_ref,
                            ),
                            source_ref=attack_pattern_ref,
                            target_ref=parent_attack_pattern_ref,
                            relationship_type=relationship_type,
                            created_by_ref=self._get_created_by_ref(
                                *technique.contributors
                            ),
                            created=technique.created,
                            modified=technique.modified,
                            revoked=technique.revoked,
                            object_marking_refs=self.marking_definitions,
                        )
                    )

        return relationships

    @cache
    def _get_component_ref(self, object_id: str):
        return next(
            (
                data_component["id"]
                for data_component in self.mitre_data_components
                if object_id == data_component[self.X_SOURCE_ID]
            ),
            None,
        )

    @cache
    def _get_contributor_name(self, contributor: str):
        """Returns the first matching identity name.

        If not found return the original input.
        """
        return next(
            (
                cast(str, identity["name"])
                for identity in self.identities
                if contributor == identity[self.X_SOURCE_ID]
                or contributor == identity["name"]
            ),
            contributor,
        )

    @cache
    def _get_contributor_ref(self, object_id: str):
        return next(
            (
                identity["id"]
                for identity in self.identities
                if object_id == identity[self.X_SOURCE_ID]
            ),
            None,
        )

    @cache
    def _get_created_by_ref(self, *contributors: str):
        """Returns the first matching contributors as the author.

        If not found return the default value.
        """
        return next(
            (
                identity["id"]
                for contributor in contributors
                for identity in self.identities
                if contributor == identity[self.X_SOURCE_ID]
                or contributor == identity["name"]
            ),
            self.DEFAULT_AUTHOR["id"],
        )

    @cache
    def _get_mitigation_ref(self, object_id: str):
        return next(
            (
                course_of_action["id"]
                for course_of_action in self.course_of_actions
                if object_id == course_of_action[self.X_SOURCE_ID]
            ),
            None,
        )

    @cache
    def _get_object_ref(self, object_id: str):
        patterns, funcs = [], {}
        for t in self.manifest.mapping().values():
            if callable(func := getattr(self, f"_get_{t._type}_ref", None)):
                patterns.append(rf"(?P<{t._type}>{t._pattern})")
                funcs[t._type] = func
        else:
            return (
                next(
                    (funcs[k](object_id) for k, v in m.groupdict().items() if v),
                    None,
                )
                if patterns and (m := re.search("|".join(patterns), object_id))
                else None
            )

    @cache
    def _get_source_ref(self, object_id: str):
        return next(
            (
                data_source["id"]
                for data_source in self.mitre_data_sources
                if object_id == data_source[self.X_SOURCE_ID]
            ),
            None,
        )

    @cache
    def _get_phase_ref(self, object_id: str):
        return next(
            (
                tactic["id"]
                for tactic in self.mitre_matrix
                if object_id == tactic[self.X_SOURCE_ID]
            ),
            None,
        )

    @cache
    def _get_tactic_ref(self, object_id: str):
        return next(
            (
                tactic["id"]
                for tactic in self.mitre_tactics
                if object_id == tactic[self.X_SOURCE_ID]
            ),
            None,
        )

    @cache
    def _get_technique_ref(self, object_id: str):
        return next(
            (
                attack_pattern["id"]
                for attack_pattern in self.attack_patterns
                if object_id == attack_pattern[self.X_SOURCE_ID]
            ),
            None,
        )

    @cache
    def _get_tool_ref(self, object_id: str):
        return next(
            (tool["id"] for tool in self.tools if object_id == tool[self.X_SOURCE_ID]),
            None,
        )


class Parser:

    def __init__(self, manifest: Manifest):
        self.manifest = manifest
        self.stix = Stix(self.manifest)

    def to_stix(self) -> str:
        """Fetch JSON-formatted SITX bundle objects file.

        :returns: Path of bundle file.
        """
        bundle = Bundle(
            *self.stix.marking_definitions,
            *self.stix.identities,
            *self.stix.attack_patterns,
            *self.stix.course_of_actions,
            *self.stix.tools,
            *self.stix.notes,
            *self.stix.relationships,
            *self.stix.mitre_data_components,
            *self.stix.mitre_data_sources,
            *self.stix.mitre_tactics,
            *self.stix.mitre_matrix,
            *(
                []
                if any(
                    identity["id"] == self.stix.DEFAULT_AUTHOR["id"]
                    for identity in self.stix.identities
                )
                else [self.stix.DEFAULT_AUTHOR]
            ),
            allow_custom=True,
        )

        filepath = get_settings().artifact_path
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(bundle.serialize(pretty=False, ensure_ascii=False, indent=4))

        return filepath

    def to_json(self):  # type: ignore[annotation-unchecked]
        """Fetch Markdown-formatted documents of the framework according to the bundle data.

        :returns: Storage path and content of each file.
        """
        grouped: defaultdict[str, list] = defaultdict(list)
        for k, v in Manifest.mapping().items():
            is_identity = v._group in (Individual._group, Organization._group)
            grouped[v._group].extend(
                {"type": v._type}
                | e.model_dump(
                    mode="json",
                    by_alias=True,
                    context={"as_relative_url": True, "exclude_self": True},
                )
                for e in cast(list, getattr(self.manifest, k))
                if isinstance(e, v)
                and (e.id != get_settings().author.alias if is_identity else True)
            )

        for group, items in grouped.items():
            filepath = get_settings().get_file_path(f"{group}.json")
            filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(
                    sorted(items, key=itemgetter("id")), f, ensure_ascii=False, indent=4
                )

        return get_settings().get_file_path()
