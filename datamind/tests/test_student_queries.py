import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from datamind.core.agent import DataMindAgent

def test_student_pipeline():
    agent = DataMindAgent()
    print(f"Active dataset: {agent.active_dataset_key}")
    print(f"Target table: {agent.dataset_info['table_name']}")

    queries = [
        "Compare the pass rate and average final grade between Math and Portuguese students",
        "What is the average final grade across weekly study time levels?",
        "what about female students in math"
    ]

    for q in queries:
        print(f"\n==========================================")
        print(f"USER QUERY: {q}")
        print(f"==========================================")
        res = agent.answer_question(q)
        print(f"STATUS: {res.get('status')}")
        print(f"GENERATED SQL:\n{res.get('sql')}\n")
        print(f"EXECUTION TIME: {res.get('execution_time_ms')} ms")
        print(f"ROWS RETURNED: {len(res.get('rows', []))}")
        print(f"DIRECT ANSWER:\n{res.get('direct_answer')}\n")

if __name__ == "__main__":
    test_student_pipeline()
