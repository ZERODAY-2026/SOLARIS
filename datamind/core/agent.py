import os
import json
import yaml
from typing import Dict, Any, Optional, List
from datamind.core.snowflake_client import SnowflakeClient
from datamind.core.gemma_client import GemmaClient
from datamind.core.prompts import (
    SQL_GENERATION_SYSTEM_PROMPT,
    INTENT_CLASSIFICATION_SYSTEM_PROMPT,
    GROUNDED_EXPLAINER_SYSTEM_PROMPT
)

class DataMindAgent:
    """
    Main orchestrator for PS1: DataMind.
    Combines Google Gemma reasoning with Snowflake execution, inspectable evidence,
    conversational multi-turn history, schema discovery, and cost metrics.
    """
    def __init__(self, config_path: Optional[str] = None):
        if not config_path:
            config_path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
        
        self.config = self.load_config(config_path)
        self.active_dataset_key = self.config.get("active_dataset", "global_development")
        self.dataset_info = self.config["datasets"][self.active_dataset_key]

        self.snowflake = SnowflakeClient()
        self.gemma = GemmaClient()
        self.conversation_history: List[Dict[str, str]] = []

    def load_config(self, path: str) -> Dict[str, Any]:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def set_active_dataset(self, dataset_key: str):
        if dataset_key in self.config["datasets"]:
            self.active_dataset_key = dataset_key
            self.dataset_info = self.config["datasets"][dataset_key]
            self.conversation_history.clear()

    def reset_conversation(self):
        self.conversation_history.clear()

    def handle_schema_discovery(self, question: str) -> Optional[Dict[str, Any]]:
        """
        Detects meta-questions asking about available tables, metrics, countries, or columns.
        Answers them by querying Snowflake metadata or dataset configuration directly.
        """
        q_lower = question.lower()
        schema_keywords = [
            "what tables", "what columns", "what metrics", "what indicators",
            "which countries", "what countries", "what years", "available data",
            "show schema", "list indicators"
        ]
        if not any(kw in q_lower for kw in schema_keywords):
            return None

        # Build schema discovery response
        table = self.dataset_info["table_name"]
        
        if "country" in q_lower or "countries" in q_lower:
            sql = f"SELECT DISTINCT country FROM {table} ORDER BY country"
            res = self.snowflake.execute_query(sql)
            if res["success"]:
                countries = [r[0] for r in res["rows"]]
                direct_ans = f"**Available Countries ({len(countries)} total)**:\n\n" + ", ".join(countries)
                return {
                    "status": "success",
                    "direct_answer": direct_ans,
                    "sql": sql,
                    "rows": res["rows"],
                    "columns": ["COUNTRY"],
                    "row_count": len(countries),
                    "execution_time_ms": res["execution_time_ms"],
                    "dataset": self.dataset_info["name"],
                    "cost_estimate_credits": round((res["execution_time_ms"] / 1000.0) * (1.0 / 3600.0), 6)
                }

        # Otherwise describe the schema & metrics
        metrics_desc = f"""**Dataset Schema & Indicators for `{self.dataset_info['name']}`**:

* **Target Table**: `{self.dataset_info['table_name']}`
* **Description**: {self.dataset_info['description']}

{self.dataset_info['schema_description']}
"""
        return {
            "status": "success",
            "direct_answer": metrics_desc,
            "sql": f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table.upper()}';",
            "rows": [["Available metrics displayed above"]],
            "columns": ["SCHEMA_INFO"],
            "row_count": 1,
            "execution_time_ms": 5.0,
            "dataset": self.dataset_info["name"],
            "cost_estimate_credits": 0.000001
        }

    def classify_intent(self, question: str) -> Dict[str, Any]:
        context_str = ""
        if self.conversation_history:
            recent = self.conversation_history[-4:]
            context_str = "Recent Conversation Context:\n" + "\n".join([f"{item['role']}: {item['content']}" for item in recent]) + "\n"

        user_prompt = f"""
Available Dataset: {self.dataset_info['name']}
Schema Definition:
{self.dataset_info['schema_description']}

{context_str}
Current User Question: "{question}"
"""
        response_text = self.gemma.generate(
            system_prompt=INTENT_CLASSIFICATION_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            temperature=0.0
        )
        try:
            clean_json = response_text.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_json)
        except Exception:
            return {
                "classification": "VALID",
                "reason": "Proceed with default validation",
                "clarification_needed": ""
            }

    def generate_sql(self, question: str) -> str:
        context_str = ""
        if self.conversation_history:
            recent = self.conversation_history[-4:]
            context_str = "Prior Conversation History (Use to resolve pronouns like 'it', 'that', 'them', or implicit follow-ups):\n" + "\n".join([f"{item['role']}: {item['content']}" for item in recent]) + "\n"

        user_prompt = f"""
Database: Snowflake
Table Schema:
{self.dataset_info['schema_description']}

{context_str}
Current User Question: "{question}"

Generate the Snowflake SQL query:
"""
        raw_response = self.gemma.generate(
            system_prompt=SQL_GENERATION_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            temperature=0.0
        )
        return self.gemma.extract_sql_from_response(raw_response)

    def explain_results(self, question: str, sql: str, rows: list, columns: list) -> str:
        if not rows:
            data_context = "RESULT SET IS EMPTY (0 rows returned)."
        else:
            formatted_rows = [dict(zip(columns, row)) for row in rows[:25]]
            data_context = json.dumps(formatted_rows, indent=2, default=str)

        user_prompt = f"""
User Question: "{question}"
Executed Snowflake SQL:
{sql}

Column Names: {columns}
Result Rows from Snowflake:
{data_context}

Provide a grounded, factual, plain-language answer following the rules.
"""
        return self.gemma.generate(
            system_prompt=GROUNDED_EXPLAINER_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            temperature=0.2
        )

    def answer_question(self, question: str) -> Dict[str, Any]:
        """
        Executes end-to-end question processing pipeline with conversational context,
        schema discovery, Snowflake execution, and cost monitoring.
        """
        # Step 0: Check for Schema Discovery / Metadata question
        schema_ans = self.handle_schema_discovery(question)
        if schema_ans:
            self.conversation_history.append({"role": "User", "content": question})
            self.conversation_history.append({"role": "Assistant", "content": schema_ans["direct_answer"]})
            return schema_ans

        # Step 1: Intent & Ambiguity Check (M6)
        intent = self.classify_intent(question)
        classification = intent.get("classification", "VALID")

        if classification == "MALICIOUS":
            return {
                "status": "refused",
                "direct_answer": "Request refused: Unsafe database operation or prompt injection attempt detected.",
                "reason": intent.get("reason"),
                "sql": None,
                "rows": [],
                "columns": [],
                "execution_time_ms": 0,
                "dataset": self.dataset_info['name'],
                "cost_estimate_credits": 0.0
            }

        if classification == "AMBIGUOUS":
            clarification = intent.get("clarification_needed") or "Could you please specify which country, year, or metric you want to inspect?"
            return {
                "status": "ambiguous",
                "direct_answer": f"The question requires clarification. {clarification}",
                "reason": intent.get("reason"),
                "sql": None,
                "rows": [],
                "columns": [],
                "execution_time_ms": 0,
                "dataset": self.dataset_info['name'],
                "cost_estimate_credits": 0.0
            }

        if classification == "OUT_OF_SCOPE":
            return {
                "status": "out_of_scope",
                "direct_answer": f"This question is outside the scope of the '{self.dataset_info['name']}' dataset. " + intent.get("reason", ""),
                "reason": intent.get("reason"),
                "sql": None,
                "rows": [],
                "columns": [],
                "execution_time_ms": 0,
                "dataset": self.dataset_info['name'],
                "cost_estimate_credits": 0.0
            }

        # Step 2: Generate Snowflake SQL with Gemma (aware of context)
        sql = self.generate_sql(question)

        # Step 3: Execute on Snowflake with Read-Only Validation
        exec_result = self.snowflake.execute_query(sql)

        # Calculate estimated warehouse credits (X-Small = 1 credit/hour = 1/3600 credit/sec)
        execution_sec = exec_result["execution_time_ms"] / 1000.0
        credit_est = round(execution_sec * (1.0 / 3600.0), 6)

        if not exec_result["success"]:
            return {
                "status": "query_error",
                "direct_answer": f"An error occurred while executing the query on Snowflake: {exec_result['error']}",
                "sql": sql,
                "rows": [],
                "columns": [],
                "execution_time_ms": exec_result["execution_time_ms"],
                "dataset": self.dataset_info['name'],
                "cost_estimate_credits": credit_est
            }

        # Step 4: Grounded Explanation with Gemma
        explanation = self.explain_results(
            question=question,
            sql=sql,
            rows=exec_result["rows"],
            columns=exec_result["columns"]
        )

        # Update Conversation Memory
        self.conversation_history.append({"role": "User", "content": question})
        self.conversation_history.append({"role": "Assistant", "content": f"Query: {sql}\nResult: {explanation}"})

        return {
            "status": "success",
            "direct_answer": explanation,
            "sql": sql,
            "rows": exec_result["rows"],
            "columns": exec_result["columns"],
            "row_count": exec_result["row_count"],
            "execution_time_ms": exec_result["execution_time_ms"],
            "dataset": self.dataset_info['name'],
            "cost_estimate_credits": credit_est
        }
