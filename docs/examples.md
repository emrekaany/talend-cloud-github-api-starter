# Safe command-line examples

Every value on this page is synthetic or schematic. Nothing came from a client, employer, private repository, live tenant, screenshot, benchmark, or customer workload.

## Offline demo

```bash
talend-api demo
```

The demo exercises synthetic Talend API metadata and a synthetic Talend Studio artifact pair:

```text
synthetic API response       -> Talend metadata model --+
                                                       +-> output policy -> local_view.json
synthetic .properties/.item  -> safe XML parser -------+                 -> share_safe.json
```

The command makes no provider request and asks for no credential.

## Demo share-safe shape

The bundled fixture currently produces an identity-free shape like this:

```json
{
  "output_class": "share_safe",
  "schema_version": "2.0",
  "source": {"provider": "offline_synthetic_fixture"},
  "studio_aggregates": {
    "component_count": 2,
    "job_count": 1
  },
  "talend_aggregates": {
    "runs": {
      "execution_destination_counts": {"REMOTE_ENGINE": 1},
      "execution_status_counts": {},
      "execution_type_counts": {"SCHEDULED": 1},
      "record_count": 1,
      "status_counts": {"execution_successful": 1}
    },
    "tasks": {"record_count": 1},
    "workspaces": {"record_count": 1}
  },
  "warning_count": 0
}
```

These counts describe bundled synthetic records only. They are not customer evidence, a performance benchmark, a scale claim, or proof of live Talend access.

## Local Talend Studio project

```bash
talend-api local jobs /path/to/TALEND_PROJECT \
  --path-prefix process
```

`/path/to/TALEND_PROJECT` is a placeholder. Use only a project you own or are authorized to inspect. The command is local and makes no Talend or GitHub request.

For a safe practice project, create newly authored synthetic `.properties` / `.item` fixtures. Do not reuse a redacted client file: redaction does not change provenance or publication rights.

## Public GitHub inspection

```bash
talend-api github jobs example-owner/example-repository \
  --ref main \
  --path-prefix synthetic-project/process
```

The owner, repository, ref, and path are documentation placeholders; they are not claimed to identify an existing repository. Replace them only with public source you are authorized to inspect. GitHub access is anonymous in this starter.

## Talend API reads

After configuring your own authorized account as described in [Talend API setup](talend-api.md):

```bash
talend-api talend workspaces
talend-api talend tasks --help
talend-api talend runs --help
```

The documentation never supplies a working tenant, regional host, token, workspace ID, task ID, or run ID. Do not paste real values into examples, issues, screenshots, or transcripts.

## Two output classes

`local_view.json` is permission-restricted where supported and intended only for the operator. Depending on the command, it may contain account-visible resource names/IDs, public repository revision/path details, or local job labels. Do not publish it.

`share_safe.json` is constructed separately from an identity-free allowlist. It excludes job labels, filesystem paths, repository owner/name, refs, commit SHAs, workspace/task names, raw IDs, and hashed identities. It still requires human review because aggregate types and counts can reveal architecture.

Neither output includes raw Studio XML, executable content, logs, or exception
bodies. The local Talend API view can include a recursively redacted provider
response and must remain private. The share-safe contract additionally excludes:

- token, authorization header, cookie, password, or environment dump;
- person, email, account, tenant, owner, or repository identity from share-safe output;
- context and connection values;
- SQL, Java, shell, mapper expressions, and generated code;
- raw or redacted provider JSON and all `.item` / `.properties` content.

If an output unexpectedly contains a secret or excluded field, stop sharing it, rotate the credential if necessary, and use the private vulnerability route in [SECURITY.md](../SECURITY.md).
