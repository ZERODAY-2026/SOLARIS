import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from datamind.core.agent import DataMindAgent

def test_typos():
    agent = DataMindAgent()
    test_queries = [
        "Wat was Indias gdp in 2023?",           # Typos: Wat, Indias
        "compar CO2 emisions of Chna and Us in 2022", # Typos: compar, emisions, Chna, Us
        "show me populashun of germny in 2021"   # Typos: populashun, germny
    ]

    for q in test_queries:
        print(f"\n==========================================")
        print(f"QUERY WITH TYPOS: {q}")
        print(f"==========================================")
        res = agent.answer_question(q)
        print("STATUS:", res["status"])
        print("RESOLVED SQL:\n", res["sql"])
        print("ROWS FETCHED:", res["rows"])
        print("DIRECT ANSWER:\n", res["direct_answer"][:280] + "...")

if __name__ == "__main__":
    test_typos()
