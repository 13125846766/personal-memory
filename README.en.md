# personal-memory

**A personal archive for Codex that you can inspect, edit, and take with you, so you spend less time repeating your background in new chats.**

Save your background, preferences, and goals, then recall relevant details when needed. A local web UI lets you review, correct, and delete records. You can also generate a context card to paste into another AI tool.

English · [中文](README.md)

Python 3.10+ · No third-party runtime dependencies · No telemetry · [MIT](LICENSE) · v0.2

![Local management UI with fictional demo data](docs/preview.jpg)

[Quick start](#quick-start) · [Example prompts](#example-prompts) · [Privacy and data](#privacy-and-data) · [Report an issue](https://github.com/13125846766/personal-memory/issues)

## What you can do

| Situation | How to use it |
| --- | --- |
| Start a new chat without repeating your background | Recall saved education, communication preferences, or current goals when needed |
| Check what the AI has remembered | Search, filter, and edit records in the local UI; inspect sources and revision history |
| Keep work and personal context separate | Save and retrieve records under profiles such as personal and work |
| Continue a discussion with another AI | Generate a context card with the topics you choose |
| Correct or withdraw information | Update outdated details, or delete a record and its database revision history |

Imported records enter a pending-review inbox. Temporary goals can have expiry dates. Context cards exclude sensitive, pending, and expired records by default.

The archive is stored on your computer. **When you use a cloud model, information selected for context may still be sent with the request.** See [Privacy and data](#privacy-and-data).

## Quick start

Requires Python 3.10+. To use the skill, you need a Codex environment that supports local skills and script execution. On macOS/Linux, you may need to use `python3` instead of `python` in the commands below.

### 1. Download and install

```sh
git clone https://github.com/13125846766/personal-memory.git
cd personal-memory
python install.py
```

Without Git, [download the ZIP](https://github.com/13125846766/personal-memory/archive/refs/heads/main.zip), extract it, and run `python install.py` from the project directory.

The default installation directory is `~/.agents/skills/personal-memory/`. The installer copies only skill files; it does not read or copy your private archive. If the skill does not appear, reopen the chat or restart the client and check the skill list. [Official Codex skill directory documentation](https://learn.chatgpt.com/docs/build-skills)

### 2. Save your first preference in Codex

Select the Personal Memory skill, or enter:

```text
$personal-memory Initialize my local archive.
```

Then save a preference you want future chats to use, for example:

```text
$personal-memory Remember my communication preference: give the conclusion first, then explain the details.
```

In a new chat, explicitly recall the relevant context:

```text
$personal-memory Read my communication preferences and use them when answering my next questions.
```

### 3. Open the local management UI

From the downloaded project directory, run:

```sh
python skills/personal-memory/scripts/memory.py serve --open
```

On Windows, you can also double-click `Launch.cmd`. View and edit records in your browser. The terminal prints the local address; press `Ctrl+C` to stop the server. The UI requires no project account and can be tried without installing the skill.

To try sample records, import [examples/import.example.json](examples/import.example.json) in the UI. It contains only fictional data, and imported records require review.

## Example prompts

Enter these prompts in Codex and adapt the details to your needs:

```text
$personal-memory Remember: my school and major are ...
$personal-memory Use my educational background to make a study plan.
$personal-memory Organize the old chats I specify into memory. Distinguish what I stated from inferences.
$personal-memory List my saved personal information and its sources.
$personal-memory Forget the records about my previous relationship.
$personal-memory Open the local memory management UI.
$personal-memory Create a context card for another AI using only my educational background.
$personal-memory Check whether my temporary goals have expired.
```

By default, the skill does not silently accumulate new information. You can explicitly authorize ongoing saving within a limited scope, without repeated confirmation inside that scope. Automatic skill selection depends on the host; explicit invocation is more reliable. An ordinary web chat cannot directly access the archive on your computer.

## Features and current limits

- The UI supports keyword search, topic and status filters, editing, revision history, and deletion. Sensitive records are hidden by default.
- Identical content is skipped after normalization. Conflicting current values with the same topic and `key` enter pending review. Field conflict detection requires matching keys; semantic conflict detection is not implemented.
- Keyword search uses local text matching, with no remote embedding service or API dependency.
- There is no background collection, automatic sync, or scanning of all chats.
- This version does not directly parse arbitrary raw chat exports from ChatGPT or other platforms. First ask the skill to organize chats you authorize, then import structured candidate records.

### Import, export, and context cards

| Action | Behavior |
| --- | --- |
| Import JSON | Preserve sources and place all new records into pending review |
| Export JSON | Download all current records in the selected profile, including hidden sensitive, expired, and pending records; exclude revision history |
| Restore an export | Assign new IDs and require review again |
| Generate a context card | Use the current filters and include only confirmed, unexpired records; require explicit inclusion of sensitive content |

Exports are plaintext backups. Save them in a private directory; the browser controls the download location. Context cards default to a maximum of 3,000 characters, not tokens. When the budget is exceeded, entries remain intact and the number omitted is reported.

For the full command reference and data format, see [commands.md](skills/personal-memory/references/commands.md) (in Chinese).

## Privacy and data

### Where your private archive lives

The `PERSONAL_MEMORY_DIR` environment variable takes precedence. Otherwise, the defaults are:

| System | Default directory |
| --- | --- |
| Windows | `%LOCALAPPDATA%/CodexPersonalMemory/` |
| Linux/macOS | `${XDG_DATA_HOME:-~/.local/share}/codex-personal-memory/` |

Records are stored in `memory.sqlite3`. This directory must be outside the skill, source package, and Git repository. The database is not written into the downloaded project directory. Installation and upgrades do not overwrite private data.

Profiles share a local database and separate retrieval scopes. They do not provide access isolation between different users.

### What to understand before use

**Local storage does not mean local inference.** When using a cloud model, information read into context is processed with the model request and may also appear in chats and tool output. This project cannot guarantee that information stays on your device, that servers retain nothing, or that data is excluded from training. Keeping all information on-device requires a local model and a verified offline execution environment.

The archive is plaintext SQLite, with no encryption or separate access control. Skill instructions cannot prevent another program with file access from reading it. Choose a directory outside cloud-sync folders, and use operating-system permissions, disk encryption, and backups as appropriate.

The management UI listens only on `127.0.0.1` and stops when the server exits. The page requests no external resources. Its API uses a per-start token and origin checks; these do not protect against programs that already have local file access.

Deleting a record also deletes its database revision history. It does not delete old chats, tool logs, system backups, or built-in Memories. Personality-related records should retain sources and uncertainty; temporary emotions or model inferences should not become fixed facts.

### Relationship to built-in Memories

Codex has a separate local Memories feature that, when enabled, can generate memories from eligible chats in the background. This skill provides a directly editable personal archive with topic-based recall. It does not modify built-in memories or promise to preserve your entire history. [Official Memories documentation](https://learn.chatgpt.com/docs/customization/memories)

## Upgrades and custom installation

Download the updated code, then run from the project directory:

```sh
python install.py --upgrade
```

Upgrades update only skill files, without reading or copying private data. If your host uses a custom skill location, such as a configured `$CODEX_HOME/skills/`, specify the complete destination directory with `--target`. Follow your host's actual configuration:

```sh
python install.py --target "/full/path/to/skills/personal-memory"
```

Avoid installing duplicate copies with the same skill name. Markdown archives from v0.1 are not silently imported or deleted. `doctor` reports old files it finds; migration can be organized with your authorization. An empty index needs no migration.

<details>
<summary>Manual installation with Windows PowerShell</summary>

Run from the project directory:

```powershell
$skillParent = Join-Path $env:USERPROFILE '.agents/skills'
$skillTarget = Join-Path $skillParent 'personal-memory'
if (Test-Path -LiteralPath $skillTarget) { throw 'The destination already exists. Review it before continuing.' }
New-Item -ItemType Directory -Path $skillParent -Force | Out-Null
Copy-Item -LiteralPath './skills/personal-memory' -Destination $skillTarget -Recurse
```

</details>

## Feedback and contributions

For installation, invocation, or UI problems, [open an issue](https://github.com/13125846766/personal-memory/issues) with your operating system, Python version, reproduction steps, and error message. Reproduce problems with fictional data. Do not upload real archives, chat histories, or screenshots containing private information.

Run the checks locally:

```sh
python -m unittest discover -s tests -v
```

Tests use isolated fictional data and cover profile access boundaries, deduplication, import transactions, expiry and sensitive filtering, field conflicts, concurrent corrections, deletion history, HTTP origin and token checks, and installation/upgrades.

The public repository distributes only general instructions, code, documentation, tests, and fictional examples. Keep real information in an external private directory, away from examples, screenshots, tests, and issue attachments. Check files and history before publishing; `.gitignore` cannot remove data already tracked or committed.

## License

The [MIT license](LICENSE) covers the repository's instructions and code. It grants no rights to anyone's private data.
