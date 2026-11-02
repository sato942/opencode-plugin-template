# The feature's name — specification

Copy this file to `<feature>.spec.md`, replace `CODE` with the file's [code](README.md#code-standard), and delete these lines and any part that truly does not apply.

| | |
|---|---|
| **Spec file** | `specs/<feature>.spec.md` |
| **Code** | `CODE` (requirements `CODE-NNN`, open questions `CODE-Qn`, validations `CODE-Vn`) |
| **Features** | The feature notes it covers, and the map parts it touches |
| **Version** | 0.1, the date ({{TIMEZONE}}) |
| **Spec status** | Draft. Everything stays Proposed until the owner reviews the file |
| **Implementation** | Not started. Every validation is `UNEXECUTED` |

**The owner, on the date:** "their words". The evidence is the study it rests on.

One or two sentences on what this file specifies.

## 1. Scope

**In scope:** what this file decides.

**Out of scope, each owned elsewhere:** what it does not decide, and who does.

## 2. Sources, labels and units

**Sources.** Each source's identity (revision, hash, version or date), and when it was checked.

**Labels:** **Source** (from the adopted source, unchanged), **Decided** (an owner decision), **Invariant** (required by an [architecture invariant](../AGENTS.md#architecture-invariants)), **Recorded** (a requirement of another spec file, restated), **Proposed** (binding only once the owner agrees), **Open** (waiting for the owner or a measurement).

**Units.** The units and encodings the numbers below use.

## 3. Decisions applied

| ID | Decision | Owner, date and time | Requirements |
|---|---|---|---|

## 4. Terms

| Term | Meaning |
|---|---|

## 5. The first component

- **CODE-001** [Proposed] One requirement, specific enough that two developers who never talk would build the same thing: every format field by field; every algorithm as pseudo-code with a worked example; every number with its unit and source; every interface with its inputs, outputs and errors; what happens on failure and restart.

## 6. Secrets, authority and effects

| Invariant | How this file keeps it |
|---|---|
| 1. Secrets stay out | |
| 2. No effect replay | |
| 3. Exact identity | |

## 7. What is measured

- **CODE-010** [Proposed] What is measured, against which baseline, and which settings the measurement may change. Leave this part out if no main value is at stake.

## 8. Conformance and traceability

| Source or rule | Requirement |
|---|---|

## 9. Open questions

- **CODE-Q1** The question. What settles it: the owner, a study or a measurement. Options and one recommended, once its research exists.

## 10. Validation

All `UNEXECUTED`. Each runs the real thing through its real entry point and leaves its inputs, versions, outputs and date.

- **CODE-V1** What is run, what is observed and which requirements it checks (CODE-001).

## 11. Change log

| Version | Date and time | Change |
|---|---|---|
| 0.1 | The date and time | First Draft |
