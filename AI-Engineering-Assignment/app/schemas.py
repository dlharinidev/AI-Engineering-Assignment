from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class NodeBase(BaseModel):
    heading: str
    content: str
    level: int
    content_hash: str

class NodeResponse(NodeBase):
    id: int
    parent_id: Optional[int]
    logical_node_id: str
    
    class Config:
        from_attributes = True

class NodeTreeResponse(NodeBase):
    id: int
    parent_id: Optional[int]
    logical_node_id: str
    children: List['NodeTreeResponse'] = []
    
    class Config:
        from_attributes = True

class DocumentResponse(BaseModel):
    id: int
    version: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class SelectionCreate(BaseModel):
    name: str
    node_ids: List[int]
    version: int

class DiffResponse(BaseModel):
    has_changed: bool
    diff_summary: str

class TestCase(BaseModel):
    title: str
    steps: str
    expected_result: str

class TestCaseResponse(BaseModel):
    selection_id: int
    is_stale: bool
    test_cases: List[TestCase]

# Rebuild model for recursive reference
NodeTreeResponse.model_rebuild()