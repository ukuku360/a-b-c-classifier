from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_XLSX = PROJECT_ROOT / "token404_sample_yh.xlsx"

ISSUE_LABEL = "ISSUE"
REMEDIATION_LABEL = "REMEDIATION"
OTHER_LABEL = "OTHER"

LABELS = (ISSUE_LABEL, REMEDIATION_LABEL, OTHER_LABEL)
PRIMARY_LABELS = (ISSUE_LABEL, REMEDIATION_LABEL)
LABEL_ALIASES = {
    "A": ISSUE_LABEL,
    "ISSUE": ISSUE_LABEL,
    "B": REMEDIATION_LABEL,
    "REMEDIATION": REMEDIATION_LABEL,
    "C": OTHER_LABEL,
    "OTHER": OTHER_LABEL,
}
C_SUBTYPES = ("background", "status", "effect", "attestation", "other")

LEGACY_HINT_COLUMNS = (
    "impact",
    "remediation",
    "attestation",
    "find_opinion",
    "find_remedia_header",
    "remedia_start_seq",
)

BANNED_FEATURES = (
    "impact",
    "remediation",
    "attestation",
    "find_opinion",
    "find_remedia_header",
    "remedia_start_seq",
    "mgt_opinion",
    "opinion_404_mgt_q0",
    "opinion_404_mgt_q4",
    "opinion_404_audit_q0",
    "opinion_404_audit_q4",
    "count_weak",
    "noteff_acc_rule",
    "noteff_acc_reas_keys",
    "noteff_acc_reas_phr",
    "noteff_fin_fraud",
    "noteff_finfraud_keys",
    "noteff_finfraud_phr",
    "notefferrors",
    "exe_reas_keys",
    "noteff_reas_phr",
    "noteff_other",
    "noteff_other_reas_keys",
    "noteff_other_reas_phr",
    "audit_fees",
    "non_audit_fees",
    "matchqu_tso_markcap",
    "seq",
)

DEFAULT_TEST_DOCS = 20
DEFAULT_RANDOM_STATE = 42
DEFAULT_PROB_THRESHOLD = 0.85
DEFAULT_MARGIN_THRESHOLD = 0.20
TARGET_AUTO_PRECISION = 0.90
SHORT_SENTENCE_CHARS = 140

THRESHOLD_GRID = tuple(round(x, 2) for x in (0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95))

MODEL_SPECS = (
    {
        "name": "centroid_e5",
        "embedding_model": "intfloat/e5-large-v2",
        "classifier": "centroid",
        "calibration_method": None,
    },
    {
        "name": "e5_logreg",
        "embedding_model": "intfloat/e5-large-v2",
        "classifier": "logreg",
        "calibration_method": "sigmoid",
    },
    {
        "name": "bge_svm",
        "embedding_model": "BAAI/bge-base-en-v1.5",
        "classifier": "linear_svm",
        "calibration_method": "sigmoid",
    },
)


def normalize_label(value: object) -> str:
    text = "" if value is None else str(value).strip()
    if not text or text.lower() == "nan":
        return ""
    return LABEL_ALIASES.get(text.upper(), text)
