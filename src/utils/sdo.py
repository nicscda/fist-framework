from stix2 import CustomObject
from stix2.properties import ListProperty, ReferenceProperty, StringProperty


@CustomObject(
    "x-mitre-data-component",
    [
        ("name", StringProperty(required=True)),
        ("description", StringProperty()),
    ],
)
class MitreDataComponent(object):
    """Data component SDO, definition reference MITRE ATT&CK®."""

    pass


@CustomObject(
    "x-mitre-data-source",
    [
        ("name", StringProperty(required=True)),
        ("description", StringProperty()),
    ],
)
class MitreDataSource(object):
    """Data source SDO, definition reference MITRE ATT&CK®."""

    pass


@CustomObject(
    "x-mitre-tactic",
    [
        ("name", StringProperty(required=True)),
        ("description", StringProperty()),
    ],
)
class MitreTactic(object):
    """Tactic SDO, definition reference MITRE ATT&CK®."""

    pass


@CustomObject(
    "x-mitre-matrix",
    [
        ("name", StringProperty(required=True)),
        ("description", StringProperty(required=True)),
        (
            "tactic_refs",
            ListProperty(
                ReferenceProperty(valid_types=["x-mitre-tactic"]),
                default=[],
            ),
        ),
    ],
)
class MitreMatrix(object):
    """Matrix SDO, definition reference MITRE ATT&CK®."""

    pass
