# AGENTS.md

This document is a quick, actionable guide for automated agents (and humans) working on this repository. It summarizes what the project does, how it's structured, how to run and test it, and the typical tasks agents may perform.

## Project overview

- Name: `pydicom-background-editor`
- Goal: Apply scripted "background edits" to DICOM series using CSV-defined operations.
- Core idea: A CSV describes a list of series and a list of operations (edits) to apply. The code parses DICOM "paths" that can traverse into nested Sequences and private blocks, finds matching elements, and applies operations like setting a tag value.

## Tech stack

- Language: Python 3.12+
- Key dependency: `pydicom>=3.0.1`
- Dependency/runner: `uv` (uv.lock present)
- Build backend: `hatchling`
- Tests: `pytest`

## Repository layout

- `src/pydicom_background_editor/`
  - `__init__.py` – exports a small public surface for tests and CLI (`Operation`, `parse`, `traverse`).
  - `editor.py` – defines `Operation` (a dataclass for CSV rows) and `Editor` with supported edit ops.
    - Implemented operation: `set_tag` (method `_op_set_tag`).
    - Uses path parsing/traversal to find or add elements and set their values.
  - `path.py` – parser and traversal utilities for DICOM "paths".
    - `parse(path: str) -> Path` – parses a path string into a Path object (list of Segment/Sequence hops).
    - `traverse(ds: Dataset, parsed_path: Path) -> list` – returns a list of matching DataElements.
    - `add_tag(ds: Dataset, parsed_path: Path, value, vr: str | None = None)` – creates missing terminal element; if VR not provided, looks up in DICOM dictionary, raises ValueError if not found.
    - Supports private blocks via `(gggg,"OWNER",ee)` and sequence indices with concrete `[N]` or wildcard `[<N>]` hops.
    - Note: Private creator blocks are searched first in the current dataset, then fall back to the base dataset if not found at the current level.
  - `main.py` – CLI entry point for reading a CSV and grouping edits by `series_instance_uid`.
    - Current stub applies just the first operation of each group to a sample file for demonstration.
- `tests/`
  - `dataset.py` – constructs an in-memory `pydicom.Dataset` with nested sequences and private tags for tests.
  - `test_path_parsing.py` – validates parsing of segments, sequences, and private creator forms.
  - `test_path_traversal.py` – validates traversal over concrete and wildcard hops, plus private tags.
  - `test_editor.py` – validates basic `Editor` behavior for `set_tag` and traversal-backed edits.
- `background_editor_example_input*.csv` / `short.csv` – example CSVs illustrating the input format.

## CLI

- Entry points:
  - `uv run main`
  - `python -m pydicom_background_editor.main`
  - Installed script alias: `main` (via `[project.scripts]`)
- Arguments:
  - `input` (positional, optional; defaults to `short.csv`): CSV file with edits.
- Behavior (current state):
  - Validates required columns.
  - Groups rows into (series list, operations list) chunks.
  - For each group, applies only the first operation to a sample `files/seg.dcm` (prototype behavior; extend as needed).
  - **Limitation**: Currently breaks after processing the first series group (contains a `break` statement in the main loop).

## CSV format

Required columns (must exist in the header):

- `series_instance_uid` – when present, denotes the start of a new series group (no op/tag/vals on the same row).
- `op` – operation name (e.g., `set_tag`).
- `tag` – DICOM path in meta-quoted form (see syntax below), e.g., `"<(0010,0010)>` or `"<(0008,1110)[<0>](0008,1155)>`.
- `val1`, `val2` – operation parameters (semantics depend on `op`).

Example (excerpt from `short.csv`):

```
series_instance_uid,num_files,op,tag,val1,val2,Operation,edit_description,notify,activity_id
1.3.6.1.4.1.14519.5.2.1.2745...,6,,,,,,,
,,set_tag,"<(0013,""CTP"",13)>",<21113544>,<>,,,,
,,string_replace,"<(0008,0018)>",<1.3.6.1.4.1.14519.5.2.1>,<1.3.6.1.4.1.14519.5.2.1.2111.3544>,,,,
```

Note: Excel-style meta quotes are common in source CSVs (angle brackets and doubled quotes). The parser expects the outer `<...>` in the `tag` string.

## DICOM path syntax (supported)

- Segment (public): `<(0008,1110)>`
- Segment (private creator block): `<(0013,"CTP",10)>` where:
  - `0013` is group, `CTP` is the private owner string, `10` is owner-relative element.
- Sequence hop (concrete index): `[2]`
- Sequence hop (wildcard index): `[<0>]` – traverse all items at this level.
- Compose hops: `<(5200,9230)[<0>](0008,9124)[<0>](0008,2112)[<0>](0040,a170)[<0>](0008,0100)>`

