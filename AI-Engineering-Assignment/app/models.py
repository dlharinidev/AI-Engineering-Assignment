from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql import func
from .database import Base

class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, default="CT-200 Manual")
    version = Column(Integer, index=True) # e.g., 1 or 2
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Node(Base):
    __tablename__ = "nodes"
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    
    # Hierarchy
    parent_id = Column(Integer, ForeignKey("nodes.id"), nullable=True)
    level = Column(Integer) # 0 for Title, 1 for H1, etc.
    heading = Column(String)
    content = Column(Text)
    content_hash = Column(String) # For staleness detection
    
    # Metadata
    logical_node_id = Column(String, index=True) # ID that stays same across v1 and v2
    
    children = relationship("Node", backref=backref("parent_node", remote_side=[id]))
    document = relationship("Document")

class Selection(Base):
    __tablename__ = "selections"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    version_pinned = Column(Integer) # The document version this selection was made against
    # Store node IDs as a comma-separated string or a separate mapping table
    node_ids = Column(String)