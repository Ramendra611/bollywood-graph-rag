# Bollywood GraphRAG — Complete Project Walkthrough

A plain-English guide to every concept, every file, and every design decision in this project.

---

## Table of Contents

1. [What problem does this solve?](#1-what-problem-does-this-solve)
2. [The big picture — what happens when you ask a question](#2-the-big-picture)
3. [The knowledge graph — nodes, edges, and ontology](#3-the-knowledge-graph)
4. [File-by-file breakdown](#4-file-by-file-breakdown)
5. [Embeddings deep dive — where they live, how they work, and better alternatives](#5-embeddings-deep-dive)
6. [The 4-stage GraphRAG pipeline in detail](#6-the-4-stage-graphrag-pipeline-in-detail)
7. [The API layer (FastAPI)](#7-the-api-layer)
8. [The UI layer (Streamlit)](#8-the-ui-layer)
9. [Docker and infrastructure](#9-docker-and-infrastructure)
10. [Key concepts cheat sheet for interviews or teaching](#10-key-concepts-cheat-sheet)

---

## 1. What Problem Does This Solve?

### The plain RAG problem

A standard RAG (Retrieval-Augmented Generation) system works like this:
- You dump your documents into a vector database as chunks of text.
- A user asks a question → you embed the question → you find the most similar chunks → you send those chunks to an LLM.

This works well for **document search** but breaks badly for **relational questions**:

> *"Which music composers have worked on films that won both a National Award and a Filmfare Award?"*

To answer this you need to:
1. Find music composers (entities)
2. Find which films they worked on (relationship traversal)
3. Find which of those films won National Awards (another relationship)
4. Cross-check which of those also won Filmfare (filtering)

A chunk-based vector search cannot do multi-hop reasoning. It finds chunks that *mention* composers and awards, but it cannot *trace the path* between them.

### The GraphRAG solution

Instead of storing text chunks, we store structured **entities and relationships** in a graph database (Neo4j). When a user asks a question:
1. We find the most relevant *nodes* (not text chunks) using vector similarity.
2. We *traverse the graph* from those nodes — following edges to collect structured facts.
3. We hand those facts to the LLM as context.

The LLM doesn't hallucinate connections — every fact it uses came directly from a verified graph edge.

---

## 2. The Big Picture

Here is the full data and request flow in this project:

```
──────────────────────────────────────────────────────────────────
DATA SETUP (run once)
──────────────────────────────────────────────────────────────────

bollywood_data.py          loader.py              Neo4j
(Python lists of     ───►  (MERGE Cypher   ───►  (Graph stored
 nodes + edges)             statements)            on disk)
                                │
                                ▼
                         embeddings.py
                         (Node → sentence → OpenAI API → vector)
                                │
                                ▼
                         Neo4j nodes now have an
                         `embedding` property (JSON list of floats)

──────────────────────────────────────────────────────────────────
REQUEST FLOW (every time a user asks a question)
──────────────────────────────────────────────────────────────────

User types question
        │
        ▼
   app.py (Streamlit)
        │  HTTP POST /ask
        ▼
   api.py (FastAPI)
        │  calls
        ▼
   graphrag.py — Stage 1: embed question → cosine similarity → top-k nodes
        │
        ▼
   graphrag.py — Stage 2: graph traversal (Cypher MATCH path)
        │
        ▼
   graphrag.py — Stage 3: serialise subgraph to structured text
        │
        ▼
   graphrag.py — Stage 4: send text to GPT-4o → natural language answer
        │
        ▼
   api.py → app.py → User sees the answer
```

---

## 3. The Knowledge Graph

### What is a knowledge graph?

A knowledge graph is a way of storing facts as a network of **entities** (nodes) connected by **relationships** (edges). Instead of a flat table, you store:

```
Shah Rukh Khan  ──[ACTED_IN]──►  Dangal
                                   │
                                   ▼
                              [WON]──► National Award Best Film 2017
```

Every fact is a triple: **(Subject) → [Relationship] → (Object)**

### This project's ontology

An **ontology** is the schema of your graph — what kinds of things exist and how they connect.

```
NODE TYPES (labels)
────────────────────────────────────────────────────────
Person          name, born, profession, hometown
Movie           title, year, genre, box_office_crore, description
ProductionHouse name, founded, founder, hq
Award           name, category, year

RELATIONSHIP TYPES
────────────────────────────────────────────────────────
(Person)          -[:ACTED_IN {character, lead_role}]->  (Movie)
(Person)          -[:DIRECTED]->                         (Movie)
(Person)          -[:COMPOSED_MUSIC_FOR]->               (Movie)
(Person/Movie)    -[:WON]->                              (Award)
(ProductionHouse) -[:PRODUCED]->                         (Movie)
```

### Why Neo4j?

Neo4j is the most popular **property graph database**. Key features used in this project:

- **Cypher** — a query language that reads like a diagram of the graph
- **MERGE** — upsert semantics (create if not exists, match if it does)
- **Bolt protocol** — efficient binary protocol for Python driver connections
- **APOC plugin** — extended procedures for import, export, and graph algorithms

---

## 4. File-by-File Breakdown

### `src/data/bollywood_data.py` — The raw dataset

This is just Python data — no database logic. Five lists:

| List | What it contains |
|---|---|
| `PEOPLE` | 35 people (actors, directors, composers) as dicts |
| `MOVIES` | 26 movies with descriptions and box office figures |
| `PRODUCTION_HOUSES` | 10 studios |
| `AWARDS` | 25 awards (Filmfare, National, Oscar, Civilian) |
| `ACTED_IN`, `DIRECTED`, etc. | Relationship tuples linking the above |

**Why keep data separate from loader logic?**  
It makes the dataset easy to extend — you add a movie here and the loader, embeddings, and graph all pick it up automatically. No SQL migrations, no schema changes.

---

### `src/db.py` — Database connection wrapper

```python
class Neo4jConnection:
    def read(self, query, params) -> list[dict]
    def write(self, query, params) -> None
    def write_batch(self, query, rows, batch_size) -> int
```

All database access in the project goes through this class. It:
- Reads Neo4j connection credentials from `.env`
- Manages a connection pool via the official Neo4j Python driver
- Supports Python context manager (`with Neo4jConnection() as db:`)

**Why a wrapper?** So no module ever touches the raw driver — if you swap databases, you change one file.

---

### `src/loader.py` — Loading nodes and relationships into Neo4j

This file reads the Python lists from `bollywood_data.py` and writes them to Neo4j using Cypher's `MERGE` statement.

**What is MERGE?**

```cypher
MERGE (n:Person {name: "Aamir Khan"})
SET n.born = 1965, n.profession = "Actor-Director"
```

`MERGE` means: *"If a Person node with this name already exists, use it. If not, create it."* This is why you can safely re-run `loader.py` — it never creates duplicates.

**Constraints:**

```cypher
CREATE CONSTRAINT bw_person IF NOT EXISTS FOR (p:Person) REQUIRE p.name IS UNIQUE
```

Constraints act like a unique index. They prevent duplicate nodes AND speed up MERGE lookups (Neo4j checks the index instead of scanning all nodes).

**What gets loaded:**

```
[1/2] Loading nodes
  ✓ 35 Person nodes
  ✓ 26 Movie nodes
  ✓ 10 ProductionHouse nodes
  ✓ 25 Award nodes

[2/2] Loading relationships
  ✓ 41 ACTED_IN relationships
  ✓ 26 DIRECTED relationships
  ✓ 18 COMPOSED_MUSIC_FOR relationships
  ✓ 20 PRODUCED relationships
  ✓ 22 WON relationships
```

---

### `src/embeddings.py` — Vector embeddings on graph nodes

This is the bridge between the graph world and the AI/ML world. Full explanation in Section 5 below.

---

### `src/graphrag.py` — The pipeline

The core of the project. Full explanation in Section 6 below.

---

### `src/api.py` — FastAPI backend

REST endpoints that wrap the pipeline. Full explanation in Section 7 below.

---

### `src/app.py` — Streamlit frontend

Four-page UI. Full explanation in Section 8 below.

---

## 5. Embeddings Deep Dive

This is the most conceptually important part of the project.

### What is a vector embedding?

An **embedding** is a way of converting text into a list of numbers (a vector) such that similar meanings produce similar numbers.

Example:
```
"Aamir Khan is an actor born in 1965"  →  [0.12, -0.87, 0.34, 0.05, ..., 0.91]  (1536 numbers)
"Shah Rukh Khan is an actor from Delhi" →  [0.15, -0.82, 0.39, 0.02, ..., 0.88]  (1536 numbers)
"The Eiffel Tower is in Paris"          →  [-0.71, 0.23, -0.55, 0.91, ..., -0.12] (1536 numbers)
```

The first two vectors will be very close to each other (both describe Bollywood actors). The third will be far away (irrelevant topic). This "closeness" is measured with **cosine similarity**.

### Step 1 — Convert each node to a sentence

Before you can embed a node, you have to convert its properties into a meaningful sentence. See `node_to_text()` in [src/embeddings.py](src/embeddings.py):

```python
# For a Movie node:
"'Dangal' is a Sports Biopic Hindi film released in 2016.
 The real story of Mahavir Singh Phogat who trains his daughters..."

# For a Person node:
"Aamir Khan is an Indian Actor-Director born in 1965 from Mumbai."

# For a ProductionHouse node:
"Yash Raj Films is a Bollywood production house founded in 1970 by Yash Chopra."
```

This matters a lot. A poorly written sentence = a bad embedding = wrong nodes retrieved for a question.

### Step 2 — Call OpenAI's embedding API

```python
response = client.embeddings.create(
    input=["'Dangal' is a Sports Biopic..."],
    model="text-embedding-3-small"
)
vector = response.data[0].embedding  # list of 1536 floats
```

`text-embedding-3-small` is OpenAI's efficient embedding model. It converts any text into a 1536-dimensional vector.

### Step 3 — Store the vector on the Neo4j node

```python
db.write("""
    MATCH (n) WHERE id(n) = $nid
    SET n.embedding = $vec,
        n.embedding_text = $txt
""", {"nid": node_id, "vec": json.dumps(vector), "txt": sentence})
```

**The vector is stored as a JSON string property on the node itself.** Every node in the graph now carries its own embedding alongside its regular properties.

```
Neo4j Node: Movie {
    title: "Dangal",
    year: 2016,
    genre: "Sports Biopic",
    box_office_crore: 2024.0,
    description: "The real story of...",
    embedding: "[0.12, -0.87, 0.34, ...]",   ← stored as JSON string
    embedding_text: "'Dangal' is a Sports Biopic..."
}
```

### Where exactly are the embeddings stored?

**In Neo4j, as a property on each node.** Not in a separate vector database, not in a file — directly on the node alongside `title`, `year`, etc.

This is the simplest approach: one system holds everything. The graph structure AND the vector search data live together in Neo4j.

### How similarity search works at query time

When a user asks a question:

```python
# 1. Embed the question
q_vec = client.embeddings.create(input=["Which films crossed 1000 crore?"], ...).data[0].embedding

# 2. Fetch ALL node embeddings from Neo4j
rows = db.read("MATCH (n) WHERE n.embedding IS NOT NULL RETURN n, labels(n)[0] AS lbl")

# 3. Compute cosine similarity between question vector and each node vector
for row in rows:
    node_vec = json.loads(row["n"]["embedding"])
    score = cosine_similarity(q_vec, node_vec)

# 4. Sort by score, take top-k
```

**Cosine similarity** measures the angle between two vectors. Score of 1.0 = identical direction = same meaning. Score of 0 = perpendicular = completely unrelated.

```
cosine_similarity(a, b) = (a · b) / (|a| × |b|)
```

---

### Could we use FAISS or ChromaDB instead? — Yes, and here's why you'd want to

The current approach (store embeddings as JSON strings, compute similarity in Python) is called **brute-force search** — it compares every node to the query. It works fine for ~1000 nodes, but it has two problems at scale:

1. **Speed** — at 1 million nodes, comparing every embedding is slow.
2. **Memory** — pulling all embeddings from Neo4j on every query is wasteful.

Here's a comparison of the alternatives:

| Approach | Used in this project | When to use |
|---|---|---|
| JSON string on Neo4j node | Yes | < 10k nodes, simplicity matters, one system to manage |
| Neo4j vector index (Enterprise) | No | > 10k nodes, want everything in one system |
| FAISS (Meta's library) | No | > 100k nodes, need fastest possible ANN search, no persistence needed |
| ChromaDB | No | Want a purpose-built vector DB with persistence and metadata filtering |
| Pinecone / Weaviate / Qdrant | No | Production SaaS, managed vector search |

**FAISS** (Facebook AI Similarity Search) builds an Approximate Nearest Neighbour (ANN) index. Instead of comparing every vector, it builds a spatial index (like an inverted file or HNSW graph) so you can find the top-k similar vectors in milliseconds even with millions of entries.

**ChromaDB** is a local vector database with a Python API. It persists embeddings to disk, supports metadata filtering, and is much easier to use than FAISS for development.

**How you'd plug in ChromaDB instead:**

```python
# embeddings.py — instead of storing on the Neo4j node:
import chromadb
chroma = chromadb.PersistentClient(path="./chroma_store")
collection = chroma.get_or_create_collection("bollywood_nodes")

collection.add(
    ids=[str(node_id)],
    embeddings=[vector],
    documents=[sentence],
    metadatas=[{"label": label, "name": node_name}]
)

# find_top_nodes — instead of fetching all from Neo4j:
results = collection.query(
    query_embeddings=[q_vec],
    n_results=top_k
)
# returns the top-k closest nodes
```

The rest of the pipeline (graph traversal, LLM) stays exactly the same. Only Stage 1 changes.

**For this project, Neo4j JSON storage is the right call** — the graph has ~96 nodes. The simplicity of one system beats the added complexity of a second database.

---

## 6. The 4-Stage GraphRAG Pipeline in Detail

All of this lives in [src/graphrag.py](src/graphrag.py).

### Stage 1 — Vector Search (find_top_nodes in embeddings.py)

**Input:** User's natural language question  
**Output:** Top-k graph nodes most semantically related to the question

```
Question: "Which films did Aamir Khan and AR Rahman collaborate on?"
    ↓ embed
[0.23, -0.54, 0.87, ...]  (1536-dim vector)
    ↓ cosine similarity against all 96 node embeddings
    ↓ top-3 results:
  [Person] Aamir Khan          score=0.91
  [Person] AR Rahman            score=0.88
  [Movie]  Lagaan               score=0.82
```

**Why does this work?**  
The question mentions "Aamir Khan" and "AR Rahman" by name. When the nodes were embedded, "Aamir Khan is an Indian Actor-Director..." and "AR Rahman is an Indian Music Composer..." were embedded with similar contextual meaning. So the question vector lands close to those node vectors in the 1536-dimensional space.

It also works for *concept* searches without exact names:
```
Question: "cricket match set in British India"
→ finds: Movie "Lagaan" (score=0.89)  ← no name mentioned, pure concept match
```

---

### Stage 2 — Graph Traversal (retrieve_subgraph)

**Input:** A node name + label (e.g. "Aamir Khan", "Person")  
**Output:** A dict with the central node's properties and all edge triples within N hops

```cypher
MATCH (start:Person)
WHERE start.name = "Aamir Khan"
OPTIONAL MATCH path = (start)-[*1..2]-(neighbor)
WITH start, collect(DISTINCT {
    from: startNode(last(relationships(path))).name,
    rel:  type(last(relationships(path))),
    to:   endNode(last(relationships(path))).name
}) AS edges
RETURN start, labels(start)[0] AS start_label, edges
```

**What does `[*1..2]` mean?**  
Walk between 1 and 2 relationship hops from the starting node, in any direction. So from "Aamir Khan" at hop 1 you get movies he acted in; at hop 2 you get the awards those movies won, the directors of those movies, the production houses, etc.

**What comes back:**

```python
{
    "center": {"name": "Aamir Khan", "born": 1965, "profession": "Actor-Director", ...},
    "label": "Person",
    "edges": [
        {"from": "Aamir Khan", "rel": "ACTED_IN",           "to": "Lagaan"},
        {"from": "Aamir Khan", "rel": "ACTED_IN",           "to": "3 Idiots"},
        {"from": "Aamir Khan", "rel": "DIRECTED",           "to": "Taare Zameen Par"},
        {"from": "AR Rahman",  "rel": "COMPOSED_MUSIC_FOR", "to": "Lagaan"},
        {"from": "Lagaan",     "rel": "WON",                "to": "National Award Best Film 2002"},
        ...
    ]
}
```

This is the power of graph traversal — one Cypher query collects all connected facts within 2 hops, giving the LLM a rich, structured neighbourhood of facts around each relevant entity.

---

### Stage 3 — Context Assembly (subgraph_to_context)

**Input:** The subgraph dict from Stage 2  
**Output:** A human-readable text block that the LLM can reason over

```python
def subgraph_to_context(subgraph):
    # Serialise center node properties
    # Then list every edge as "Source –[RELATIONSHIP]→ Target"
```

Output looks like:

```
ENTITY: Aamir Khan [Person]
Properties: born=1965, profession=Actor-Director, hometown=Mumbai

CONNECTIONS:
  • Aamir Khan  –[ACTED_IN]→  Lagaan
  • Aamir Khan  –[ACTED_IN]→  3 Idiots
  • Aamir Khan  –[DIRECTED]→  Taare Zameen Par
  • AR Rahman   –[COMPOSED_MUSIC_FOR]→  Lagaan
  • Lagaan      –[WON]→  National Award Best Film 2002
  • Nitesh Tiwari –[DIRECTED]→  Dangal
  ...
```

For top_k=3, this is done for each of the 3 retrieved nodes and the blocks are concatenated with separators. The LLM receives the full combined context.

**Why not pass the raw graph data structure?**  
LLMs work on text. The bullet-point format with entity/relationship labels is clear, unambiguous, and easy for GPT-4o to parse and reason over.

---

### Stage 4 — LLM Reasoning (generate_answer)

**Input:** The user's question + the assembled context text  
**Output:** A natural language answer grounded in the graph facts

```python
SYSTEM_PROMPT = """You are an expert on Bollywood cinema...
Answer questions using exclusively the structured knowledge graph data provided.
Treat every fact in it as ground truth.
If context is insufficient, say so — do not speculate."""

user_msg = f"""
QUESTION: {question}
KNOWLEDGE GRAPH CONTEXT:
{context}
Please provide a clear, accurate answer based only on the information above.
"""

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[system, user_msg],
    temperature=0.2,   # low temperature = factual, less creative
)
```

**temperature=0.2** keeps the model close to what the context says. Higher temperature = more creative but more likely to stray from the facts.

**The key instruction: "do not speculate."** Since every fact in the context came from a verified graph edge, the LLM's answer is grounded. If the graph doesn't contain the answer, the LLM says so.

---

## 7. The API Layer

[src/api.py](src/api.py) wraps the pipeline in a FastAPI REST server.

### Endpoints

| Method | Path | What it does |
|---|---|---|
| `GET` | `/health` | Confirms Neo4j connection is live |
| `POST` | `/ask` | Full GraphRAG pipeline — takes a question, returns an answer |
| `GET` | `/search` | Vector similarity search only (no LLM, no traversal) |
| `GET` | `/graph/{name}` | Returns the neighbourhood context of one named entity |
| `GET` | `/stats` | Node and relationship counts |
| `GET` | `/movies` | List all movies with filters |
| `GET` | `/person/{name}/filmography` | All roles, directed films, compositions, awards for one person |
| `POST` | `/cypher` | Run a raw read-only Cypher query (dev tool) |

### Why FastAPI?

- Auto-generates interactive docs at `/docs` (Swagger UI)
- Pydantic models for request/response validation
- Async-ready for production scaling
- Type hints throughout for IDE support

### Why a separate API instead of calling Neo4j directly from Streamlit?

Separation of concerns. The Streamlit app only knows HTTP — it doesn't need a database driver or OpenAI API key. This means:
- The frontend and backend can be on different machines
- You can replace Streamlit with a mobile app or another frontend later
- The API can be used by curl, Postman, or any other client independently

---

## 8. The UI Layer

[src/app.py](src/app.py) is a 4-page Streamlit app.

### Page 1 — Chat

The main page. A chat interface that calls `POST /ask` and displays:
- The natural language answer
- Which graph nodes were retrieved (with their similarity scores)
- A preview of the raw graph context that was sent to the LLM

**Sidebar sliders:**
- `top_k` (1–6): how many starting nodes to retrieve. Higher = more context, slower, better for complex questions.
- `hops` (1–3): traversal depth. 1 hop = direct connections only. 2 hops = connections of connections. 3 hops = very broad context, can add noise.

### Page 2 — Explore

Two tools:
1. **Entity browser** — type any entity name, get its full graph neighbourhood as text
2. **Similarity search** — type any topic, see which nodes match and their scores

Great for understanding what the graph knows and testing what embedding quality looks like.

### Page 3 — Movies

Browse all 26 movies with genre and box-office filters. Each movie can expand to show its full graph context (cast, director, composer, awards, production house).

### Page 4 — Stats

Node and relationship counts visualised as progress bars. Also includes a live Cypher query runner so you can explore the graph directly from the UI without opening Neo4j Browser.

---

## 9. Docker and Infrastructure

### docker-compose.yml

Three services:

```
neo4j      — Graph database, ports 7474 (browser) and 7687 (Bolt)
api        — FastAPI, port 8000, depends_on neo4j health
streamlit  — Streamlit, port 8501, depends_on api
```

**`depends_on` with `condition: service_healthy`** means Docker will not start the API container until Neo4j passes its health check (`neo4j status`). This prevents the API from crashing on startup because the database isn't ready.

**Volumes** mount `./neo4j_data` from the host into the container. This means your graph data persists even if you stop and recreate the containers.

**`restart: unless-stopped`** means each service will automatically restart if it crashes, which is production-appropriate behaviour.

### The two Dockerfiles

`Dockerfile.api` — builds the FastAPI container: installs requirements, copies src/, runs uvicorn.  
`Dockerfile.streamlit` — builds the Streamlit container: installs requirements, copies src/, runs streamlit.

Both are kept separate so they can be built and scaled independently.

---

## 10. Key Concepts Cheat Sheet

For explaining GraphDB and GraphRAG to anyone:

---

**Graph Database**  
A database where data is stored as nodes (entities) and edges (relationships). Best for questions that involve traversing connections, like "who is connected to who through what?"

**Property Graph**  
A graph where both nodes and edges can carry key-value properties. Neo4j is a property graph database.

**Cypher**  
Neo4j's query language. Reads like a diagram: `(Person)-[:ACTED_IN]->(Movie)` means "find a Person that has an ACTED_IN relationship to a Movie."

**MERGE (upsert)**  
Create a node/relationship if it doesn't exist; match and reuse it if it does. Prevents duplicates and makes scripts safe to re-run.

**Ontology**  
The schema of your knowledge graph — what node types exist, what relationship types connect them, and what properties each carries.

**Embedding**  
Converting text into a fixed-length list of numbers (a vector) where similar meanings produce similar vectors. Enables semantic search.

**Cosine Similarity**  
A measure of how similar two vectors are, based on the angle between them. 1.0 = same direction = same meaning. 0 = perpendicular = unrelated.

**Vector Search**  
Finding the items in a database whose embeddings are most similar to a query embedding. Used in Stage 1 of the pipeline.

**Brute-Force vs ANN Search**  
Brute-force compares every vector to the query — accurate but slow at scale. Approximate Nearest Neighbour (ANN) methods like FAISS build an index for fast approximate search at the cost of a tiny accuracy loss.

**Graph Traversal**  
Walking the graph from a starting node, following edges hop by hop, to collect connected facts. The key capability that makes GraphRAG better than plain RAG for relational questions.

**RAG (Retrieval-Augmented Generation)**  
Giving an LLM context retrieved from an external source before asking it to answer. Reduces hallucination because the model can cite real data rather than invent it.

**GraphRAG**  
RAG where the retrieved context comes from graph traversal rather than vector-matched text chunks. Better for questions that require multi-hop reasoning over structured relationships.

**Triple**  
The fundamental unit of a knowledge graph fact: (Subject) → [Predicate] → (Object). E.g.: Aamir Khan → ACTED_IN → Dangal.

**N-hop neighbourhood**  
All nodes reachable from a starting node by following at most N relationship steps in any direction.

---

*Built as part of the GraphRAG Masterclass at CodeVerra*
