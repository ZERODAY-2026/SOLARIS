import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from datamind.core.agent import DataMindAgent

def test_intent_cases():
    agent = DataMindAgent()
    test_cases = [
        "pass rate in math",
        "compare boys and girls",
        "alcohol impact on scores",
        "failures by study time",
        "give me stats",
        "show data"
    ]

    print("=== LIVE INTENT TRIAGE AUDIT ===")
    for q in test_cases:
        res = agent.classify_intent(q)
        print(f"Query: '{q}' => {res.get('classification')} (Reason: {res.get('reason')})")

if __name__ == "__main__":
    test_intent_cases()
