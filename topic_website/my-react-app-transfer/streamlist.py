from pathlib import Path

import pandas as pd
import pyodbc
import streamlit as st


BASE_DIR = Path(__file__).resolve().parent
GATEWAY_LOG_FILE = BASE_DIR / "gateway.log"
SQL_PREVIEW_LOG_FILE = BASE_DIR / "sql_preview.log"

DB_CONFIG = {
    "driver": "{ODBC Driver 18 for SQL Server}",
    "server": r"LAPTOP-DSOT480A\SQLEXPRESS02",
    "database": "wind_turbine",
}


def get_sql_connection():
    conn_str = (
        f"DRIVER={DB_CONFIG['driver']};"
        f"SERVER={DB_CONFIG['server']};"
        f"DATABASE={DB_CONFIG['database']};"
        "Trusted_Connection=yes;"
        "TrustServerCertificate=yes;"
    )
    return pyodbc.connect(conn_str)


def read_sql_table(table_name):
    with get_sql_connection() as conn:
        return pd.read_sql(
            f"SELECT TOP 100 * FROM dbo.{table_name} ORDER BY id DESC",
            conn,
        )


def clear_sql_tables():
    with get_sql_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM dbo.cnn_result_log")
        cursor.execute("DELETE FROM dbo.sensor_summary")
        conn.commit()


def read_log(file_path):
    if not file_path.exists():
        return ""

    return file_path.read_text(encoding="utf-8")


def clear_file(file_path):
    file_path.write_text("", encoding="utf-8")


st.set_page_config(
    page_title="Python IoT Gateway Monitor",
    layout="wide",
)

st.title("Python IoT Gateway / SQL / CNN Monitor")

with st.sidebar:
    st.subheader("Controls")

    if st.button("Refresh"):
        st.rerun()

    if st.button("Show SQL Tables"):
        st.session_state["show_sql"] = True
        st.rerun()

    if st.button("Hide SQL Tables"):
        st.session_state["show_sql"] = False
        st.rerun()

    if st.button("Clear sql_preview.log"):
        clear_file(SQL_PREVIEW_LOG_FILE)
        st.success("sql_preview.log cleared")

    if st.button("Clear SQL Tables and Logs"):
        try:
            clear_sql_tables()
            clear_file(SQL_PREVIEW_LOG_FILE)
            clear_file(GATEWAY_LOG_FILE)
            st.session_state["show_sql"] = True
            st.success("SQL tables and logs cleared")
            st.rerun()
        except Exception as error:
            st.error(f"Clear failed: {error}")

if st.session_state.get("show_sql", False):
    st.subheader("sensor_summary")
    try:
        st.dataframe(read_sql_table("sensor_summary"), use_container_width=True)
    except Exception as error:
        st.error(f"Failed to read sensor_summary: {error}")

    st.subheader("cnn_result_log")
    try:
        st.dataframe(read_sql_table("cnn_result_log"), use_container_width=True)
    except Exception as error:
        st.error(f"Failed to read cnn_result_log: {error}")

left, right = st.columns(2)

with left:
    st.subheader("Gateway Log")
    st.text_area("gateway.log", read_log(GATEWAY_LOG_FILE), height=500)

with right:
    st.subheader("SQL Preview Log")
    st.text_area("sql_preview.log", read_log(SQL_PREVIEW_LOG_FILE), height=500)