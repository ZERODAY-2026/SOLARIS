import os
import re
import time
from typing import Dict, Any, List, Tuple
import snowflake.connector
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

class SnowflakeClient:
    """
    Manages secure, read-only Snowflake execution with timing,
    metadata extraction, and SQL safety guardrails.
    """
    def __init__(self):
        self.account = os.getenv("SNOWFLAKE_ACCOUNT", "ol15456")
        self.host = os.getenv("SNOWFLAKE_HOST", "ol15456.ap-south-1.aws.snowflakecomputing.com")
        self.user = os.getenv("SNOWFLAKE_USER", "KIRITO2026")
        self.password = os.getenv("SNOWFLAKE_PASSWORD", "91RIOMTITAnkirito")
        self.warehouse = os.getenv("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH")
        self.database = os.getenv("SNOWFLAKE_DATABASE", "DATAMIND_DB")
        self.schema = os.getenv("SNOWFLAKE_SCHEMA", "PUBLIC")
        self.role = os.getenv("SNOWFLAKE_ROLE", "ACCOUNTADMIN")

    def get_connection(self):
        return snowflake.connector.connect(
            user=self.user,
            password=self.password,
            account=self.account,
            host=self.host,
            warehouse=self.warehouse,
            database=self.database,
            schema=self.schema,
            role=self.role
        )

    def validate_sql_safety(self, sql: str) -> Tuple[bool, str]:
        """
        Ensures the query is strictly a read-only SELECT or WITH statement.
        Rejects any mutation, DDL, or privilege alterations.
        """
        clean_sql = sql.strip().rstrip(";")
        # Remove comments
        clean_sql = re.sub(r'--.*$', '', clean_sql, flags=re.MULTILINE)
        clean_sql = re.sub(r'/\*.*?\*/', '', clean_sql, flags=re.DOTALL).strip()

        # Reject disallowed keywords
        disallowed = [
            "DROP", "DELETE", "TRUNCATE", "INSERT", "UPDATE", "ALTER",
            "CREATE", "GRANT", "REVOKE", "MERGE", "CALL", "EXECUTE"
        ]
        tokens = re.findall(r'\b[A-Za-z_]+\b', clean_sql.upper())
        for token in tokens:
            if token in disallowed:
                return False, f"Prohibited keyword detected: '{token}'. Only read-only SELECT queries are permitted."

        if not (clean_sql.upper().startswith("SELECT") or clean_sql.upper().startswith("WITH")):
            return False, "Query must start with SELECT or WITH."

        return True, "Valid"

    def execute_query(self, sql: str) -> Dict[str, Any]:
        """
        Executes a validated query on Snowflake, tracking execution time,
        returned rows, and column metadata.
        """
        is_safe, reason = self.validate_sql_safety(sql)
        if not is_safe:
            return {
                "success": False,
                "error": f"Security Guardrail Refusal: {reason}",
                "sql": sql,
                "rows": [],
                "columns": [],
                "execution_time_ms": 0
            }

        start_time = time.time()
        conn = None
        cur = None
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            cur.execute(sql)
            
            columns = [desc[0] for desc in cur.description] if cur.description else []
            rows = cur.fetchall()
            elapsed_ms = round((time.time() - start_time) * 1000, 2)

            return {
                "success": True,
                "error": None,
                "sql": sql,
                "rows": rows,
                "columns": columns,
                "row_count": len(rows),
                "execution_time_ms": elapsed_ms
            }
        except Exception as e:
            elapsed_ms = round((time.time() - start_time) * 1000, 2)
            return {
                "success": False,
                "error": str(e),
                "sql": sql,
                "rows": [],
                "columns": [],
                "execution_time_ms": elapsed_ms
            }
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()

    def get_table_schema_docs(self, table_name: str) -> str:
        """
        Retrieves column names and types from information_schema.
        """
        query = f"""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_schema = '{self.schema.upper()}' 
          AND table_name = '{table_name.upper()}'
        ORDER BY ordinal_position
        """
        res = self.execute_query(query)
        if res["success"] and res["rows"]:
            lines = [f"- {row[0]} ({row[1]})" for row in res["rows"]]
            return "\n".join(lines)
        return "No schema found."
