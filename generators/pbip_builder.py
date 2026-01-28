import os
import json
import uuid
from core.translator import FormulaTranslator

class PBIPBuilder:
    def __init__(self, workbook_data, output_dir):
        self.workbook = workbook_data
        self.output_dir = output_dir
        self.project_name = self._sanitize(self.workbook.name.replace('.twbx', '').replace('.twb', ''))
        # The project folder itself should be the output_dir
        self.project_dir = output_dir 
        self.report_dir = os.path.join(self.project_dir, f"{self.project_name}.Report")
        self.model_dir = os.path.join(self.project_dir, f"{self.project_name}.SemanticModel")

    def build(self):
        os.makedirs(self.project_dir, exist_ok=True)
        os.makedirs(self.report_dir, exist_ok=True)
        os.makedirs(self.model_dir, exist_ok=True)
        
        self._create_pbip_file()
        self._create_semantic_model()
        self._create_report_definition()
        self._create_pbi_folder()

    def _create_pbip_file(self):
        pbip_content = {
            "version": "1.0",
            "artifacts": [
                {
                    "report": {
                        "path": f"{self.project_name}.Report"
                    }
                },
                {
                    "semanticModel": {
                        "path": f"{self.project_name}.SemanticModel"
                    }
                }
            ],
            "settings": {
                "enableAutoRecovery": True
            }
        }
        pbip_path = os.path.join(self.project_dir, f"{self.project_name}.pbip")
        with open(pbip_path, 'w') as f:
            json.dump(pbip_content, f, indent=2)

    def _create_pbi_folder(self):
        pbi_path = os.path.join(self.project_dir, ".pbi")
        os.makedirs(pbi_path, exist_ok=True)
        settings = {
            "version": "1.0",
            "isAutoRecoveryEnabled": True
        }
        with open(os.path.join(pbi_path, "localSettings.json"), 'w') as f:
            json.dump(settings, f, indent=2)

    def _create_semantic_model(self):
        # definition.pbism
        pbism = {
            "version": "1.0",
            "settings": {}
        }
        with open(os.path.join(self.model_dir, "definition.pbism"), 'w') as f:
            json.dump(pbism, f, indent=2)
            
        def_path = os.path.join(self.model_dir, "definition")
        os.makedirs(def_path, exist_ok=True)
        
        # model.tmdl
        model_tmdl = [
            "model Model",
            "	compatibilityLevel: 1550",
            "	culture: en-US",
            "	defaultPowerBIDataSourceVersion: powerBI_V3",
            "	sourceQueryCulture: en-US",
            "	displayOptions: [",
            "		category: base",
            "	]",
            ""
        ]
        with open(os.path.join(def_path, "model.tmdl"), 'w') as f:
            f.write("\n".join(model_tmdl))
            
        # expressions.tmdl (M Queries)
        expressions_tmdl = ["expression Expressions", ""]
        for ds in self.workbook.datasources:
            ds_name = self._sanitize(ds.name)
            expressions_tmdl.extend([
                f"	expression '{ds_name}' =",
                "		```",
                "		let",
                "			Source = #table(",
                '				type table [Column1 = text],',
                '				{}',
                "			)",
                "		in",
                "			Source",
                "		```",
                ""
            ])
        with open(os.path.join(def_path, "expressions.tmdl"), 'w') as f:
            f.write("\n".join(expressions_tmdl))

        # tables/
        tables_path = os.path.join(def_path, "tables")
        os.makedirs(tables_path, exist_ok=True)
        
        for ds in self.workbook.datasources:
            ds_name = self._sanitize(ds.name)
            tmdl = [
                f"table '{ds_name}'",
                f"	lineageTag: {uuid.uuid4()}",
                ""
            ]
            
            # Columns
            for field in ds.fields:
                if not field.formula:
                    tmdl.extend([
                        f"	column '{field.name}'",
                        f"		dataType: {self._map_datatype(field.datatype)}",
                        f"		lineageTag: {uuid.uuid4()}",
                        f"		summarizeBy: none",
                        f"		sourceLineageTag: {field.name}",
                        ""
                    ])
            
            # Measures
            for field in ds.fields:
                if field.formula:
                    dax = FormulaTranslator.translate(field.formula)
                    tmdl.extend([
                        f"	measure '{field.name}' = {dax}",
                        f"		lineageTag: {uuid.uuid4()}",
                        ""
                    ])
            
            # Partition
            tmdl.extend([
                f"	partition '{ds_name}-partition' = m",
                "		mode: import",
                f"		source =",
                "			```",
                f"			{ds_name}",
                "			```",
                ""
            ])
            
            with open(os.path.join(tables_path, f"{ds_name}.tmdl"), 'w') as f:
                f.write("\n".join(tmdl))

    def _sanitize(self, name):
        # Remove characters that are problematic for file systems and Power BI
        return name.strip("[]").replace("/", "_").replace("\\", "_").replace(":", "_").replace("?", "_")

    def _map_datatype(self, tableau_type):
        mapping = {
            'string': 'string',
            'integer': 'int64',
            'real': 'double',
            'datetime': 'dateTime',
            'date': 'dateTime',
            'boolean': 'boolean'
        }
        return mapping.get(tableau_type, 'string')

    def _create_report_definition(self):
        # definition.pbir
        pbir = {
            "version": "1.0",
            "datasetReference": {
                "byPath": {
                    "path": f"../{self.project_name}.SemanticModel"
                }
            }
        }
        with open(os.path.join(self.report_dir, "definition.pbir"), 'w') as f:
            json.dump(pbir, f, indent=2)
            
        def_path = os.path.join(self.report_dir, "definition")
        os.makedirs(def_path, exist_ok=True)
        
        # Prepare pages
        pages_metadata = []
        pages_path = os.path.join(def_path, "pages")
        os.makedirs(pages_path, exist_ok=True)
        
        for ws in self.workbook.worksheets:
            page_id = str(uuid.uuid4())
            page_name = self._sanitize(ws.name)
            
            pages_metadata.append({
                "name": page_id,
                "displayName": ws.name
            })
            
            page_dir = os.path.join(pages_path, page_id)
            os.makedirs(page_dir, exist_ok=True)
            
            page_json = {
                "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/1.0.0/schema.json",
                "name": page_id,
                "displayName": ws.name,
                "displayOption": "FitToPage",
                "width": 1280,
                "height": 720,
                "config": {
                    "layouts": []
                }
            }
            with open(os.path.join(page_dir, "page.json"), 'w') as f:
                json.dump(page_json, f, indent=2)
            
            os.makedirs(os.path.join(page_dir, "visuals"), exist_ok=True)

        # report.json
        report_json = {
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/1.0.0/schema.json",
            "id": str(uuid.uuid4()),
            "name": self.project_name,
            "themeCollection": {
                "baseTheme": {
                    "name": "CY24SU02",
                    "version": "5.0.0",
                    "type": "default"
                }
            },
            "layoutOptimization": "horizontal",
            "pages": pages_metadata,
            "config": {
                "version": "5.59",
                "settings": {
                    "isPersistentUserStateDisabled": False,
                    "hideVisualContainerHeader": False,
                    "useDefaultAggregateDisplayName": True
                }
            }
        }
        with open(os.path.join(def_path, "report.json"), 'w') as f:
            json.dump(report_json, f, indent=2)
