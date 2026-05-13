"""
NER Agent — Regex + keyword based biomedical entity extraction.
Extracts drug names, conditions, and biological entities from trial text.
Uses a deterministic approach that works reliably without external API calls.
"""
import re
import logging

logger = logging.getLogger(__name__)

# Common drug/intervention suffixes used in clinical trials
DRUG_SUFFIXES = re.compile(
    r'\b\w+(?:mab|nib|zumab|ximab|lumab|tinib|ciclib|rafenib|lizumab|'
    r'parib|vastatin|sartan|pril|olol|azole|mycin|cycline|cillin|'
    r'oxacin|tadine|tidine|dipine|lukast|tropin|steride|fenac|'
    r'setron|triptan|dronate|vir|ide|ine|one|ol)\b',
    re.IGNORECASE
)

# Common clinical condition keywords
CONDITION_KEYWORDS = [
    "cancer", "carcinoma", "tumor", "tumour", "sarcoma", "lymphoma", "leukemia",
    "melanoma", "glioma", "myeloma", "adenoma",
    "diabetes", "hypertension", "obesity", "asthma", "copd",
    "alzheimer", "parkinson", "dementia", "depression", "anxiety", "schizophrenia",
    "stroke", "ischemia", "infarction", "heart failure", "atrial fibrillation",
    "arthritis", "lupus", "psoriasis", "eczema", "fibromyalgia", "osteoporosis",
    "hepatitis", "cirrhosis", "pancreatitis", "crohn", "colitis",
    "sepsis", "infection", "hiv", "covid", "influenza",
    "anemia", "thrombosis", "hemophilia",
    "epilepsy", "migraine", "neuropathy", "sclerosis",
    "renal failure", "kidney disease", "liver disease",
    "narcolepsy", "insomnia", "sleep apnea",
]

CONDITION_PATTERN = re.compile(
    r'\b(' + '|'.join(re.escape(k) for k in CONDITION_KEYWORDS) + r')\b',
    re.IGNORECASE
)


async def run_ner(text: str) -> dict:
    """
    Extract drug names and conditions from trial text using regex patterns.
    Returns dict with 'drugs' and 'conditions' lists.
    """
    if not text or len(text.strip()) < 10:
        return {"drugs": [], "conditions": []}

    truncated = text[:3000]

    drugs = set()
    conditions = set()

    # Extract drug-like words by suffix patterns
    for match in DRUG_SUFFIXES.finditer(truncated):
        word = match.group(0).strip()
        if len(word) >= 4:
            drugs.add(word.lower())

    # Extract condition keywords
    for match in CONDITION_PATTERN.finditer(truncated):
        word = match.group(0).strip()
        conditions.add(word.lower())

    # Also extract capitalized multi-word terms that look like proper drug names
    # e.g. "Tocilizumab", "AXS-14", "ALKS 2680"
    proper_drug = re.findall(r'\b[A-Z][a-z]+-?\d*\b|\b[A-Z]{2,}-?\d+\b', truncated)
    for w in proper_drug:
        if len(w) >= 4 and not w.lower() in {"phase", "study", "trial", "this", "that", "with"}:
            drugs.add(w)

    logger.debug(f"NER extracted: {len(drugs)} drugs, {len(conditions)} conditions")
    return {
        "drugs": sorted(drugs)[:20],       # cap at 20 to avoid noise
        "conditions": sorted(conditions)[:15],
    }
