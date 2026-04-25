# src/graphrag.py
# ─────────────────────────────────────────────────────────────────────────────
# The GraphRAG pipeline for the Bollywood Knowledge Graph.
#
# Pipeline stages:
#   1. Vector Search    — find the most relevant graph nodes for the question
#   2. Graph Traversal  — walk the neighbourhood of each relevant node
#   3. Context Assembly — serialise the subgraph into structured text
#   4. LLM Reasoning    — generate a natural language answer from that context
# ─────────────────────────────────────────────────────────────────────────────

import os
from openai import OpenAI
from dotenv import load_dotenv
from db import Neo4jConnection
from embeddings import find_top_nodes

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# ─────────────────────────────────────────────────────────────────────────────
# STAGE 2: Graph Traversal
# ─────────────────────────────────────────────────────────────────────────────

def retrieve_subgraph(node_name: str, node_label: str, db: Neo4jConnection, hops: int = 2) -> dict:
    """
    Collect all nodes and relationships within `hops` of the starting node.

    The query returns structured data: the central node's properties, plus
    every (source, rel_type, target) triple in the neighbourhood. This
    triple format is easy for the LLM to reason over.
    """
    query = f"""
        MATCH (start:{node_label})
        WHERE start.name = $name OR start.title = $name

        OPTIONAL MATCH path = (start)-[*1..{hops}]-(neighbor)

        WITH start,
             collect(DISTINCT {{
                 from: COALESCE(startNode(last(relationships(path))).name,
                                startNode(last(relationships(path))).title),
                 rel:  type(last(relationships(path))),
                 to:   COALESCE(endNode(last(relationships(path))).name,
                                endNode(last(relationships(path))).title),
                 to_label: labels(endNode(last(relationships(path))))[0]
             }}) AS edges

        RETURN start, labels(start)[0] AS start_label, edges
    """
    rows = db.read(query, {"name": node_name})
    if not rows:
        return {}

    row = rows[0]
    return {
        "center":  row["start"],
        "label":   row["start_label"],
        "edges":   [e for e in row["edges"] if e.get("from") and e.get("to")],
    }


# ─────────────────────────────────────────────────────────────────────────────
# STAGE 3: Context Assembly
# ─────────────────────────────────────────────────────────────────────────────

def subgraph_to_context(subgraph: dict) -> str:
    """
    Serialise a subgraph dict into a clean, LLM-readable text block.

    Format:
        ENTITY: <name> [<label>]
        Properties: key=value, ...
        CONNECTIONS:
          • Source –[RELATIONSHIP]→ Target
    """
    if not subgraph or not subgraph.get("center"):
        return ""

    center = subgraph["center"]
    label  = subgraph.get("label", "")

    # Build property summary, skipping internal embedding fields
    skip = {"embedding", "embedding_text"}
    props = ", ".join(
        f"{k}={v}" for k, v in center.items()
        if k not in skip and v is not None
    )

    lines = [
        f"ENTITY: {center.get('name') or center.get('title', 'Unknown')} [{label}]",
        f"Properties: {props}",
        "",
        "CONNECTIONS:",
    ]

    seen = set()
    for edge in subgraph.get("edges", []):
        triple = (edge["from"], edge["rel"], edge["to"])
        if triple in seen:
            continue
        seen.add(triple)
        lines.append(f"  • {edge['from']}  –[{edge['rel']}]→  {edge['to']}")

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# STAGE 4: LLM Answer Generation
# ─────────────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an expert on Bollywood cinema with deep knowledge of Hindi films,
actors, directors, music composers, production houses, and awards.

You answer questions using exclusively the structured knowledge graph data provided
in each message. The data comes from a verified database, so treat every fact in it
as ground truth.

Guidelines:
- Answer directly and concisely.
- If the context contains enough information, give a complete answer.
- If the context is insufficient, say so clearly — do not speculate.
- Do not mention the graph, database, or retrieval process in your answer.
- For list-type answers, use bullet points.
- Keep answers friendly and conversational."""


def generate_answer(question: str, context: str) -> str:
    """Call the LLM with the assembled context to generate a final answer."""
    user_msg = f"""Based on the following Bollywood knowledge graph data, please answer:

QUESTION: {question}

KNOWLEDGE GRAPH CONTEXT:
{context}

Please provide a clear, accurate answer based only on the information above."""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_msg},
        ],
        temperature=0.2,
    )
    return response.choices[0].message.content.strip()


# ─────────────────────────────────────────────────────────────────────────────
# FULL PIPELINE
# ─────────────────────────────────────────────────────────────────────────────

def graphrag_answer(
    question: str,
    db: Neo4jConnection,
    top_k: int = 3,
    hops: int = 2,
    verbose: bool = False,
) -> dict:
    """
    Answer a question about Bollywood using the full GraphRAG pipeline.

    Returns a dict with:
        answer:          Final natural language answer
        context:         The raw graph context used
        retrieved_nodes: List of nodes found by vector search
        cypher_used:     None (traversal is graph-native, not text-to-cypher)
    """

    # ── Stage 1: Vector Search ─────────────────────────────────────────────
    relevant_nodes = find_top_nodes(question, db, top_k=top_k)

    if not relevant_nodes:
        return {
            "answer": "I could not find any relevant entities in the knowledge graph for this question.",
            "context": "", "retrieved_nodes": [],
        }

    if verbose:
        print(f"\n[Vector Search] Top {top_k} nodes:")
        for n in relevant_nodes:
            print(f"  [{n['label']:<15}] {n['name']:<35} score={n['score']:.3f}")

    # ── Stage 2 & 3: Traversal + Context Assembly ──────────────────────────
    context_blocks = []
    for node in relevant_nodes:
        sg = retrieve_subgraph(node["name"], node["label"], db, hops=hops)
        block = subgraph_to_context(sg)
        if block:
            context_blocks.append(block)

    context = "\n\n───────────────────────────────────\n\n".join(context_blocks)

    if verbose:
        fact_count = context.count("•")
        print(f"[Traversal] {fact_count} connection facts collected across {len(context_blocks)} subgraphs")

    # ── Stage 4: LLM Reasoning ─────────────────────────────────────────────
    answer = generate_answer(question, context)

    return {
        "answer":          answer,
        "context":         context,
        "retrieved_nodes": [{"name": n["name"], "label": n["label"], "score": n["score"]}
                            for n in relevant_nodes],
    }


# ─────────────────────────────────────────────────────────────────────────────
# QUICK TEST
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    questions = [
        "Which films did Aamir Khan and AR Rahman collaborate on?",
        "Which Bollywood actors worked under Rajkumar Hirani's direction?",
        "Which movies produced by Yash Raj Films have Shah Rukh Khan?",
        "What national awards have films from Aamir Khan Productions won?",
        "Which actresses starred in films produced by Dharma Productions?",
    ]

    with Neo4jConnection() as db:
        for q in questions:
            print(f"\n{'='*65}")
            print(f"Q: {q}")
            print("─"*65)
            result = graphrag_answer(q, db, verbose=True)
            print(f"\nA: {result['answer']}")
