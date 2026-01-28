from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class TableauField(BaseModel):
    name: str
    caption: Optional[str] = None
    datatype: str
    role: str  # dimension or measure
    type: str  # nominal, quantitative, etc.
    formula: Optional[str] = None
    alias: Optional[str] = None

class TableauDataSource(BaseModel):
    name: str
    connection_type: str
    fields: List[TableauField] = []

class TableauVisual(BaseModel):
    name: str
    type: str
    fields: List[str] = []
    filters: List[Dict[str, Any]] = []

class TableauWorksheet(BaseModel):
    name: str
    visual: TableauVisual

class TableauWorkbook(BaseModel):
    name: str
    datasources: List[TableauDataSource] = []
    worksheets: List[TableauWorksheet] = []
