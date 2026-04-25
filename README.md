# 🎬 Bollywood GraphRAG

A complete GraphRAG (Graph Retrieval-Augmented Generation) system built on a **Bollywood knowledge graph**. Ask questions about Hindi cinema in plain English — the system finds the answer by traversing a Neo4j graph of movies, actors, directors, composers, and awards, then generating a natural language response via GPT-4o.

---

## What This Project Demonstrates

| Concept | How it appears in this project |
|---|---|
| Graph database fundamentals | Neo4j with a Bollywood ontology |
| Cypher query language | Loader, traversal, and stat queries |
| Vector embeddings on graph nodes | Each node carries an OpenAI embedding |
| GraphRAG pipeline | Vector search → graph traversal → LLM answer |
| FastAPI backend | REST endpoints for all pipeline operations |
| Streamlit frontend | 4-page chat + explorer interface |
| Docker Compose | One command to start everything |

---

## Knowledge Graph Ontology

```
NODES
──────────────────────────────────────────────────────────
Person          {name, born, profession, hometown}
Movie           {title, year, genre, box_office_crore, description}
ProductionHouse {name, founded, founder, hq}
Award           {name, category, year}

RELATIONSHIPS
──────────────────────────────────────────────────────────
(Person) -[:ACTED_IN        {character, lead_role}]-> (Movie)
(Person) -[:DIRECTED]->                               (Movie)
(Person) -[:COMPOSED_MUSIC_FOR]->                     (Movie)
(Person) -[:WON]->                                    (Award)
(Movie)  -[:WON]->                                    (Award)
(ProductionHouse) -[:PRODUCED]->                      (Movie)
```

---

## Setup

### Prerequisites

| Tool | Version | Notes |
|---|---|---|
| Docker Desktop | Latest | Must be running |
| Python | 3.11+ | For running scripts locally |
| OpenAI API key | — | Required for embeddings + GPT-4o |

### 1. Clone and configure

```bash
git clone <repo-url>
cd bollywood-graphrag

# Copy the env template
cp .env.example .env

# Edit .env and add your OpenAI key
```

Your `.env` file:
```
OPENAI_API_KEY=sk-...
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=bollywood2024!
```

### 2. Start Neo4j

```bash
docker compose up neo4j -d

# Wait ~15 seconds, then verify:
docker compose logs neo4j | grep "Started"
```

Open the Neo4j Browser at http://localhost:7474 (user: `neo4j`, password: `bollywood2024!`)

### 3. Install Python dependencies

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Load the knowledge graph

```bash
cd src
python loader.py
```

Expected output:
```
[1/2] Loading nodes...
  ✓ Constraints active
  ✓ 35 Person nodes
  ✓ 26 Movie nodes
  ✓ 10 ProductionHouse nodes
  ✓ 25 Award nodes

[2/2] Loading relationships...
  ✓ 41 ACTED_IN relationships
  ✓ 27 DIRECTED relationships
  ...
```

### 5. Add vector embeddings

```bash
python embeddings.py
```

This calls the OpenAI embeddings API for each node and stores the vectors in Neo4j. Run once; re-running is safe (overwrites existing embeddings).

### 6. Run the Streamlit app

```bash
streamlit run app.py
```

Open http://localhost:8501

### 7. (Optional) Run the FastAPI backend separately

```bash
uvicorn api:app --reload --port 8000
# API docs at http://localhost:8000/docs
```

### 8. (Optional) Start everything with Docker Compose

```bash
docker compose up --build
```

| Service | URL |
|---|---|
| Neo4j Browser | http://localhost:7474 |
| FastAPI docs | http://localhost:8000/docs |
| Streamlit chat | http://localhost:8501 |

---

## Usage

### Streamlit Chat Interface

The **💬 Chat** page lets you ask natural language questions. Try:

- *"Which films has Shah Rukh Khan done with Yash Raj Films?"*
- *"Which music composers have worked with Aamir Khan productions?"*
- *"Name all the National Award winning films in the graph."*
- *"Which actors directed by Rajkumar Hirani also worked with AR Rahman?"*

The **🔍 Explore** page lets you look up any entity by name and see its full graph neighbourhood.

### FastAPI Endpoints

