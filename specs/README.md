# Spec files

How spec files are named, written and changed, and the index of all of them. This file ranks with [AGENTS.md](../AGENTS.md) ([Authority](../AGENTS.md#authority) item 2).

Every feature is specified in its own spec file, in enough detail to build it without guessing. Copy [TEMPLATE.md](TEMPLATE.md) for a new one.

**Naming and place.**

1. Spec files live in this folder, each named `<feature>.spec.md`: the feature's short name in lowercase words joined by hyphens, as the owner would say it. The file name carries no F-number; the header lists the features it covers.
2. One spec file covers one feature. A broad feature can need several.
3. Each spec file has a code, one whole word that no other spec file uses, by the [code standard](#code-standard), such as `LOGIN`. Its requirements are `CODE-NNN`, its open questions `CODE-Qn` and its validations `CODE-Vn`. Each is defined once, as a list item that starts with the ID in bold (`- **LOGIN-001**`). IDs are numbered in the order written and never renumbered or reused; a withdrawn requirement keeps its ID, marked withdrawn with the date and the reason.
4. **Map it.** In the change that creates a spec file, add its row to the [spec file table](#spec-file-table): path, features, code, scope and when to read it. That table is the only index of spec files.

**Generating one.**

1. **Gather the sources:** the owner's words; the feature notes; any source the owner adopted; the dated owner decisions; the architecture invariants; and the other spec files it touches. Pin each source's identity (revision, hash, version or date), check that it is still current, and log the check in the matching research log.
2. **"1 to 1" means nothing is lost.** When the owner asks for a source to be extracted 1 to 1, every part of it maps to a requirement or an evidence note: every rule, number, format, algorithm and example. A traceability table shows each part as Adopted, Changed (naming the decision), Dropped (giving the reason) or Evidence.
3. **Apply every owner decision** that changes the source, in a "Decisions applied" table with its date and the requirements it affects.
4. **Restate in our own words.** Copy no prose, prompt or code from a source unless its license allows it. Record the license in [LEGAL_FLAGS.md](../LEGAL_FLAGS.md).
5. **Label each requirement:**
   - **Source:** from the adopted source, unchanged;
   - **Decided:** from an owner decision;
   - **Invariant:** required by an architecture invariant;
   - **Recorded:** a requirement of another spec file, restated;
   - **Proposed:** our design where the source is silent or unclear, the default for prototypes and binding only once the owner agrees;
   - **Open:** waiting for the owner or a measurement.

   Keep evidence apart from requirements: a source's claims and numbers are never this project's measurements.
6. **Flag** inconsistencies inside a source and conflicts with other documents as Open. Never resolve them silently.
7. **Open questions** say what settles each, and each has a row in the map's decisions. None is put to the owner before the research that [Decisions rest on research](../AGENTS.md#decisions-rest-on-research) requires.

**How detailed.** Detailed enough that two developers who never talk would build the same thing. Every spec file has these parts, in this order:

1. a header table: path, code, features, version, spec status (Draft until the owner reviews it, then Agreed, or Superseded) and implementation status;
2. scope, in and out, naming who owns the rest;
3. sources, labels and units;
4. the decisions applied;
5. terms;
6. requirements by component, with:
   - every data format field by field: type, unit, encoding and range;
   - every algorithm as pseudo-code, with a worked example;
   - every number with its unit and its source;
   - every interface with its inputs, outputs and errors;
   - ordering, concurrency, failure, restart and recovery;
7. secrets, authority and effects, tied to the architecture invariants;
8. what is measured and the settings that measurement may change;
9. conformance and traceability tables;
10. open questions;
11. validations, `UNEXECUTED` until run, each naming the requirements it checks;
12. a change log with dates and times, as the file's last lines.

Leave out a part that truly does not apply, and scale the detail to the feature: a small feature gets a short spec file. A validation demonstrates the real thing ([How work gets done](../AGENTS.md#how-work-gets-done)); it does not ask for a test suite, and a spec file sets no test count or coverage target.

**Authority.** A spec file is authoritative for its scope ([Authority](../AGENTS.md#authority) item 4). Where it disagrees with the owner's words or a feature note's owner intent, the spec file is wrong: check the source and correct the spec file in the same change.

**Feature notes.** Feature notes hold the owner's words and the evidence found at intake, with a link to the spec file. Spec files hold the design, the validations and what each decision means ([What a feature note holds](../features/README.md#what-a-feature-note-holds)). An owner decision has its words in the feature note, its meaning in the affected spec file's "Decisions applied" table and requirements, and a line that links to it in the map's decisions and in [STATE.md](../STATE.md).

**When a spec file is written.** When the owner asks for it, and in any case before implementation of that feature starts. Until then, it has no row in STATE.md's progress table.

**Changing one.** In the same change:

- bump its version and add a change-log line;
- update its row in STATE.md's progress table;
- update [FEATURE_MATRIX.md](../FEATURE_MATRIX.md) if a feature changes on a target;
- update its parts in [PROJECT_MAP.html](../PROJECT_MAP.html) (working rule 11);
- run the project check (`python -I tools/check_project.py .`), which also checks the spec IDs and this table.

## Code standard

A spec file's **code** is the word that starts every ID in it, as `LOGIN` does in `LOGIN-011`. The [map](../PROJECT_MAP.html#codes) shows every code.

A code is:

1. one English word, singular, in capitals, of 3 to 8 letters;
2. taken from the spec file's name or title, so a reader can tell which file it is without a key;
3. never an abbreviation, an acronym or a blend;
4. used by no other spec file;
5. fixed once the spec file exists.

**Other kinds of ID.** These are not spec file codes, and they keep their forms.

| Kind | Form | Where it is defined |
|---|---|---|
| Feature | `F012` | [features/](../features/README.md) |
| Decision label in a spec file | `LOGIN A14` | That file's decisions table; always cited with its code |
| Map part and map source | `A3.13`, `S12` | [The map](../PROJECT_MAP.html) |
| Study finding | `E9`, `B6`, `N2` | Its study; always cited with the study |

## Spec file table

| Spec file | Features | Code | Scope | Read when |
|---|---|---|---|---|
