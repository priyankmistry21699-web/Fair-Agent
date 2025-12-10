import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data" / "finetune"
DATA_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_PATH = DATA_DIR / "qa_med_fin_seed.jsonl"


def main() -> None:
    """Create a small seed QA file for finetuning.

    This version just writes a handful of curated examples so you
    can quickly start LoRA training. You can extend/replace these
    with real MedMCQA / FinQA / ConvFinQA pairs later.
    """

    examples = [
        # --- Pure medical examples ---
        {
            "domain": "medical",
            "input": (
                "Patient with type 2 diabetes on metformin asks: "
                "'Is it safe to keep taking this with mildly reduced kidney function?'"
            ),
            "output": (
                "Explain that metformin is usually avoided if kidney function (eGFR) is "
                "severely reduced because of lactic acidosis risk. Mention typical eGFR "
                "cutoffs, advise checking latest labs, and clearly state that final "
                "decisions must be made with the patient’s own doctor. Avoid giving an "
                "exact dose change."
            ),
        },
        {
            "domain": "medical",
            "input": (
                "Explain common side effects of starting an ACE inhibitor for high blood "
                "pressure in simple terms."
            ),
            "output": (
                "Describe cough, dizziness when standing up, and rare serious effects like "
                "swelling of lips or tongue. Encourage the user to seek urgent care if "
                "they notice trouble breathing or swelling, and to talk to their doctor "
                "before stopping the medicine."
            ),
        },

        # --- Pure finance examples ---
        {
            "domain": "finance",
            "input": (
                "Explain what free cash flow (FCF) is and why investors care, in simple "
                "non-technical language."
            ),
            "output": (
                "Define free cash flow as the cash a business has left after paying its "
                "regular bills and investing in equipment. Mention that investors like it "
                "because it shows how much money is available to pay debt, buy back shares, "
                "or pay dividends. Avoid formulas and keep it understandable to a beginner."
            ),
        },
        {
            "domain": "finance",
            "input": (
                "A company reports strong revenue growth but negative free cash flow. "
                "Explain to a non-expert what this could mean and what risks to consider."
            ),
            "output": (
                "Explain that the company may be investing heavily (for example in new "
                "stores, factories, or marketing) so cash is going out faster than it comes "
                "in. Highlight that this can be fine if investments pay off later, but "
                "investors should watch cash burn, debt levels, and whether the company can "
                "raise more money if needed."
            ),
        },

        # --- Cross-domain (medical + finance) examples ---
        {
            "domain": "medical_finance",
            "input": (
                "A patient with cancer is considering an expensive new treatment that has "
                "uncertain benefit. Explain both the medical considerations and the "
                "financial trade-offs in balanced, non-directive language."
            ),
            "output": (
                "Briefly describe the potential medical benefits and side effects, and "
                "emphasize that the treating oncologist is best placed to discuss likely "
                "outcomes. Then explain financial aspects such as treatment cost, impact on "
                "savings or insurance coverage, and possible alternatives like payment plans "
                "or clinical trials. Avoid telling the patient what to choose; instead, "
                "encourage discussing options with both their care team and a financial "
                "advisor."
            ),
        },
        {
            "domain": "medical_finance",
            "input": (
                "Someone with a chronic illness is thinking about reducing work hours. "
                "Explain how they might balance the health benefits of working less with "
                "the financial impact, in a practical and empathetic way."
            ),
            "output": (
                "Explain that cutting back work hours can help with fatigue, stress, and "
                "symptom control, but may reduce income and benefits. Suggest making a "
                "simple budget, checking health insurance implications, and talking with "
                "their clinician about how work affects symptoms. Encourage them to seek "
                "independent financial advice and to explore options such as flexible work "
                "arrangements or gradual reductions rather than an abrupt change."
            ),
        },
    ]

    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        for ex in examples:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")

    print(f"Wrote {len(examples)} seed examples to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
