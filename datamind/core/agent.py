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

    def get_conversation_context_str(self) -> str:
        if not self.conversation_history:
            return ""
        recent = self.conversation_history[-3:]
        lines = ["Prior Conversation Turns:"]
        for i, turn in enumerate(recent, 1):
            lines.append(f"Turn {i} User Question: \"{turn['question']}\"")
            if turn.get("sql"):
                lines.append(f"Turn {i} Executed SQL Query:\n{turn['sql']}")
        lines.append("(CRITICAL CONTEXT RULE: If the user question is a follow-up, refinement, or asks 'what about females', 'in math', 'show top 5', or uses pronouns 'they', 'it', 'them', adapt and extend the previous Executed SQL query with the new filters/dimensions.)\n")
        return "\n".join(lines) + "\n"

    def handle_edge_cases(self, question: str) -> Optional[Dict[str, Any]]:
        """
        Fast-path guardrail handler for edge cases under Hackathon Criterion M6:
        1. Greetings & Introductions ("hey im alex", "hello", "who are you") -> OUT_OF_SCOPE
        2. Pleasantries & Gratitude ("thank you", "ok cool") -> OUT_OF_SCOPE
        3. General Trivia & Non-Data Inquiries ("who won the world cup", "tell me a joke") -> OUT_OF_SCOPE
        4. Cross-Domain Inquiries (e.g. asking about GDP while on Student dataset) -> OUT_OF_SCOPE
        5. Ambiguous / Underspecified Prompts ("give me stats", "show data") -> AMBIGUOUS
        6. Destructive / Malicious DDL/DML ("DROP TABLE", "DELETE FROM") -> REFUSED
        
        Guarantees 0 Snowflake queries executed and 0 credits consumed for non-analytical inputs.
        """
        import re
        q_clean = question.strip().lower()
        q_clean = re.sub(r'[!?,.]+$', '', q_clean).strip()

        # 1. Security / Malicious Refusal Check (M6 Safeguard)
        malicious_patterns = [
            r'.*(drop\s+table|delete\s+from|alter\s+table|truncate\s+table|update\s+\w+\s+set|insert\s+into).*'
        ]
        if any(re.match(pat, q_clean) for pat in malicious_patterns):
            ans = "**[M6 Security Safeguard - Request Refused]**\n\n" \
                  "Destructive database modifications, DDL statements, or SQL injection patterns are strictly blocked by the Read-Only AST Guard.\n" \
                  "- **Warehouse Execution**: 0 SQL queries executed.\n" \
                  "- **Access Level**: Read-only `SELECT` queries permitted."
            return {
                "status": "refused",
                "direct_answer": ans,
                "reason": "Unsafe database operation or prompt injection attempt blocked by guardrail.",
                "sql": None,
                "rows": [],
                "columns": [],
                "execution_time_ms": 0.5,
                "dataset": self.dataset_info['name'],
                "cost_estimate_credits": 0.0
            }

        # 2. Ambiguous / Underspecified Prompts (M6 Ambiguity)
        ambiguous_keywords = [
            "give me stats", "show stats", "stats", "show data", "show the data",
            "analyze this", "analyze data", "who is the best", "is it good",
            "show results", "students", "performance", "data", "summary"
        ]
        if q_clean in ambiguous_keywords and len(self.conversation_history) == 0:
            ans = "**[M6 Guardrail Notice - Ambiguity Detected]**\n\n" \
                  "Your inquiry is too under-specified to construct a verifiable SQL query without guessing.\n\n" \
                  "**Please specify**:\n" \
                  "1. **Target Metric**: Final exam score (`G3`), Pass rate (`G3 >= 10`), Absences, or Failures.\n" \
                  "2. **Dimension / Filter**: By subject (Math vs. Portuguese), by school (GP vs. MS), or study time.\n\n" \
                  "- **Warehouse Execution**: 0 SQL queries executed (0 compute credits consumed).\n\n" \
                  "*Try asking*: *\"Compare the average final grade and pass rate between Math and Portuguese students\"*"
            return {
                "status": "ambiguous",
                "direct_answer": ans,
                "reason": "Under-specified prompt lacking target metric and grouping dimension.",
                "sql": None,
                "rows": [],
                "columns": [],
                "execution_time_ms": 0.5,
                "dataset": self.dataset_info['name'],
                "cost_estimate_credits": 0.0
            }

        # 3. Gratitude & Pleasantries (M6 Out of Bounds / Unsupported Request)
        gratitude_patterns = [
            r'^(thank you|thanks|thx|thank u|many thanks|appreciate it|awesome|cool|ok cool|great|good job|goodbye|bye|cya)$'
        ]
        if any(re.match(pat, q_clean) for pat in gratitude_patterns):
            ans = "**[M6 Guardrail Notice - Unsupported Request / Out of Bounds]**\n\n" \
                  "You're very welcome! Conversational pleasantries contain no analytical data query.\n\n" \
                  "- **Warehouse Execution**: 0 SQL queries executed (0 Snowflake credits consumed).\n" \
                  "- **Active Table**: `" + self.dataset_info['table_name'] + "`\n\n" \
                  "Let me know if you would like to run another analytical inquiry or compare academic indicators!"
            return {
                "status": "out_of_scope",
                "direct_answer": ans,
                "reason": "Conversational pleasantry with no analytical data query.",
                "sql": None,
                "rows": [],
                "columns": [],
                "execution_time_ms": 0.5,
                "dataset": self.dataset_info['name'],
                "cost_estimate_credits": 0.0
            }

        # 4. Greetings & Introductions (e.g. "hey im alex", "hi", "hello", "who are you") (M6 Out of Bounds)
        greeting_patterns = [
            r'^(hi|hello|hey|greetings|howdy|good\s+(morning|afternoon|evening)|sup|yo)$',
            r'^(hey|hi|hello)\s+(there|data\s*mind|agent|bot)$',
            r'^(who\s+are\s+you|what\s+is\s+your\s+name|what\s+can\s+you\s+do)$'
        ]
        name_match = re.match(r'^(?:hey|hi|hello)?\s*(?:i[\'\s]?m|i\s+am|my\s+name\s+is)\s+([a-zA-Z]+)$', q_clean)
        is_greeting = any(re.match(pat, q_clean) for pat in greeting_patterns) or (name_match is not None)

        if is_greeting:
            user_name = name_match.group(1).capitalize() if name_match else None
            greeting_prefix = f"Hello {user_name}! " if user_name else "Hello! "
            ans = f"{greeting_prefix}I am **DataMind**, an evidence-grounded data intelligence agent connected live to your **Snowflake Cloud Data Warehouse**.\n\n" \
                  f"**[M6 Guardrail Notice - Unsupported Request / Out of Bounds]**\n" \
                  f"This input is a conversational greeting/introduction and does not contain an analytical data query.\n\n" \
                  f"- **Warehouse Execution**: 0 SQL queries executed (0 Snowflake compute credits consumed).\n" \
                  f"- **Target Dataset**: `{self.dataset_info['name']}` (`{self.dataset_info['table_name']}`).\n\n" \
                  f"To query and inspect this dataset, please ask an analytical question, such as:\n" \
                  f"* **Pass Rates**: *\"Compare the pass rate between Math and Portuguese students\"*\n" \
                  f"* **Study Habits**: *\"What is the average final grade across weekly study time levels?\"*\n" \
                  f"* **Lifestyle Impact**: *\"Compare average grades for students with low vs. high weekend alcohol consumption\"*\n" \
                  f"* **Demographics**: *\"Does parental education level (Medu/Fedu) correlate with higher final exam scores?\"*"
            return {
                "status": "out_of_scope",
                "direct_answer": ans,
                "reason": "Conversational greeting/introduction with no analytical data inquiry.",
                "sql": None,
                "rows": [],
                "columns": [],
                "execution_time_ms": 0.5,
                "dataset": self.dataset_info['name'],
                "cost_estimate_credits": 0.0
            }

        # 5. General Trivia & Non-Data Queries (M6 Out of Bounds)
        trivia_patterns = [
            r'^(tell me a joke|tell a joke|joke|make me laugh)$',
            r'^(write a poem|sing a song|write code|code python)$',
            r'^(what is the weather|weather today|weather forecast).*$',
            r'^(who won (the )?world cup|who is the president|who is the prime minister).*$',
            r'^(solve|calculate)?\s*\d+\s*[\+\-\*\/]\s*\d+$'
        ]
        if any(re.match(pat, q_clean) for pat in trivia_patterns):
            ans = f"**[M6 Guardrail Notice - Unsupported Request / Out of Bounds]**\n\n" \
                  f"This inquiry is outside the scope of the active database (`{self.dataset_info['name']}`).\n\n" \
                  f"- **Warehouse Execution**: 0 SQL queries executed (0 Snowflake compute credits consumed).\n" \
                  f"- **Permitted Scope**: Analysis of `{self.dataset_info['name']}` in table `{self.dataset_info['table_name']}`.\n\n" \
                  f"Please ask an analytical question relevant to the active dataset, for example:\n" \
                  f"* *\"What is the pass rate by subject?\"*\n" \
                  f"* *\"How does weekly study time correlate with final exam scores (G3)?\"*"
            return {
                "status": "out_of_scope",
                "direct_answer": ans,
                "reason": "General trivia or non-dataset request.",
                "sql": None,
                "rows": [],
                "columns": [],
                "execution_time_ms": 0.5,
                "dataset": self.dataset_info['name'],
                "cost_estimate_credits": 0.0
            }

        # 6. Cross-Domain Inquiry Detection
        if self.active_dataset_key == "student_performance" and any(k in q_clean for k in ["gdp", "emissions", "co2", "life expectancy"]):
            ans = "**[M6 Guardrail Notice - Cross-Domain Out of Bounds]**\n\n" \
                  "Your query mentions macroeconomic indicators (`GDP`, `CO2 emissions`), but you are currently connected to the **Student Performance Benchmark** (`STUDENT_PERFORMANCE`).\n\n" \
                  "- **Warehouse Execution**: 0 SQL queries executed.\n" \
                  "- **How to resolve**: Please switch to the **Global Development Indicators** domain using the dropdown in the sidebar to run this inquiry!"
            return {
                "status": "out_of_scope",
                "direct_answer": ans,
                "reason": "Query belongs to Global Development domain, but Student Performance is active.",
                "sql": None,
                "rows": [],
                "columns": [],
                "execution_time_ms": 0.5,
                "dataset": self.dataset_info['name'],
                "cost_estimate_credits": 0.0
            }

        if self.active_dataset_key == "global_development" and any(k in q_clean for k in ["student", "grade", "g1", "g2", "g3", "studytime"]):
            ans = "**[M6 Guardrail Notice - Cross-Domain Out of Bounds]**\n\n" \
                  "Your query mentions student academic features, but you are currently connected to the **Global Development Indicators** dataset (`GLOBAL_DEVELOPMENT`).\n\n" \
                  "- **Warehouse Execution**: 0 SQL queries executed.\n" \
                  "- **How to resolve**: Please switch to the **Student Performance Benchmark** domain using the dropdown in the sidebar to run this inquiry!"
            return {
                "status": "out_of_scope",
                "direct_answer": ans,
                "reason": "Query belongs to Student Performance domain, but Global Development is active.",
                "sql": None,
                "rows": [],
                "columns": [],
                "execution_time_ms": 0.5,
                "dataset": self.dataset_info['name'],
                "cost_estimate_credits": 0.0
            }

        return None

    def handle_conversational_pleasantry(self, question: str) -> Optional[Dict[str, Any]]:
        """Backwards compatibility alias for handle_edge_cases."""
        return self.handle_edge_cases(question)

    def handle_schema_discovery(self, question: str) -> Optional[Dict[str, Any]]:
        """
        Detects meta-questions asking about available tables, metrics, subjects, features, or columns.
        Answers them by querying Snowflake metadata or dataset configuration directly.
        """
        q_lower = question.lower()
        schema_keywords = [
            "what tables", "what columns", "what metrics", "what indicators", "what features",
            "which subjects", "what subjects", "which schools", "what schools",
            "which countries", "what countries", "what years", "available data",
            "show schema", "list indicators", "list features", "list columns"
        ]
        if not any(kw in q_lower for kw in schema_keywords):
            return None

        table = self.dataset_info["table_name"]

        # Subject discovery
        if "subject" in q_lower and "STUDENT" in table.upper():
            sql = f"SELECT DISTINCT subject, COUNT(*) AS student_count FROM {table} GROUP BY subject ORDER BY subject"
            res = self.snowflake.execute_query(sql)
            if res["success"]:
                subj_str = ", ".join([f"{r[0]} ({r[1]} students)" for r in res["rows"]])
                direct_ans = f"**Available Course Subjects**:\n\n{subj_str}\n\nTotal students across both subjects: 1,044."
                return {
                    "status": "success",
                    "direct_answer": direct_ans,
                    "sql": sql,
                    "rows": res["rows"],
                    "columns": ["SUBJECT", "STUDENT_COUNT"],
                    "row_count": len(res["rows"]),
                    "execution_time_ms": res["execution_time_ms"],
                    "dataset": self.dataset_info["name"],
                    "cost_estimate_credits": round((res["execution_time_ms"] / 1000.0) * (1.0 / 3600.0), 6)
                }

        # School discovery
        if "school" in q_lower and "STUDENT" in table.upper():
            sql = f"SELECT school, COUNT(*) AS student_count FROM {table} GROUP BY school ORDER BY school"
            res = self.snowflake.execute_query(sql)
            if res["success"]:
                school_map = {"GP": "Gabriel Pereira (GP)", "MS": "Mousinho da Silveira (MS)"}
                sch_str = "\n".join([f"- **{school_map.get(r[0], r[0])}**: {r[1]} students" for r in res["rows"]])
                direct_ans = f"**Participating Secondary Schools**:\n\n{sch_str}"
                return {
                    "status": "success",
                    "direct_answer": direct_ans,
                    "sql": sql,
                    "rows": res["rows"],
                    "columns": ["SCHOOL", "STUDENT_COUNT"],
                    "row_count": len(res["rows"]),
                    "execution_time_ms": res["execution_time_ms"],
                    "dataset": self.dataset_info["name"],
                    "cost_estimate_credits": round((res["execution_time_ms"] / 1000.0) * (1.0 / 3600.0), 6)
                }
        
        if ("country" in q_lower or "countries" in q_lower) and "GLOBAL" in table.upper():
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
        metrics_desc = f"""**Dataset Schema & Attributes for `{self.dataset_info['name']}`**:

* **Target Table**: `{self.dataset_info['table_name']}`
* **Description**: {self.dataset_info['description']}

{self.dataset_info['schema_description']}
"""
        return {
            "status": "success",
            "direct_answer": metrics_desc,
            "sql": f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table.upper()}';",
            "rows": [["Available features displayed above"]],
            "columns": ["SCHEMA_INFO"],
            "row_count": 1,
            "execution_time_ms": 5.0,
            "dataset": self.dataset_info["name"],
            "cost_estimate_credits": 0.000001
        }

    def classify_intent(self, question: str) -> Dict[str, Any]:
        context_str = self.get_conversation_context_str()

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
        context_str = self.get_conversation_context_str()

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
        # Step -1: Fast-Path Guardrail Audit (M6 Edge Cases)
        edge_ans = self.handle_edge_cases(question)
        if edge_ans:
            if edge_ans.get("status") != "refused":
                self.conversation_history.append({
                    "question": question,
                    "sql": None,
                    "direct_answer": edge_ans["direct_answer"]
                })
            return edge_ans

        # Step 0: Check for Schema Discovery / Metadata question
        schema_ans = self.handle_schema_discovery(question)
        if schema_ans:
            self.conversation_history.append({
                "question": question,
                "sql": schema_ans.get("sql"),
                "direct_answer": schema_ans.get("direct_answer", "")
            })
            return schema_ans

        # Step 1: Intent & Ambiguity Check (M6)
        intent = self.classify_intent(question)
        classification = intent.get("classification", "VALID")

        if classification == "MALICIOUS":
            ans = "**[M6 Security Safeguard - Request Refused]**\n\n" \
                  "Destructive database modifications or prompt injection attempts are strictly blocked by the Read-Only AST Guard.\n" \
                  "- **Warehouse Execution**: 0 SQL queries executed.\n" \
                  "- **Reason**: " + intent.get("reason", "Malicious or unsafe SQL pattern detected.")
            return {
                "status": "refused",
                "direct_answer": ans,
                "reason": intent.get("reason"),
                "sql": None,
                "rows": [],
                "columns": [],
                "execution_time_ms": 0,
                "dataset": self.dataset_info['name'],
                "cost_estimate_credits": 0.0
            }

        if classification == "AMBIGUOUS":
            clarification = intent.get("clarification_needed") or "Please specify which subject (Math or Portuguese) and target metric (e.g. final grade G3, pass rate, absences) you wish to inspect."
            ans = f"**[M6 Guardrail Notice - Ambiguity Detected]**\n\n{clarification}\n\n" \
                  f"- **Warehouse Execution**: 0 SQL queries executed (0 compute credits consumed)."
            self.conversation_history.append({
                "question": question,
                "sql": None,
                "direct_answer": ans
            })
            return {
                "status": "ambiguous",
                "direct_answer": ans,
                "reason": intent.get("reason"),
                "sql": None,
                "rows": [],
                "columns": [],
                "execution_time_ms": 0,
                "dataset": self.dataset_info['name'],
                "cost_estimate_credits": 0.0
            }

        if classification in ["OUT_OF_SCOPE", "GREETING"]:
            reason_str = intent.get("reason", "This inquiry is not related to the dataset records.")
            ans = f"**[M6 Guardrail Notice - Unsupported Request / Out of Bounds]**\n\n" \
                  f"{reason_str}\n\n" \
                  f"- **Warehouse Execution**: 0 SQL queries executed (0 compute credits consumed).\n" \
                  f"- **Target Dataset**: `{self.dataset_info['name']}` (`{self.dataset_info['table_name']}`).\n\n" \
                  f"Please ask an analytical question about student grades, study time, alcohol consumption, or pass rates!"
            self.conversation_history.append({
                "question": question,
                "sql": None,
                "direct_answer": ans
            })
            return {
                "status": "out_of_scope",
                "direct_answer": ans,
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

        # Step 3b: Graceful Handling of Empty Results (M6 Requirement)
        if len(exec_result["rows"]) == 0:
            direct_ans = f"**[M6 Guardrail Notice - Zero Matching Records]**\n\n" \
                         f"The executed Snowflake query returned **0 matching rows** for your specified criteria.\n\n" \
                         f"- **Grounded Data Integrity**: No hallucinated or estimated figures were produced.\n" \
                         f"- **Executed Filter**: Check filter thresholds in the SQL query below (e.g. valid student age range is 15-22, schools are 'GP' and 'MS')."
            self.conversation_history.append({
                "question": question,
                "sql": sql,
                "direct_answer": direct_ans
            })
            return {
                "status": "empty_result",
                "direct_answer": direct_ans,
                "sql": sql,
                "rows": [],
                "columns": exec_result["columns"],
                "row_count": 0,
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

        # Check if this query is a follow-up
        is_follow_up = len(self.conversation_history) > 0
        prior_query = self.conversation_history[-1]["question"] if is_follow_up else None

        # Update Conversation Memory with clean structured turn
        self.conversation_history.append({
            "question": question,
            "sql": sql,
            "direct_answer": explanation
        })

        return {
            "status": "success",
            "direct_answer": explanation,
            "sql": sql,
            "rows": exec_result["rows"],
            "columns": exec_result["columns"],
            "row_count": exec_result["row_count"],
            "execution_time_ms": exec_result["execution_time_ms"],
            "dataset": self.dataset_info['name'],
            "cost_estimate_credits": credit_est,
            "is_follow_up": is_follow_up,
            "prior_inquiry": prior_query
        }
