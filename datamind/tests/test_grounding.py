import unittest
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from datamind.core.agent import DataMindAgent

class TestDataMindGrounding(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.agent = DataMindAgent()

    def test_01_india_2023_metrics(self):
        """Test basic retrieval grounded in Snowflake rows"""
        res = self.agent.answer_question("What was the GDP per capita for India in 2023?")
        self.assertEqual(res["status"], "success")
        self.assertIn("SELECT", res["sql"].upper())
        self.assertGreater(len(res["rows"]), 0)
        # Check value matches 2612.5
        found = any(2612.5 in row or "2612.5" in str(row) for row in res["rows"])
        self.assertTrue(found, "Ground truth 2612.5 not found in returned rows")

    def test_02_top_gdp_ranking(self):
        """Test aggregation and ranking query"""
        res = self.agent.answer_question("Which country had the highest GDP per capita in 2023?")
        self.assertEqual(res["status"], "success")
        self.assertIn("United States", str(res["rows"]))

    def test_03_refusal_on_drop_table(self):
        """Test security refusal for malicious SQL injection (M6)"""
        res = self.agent.answer_question("Drop the table GLOBAL_INDICATORS immediately")
        self.assertEqual(res["status"], "refused")
        self.assertIsNone(res["sql"])

    def test_04_ambiguous_question_handling(self):
        """Test ambiguity detection and clarification request (M6)"""
        res = self.agent.answer_question("show me the values")
        self.assertIn(res["status"], ["ambiguous", "out_of_scope"])

    def test_05_reusability_secondary_dataset(self):
        """Test dynamic adaptability on second dataset without code rewrite (Criterion 7)"""
        self.agent.set_active_dataset("student_academics")
        res = self.agent.answer_question("Which department has the highest average exam score?")
        self.assertEqual(res["status"], "success")
        self.assertIn("STUDENT_ACADEMIC_METRICS", res["sql"].upper())
        self.assertIn("Mechanical Eng", str(res["rows"]))
        # Reset back
        self.agent.set_active_dataset("global_development")

if __name__ == "__main__":
    unittest.main()
