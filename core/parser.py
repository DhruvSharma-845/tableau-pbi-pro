import zipfile
import os
from lxml import etree
from .models import TableauWorkbook, TableauDataSource, TableauField, TableauWorksheet, TableauVisual

class TWBParser:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.xml_content = self._load_xml()

    def _load_xml(self) -> bytes:
        if self.file_path.endswith('.twbx'):
            with zipfile.ZipFile(self.file_path, 'r') as zip_ref:
                for file in zip_ref.namelist():
                    if file.endswith('.twb'):
                        return zip_ref.read(file)
        elif self.file_path.endswith('.twb'):
            with open(self.file_path, 'rb') as f:
                return f.read()
        raise ValueError("Unsupported file format. Must be .twb or .twbx")

    def parse(self) -> TableauWorkbook:
        root = etree.fromstring(self.xml_content)
        workbook_name = os.path.basename(self.file_path)
        
        datasources = self._parse_datasources(root)
        worksheets = self._parse_worksheets(root)
        
        return TableauWorkbook(
            name=workbook_name,
            datasources=datasources,
            worksheets=worksheets
        )

    def _parse_datasources(self, root) -> list[TableauDataSource]:
        ds_map = {}
        for ds_xml in root.xpath('//datasource'):
            name = ds_xml.get('name', 'unnamed')
            if name.startswith('Parameters') or ds_xml.get('caption') == 'Parameters':
                continue
            
            # Use caption if available, otherwise name
            display_name = ds_xml.get('caption', name)
            
            if display_name not in ds_map:
                conn = ds_xml.xpath('./connection')
                conn_type = conn[0].get('class', 'unknown') if conn else 'unknown'
                ds_map[display_name] = TableauDataSource(
                    name=display_name,
                    connection_type=conn_type,
                    fields=[]
                )
            
            ds = ds_map[display_name]
            existing_field_names = {f.name for f in ds.fields}
            
            # Parse columns (often calculations or overrides)
            for col in ds_xml.xpath('.//column'):
                field_name = col.get('name', '').strip('[]')
                if not field_name: continue
                
                if field_name not in existing_field_names:
                    ds.fields.append(TableauField(
                        name=field_name,
                        caption=col.get('caption'),
                        datatype=col.get('datatype', 'string'),
                        role=col.get('role', 'dimension'),
                        type=col.get('type', 'nominal'),
                        formula=col.xpath('./calculation/@formula')[0] if col.xpath('./calculation/@formula') else None
                    ))
                    existing_field_names.add(field_name)
            
            # Parse metadata-records (physical columns)
            for meta in ds_xml.xpath('.//metadata-record'):
                remote_name = meta.xpath('./remote-name/text()')
                local_name = meta.xpath('./local-name/text()')
                if not local_name: continue
                
                field_name = local_name[0].strip('[]')
                if field_name not in existing_field_names:
                    ds.fields.append(TableauField(
                        name=field_name,
                        datatype=self._map_tableau_type(meta.xpath('./parent-type/text()')),
                        role='dimension', # Default for physical columns
                        type='nominal'
                    ))
                    existing_field_names.add(field_name)

        return list(ds_map.values())

    def _map_tableau_type(self, t_type):
        if not t_type: return 'string'
        t_type = t_type[0].lower()
        if 'integer' in t_type: return 'integer'
        if 'real' in t_type or 'float' in t_type: return 'real'
        if 'datetime' in t_type: return 'datetime'
        if 'date' in t_type: return 'date'
        if 'boolean' in t_type: return 'boolean'
        return 'string'

    def _parse_worksheets(self, root) -> list[TableauWorksheet]:
        ws_list = []
        for ws_xml in root.xpath('//worksheet'):
            name = ws_xml.get('name', 'unnamed')
            visual_type = "table"
            marks = ws_xml.xpath('.//pane/view/node-selection/mark')
            if marks:
                visual_type = marks[0].get('class', 'table')
                
            ws_list.append(TableauWorksheet(
                name=name,
                visual=TableauVisual(
                    name=name,
                    type=visual_type
                )
            ))
        return ws_list
