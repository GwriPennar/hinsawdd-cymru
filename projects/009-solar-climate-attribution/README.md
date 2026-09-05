# Project 009: Solar variability and modern warming

**Hinsawdd Cymru | Evidence review and reproducible research protocol**

Status: **Stage A research baseline, provisional.** Established 5 September 2026. This is not a completed numerical attribution study or a cover-to-cover review of Javier Vinós's book.

## Research question

Do proposed millennial solar variations, particularly the Eddy and Bray/Hallstatt cycles, provide a reproducible, quantitatively adequate explanation of modern global warming? How does that explanation compare with human forcing, other natural forcing and internal variability?

The project was prompted by public claims that the Sun, rather than human activities, explains current warming and predicts approximately another century of glacier melting before cooling. The target of evaluation is the claim, not the character or motives of its advocate. A successful project may reject, qualify or support individual propositions. Rejecting a solar-only explanation does not imply that the Sun has no climatic influence.

## Initial assessment

Historical solar-proxy data exist. Some published studies report long-period solar signals. Neither fact establishes an accurate global-temperature reconstruction or a reliable forecast. The literature disagrees about the robustness and origin of the proposed millennial signals. Modern solar-only attribution is inconsistent with the assessed evidence, while an indirect solar mechanism requires its own quantitative test. See the claim-by-claim [evidence review](EVIDENCE_REVIEW.md) and [source register](sources.json).

These are literature-based assessments, not results of calculations performed by this project. The reference book remains a hypothesis source, with page-level auditing pending.

## Contents

- [Evidence review](EVIDENCE_REVIEW.md): observations, periodicity, attribution, historical comparisons, indirect mechanisms and forecasting.
- [Research protocol](PROTOCOL.md): competing hypotheses, bias controls, tests, uncertainty and publication gates.
- [Machine-readable source register](sources.json): nineteen sources, access levels, supporting evidence and limitations.
- [Claim ledger](claims.json): ten separately testable propositions, including corrections to our own initial framing.
- [Dataset acquisition register](datasets.json): candidate products and explicit acquisition status.
- [Public reply and source](COMMUNICATIONS.md): copy-ready wording with restricted claims.
- [Research log and limitations](RESEARCH_LOG.md): searches, provenance, unresolved access and corrections.

## What has and has not been done

| Work | Stage A status |
|---|---|
| Read and compare central solar literature | Relevant sections or abstracts reviewed; access level recorded individually |
| Include evidence favourable to solar influence | Included, not treated as proof of modern solar dominance |
| Separate the book from stronger social-media claims | Done using the author's public Q&A |
| Establish claim ledger and prospective analysis rules | Done |
| Download and version scientific datasets | Not yet done |
| Reproduce the three circulated figures | Not yet done; original numerical inputs and plotting settings are not supplied |
| Run spectral, wavelet or climate-attribution experiments | Not yet done |
| Audit the entire book and bibliography | Not done; metadata, abstract and supplied figures only |
| Obtain independent scientific review | Pending |

## Reproduce the evidence checks

Python 3.11+, standard library only, from the repository root:

```sh
python projects/009-solar-climate-attribution/validate.py
python -m unittest discover -s projects/009-solar-climate-attribution/tests -v
python projects/009-solar-climate-attribution/validate.py --output build/project-009/validation.json --catalogue build/project-009/SOURCES.md
```

The checks verify register structure, identifiers, references and provenance status. **Passing tests does not verify the scientific conclusions or live availability of external links.** A dedicated GitHub Actions workflow runs these checks and retains the catalogue and validation output. No scheduled source refresh, external posting or automatic merge is enabled.

## Next milestone

Stage B will freeze a documented data snapshot, reproduce the relevant source analyses, and compare results across reconstructions before publishing new climate figures. Numerical choices must be committed before running those experiments. New figures must be code-generated, dark-mode-first, unit-labelled and consistent with the repository's [visual standards](../../VISUAL_STYLE.md). Hypotheses, observed data, proxy reconstructions and projections must have distinct labels.

## Scope and independence

The research question is global, with implications for interpretation of Welsh climate evidence. A North Atlantic signal is not automatically a Wales-wide or global signal. Project numbering was checked against main and available branches: 009 was unused; 008 is left untouched, not assigned by this work.

Code follows the repository MIT licence. Third-party publications and datasets retain their own terms. The book, social-media screenshots and journal PDFs are not redistributed. This is independent work, not an endorsement by any cited institution.
