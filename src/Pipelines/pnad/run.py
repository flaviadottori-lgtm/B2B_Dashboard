"""
Scaffold pipeline PNAD/PNADc - ainda sem ingestão real
"""
import argparse

def main():
    parser = argparse.ArgumentParser(description="PNAD Cloud Pipeline Runner (scaffold)")
    parser.add_argument("--competencia", type=str, help="Competência/Período (ex: 2021-01)")
    args = parser.parse_args()
    print("PNAD pipeline scaffold: aguardando microdados e fonte oficial.")

if __name__ == "__main__":
    main()
