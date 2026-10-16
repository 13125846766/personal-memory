# Local memory tools

The scripts use Python 3.10+ and its standard library; no pip install or API key is needed. Resolve `scripts/memory.py` relative to this skill. In examples below `python memory.py` means the actual Python executable and absolute script path.

Global options appear BEFORE the command: `--vault <external-directory>` and `--profile <name>` (default `default`). Profile names are 1–32 lowercase ASCII letters/digits/underscores/hyphens. Profiles separate retrieval, not OS-level permissions.

```text
python memory.py init
python memory.py serve --open
python memory.py doctor
python memory.py profiles
python memory.py --profile work list --query "Python" --topic education
python memory.py --profile work list --include-sensitive
python memory.py add --file <private-record.json>
python memory.py import --file <authorized-records.json>
python memory.py update <id> --file <private-patch.json> --version <current-version>
python memory.py history <id>
python memory.py forget <id>
python memory.py capsule --topics education goals --budget 3000
python memory.py export --out <external-private-backup.json>
```

## Data and lifecycle

Authoritative storage is `memory.sqlite3` in the external vault. The UI and CLI use the same database. Use these helpers for writes instead of editing SQLite directly. Commands emit JSON. Default `list` hides sensitive records. To read active records use `list --status active`; this also excludes expired records. `list` with no status includes pending and expired records for review.

An input record contains `statement`, `topic`, `source`, `kind`, `sensitivity`, `status`, optional `expires` (YYYY-MM-DD), and optional `key` (e.g. `current-school`). Defaults: preferences/user-stated/ordinary/pending. `source` records provenance; a missing original date is unknown, not today's date. `created` and `updated` timestamps are UTC. Expiry comparison uses the local computer's date; account for this if its timezone differs from the user.

`add` uses supplied status after validation; use `active` for the user's explicit durable statement. `tentative` always remains pending. `import` accepts a JSON list or an object with `memories: [...]`, validates the whole batch atomically, ignores exact normalized duplicates within the same profile/topic, and puts ALL new records into pending review. It does not extract personal facts from arbitrary chat exports. The agent must first interpret authorized chat content, distinguish speakers and quotes, and create concise structured candidate records in a private temporary file. Never place these files in a repo or public output.

Records sharing a nonempty key in the same profile/topic cannot become active with competing current values. A new conflicting record is pending; approval requires correcting/removing the existing active record. Blank keys cannot be checked for semantic contradictions. No semantic embeddings or remote model calls are implemented.

Updates require the current `version` to prevent stale overwrites. Older versions remain as correction history. Do not create a new record to bypass a conflict. For explicit corrections, patch the existing record and cite the correction as its new source. A direct correction does not need another user confirmation.

For sensitive facts, use `--include-sensitive` only when needed for the authorized task. Capsules contain only active, unexpired records; sensitive records are excluded unless explicitly included. Character budgets (200–20000, default 3000) are not token counts. They select whole records and report omissions. Capsules are PRIVATE content, never public artifacts. Read and review before pasting into another provider.

## Deletion and backup

`forget` permanently deletes one record and all its revisions in that database. The CLI is immediate because the user's deletion request supplies authorization; the management UI has a confirmation to prevent accidental clicks. For a request to forget a topic or fact, inspect relevant active/pending/expired records AND their histories, delete every matching record, and check legacy Markdown files too. It does not erase external exports, earlier chats, OS snapshots or provider logs. SQLite secure_delete is enabled; this is not a claim of forensic erasure on SSDs or backups.

`export` creates a new plaintext JSON file and never overwrites one. It exports the selected profile's current records, including pending, expired and sensitive records, without historical revisions. CLI export refuses Git/skill directories. Browser downloads depend on the user's configured download folder, so the UI explains their sensitivity. Importing a backup restores records as pending review and assigns new IDs; it is not an exact database/history restore.

## Legacy v0.1 Markdown

`doctor` reports topic Markdown files, but never silently imports or deletes them. For an authorized migration, parse those files with attention to provenance, import candidates, compare results, and remove original redundant records only when the migration scope authorizes it. Never claim migrated data was forgotten while retaining the old Markdown copy. An empty v0.1 index needs no migration.

## Local UI

`serve` binds only to `127.0.0.1` on a random port, or `--port <port>`. `--open` opens the default browser. Requests require the matching Host, same-origin checks, and a per-run request token for APIs. There are no external assets, telemetry, CORS allowances, or outbound API dependencies. Stop with Ctrl+C. Other processes with local filesystem access are outside this UI's protection; profiles are not authentication accounts.
