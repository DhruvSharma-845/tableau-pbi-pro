import argparse
import os
import sys
from core.parser import TWBParser
from generators.pbip_builder import PBIPBuilder

def main():
    parser = argparse.ArgumentParser(description="Tableau to Power BI PBIP Converter")
    parser.add_argument("input", help="Path to .twbx or .twb file")
    parser.add_argument("-o", "--output", default="output", help="Output directory")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"Error: File {args.input} not found.")
        sys.exit(1)
        
    print(f"Parsing Tableau workbook: {args.input}")
    try:
        parser = TWBParser(args.input)
        workbook = parser.parse()
        
        print(f"Found {len(workbook.datasources)} data sources and {len(workbook.worksheets)} worksheets.")
        
        os.makedirs(args.output, exist_ok=True)
        builder = PBIPBuilder(workbook, args.output)
        builder.build()
        
        print(f"Success! PBIP project created at: {os.path.abspath(args.output)}")
        print("You can now open the .pbip file in Power BI Desktop.")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
