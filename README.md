# locus-reference

Working demonstrators of the [LOCUS Architecture](https://github.com/RFerminH/LOCUS-Architecture). Start with the [Public Overview](https://doi.org/10.5281/zenodo.21518833) for the architecture itself.

## Current demonstrator: clinical second opinion

A command-line program in which AI provides a second opinion formed without seeing the clinician's formulation, while clinical determination remains with the clinician. Work in progress.

LOCUS elements implemented:

- **Compartmentalized Potentia.** AI capability is distributed across specialized Potentiae: Intake Splitter, Urgency Screener, Formulator, Comparator and Analyst. Each receives only the information required for its task. The Formulator Potentia sees the evidence, never the clinician's formulation. It returns one leading formulation with a differential.
- **Hormetic Friction.** Before Potentia's rationale is exposed, the clinician explains their own formulation. When formulations converge, Potentia's formulation is shown first and the friction is lighter. Potestas can skip this step or decline the second opinion; the choice is recorded.
- **AIsight.** The Analyst Potentia exposes the executive-relevant state of the delegated work (where the two formulations converge and diverge, and which evidence bears on the difference) at a resolution sufficient for the clinician's determination, without transferring the full burden of the analysis.
- **Reserved Determination.** Final clinical determination remains with the clinician (Potestas).
- **Trace.** Each session records, as a single ordered timeline, human input, component outputs and exposure events.
- **Reserved Safety Return.** A time-critical safety condition interrupts the ordinary flow and returns control to Potestas. Break-Glass may then be invoked by Potestas to bypass the Pairing Hold (the withholding of Potentia's response until the clinician has explained their own).

## Status and limits

- Synthetic cases only. Not clinically validated; not for clinical use.
- All components currently use the same model (Gemini). Compartmentalization separates information and jurisdiction, not model-level failure modes.
- 20 automated tests (`pytest`) check flow, exposure order in Trace, component information access and retry behaviour, using fake components. Targeted mutation checks confirm that the isolation and retry tests fail when the code they protect is broken. They do not evaluate model-output quality.

## Running it

Requires Python 3, a Gemini API key in a `.env` file (`GEMINI_API_KEY=...`) and the packages `google-genai`, `pydantic`, `python-dotenv` and `pytest`.

```
cd src
python main.py
```

Tests, from the repository root:

```
python -m pytest
```

## Author

Rafael Fermin Hernandez · [ORCID 0009-0007-1831-8294](https://orcid.org/0009-0007-1831-8294)