```bash
# Ask a question
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Which films did Aamir Khan direct?", "top_k": 3, "hops": 2}'

# Vector search
curl "http://localhost:8000/search?q=revenge+thriller&label=Movie"

# Get an entity's neighbourhood
curl "http://localhost:8000/graph/Dangal?label=Movie&hops=2"

# Filmography of a person
curl "http://localhost:8000/person/AR%20Rahman/filmography"

# Graph statistics
curl "http://localhost:8000/stats"
```

---

## Project Structure

```
bollywood-graphrag/
├── docker-compose.yml          ← All services: Neo4j + API + Streamlit
├── requirements.txt
├── .env.example
├── Dockerfile.api              ← FastAPI container
├── Dockerfile.streamlit        ← Streamlit container
└── src/
    ├── db.py                   ← Neo4j connection wrapper
    ├── loader.py               ← Load ontology + data into Neo4j
    ├── embeddings.py           ← Compute + store node embeddings
    ├── graphrag.py             ← The full GraphRAG pipeline
    ├── api.py                  ← FastAPI backend
    ├── app.py                  ← Streamlit frontend
    └── data/
        └── bollywood_data.py   ← All graph data (nodes + relationships)
```

---

## How the GraphRAG Pipeline Works

```
User question (text)
       │
       ▼
┌──────────────────────────────┐
│  1. Vector Search            │  Embed question → find top-k similar nodes
│     (embeddings.py)          │  e.g. "Who directed PK?" → [Rajkumar Hirani, PK]
└──────────────────┬───────────┘
                   │  top-k node identifiers
                   ▼
┌──────────────────────────────┐
│  2. Graph Traversal          │  Walk N hops from each identified node
│     (graphrag.py)            │  Collect all connected facts as triples
└──────────────────┬───────────┘
                   │  subgraph as structured text
                   ▼
┌──────────────────────────────┐
│  3. LLM Answer Generation    │  GPT-4o reasons over graph context
│     (OpenAI GPT-4o)          │  Returns grounded, verifiable answer
└──────────────────────────────┘
```

---

## Extending the Project

### Adding more movies
Add entries to `MOVIES`, `ACTED_IN`, `DIRECTED` etc. in `src/data/bollywood_data.py`, then re-run `loader.py` and `embeddings.py`.

### Adding a new relationship type
1. Add rows to the relevant list in `bollywood_data.py`
2. Add a loading function in `loader.py`
3. Call it from `load_all()`

### Switching to a different LLM
Replace the `openai` calls in `graphrag.py` with any OpenAI-compatible API (Anthropic, Gemini, Groq etc.).

---

## Interesting Graph Queries to Try in Neo4j Browser

```cypher
-- All Aamir Khan films with box office > 200 crore
MATCH (p:Person {name: 'Aamir Khan'})-[:ACTED_IN]->(m:Movie)
WHERE m.box_office_crore > 200
RETURN m.title, m.year, m.box_office_crore ORDER BY m.box_office_crore DESC

-- Directors who also acted in their own films
MATCH (p:Person)-[:DIRECTED]->(m:Movie)<-[:ACTED_IN]-(p)
RETURN p.name, m.title

-- Movies where AR Rahman composed and the film won a National Award
MATCH (ar:Person {name:'AR Rahman'})-[:COMPOSED_MUSIC_FOR]->(m:Movie)-[:WON]->(a:Award)
WHERE a.category = 'National'
RETURN m.title, a.name

-- Shortest path between Shah Rukh Khan and AR Rahman
MATCH path = shortestPath(
    (a:Person {name: 'Shah Rukh Khan'})-[*]-(b:Person {name: 'AR Rahman'})
)
RETURN [n IN nodes(path) | coalesce(n.name, n.title)] AS path, length(path) AS hops

-- All films produced by Yash Raj that crossed 500 crore
MATCH (ph:ProductionHouse {name: 'Yash Raj Films'})-[:PRODUCED]->(m:Movie)
WHERE m.box_office_crore > 500
RETURN m.title, m.year, m.box_office_crore ORDER BY m.box_office_crore DESC
```

---

*Built as part of the GraphRAG Masterclass at [codeverra](https://www.codeverra.com)*
