import json
from report_data import getReportData

def main():
    report = getReportData()
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
