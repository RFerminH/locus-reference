def label(text):
    return text.replace("_"," ").upper()

def bullets(items):
    if not items:
        return "  none"
    lines=[]
    for item in items:
        lines.append("  - " + item)

    return "\n".join(lines)



def show_vector(vector):
    lines= []
    lines.append(vector.finding)
    lines.append("   State: " + label(vector.case_state))
    lines.append("   Presence frequency: " + label(vector.presence_frequency_given_formulation))
    lines.append("   Effect: " + label(vector.case_effect))

    if vector.evidence_basis:
        lines.append('   Evidence: "' + vector.evidence_basis + '"')
    lines.append("   Basis: " + vector.assessment_basis)

    return "\n".join(lines)


def show_formulation(title, block):
    lines = []
    lines.append(title)
    lines.append("  Formulation: " + block.formulation)
    lines.append("  Clinical node: " + block.mapped_clinical_node)

    if block.stated_qualifiers:
        qualifiers = ", ".join(block.stated_qualifiers)
    else:
        qualifiers = "none"
    lines.append("  Stated qualifiers: " + qualifiers)

    lines.append("")
    shown = 0
    for vector in block.vectors:
        if not is_set_aside(vector):
            lines.append(show_vector(vector))
            lines.append("")
            shown = shown + 1
    if shown == 0:
        lines.append("  none")
        lines.append("")
    return "\n".join(lines)

def show_claims(claims):
    if not claims:
        return "  none"
    lines = []
    for claim in claims:
        lines.append("  - [" + label(claim.source) + "] " + claim.claim)
        lines.append("    " + claim.note)
    return "\n".join(lines)

def render_analysis(analysis):
    parts = []
    parts.append("DECISION FORK")
    parts.append("  " + analysis.decision_fork.strip())
    parts.append("")
    parts.append(show_formulation("POTESTAS FORMULATION", analysis.potestas_formulation_analysis))
    parts.append(show_formulation("POTENTIA FORMULATION", analysis.potentia_formulation_analysis))
    parts.append("SHARED GROUND")
    parts.append(bullets(analysis.shared_ground))
    parts.append("")
    parts.append("KEY DISCRIMINATORS")
    parts.append(bullets(analysis.key_discriminators))
    parts.append("")
    parts.append("MISSING DISCRIMINATING EVIDENCE")
    parts.append(bullets(analysis.missing_discriminating_evidence))
    parts.append("")
    parts.append("UNSUPPORTED OR OVEREXTENDED CLAIMS")
    parts.append(show_claims(analysis.unsupported_or_overextended_claims))
    parts.append("")
    parts.append("SET ASIDE (NOT DECISIVE)")
    parts.append(show_set_aside(analysis))
    return "\n".join(parts)


def is_set_aside(vector):
    if vector.case_state.value == "not_identified":
        return True
    if vector.case_effect.value in ("neutral", "unresolved"):
        return True
    return False


def set_aside_lines(name, block):
    lines = []
    for vector in block.vectors:
        if is_set_aside(vector):
            lines.append("  - [" + name + "] " + vector.finding + ": " + label(vector.case_state) + ", " + label(vector.case_effect))
            lines.append("    " + vector.assessment_basis)
    return lines


def show_set_aside(analysis):
    lines = []
    lines = lines + set_aside_lines("POTESTAS", analysis.potestas_formulation_analysis)
    lines = lines + set_aside_lines("POTENTIA", analysis.potentia_formulation_analysis)
    for item in analysis.unresolved_uncertainties:
        lines.append("  - [UNRESOLVED] " + item)
    if not lines:
        return "  none"
    return "\n".join(lines)