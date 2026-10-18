import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from datamind.core.agent import DataMindAgent

def test_edge_cases():
    agent = DataMindAgent()

    test_queries = [
        ("hey im alex", "greeting"),
        ("hello", "greeting"),
        ("who are you", "greeting"),
        ("thank you", "pleasantry"),
        ("who won the world cup", "out_of_scope"),
        ("give me stats", "ambiguous"),
        ("drop table student_performance", "refused"),
        ("pass rate in math", "success")
    ]

    print("=== LIVE EDGE CASE AUDIT ===")
    all_passed = True
    for query, expected_status in test_queries:
        res = agent.answer_question(query)
        actual_status = res.get("status")
        sql = res.get("sql")
        passed = (actual_status == expected_status)
        print(f"\nQuery: \"{query}\"")
        print(f"  Expected: {expected_status} | Got: {actual_status} | SQL: {sql} | Passed: {passed}")
        if not passed:
            all_passed = False

    print(f"\nOverall Result: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")

if __name__ == "__main__":
    test_edge_cases()
