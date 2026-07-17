from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from . import models, schemas, parser, versioning, database, llm
import shutil
import os
import json

router = APIRouter()

@router.post("/ingest")
def ingest_document(file: UploadFile = File(...), version: int = 1, db: Session = Depends(database.get_db)):
    temp_path = f"data/temp_{file.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    doc_record = models.Document(version=version)
    db.add(doc_record)
    db.commit()
    
    p = parser.DocumentParser(temp_path)
    nodes_data = p.parse(doc_record.id)
    
    if version > 1:
        v1_nodes = db.query(models.Node).join(models.Document).filter(models.Document.version == version - 1).all()
        nodes_data = versioning.match_nodes_v1_v2(v1_nodes, nodes_data)
    
    for nd in nodes_data:
        db_node = models.Node(
            document_id=doc_record.id,
            heading=nd['heading'],
            content=nd['content'],
            level=nd['level'],
            content_hash=nd['content_hash'],
            logical_node_id=nd.get('logical_node_id')
        )
        db.add(db_node)
    
    db.commit()
    os.remove(temp_path)
    return {"message": f"Successfully ingested version {version}", "document_id": doc_record.id}

@router.post("/selections")
def create_selection(selection: schemas.SelectionCreate, db: Session = Depends(database.get_db)):
    # Store node IDs as a JSON string
    db_selection = models.Selection(
        name=selection.name,
        version_pinned=selection.version,
        node_ids=json.dumps(selection.node_ids)
    )
    db.add(db_selection)
    db.commit()
    return {"selection_id": db_selection.id}

@router.post("/generate/{selection_id}")
def generate_tests(selection_id: int, db: Session = Depends(database.get_db)):
    selection = db.query(models.Selection).filter(models.Selection.id == selection_id).first()
    if not selection:
        raise HTTPException(status_code=404, detail="Selection not found")
    
    # Get the text from the nodes
    node_ids = json.loads(selection.node_ids)
    nodes = db.query(models.Node).filter(models.Node.id.in_(node_ids)).all()
    combined_text = "\n".join([n.content for n in nodes])
    
    # Call LLM
    test_cases = llm.generate_test_cases(combined_text)
    
    # Store in NoSQL (MongoDB)
    gen_data = {
        "selection_id": selection_id,
        "nodes_snapshot": [{"id": n.id, "hash": n.content_hash} for n in nodes],
        "test_cases": test_cases
    }
    database.generations_collection.insert_one(gen_data)
    
    return test_cases

@router.get("/staleness/{selection_id}")
def check_staleness(selection_id: int, db: Session = Depends(database.get_db)):
    selection = db.query(models.Selection).filter(models.Selection.id == selection_id).first()
    gen = database.generations_collection.find_one({"selection_id": selection_id})
    
    if not gen: return {"status": "No generation found"}

    results = []
    for snapshot in gen["nodes_snapshot"]:
        # Find the same logical node in the LATEST document version
        latest_node = db.query(models.Node).join(models.Document).order_by(models.Document.version.desc()).first() # Simplified
        # Real logic would match logical_node_id
        
        is_stale = snapshot["hash"] != latest_node.content_hash
        results.append({"node_id": snapshot["id"], "stale": is_stale})
        
    return results