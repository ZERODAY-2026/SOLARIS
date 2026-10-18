import os
import snowflake.connector
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

def populate_sample_data():
    host = os.getenv("SNOWFLAKE_HOST")
    account = os.getenv("SNOWFLAKE_ACCOUNT")
    user = os.getenv("SNOWFLAKE_USER")
    password = os.getenv("SNOWFLAKE_PASSWORD")
    database = os.getenv("SNOWFLAKE_DATABASE", "DATAMIND_DB")
    schema = os.getenv("SNOWFLAKE_SCHEMA", "PUBLIC")

    conn = snowflake.connector.connect(
        user=user,
        password=password,
        account=account,
        host=host,
        database=database,
        schema=schema
    )
    cur = conn.cursor()
    try:
        print("Checking if GLOBAL_INDICATORS is already populated...")
        cur.execute("SELECT COUNT(*) FROM GLOBAL_INDICATORS")
        count = cur.fetchone()[0]
        if count == 0:
            print("Populating GLOBAL_INDICATORS (Our World in Data benchmark subset)...")
            records = [
                # India
                ("India", "IND", 2018, 1996.9, 69.4, 1352642280, 2431.1, 95.2),
                ("India", "IND", 2019, 2100.8, 69.7, 1366417754, 2456.3, 97.8),
                ("India", "IND", 2020, 1933.1, 70.1, 1380004385, 2256.8, 99.0),
                ("India", "IND", 2021, 2256.6, 67.2, 1393409038, 2510.4, 99.6),
                ("India", "IND", 2022, 2410.9, 67.7, 1406631776, 2697.5, 99.9),
                ("India", "IND", 2023, 2612.5, 68.3, 1417173173, 2814.2, 100.0),
                # United States
                ("United States", "USA", 2018, 62996.5, 78.6, 326687501, 5275.2, 100.0),
                ("United States", "USA", 2019, 65094.8, 78.8, 328239523, 5143.9, 100.0),
                ("United States", "USA", 2020, 63027.6, 77.0, 331002651, 4715.7, 100.0),
                ("United States", "USA", 2021, 70248.6, 76.4, 331893745, 5007.3, 100.0),
                ("United States", "USA", 2022, 76398.6, 77.5, 333287557, 5053.9, 100.0),
                ("United States", "USA", 2023, 81695.2, 78.2, 334914895, 4920.1, 100.0),
                # China
                ("China", "CHN", 2018, 9976.7, 77.7, 1427647786, 10502.9, 100.0),
                ("China", "CHN", 2019, 10143.8, 78.0, 1433783686, 10741.0, 100.0),
                ("China", "CHN", 2020, 10408.7, 78.1, 1439323776, 10944.7, 100.0),
                ("China", "CHN", 2021, 12556.3, 78.2, 1444216107, 11472.1, 100.0),
                ("China", "CHN", 2022, 12720.2, 78.4, 1447301400, 11396.8, 100.0),
                ("China", "CHN", 2023, 13120.0, 78.6, 1448200000, 11620.4, 100.0),
                # Germany
                ("Germany", "DEU", 2018, 47950.4, 81.0, 82927922, 755.3, 100.0),
                ("Germany", "DEU", 2019, 46795.3, 81.3, 83132799, 709.8, 100.0),
                ("Germany", "DEU", 2020, 46252.7, 81.0, 83155031, 644.3, 100.0),
                ("Germany", "DEU", 2021, 51203.6, 80.9, 83196078, 675.2, 100.0),
                ("Germany", "DEU", 2022, 48718.3, 80.7, 83794315, 665.9, 100.0),
                ("Germany", "DEU", 2023, 52824.1, 81.2, 84358845, 605.1, 100.0),
                # Japan
                ("Japan", "JPN", 2018, 39159.4, 84.2, 126529100, 1136.2, 100.0),
                ("Japan", "JPN", 2019, 40113.1, 84.4, 126264931, 1098.5, 100.0),
                ("Japan", "JPN", 2020, 39918.2, 84.6, 125836021, 1042.8, 100.0),
                ("Japan", "JPN", 2021, 39312.7, 84.5, 125124989, 1067.4, 100.0),
                ("Japan", "JPN", 2022, 33815.3, 84.1, 124947000, 1030.5, 100.0),
                ("Japan", "JPN", 2023, 34017.5, 84.3, 124516650, 990.2, 100.0),
                # Brazil
                ("Brazil", "BRA", 2018, 9151.4, 75.3, 209469333, 447.8, 99.7),
                ("Brazil", "BRA", 2019, 8897.6, 75.3, 211049527, 441.5, 99.8),
                ("Brazil", "BRA", 2020, 6920.2, 72.8, 212559417, 421.9, 99.8),
                ("Brazil", "BRA", 2021, 7696.8, 72.8, 214326223, 452.1, 99.8),
                ("Brazil", "BRA", 2022, 8917.7, 73.4, 215313498, 442.3, 99.9),
                ("Brazil", "BRA", 2023, 10043.6, 74.0, 216422446, 435.0, 100.0)
            ]
            insert_sql = """
            INSERT INTO GLOBAL_INDICATORS (
                country, country_code, year, gdp_per_capita, life_expectancy, population, co2_emissions_mt, access_to_electricity_pct
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cur.executemany(insert_sql, records)
            print(f"Inserted {len(records)} records into GLOBAL_INDICATORS.")
        else:
            print(f"GLOBAL_INDICATORS already contains {count} rows.")

        print("Checking if STUDENT_ACADEMIC_METRICS is populated...")
        cur.execute("SELECT COUNT(*) FROM STUDENT_ACADEMIC_METRICS")
        s_count = cur.fetchone()[0]
        if s_count == 0:
            print("Populating STUDENT_ACADEMIC_METRICS (secondary adaptability dataset)...")
            students = [
                ("STU_101", "Computer Science", 18.5, 94.0, 10, 91.5, "A"),
                ("STU_102", "Computer Science", 14.0, 88.5, 9, 84.0, "B"),
                ("STU_103", "Data Science", 22.0, 96.0, 10, 95.0, "A+"),
                ("STU_104", "Data Science", 11.5, 75.0, 7, 72.0, "C"),
                ("STU_105", "Electrical Eng", 16.0, 89.0, 8, 86.5, "B+"),
                ("STU_106", "Electrical Eng", 8.0, 62.0, 5, 58.0, "D"),
                ("STU_107", "Mechanical Eng", 15.5, 82.0, 8, 79.5, "B"),
                ("STU_108", "Mechanical Eng", 20.0, 95.0, 10, 92.0, "A"),
                ("STU_109", "Computer Science", 6.0, 55.0, 4, 49.0, "F"),
                ("STU_110", "Data Science", 17.5, 91.0, 9, 88.0, "A-")
            ]
            s_sql = """
            INSERT INTO STUDENT_ACADEMIC_METRICS (
                student_id, department, study_hours_weekly, attendance_pct, assignments_completed, exam_score, grade
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cur.executemany(s_sql, students)
            print(f"Inserted {len(students)} records into STUDENT_ACADEMIC_METRICS.")
        else:
            print(f"STUDENT_ACADEMIC_METRICS already contains {s_count} rows.")

    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    populate_sample_data()
