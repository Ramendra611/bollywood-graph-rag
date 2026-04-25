# src/api.py
# ─────────────────────────────────────────────────────────────────────────────
# FastAPI backend for the Bollywood GraphRAG system.
#
# Endpoints:
#   POST /ask           — GraphRAG question answering
#   GET  /search        — Vector similarity search over nodes
#   GET  /graph/{name}  — Return the neighbourhood subgraph of an entity
#   GET  /stats         — Database statistics
#   GET  /health        — Health check
#   POST /cypher        — Run a raw read-only Cypher query (dev mode)
# ─────────────────────────────────────────────────────────────────────────────

import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
from dotenv import load_dotenv

from db import Neo4jConnection
from graphrag import graphrag_answer, retrieve_subgraph, subgraph_to_context
from embeddings import find_top_nodes

load_dotenv()

app = FastAPI(
    title="Bollywood GraphRAG API",
    description="Knowledge graph-powered question answering over Bollywood cinema",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Single shared connection (FastAPI runs in one process)
db = Neo4jConnection()


# ─────────────────────────────────────────────────────────────────────────────
# Request / Response Models
# ─────────────────────────────────────────────────────────────────────────────

class QuestionRequest(BaseModel):
    question: str = Field(..., min_length=5, example="Which films did Aamir Khan and AR Rahman work on together?")
    top_k:    int = Field(default=3, ge=1, le=10, description="Number of starting nodes for graph traversal")
    hops:     int = Field(default=2, ge=1, le=4,  description="Traversal depth from each starting node")


class QuestionResponse(BaseModel):
    question:        str
    answer:          str
    retrieved_nodes: list[dict]
    context_preview: str          # First 500 chars of context, for transparency


class CypherRequest(BaseModel):
    query: str = Field(..., example="MATCH (m:Movie) RETURN m.title LIMIT 5")


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    """Confirm the API and database are reachable."""
    try:
        count = db.read("MATCH (n) RETURN count(n) AS total")[0]["total"]
        return {"status": "ok", "node_count": count}
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.post("/ask", response_model=QuestionResponse)
def ask(req: QuestionRequest):
    """
    Answer a natural language question about Bollywood using GraphRAG.

    The pipeline:
    1. Embed the question and find the top_k most relevant graph nodes
    2. Traverse each node's neighbourhood up to `hops` relationship steps
    3. Assemble the subgraph as structured text context
    4. Call GPT-4o to generate a natural language answer from that context
    """
    try:
        result = graphrag_answer(
            question=req.question,
            db=db,
            top_k=req.top_k,
            hops=req.hops,
        )
        return QuestionResponse(
            question=req.question,
            answer=result["answer"],
            retrieved_nodes=result["retrieved_nodes"],
            context_preview=result["context"][:500],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/search")
def search(
    q: str = Query(..., description="Search term"),
    top_k: int = Query(default=5, ge=1, le=20),
    label: Optional[str] = Query(default=None, description="Filter by node label: Movie, Person, Award, ProductionHouse"),
):
    """
    Vector similarity search over graph nodes.

    Useful for exploring what entities exist in the graph related to a topic.
    """
    try:
        labels = [label] if label else None
        results = find_top_nodes(q, db, top_k=top_k, labels=labels)
        return {
            "query":   q,
            "results": [
                {"label": r["label"], "name": r["name"], "score": round(r["score"], 4)}
                for r in results
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/graph/{entity_name}")
def get_subgraph(
    entity_name: str,
    label: str = Query(default="Movie", description="Node label"),
    hops: int   = Query(default=2, ge=1, le=3),
):
    """
    Return the neighbourhood subgraph of a named entity as structured text.

    Useful for exploring what the graph knows about a specific entity.
    """
    try:
        sg      = retrieve_subgraph(entity_name, label, db, hops=hops)
        context = subgraph_to_context(sg)
        if not context:
            raise HTTPException(status_code=404, detail=f"Entity '{entity_name}' not found as {label}")
        return {"entity": entity_name, "label": label, "context": context}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
def stats():
    """Return counts of nodes and relationship types in the graph."""
    node_counts = db.read("""
        MATCH (n)
        RETURN labels(n)[0] AS label, count(n) AS count
        ORDER BY count DESC
    """)
    rel_counts = db.read("""
        MATCH ()-[r]->()
        RETURN type(r) AS rel_type, count(r) AS count
        ORDER BY count DESC
    """)
    return {
        "nodes":         node_counts,
        "relationships": rel_counts,
    }


@app.post("/cypher")
def run_cypher(req: CypherRequest):
    """
    Execute a raw Cypher query (read-only). For development and exploration.

    Only MATCH queries are accepted. Write operations are rejected.
    """
    query_upper = req.query.strip().upper()
    forbidden   = ["CREATE", "MERGE", "DELETE", "SET", "REMOVE", "DROP"]
    for word in forbidden:
        if word in query_upper:
            raise HTTPException(
                status_code=400,
                detail=f"Write operation '{word}' not permitted on this endpoint."
            )
    try:
        rows = db.read(req.query)
        return {"results": rows, "count": len(rows)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/movies")
def list_movies(limit: int = Query(default=20, le=100)):
    """Return all movies in the graph, sorted by box office."""
    rows = db.read("""
        MATCH (m:Movie)
        RETURN m.title AS title, m.year AS year,
               m.genre AS genre, m.box_office_crore AS crore
        ORDER BY m.box_office_crore DESC
        LIMIT $limit
    """, {"limit": limit})
    return {"movies": rows}


@app.get("/person/{name}/filmography")
def filmography(name: str):
    """Return the complete filmography of a person (acted, directed, composed)."""
    acted = db.read("""
        MATCH (p:Person {name: $name})-[r:ACTED_IN]->(m:Movie)
        RETURN m.title AS movie, m.year AS year, r.character AS character, r.lead_role AS lead
        ORDER BY m.year
    """, {"name": name})

    directed = db.read("""
        MATCH (p:Person {name: $name})-[:DIRECTED]->(m:Movie)
        RETURN m.title AS movie, m.year AS year
        ORDER BY m.year
    """, {"name": name})

    composed = db.read("""
        MATCH (p:Person {name: $name})-[:COMPOSED_MUSIC_FOR]->(m:Movie)
        RETURN m.title AS movie, m.year AS year
        ORDER BY m.year
    """, {"name": name})

    awards = db.read("""
        MATCH (p:Person {name: $name})-[:WON]->(a:Award)
        RETURN a.name AS award, a.category AS category, a.year AS year
        ORDER BY a.year
    """, {"name": name})

    return {
        "name":     name,
        "acted_in": acted,
        "directed": directed,
        "composed": composed,
        "awards":   awards,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
