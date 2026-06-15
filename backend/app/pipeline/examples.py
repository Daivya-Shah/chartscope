"""Curated synthetic example notes for HCC gap-engine demos.

All notes are fully synthetic — no real PHI. Each deliberately omits at least one
ICD-10 code that is clearly documented in the note text.
"""

from app.models.schemas import ExampleNote

EXAMPLE_NOTES: list[ExampleNote] = [
    ExampleNote(
        id="ex-diabetes-complications",
        title="Diabetes with CKD & Neuropathy",
        specialty="Endocrinology",
        description="Type 2 DM with documented diabetic CKD and polyneuropathy",
        note_text=(
            "SYNTHETIC PATIENT — MRN SYN-10042\n\n"
            "CHIEF COMPLAINT: Diabetes follow-up\n\n"
            "HISTORY OF PRESENT ILLNESS:\n"
            "68-year-old male with 12-year history of type 2 diabetes mellitus. "
            "HbA1c today 8.4%. Reports bilateral foot numbness and burning pain "
            "consistent with diabetic peripheral polyneuropathy. Recent nephrology "
            "consult confirmed diabetic chronic kidney disease; eGFR 38 mL/min/1.73m² "
            "(stage 3b). No chest pain or dyspnea.\n\n"
            "MEDICATIONS: metformin 1000 mg BID, lisinopril 20 mg daily, "
            "gabapentin 300 mg TID for neuropathic pain.\n\n"
            "ASSESSMENT:\n"
            "1. Type 2 diabetes mellitus — suboptimal control.\n"
            "2. Diabetic chronic kidney disease, stage 3b.\n"
            "3. Diabetic peripheral polyneuropathy.\n\n"
            "PLAN: Intensify glycemic management; continue ACE-i; nephrology follow-up in 3 months."
        ),
        # Claims only uncomplicated diabetes + hypertension — omits E11.22 (diabetic CKD)
        # and E11.42 (polyneuropathy) despite explicit documentation above.
        claimed_codes=["E11.9", "I10"],
        # expected_gap: E11.22 (diabetic CKD) and E11.42 (diabetic polyneuropathy) are
        # clearly documented but absent from claimed_codes → suspected HCC gaps later.
    ),
    ExampleNote(
        id="ex-chf-systolic",
        title="Heart Failure — Reduced EF",
        specialty="Cardiology",
        description="HFrEF with volume overload; hypertension on claim",
        note_text=(
            "SYNTHETIC PATIENT — MRN SYN-20017\n\n"
            "CHIEF COMPLAINT: Worsening dyspnea and leg swelling\n\n"
            "HISTORY OF PRESENT ILLNESS:\n"
            "74-year-old female with known chronic systolic congestive heart failure "
            "(HFrEF). Most recent echocardiogram shows left ventricular ejection fraction "
            "of 30%. Presents with 5-pound weight gain, orthopnea, and 2+ pitting edema "
            "bilaterally. Denies fever or chest pain.\n\n"
            "MEDICATIONS: carvedilol 25 mg BID, furosemide 40 mg daily, spironolactone 25 mg daily.\n\n"
            "ASSESSMENT:\n"
            "1. Acute on chronic systolic congestive heart failure exacerbation.\n"
            "2. Hypertension — at goal.\n\n"
            "PLAN: Increase furosemide to 80 mg daily; daily weights; cardiology follow-up in 1 week."
        ),
        # Claims hypertension only — omits I50.22 (chronic systolic CHF) despite EF 30%
        # and explicit CHF documentation in assessment.
        claimed_codes=["I10"],
        # expected_gap: I50.22 (chronic systolic heart failure) documented but not claimed.
    ),
    ExampleNote(
        id="ex-copd-exacerbation",
        title="COPD Exacerbation",
        specialty="Pulmonology",
        description="Acute COPD flare with increased dyspnea and purulent sputum",
        note_text=(
            "SYNTHETIC PATIENT — MRN SYN-30008\n\n"
            "CHIEF COMPLAINT: Worsening shortness of breath and cough\n\n"
            "HISTORY OF PRESENT ILLNESS:\n"
            "71-year-old male with 40 pack-year smoking history and chronic obstructive "
            "pulmonary disease. Presents with 4 days of increased dyspnea, wheezing, and "
            "purulent sputum production consistent with an acute COPD exacerbation. "
            "Oxygen saturation 88% on room air, improved to 93% on 2L nasal cannula. "
            "No pleuritic chest pain.\n\n"
            "MEDICATIONS: tiotropium, albuterol inhaler PRN, prednisone 40 mg daily "
            "(started today), azithromycin.\n\n"
            "ASSESSMENT:\n"
            "1. Chronic obstructive pulmonary disease with acute exacerbation.\n"
            "2. Hypoxemia — responsive to supplemental oxygen.\n\n"
            "PLAN: Complete 5-day steroid course; antibiotics; pulmonary follow-up in 2 weeks."
        ),
        # Claims unspecified COPD only — omits J44.1 (COPD with acute exacerbation)
        # despite explicit acute exacerbation language in HPI and assessment.
        claimed_codes=["J44.9", "I10"],
        # expected_gap: J44.1 (COPD with acute exacerbation) documented but not claimed.
    ),
]
