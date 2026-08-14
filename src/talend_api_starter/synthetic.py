"""Clearly synthetic Talend fixtures used by the offline demo and tests."""

from __future__ import annotations

from pathlib import Path

SYNTHETIC_PROPERTIES_NAME = "SyntheticCustomers_0.1.properties"
SYNTHETIC_ITEM_NAME = "SyntheticCustomers_0.1.item"

SYNTHETIC_PROPERTIES = b"""<?xml version="1.0" encoding="UTF-8"?>
<xmi:XMI xmlns:xmi="http://www.omg.org/XMI"
         xmlns:TalendProperties="http://www.talend.org/properties">
  <TalendProperties:Property xmi:id="_synthetic_property"
                             id="_synthetic_public_id"
                             label="SyntheticCustomers"
                             version="0.1"
                             statusCode="DEV"
                             item="_synthetic_process_item" />
  <TalendProperties:ProcessItem xmi:id="_synthetic_process_item"
                                property="_synthetic_property">
    <process href="SyntheticCustomers_0.1.item#/" />
  </TalendProperties:ProcessItem>
</xmi:XMI>
"""

SYNTHETIC_ITEM = b"""<?xml version="1.0" encoding="UTF-8"?>
<talendfile:ProcessType
    xmlns:talendfile="platform:/resource/org.talend.model/model/TalendFile.xsd">
  <node componentName="tFixedFlowInput" componentVersion="0.102">
    <elementParameter field="TEXT" name="UNIQUE_NAME" value="tFixedFlowInput_1" />
    <metadata connector="FLOW" name="tFixedFlowInput_1" />
  </node>
  <node componentName="tLogRow" componentVersion="0.101">
    <elementParameter field="TEXT" name="UNIQUE_NAME" value="tLogRow_1" />
    <metadata connector="FLOW" name="tLogRow_1" />
  </node>
  <connection connectorName="FLOW"
              source="tFixedFlowInput_1"
              target="tLogRow_1"
              label="row1" />
</talendfile:ProcessType>
"""

SYNTHETIC_TALEND_API_METADATA: dict[str, list[dict[str, object]]] = {
    "workspaces": [
        {
            "id": "synthetic-workspace-001",
            "name": "Synthetic Development",
            "environment": {"name": "Synthetic Environment"},
            "description": "Offline sample metadata; not a tenant export.",
        }
    ],
    "tasks": [
        {
            "id": "synthetic-task-001",
            "name": "Synthetic Customer Load",
            "workspaceId": "synthetic-workspace-001",
            "status": "READY",
        }
    ],
    "runs": [
        {
            "executionId": "synthetic-run-001",
            "taskId": "synthetic-task-001",
            "status": "execution_successful",
            "executionType": "SCHEDULED",
            "executionDestination": "REMOTE_ENGINE",
        }
    ],
}


def synthetic_files(prefix: str = "process/demo") -> dict[str, bytes]:
    prefix = prefix.strip("/")
    base = f"{prefix}/" if prefix else ""
    return {
        f"{base}{SYNTHETIC_PROPERTIES_NAME}": SYNTHETIC_PROPERTIES,
        f"{base}{SYNTHETIC_ITEM_NAME}": SYNTHETIC_ITEM,
    }


def write_synthetic_fixtures(destination: Path) -> tuple[Path, Path]:
    destination.mkdir(parents=True, exist_ok=True)
    properties_path = destination / SYNTHETIC_PROPERTIES_NAME
    item_path = destination / SYNTHETIC_ITEM_NAME
    properties_path.write_bytes(SYNTHETIC_PROPERTIES)
    item_path.write_bytes(SYNTHETIC_ITEM)
    return properties_path, item_path
