# Feature register

Every feature the owner has asked for, with its early judgment. A note is the why and the what; a [spec file](../specs/README.md) is the how. This register captures intent and feasibility. It does not approve a dependency, a paid service or implementation ([working rule 1](../AGENTS.md#working-rules)).

| ID | Feature | Early judgment and important constraint |
|---|---|---|

[RESEARCH_LOG.md](RESEARCH_LOG.md) records the actual queries, source access, version corrections and limits. Primary links appear beside claims in each feature note. Copy [TEMPLATE.md](TEMPLATE.md) for a new note.

## What a feature note holds

| What | Its home |
|---|---|
| The owner's dated words | The feature note, under "The owner's words" |
| Evidence found at intake | The feature note, under "Evidence at intake", or a dated study |
| Design, formats, rules and validations | The spec file once one covers the feature; until then the note, labelled Proposed |
| What a decision means for the requirements | The spec file's "Decisions applied" table and requirements |
| That a decision exists, and which spec carries it | The map's decisions |

When a spec file covers a feature, each design paragraph in the note is checked against the spec before it leaves the note, and anything missing is added to the spec. A note links to its spec files at the top.

## Every idea receives a quick source check

When the owner gives a feature idea, first read this index and the relevant existing notes. Allocate the next unused stable `F` ID, or update the existing ID when the idea refines the same feature. Keep IDs stable when titles change; cross-link related features rather than creating duplicate requirements.

Keep **owner intent separate from research findings and our proposals**. Record the date and the status. Do a bounded primary-source lookup for **each idea**: relevant articles, official guides, specifications or research. Record the exact queries, access method, URLs, known publication or version information and meaningful locators in the research log. A discovery snippet is a lead, not verified implementation evidence. A mutable documentation page is not a pinned dependency.

The note gives an early candid feasibility judgment, practical requirements and tradeoffs, links near factual claims, cross-feature constraints, the effect on the main values, unresolved questions and one small proposed validation. Identify sourced statements separately from our inference. Record inaccessible sources as blocked evidence, with affected claims left unknown; never fill gaps from assumption. Keep the check quick and specific rather than turning every addition into an exhaustive survey. The quick check records the idea; before any of its options is recommended for a decision, the options get the research that [Decisions rest on research](../AGENTS.md#decisions-rest-on-research) requires.

Do not mark a validation executed without observed artifacts and results. Recording a feature does not authorize installing a dependency, calling a paid API, changing product code or narrowing the owner's requirement.

## Recording new owner ideas

The next unused feature ID is **F001**. Follow the [quick source check](#every-idea-receives-a-quick-source-check) for every idea:

1. Allocate the next ID, or update the existing feature.
2. Keep owner intent separate from findings and proposals.
3. Record the date and the status.
4. Do a quick primary-source lookup. Log the queries, URLs and versions in the research log. This records the idea; before any of its options is recommended for a decision, do the research that [Decisions rest on research](../AGENTS.md#decisions-rest-on-research) requires.
5. Give a candid feasibility judgment, cross-feature constraints, the effect on the main values, open questions and **one** small `UNEXECUTED` validation.

In the same change, update the register, the feature note, the research log, the affected spec files ([Spec files](../specs/README.md)), the [feature matrix](../FEATURE_MATRIX.md) and the [project map](../PROJECT_MAP.html). A feature with no spec file yet has no row in STATE.md's progress table. Papers the owner asks for go into a dated `studies/<date>/` dossier.

## Recording owner answers

The routine each time the owner answers a question, on top of the steps above:

1. **The affected spec files:** apply the decision to the requirements, add it to the "Decisions applied" table, bump the version and add a change-log line, then update the progress table in [STATE.md](../STATE.md#progress-by-spec-file). For a feature with no spec file yet, record the decision in its feature note and in STATE.md, for its spec file to come.
2. **Each affected feature note:** the owner's words with their date and the requirement IDs that carry them, and any source checked ([What a feature note holds](#what-a-feature-note-holds)). A feature with no spec file yet also gets, in a dated section, the Proposed design, the effect on the main values, open points and one small `UNEXECUTED` validation, which move to its spec file when that is written.
3. **Summaries:** the register row here, only if the feature's spec or main constraint changes; [PRODUCT.md](PRODUCT.md) if what the product is changes; "Open owner decisions" in STATE.md; for a new spec file, the table in [specs/README.md](../specs/README.md#spec-file-table); FEATURE_MATRIX.md whenever a target's feature or technology changes; STATE.md; the map's decisions.
4. **Research logs:** this folder's log, or the dated study's own log: the time, the queries, the URLs read and not used, and versions or "moving page".
5. **Checks and delivery:** run the project check and `git diff --check`, commit only your paths, and push `main` when the owner agrees.
