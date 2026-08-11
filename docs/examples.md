# Safe examples

Every value on this page is synthetic or schematic. Nothing below came from a client, employer, private repository, live tenant, screenshot, benchmark, or customer workload.

## Offline demo

```bash
talend-api-starter demo
```

The demo exercises both synthetic paths:

```text
synthetic cloud response    ──▶ cloud metadata model ──┐
                                                         ├──▶ output policy ──┬──▶ local_view.json
synthetic .properties/.item ──▶ safe XML parser      ──┘                  └──▶ share_safe.json
```

The exact console formatting is allowed to evolve. The invariant is that demo mode does not call a provider and does not require credentials.

## Actual demo share-safe schema

The bundled demo currently writes this identity-free aggregate shape:

```json
{
  "cloud_aggregates": {
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
  "output_class": "share_safe",
  "schema_version": "1.0",
  "source": {"provider": "offline_synthetic_fixture"},
  "studio_aggregates": {
    "component_count": 2,
    "job_count": 1
  },
  "warning_count": 0
}
```

These counts describe only bundled synthetic records. They are not performance, scale, customer, or adoption metrics.

## Local-only companion

`local_view.json` is written separately and permission-restricted where the filesystem supports it. In demo mode it contains synthetic names and source paths. In live modes it can contain account-visible names/IDs, provider response metadata, or public repository revision/path details. Do not publish it.

`share_safe.json` never includes a job label, file path, repository owner/name, ref, commit SHA, workspace/task name, raw ID, or hashed identity. It still requires human review because aggregate types and counts can reveal architecture.

## Public GitHub inspection

```bash
talend-api-starter github jobs example-owner/example-repository \
  --ref main \
  --path-prefix synthetic-project/process
```

Replace the owner, repository, ref, and path with a **public** source you are authorized to inspect. The names above are documentation placeholders; they are not claimed to identify an existing repository.

## Talend Cloud reads

After the local environment is configured as described in [Talend Cloud API setup](talend-cloud-api.md):

```bash
talend-api-starter cloud workspaces
talend-api-starter cloud tasks --help
talend-api-starter cloud runs --help
```

Use `--help` to select a workspace, artifact, status, day window, or page without copying live identifiers into a public report.

## Fields excluded from share-safe output

The default share-safe contract excludes:

- token or authorization header;
- person, email, account, tenant, owner, or repository identity;
- workspace/project/task/run names and raw IDs;
- descriptions and tags;
- clone URLs and filesystem paths;
- context and connection **values**;
- SQL, Java, shell, mapper expressions, and generated code;
- raw `.item` / `.properties`, provider JSON, log, or exception body.

Recognized run-status/type buckets and counts can still reveal architecture. Treat even share-safe output as potentially sensitive and obtain the appropriate approval before sharing it.
