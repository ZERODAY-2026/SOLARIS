"""
Automated Document & Dataset Ingestor for Snowflake via Gemma 4.
Parses CSV, Excel, or tabular PDF files into structured DataFrames,
uses Gemma 4 to synthesize optimal DDL schemas & column descriptions,
creates the table in Snowflake, populates records, and registers into config.yaml.
"""

import os
import re
import yaml
import pandas as pd
import pdfplumber
from typing import Tuple, Dict, Any, Optional
from datamind.core.snowflake_client import SnowflakeClient
from datamind.core.gemma_client import GemmaClient


class DatasetAutoIngestor:
    def __init__(self, config_path: Optional[str] = None):
        if not config_path:
            candidates = [
                os.path.join(os.path.dirname(__file__), "..", "config.yaml"),
                os.path.join(os.path.dirname(__file__), "config.yaml"),
                os.path.abspath("config.yaml"),
                os.path.abspath("datamind/config.yaml")
            ]
            for c in candidates:
                if os.path.exists(c):
                    config_path = os.path.abspath(c)
                    break
            if not config_path:
                config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config.yaml"))
        self.config_path = config_path
        self.snowflake = SnowflakeClient()
        self.gemma = GemmaClient()

    def parse_uploaded_file_to_df(self, uploaded_file) -> Tuple[pd.DataFrame, str]:
        """
        Parses CSV, XLSX, XLS, or tabular PDF files into a clean Pandas DataFrame.
        """
        filename = uploaded_file.name
        ext = os.path.splitext(filename)[1].lower()

        if ext == ".csv":
            try:
                df = pd.read_csv(uploaded_file, sep=None, engine="python")
            except Exception:
                uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file)

        elif ext in [".xlsx", ".xls"]:
            df = pd.read_excel(uploaded_file)

        elif ext == ".pdf":
            # Extract tables from PDF
            all_tables = []
            with pdfplumber.open(uploaded_file) as pdf:
                for page in pdf.pages:
                    tables = page.extract_tables()
                    for t in tables:
                        if t and len(t) > 1:
                            headers = t[0]
                            headers = [h.strip() if h else f"col_{i}" for i, h in enumerate(headers)]
                            page_df = pd.DataFrame(t[1:], columns=headers)
                            all_tables.append(page_df)
            if all_tables:
                df = pd.concat(all_tables, ignore_index=True)
            else:
                raise ValueError("No tabular data detected in PDF. Please upload a CSV, Excel, or tabular PDF.")
        else:
            raise ValueError(f"Unsupported file format '{ext}'. Allowed: CSV, XLSX, XLS, PDF.")

        # Clean column names (strip whitespace, alphanumeric with underscore)
        clean_cols = []
        for i, c in enumerate(df.columns):
            c_str = str(c).strip().replace(" ", "_")
            c_clean = re.sub(r"[^A-Za-z0-9_]", "", c_str).upper()
            if not c_clean or c_clean.isdigit():
                c_clean = f"COL_{i+1}"
            clean_cols.append(c_clean)
        df.columns = clean_cols

        # Normalize table name based on file stem
        table_stem = os.path.splitext(filename)[0]
        table_name = re.sub(r"[^A-Za-z0-9_]", "_", table_stem).upper()
        if not table_name[0].isalpha():
            table_name = "DATA_" + table_name
        table_name = table_name[:40].rstrip("_")

        return df, table_name

    def infer_snowflake_schema_and_ddl(self, df: pd.DataFrame, table_name: str, friendly_name: str) -> Dict[str, Any]:
        """
        Generates clean Snowflake DDL and a rich schema description using Gemma 4.
        """
        sample_records = df.head(5).to_dict(orient="records")
        col_types_summary = {col: str(df[col].dtype) for col in df.columns}

        prompt = f"""
You are a senior Data Architect. Given this tabular dataset:
Table Name: {table_name}
Dataset Name: {friendly_name}
Column Types: {col_types_summary}
Sample Rows (first 5):
{sample_records}

Generate a concise, perfectly formatted YAML schema description block and a Snowflake CREATE TABLE statement.
Rules:
1. Map string/object to VARCHAR(255), integer to INT, float to FLOAT, dates to DATE or VARCHAR(50).
2. Write a clear 1-line business explanation for what each column represents.
3. Output valid JSON ONLY with this exact structure:
{{
  "description": "Short 1-2 sentence overview of what this dataset tracks.",
  "columns_meta": [
    {{"name": "COL_NAME", "type": "VARCHAR(255)", "desc": "Explanation of column"}}
  ]
}}
"""
        response_text = self.gemma.generate(
            system_prompt="You are an automated Snowflake data modeler. Output JSON only.",
            user_prompt=prompt,
            temperature=0.1,
            max_tokens=1500
        )

        # Parse JSON
        try:
            match = re.search(r"\{.*\}", response_text, re.DOTALL)
            parsed = yaml.safe_load(match.group(0)) if match else {}
        except Exception:
            parsed = {}

        description = parsed.get("description", f"User uploaded dataset for {friendly_name}")
        cols_meta = parsed.get("columns_meta", [])

        # Build fallback DDL if Gemma missed any columns
        col_defs = []
        schema_lines = [f"Table: {table_name}", "Columns:"]

        meta_map = {item.get("name", "").upper(): item.get("desc", "") for item in cols_meta}
        type_map = {item.get("name", "").upper(): item.get("type", "VARCHAR(255)") for item in cols_meta}

        for col in df.columns:
            inferred_type = type_map.get(col)
            if not inferred_type:
                dt = str(df[col].dtype)
                if "int" in dt:
                    inferred_type = "INT"
                elif "float" in dt:
                    inferred_type = "FLOAT"
                else:
                    inferred_type = "VARCHAR(255)"

            col_defs.append(f"{col} {inferred_type}")
            col_desc = meta_map.get(col, f"Data values for {col.lower()}")
            schema_lines.append(f"- {col.lower()} ({inferred_type}): {col_desc}")

        ddl = f"CREATE OR REPLACE TABLE {table_name} (\n  " + ",\n  ".join(col_defs) + "\n);"
        full_schema_description = "\n".join(schema_lines)

        return {
            "table_name": table_name,
            "name": friendly_name,
            "description": description,
            "schema_description": full_schema_description,
            "ddl": ddl,
            "columns": list(df.columns)
        }

    def deploy_to_snowflake_and_register(self, df: pd.DataFrame, schema_info: Dict[str, Any]) -> str:
        """
        Executes DDL on Snowflake, inserts all rows, commits transaction,
        and appends the new domain into config.yaml.
        """
        from snowflake.connector.pandas_tools import write_pandas

        table_name = schema_info["table_name"]
        conn = self.snowflake.get_connection()
        conn.autocommit(True)
        cur = conn.cursor()

        try:
            # 1. Execute CREATE TABLE
            print(f"Executing DDL for {table_name}...")
            cur.execute(schema_info["ddl"])

            # 2. Upload records via write_pandas
            print(f"Uploading {len(df)} records into Snowflake table {table_name}...")
            clean_df = df.copy()
            for col in clean_df.columns:
                if clean_df[col].dtype == "object":
                    clean_df[col] = clean_df[col].astype(str).replace({"nan": None, "None": None})
            
            success, nchunks, nrows, _ = write_pandas(
                conn=conn,
                df=clean_df,
                table_name=table_name,
                database=self.snowflake.database,
                schema=self.snowflake.schema,
                auto_create_table=False
            )
            conn.commit()
            print(f"Committed {nrows} rows into {table_name}.")

        finally:
            cur.close()
            conn.close()

        # 3. Update config.yaml with the new knowledge domain
        domain_key = table_name.lower()
        with open(self.config_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}

        if "datasets" not in cfg:
            cfg["datasets"] = {}

        cfg["datasets"][domain_key] = {
            "name": schema_info["name"],
            "table_name": table_name,
            "description": schema_info["description"],
            "schema_description": schema_info["schema_description"]
        }
        cfg["active_dataset"] = domain_key

        with open(self.config_path, "w", encoding="utf-8") as f:
            yaml.dump(cfg, f, sort_keys=False, default_flow_style=False)

        print(f"Successfully registered '{domain_key}' into {self.config_path}!")
        return domain_key
