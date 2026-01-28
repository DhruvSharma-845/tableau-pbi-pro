import re

class FormulaTranslator:
    FUNCTION_MAP = {
        'SUM': 'SUM',
        'AVG': 'AVERAGE',
        'MIN': 'MIN',
        'MAX': 'MAX',
        'COUNT': 'COUNT',
        'COUNTD': 'DISTINCTCOUNT',
        'IF': 'IF',
        'THEN': ',',
        'ELSE': ',',
        'END': ')',
        'ISNULL': 'ISBLANK',
        'ZN': 'COALESCE({}, 0)', # Better for DAX
        'ABS': 'ABS',
        'ROUND': 'ROUND',
        'ATTR': 'SELECTEDVALUE',
        'DATEDIFF': 'DATEDIFF',
        'DATEADD': 'DATEADD',
        'DATETRUNC': 'DATE_TRUNC',
        'CASE': 'SWITCH',
        'WHEN': ',',
    }

    @classmethod
    def translate(cls, formula: str) -> str:
        if not formula:
            return ""
            
        # Remove Tableau-style field references [Field Name]
        # In PBIR/TMDL measures, we often need to reference other measures or columns
        translated = formula
        
        # 1. Replace Tableau function syntax
        for tableau_func, dax_func in cls.FUNCTION_MAP.items():
            translated = re.sub(rf'\b{tableau_func}\s*\(', f'{dax_func}(', translated, flags=re.IGNORECASE)

        # 2. Handle IF/THEN/ELSE/END
        translated = re.sub(r'\bIF\b', 'IF(', translated, flags=re.IGNORECASE)
        translated = re.sub(r'\bTHEN\b', ',', translated, flags=re.IGNORECASE)
        translated = re.sub(r'\bELSEIF\b', ', IF(', translated, flags=re.IGNORECASE)
        translated = re.sub(r'\bELSE\b', ',', translated, flags=re.IGNORECASE)
        translated = re.sub(r'\bEND\b', ')', translated, flags=re.IGNORECASE)
        
        # 3. ZN(x) -> COALESCE(x, 0)
        # Simple regex for ZN(something)
        translated = re.sub(r'ZN\((.*?)\)', r'COALESCE(\1, 0)', translated, flags=re.IGNORECASE)
        
        # 4. Handle logical operators
        translated = re.sub(r'\bAND\b', '&&', translated, flags=re.IGNORECASE)
        translated = re.sub(r'\bOR\b', '||', translated, flags=re.IGNORECASE)
        
        # 5. Cleanup double commas/spaces
        translated = re.sub(r',\s*,', ',', translated)
        
        return translated.strip()
