import os
import io
import urllib.request
import zipfile
import pandas as pd
import snowflake.connector
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

def ingest_full_uci_dataset():
    host = os.getenv("SNOWFLAKE_HOST")
    account = os.getenv("SNOWFLAKE_ACCOUNT")
    user = os.getenv("SNOWFLAKE_USER")
    password = os.getenv("SNOWFLAKE_PASSWORD")
    database = os.getenv("SNOWFLAKE_DATABASE", "DATAMIND_DB")
    schema = os.getenv("SNOWFLAKE_SCHEMA", "PUBLIC")
    warehouse = os.getenv("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH")
    role = os.getenv("SNOWFLAKE_ROLE", "ACCOUNTADMIN")

    print("[1/4] Downloading official UCI Student Performance benchmark archive...")
    url = "https://archive.ics.uci.edu/static/public/320/student+performance.zip"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as resp:
        zip_bytes = resp.read()

    print("[2/4] Extracting student-mat.csv and student-por.csv...")
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as outer:
        inner_bytes = outer.read("student.zip")
        with zipfile.ZipFile(io.BytesIO(inner_bytes)) as inner:
            df_mat = pd.read_csv(inner.open("student-mat.csv"), sep=";")
            df_por = pd.read_csv(inner.open("student-por.csv"), sep=";")

    df_mat["subject"] = "Math"
    df_mat["student_id"] = [f"MAT_{i+1:03d}" for i in range(len(df_mat))]

    df_por["subject"] = "Portuguese"
    df_por["student_id"] = [f"POR_{i+1:03d}" for i in range(len(df_por))]

    df_combined = pd.concat([df_mat, df_por], ignore_index=True)
    
    # Reorder columns so student_id and subject come first
    base_cols = [c for c in df_combined.columns if c not in ["student_id", "subject"]]
    cols_ordered = ["student_id", "subject"] + base_cols
    df_combined = df_combined[cols_ordered]
    
    # Convert column names to lowercase for consistency
    df_combined.columns = [c.lower() for c in df_combined.columns]

    print(f"Combined dataset: {df_combined.shape[0]} rows, {df_combined.shape[1]} columns.")

    # Save local CSV backup for offline reference/fallback
    os.makedirs(os.path.join(os.path.dirname(__file__), "raw"), exist_ok=True)
    local_csv_path = os.path.join(os.path.dirname(__file__), "raw", "uci_student_performance_full.csv")
    df_combined.to_csv(local_csv_path, index=False)
    print(f"Saved local master CSV to {local_csv_path}")

    print("[3/4] Connecting to Snowflake and creating table STUDENT_PERFORMANCE...")
    conn = snowflake.connector.connect(
        user=user,
        password=password,
        account=account,
        host=host,
        warehouse=warehouse,
        database=database,
        schema=schema,
        role=role,
        autocommit=True
    )
    cur = conn.cursor()

    try:
        create_table_sql = """
        CREATE OR REPLACE TABLE STUDENT_PERFORMANCE (
            student_id VARCHAR(20) PRIMARY KEY,
            subject VARCHAR(20),
            school VARCHAR(10),
            sex VARCHAR(5),
            age INT,
            address VARCHAR(5),
            famsize VARCHAR(10),
            pstatus VARCHAR(5),
            medu INT,
            fedu INT,
            mjob VARCHAR(30),
            fjob VARCHAR(30),
            reason VARCHAR(30),
            guardian VARCHAR(20),
            traveltime INT,
            studytime INT,
            failures INT,
            schoolsup VARCHAR(5),
            famsup VARCHAR(5),
            paid VARCHAR(5),
            activities VARCHAR(5),
            nursery VARCHAR(5),
            higher VARCHAR(5),
            internet VARCHAR(5),
            romantic VARCHAR(5),
            famrel INT,
            freetime INT,
            goout INT,
            dalc INT,
            walc INT,
            health INT,
            absences INT,
            g1 INT,
            g2 INT,
            g3 INT
        )
        """
        cur.execute(create_table_sql)
        print("Table STUDENT_PERFORMANCE created successfully.")

        print(f"[4/4] Ingesting {len(df_combined)} student records into Snowflake...")
        col_list = list(df_combined.columns)
        placeholders = ", ".join(["%s"] * len(col_list))
        columns_str = ", ".join(col_list)
        insert_sql = f"INSERT INTO STUDENT_PERFORMANCE ({columns_str}) VALUES ({placeholders})"

        # Convert dataframe to tuples with standard python types
        records = [tuple(row) for row in df_combined.itertuples(index=False, name=None)]
        cur.executemany(insert_sql, records)
        conn.commit()
        print(f"Successfully committed all {len(records)} records into Snowflake table STUDENT_PERFORMANCE!")

        # Verify row count
        cur.execute("SELECT COUNT(*), COUNT(DISTINCT subject) FROM STUDENT_PERFORMANCE")
        verification = cur.fetchone()
        print(f"Verification: {verification[0]} total records across {verification[1]} subjects committed.")

    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    ingest_full_uci_dataset()