`traverse()` returns a list of matching elements (can be many when wildcards are used). `add_tag()` can create a missing terminal element (infers VR from the DICOM dictionary when not provided).

## Supported edit operations (current)

Implemented in `Editor` (`src/pydicom_background_editor/editor.py`):

- `set_tag`: Set the value of the target element; if the element is missing, `add_tag` is used to create it. VR defaults to 'UN' when the tag is added and not found in the DICOM dictionary. Values are automatically truncated to comply with DICOM VR length limits.

- `string_replace`: Replace all occurrences of a substring (val1) with another string (val2) in the target tag's value. Works with both single-valued and multi-valued fields. If the tag doesn't exist, no action is taken (unlike `set_tag` which creates missing tags). Supports wildcard paths to operate on multiple matching elements.

- `delete_tag`: Remove the specified tag from the dataset. Works with both concrete paths (single tag) and wildcard paths (multiple matching tags). If the tag doesn't exist, no error is raised.

- `empty_tag`: Set the target tag's value to an empty string. If the tag doesn't exist, it will be created with an empty value. Works with both concrete paths and wildcard paths to operate on multiple matching elements. Supports private tags.

- `substitute`: Conditionally replace the tag's value with val2 only if the current value exactly matches val1. If the tag doesn't exist or the value doesn't match, no action is taken. Works with both single-valued and multi-valued fields. Supports wildcard paths to operate on multiple matching elements. Supports private tags.

Planned/obvious follow-ons (outlined in `main.py` comments and historical background editor notes):

- `copy_from_tag`, `shift_date`, etc.

When adding an operation, create a method named `_op_<opname>(ds, op)` on `Editor`.

## How to run

- Install/setup (preferred: uv):

```bash
# Create/refresh the environment from pyproject/uv.lock
uv sync
```

- Run tests (uv will manage the environment automatically):

```bash
uv run pytest -q
```

- CLI smoke test:

```bash
uv run main short.csv
# Or using the installed script alias:
main short.csv
```

## Agent playbook

These roles split typical work into focused tasks. Each role lists inputs, outputs, and acceptance criteria.

### 1) Code Agent – implement/edit operations

- Inputs: New `op` name, semantics, and test cases.
- Outputs: One or more `_op_<name>` methods on `Editor` and any helpers in `path.py` if traversal needs to change.
- Criteria:
  - New and existing tests pass.
  - Operation handles missing elements using `add_tag` where appropriate.
  - No regressions in path parsing/traversal.

Suggested steps:
- Add method `_op_<name>(self, ds: Dataset, op: Operation)`.
- Parse `op.tag` and find target(s) via `traverse`.
- Update `ds` values (and VRs if needed) consistently across all matches.
- Expand tests to cover both concrete and wildcard sequences and private tags.

### 2) Test Agent – expand coverage

- Inputs: Edge cases from real CSVs and DICOM structures.
- Outputs: New tests under `tests/`.
- Criteria:
  - Cover missing tags, empty sequences, wildcard traversal, and private creator blocks.
  - Validate `add_tag` with/without explicit VR, including sequence contexts.

### 3) CLI Agent – productionize the CLI

- Inputs: Real CSVs, DICOM file discovery by `series_instance_uid`.
- Outputs: A complete CLI that reads all files for each series and applies all operations.
- Criteria:
  - Validates CSV headers and values robustly (clear errors).
  - Applies all operations per series (not just the first) across all series files.
  - Reports a summary (files touched, operations applied, failures).

### 4) Packaging/Release Agent – polish project metadata

- Inputs: `pyproject.toml` and README.
- Outputs: Accurate `description`, optional `classifiers`, and versioning.
- Criteria:
  - Installable with `pip`.
  - Clear README usage and examples.

## Constraints and conventions

- Python ≥ 3.12.
- Keep public surface minimal; export via `__init__.py` only what tests/CLI need.
- Prefer small, focused PRs with passing tests.
- When editing traversal or adding ops, consider performance on large, nested sequences.

## Quick reference

- Public API: `Operation`, `parse`, `traverse` (exported via `__init__.py`).
- Editor class: `Editor.apply_edits` (available via direct import).
- Entry point: `python -m pydicom_background_editor.main` (or `main` or `uv run main`).
- Example data: `files/seg.dcm`, `short.csv`, `background_editor_example_input.csv`, `background_editor_example_input2.csv`.

## Roadmap (suggested)

- Implement additional operations (`delete_tag`, `string_replace`, etc.), guided by the historical background editor operations.
- Expand CLI to iterate real series files (by UID) and write outputs to a configurable destination.
- Add basic typing and linting (optional: `mypy`, `ruff`).
- Add docstrings and examples to README.
- Fix issue with traverse function when processing private tags - the prviate creator block could be at any level above where the tag occurs.
