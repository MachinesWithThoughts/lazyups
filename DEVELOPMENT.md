# Development Scripts Guide

This file documents what each script in the LazyUPS repo is for, when to use it, and common examples.

## Script Index

### `run.sh`

**Purpose:** Launch the app normally, or route validation flags to validation runner.

- Normal app launch:

  ```bash
  ./run.sh
  ./run.sh --screen monitor
  ./run.sh --config-file /etc/lazyups.config
  ```

- Validation passthrough:

  ```bash
  ./run.sh --validate-runtime
  ./run.sh --validate-screens
  ./run.sh --validate-screens --validation-screens monitor,details
  ```

---

### `run-code-validations.sh`

**Purpose:** Run built-in runtime/screen validation checks.

Options:

- `--validate-runtime` → import/runtime checks
- `--validate-screens` → cycles screens headlessly
- `--validation-screens` → limit specific screens
- `--help`

Examples:

```bash
./run-code-validations.sh --validate-runtime
./run-code-validations.sh --validate-screens
./run-code-validations.sh --validate-screens --validation-screens monitor,details,devices,fields
```

---

### `preflight.sh`

**Purpose:** Full quality gate runner + timestamped report.

Runs:

- runtime validation
- screen validation
- pytest
- ruff
- mypy

Output report:

- `preflight--YYYYMMDD-HHMMSS.txt`

Example:

```bash
./preflight.sh
```

---

### `verify-app-with-python-versions.sh`

**Purpose:** Cross-version Python compatibility verification in isolated environments.

Defaults to:

- 3.12, 3.13, 3.14

Can also run specific versions:

```bash
./verify-app-with-python-versions.sh 3.13 3.14
```

Per-version outputs:

- `python-version-validation/py<version>/report.txt`
- `python-version-validation/py<version>/status.txt`

---

### `mirror.sh`

**Purpose:** Mirror private repo changes to public remote and optionally mirror release objects.

Default behavior:

- push `main`
- push tags
- mirror latest release

Common usage:

```bash
./mirror.sh
./mirror.sh --force
./mirror.sh --main-only
./mirror.sh --all
./mirror.sh --create-release v01.03.08
./mirror.sh --create-latest-release
```

Notes:

- Uses remote alias `public`
- May require `gh` auth/token for release creation even if git push works via SSH deploy key.

---

### `build-exe.sh`

**Purpose:** Build standalone executable package(s) (PyInstaller workflow).

Use when producing distributable binaries for systems without Python toolchain.

Example:

```bash
./build-exe.sh
```

---

### `check-version-sync.sh`

**Purpose:** Sanity-check version consistency across project files/tags.

Use before tagging/releasing.

Example:

```bash
./check-version-sync.sh
```

---

## Optional / Generated Helpers

### `python-version-validation/run-validation.sh`

**Purpose:** internal helper used by version-validation workflow. Not intended as primary user-facing entrypoint.

---

## Recommended Dev Workflow

1. Make code changes
2. Run quick checks:

   ```bash
   ./run-code-validations.sh --validate-runtime
   ./run-code-validations.sh --validate-screens
   ```

3. Run full gate:

   ```bash
   ./preflight.sh
   ```

4. (Release prep) multi-Python verification:

   ```bash
   ./verify-app-with-python-versions.sh
   ```

5. Commit/tag/push private repo
6. Mirror public:
   ```bash
   ./mirror.sh
   ```
