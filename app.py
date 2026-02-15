import os
import sys

if __name__ == "__main__":
    # Simple launcher for the Streamlit dashboard
    cmd = "streamlit run dashboards/app.py"
    raise SystemExit(os.system(cmd))
