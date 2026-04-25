# src/app.py
# ─────────────────────────────────────────────────────────────────────────────
# Streamlit frontend for the Bollywood GraphRAG system.
#
# Pages:
#   💬 Chat     — Conversational GraphRAG question answering
#   🔍 Explore  — Browse the graph by entity name
#   🎬 Movies   — Browse all movies with filters
#   📊 Stats    — Database and graph statistics
# ─────────────────────────────────────────────────────────────────────────────

import os
import httpx
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL", "http://localhost:8000")


# ─────────────────────────────────────────────────────────────────────────────
# Page Config
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Bollywood GraphRAG",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for a cleaner look
st.markdown("""
<style>
    .stChatMessage { border-radius: 12px; }
    .entity-chip {
        display: inline-block;
        background: #FF6B35;
        color: white;
        border-radius: 20px;
        padding: 2px 10px;
        margin: 2px;
        font-size: 0.8em;
    }
    .score-bar {
        height: 8px;
        background: linear-gradient(90deg, #FF6B35, #FFD700);
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# API Helper
# ─────────────────────────────────────────────────────────────────────────────

def api_post(endpoint: str, payload: dict) -> dict | None:
    try:
        r = httpx.post(f"{API_URL}{endpoint}", json=payload, timeout=60)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPStatusError as e:
        st.error(f"API error {e.response.status_code}: {e.response.text}")
    except Exception as e:
        st.error(f"Connection error: {e}")
    return None


def api_get(endpoint: str, params: dict = None) -> dict | None:
    try:
        r = httpx.get(f"{API_URL}{endpoint}", params=params or {}, timeout=30)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPStatusError as e:
        st.error(f"API error {e.response.status_code}: {e.response.text}")
    except Exception as e:
        st.error(f"Connection error: {e}")
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/4/44/Film_clapperboard.svg/240px-Film_clapperboard.svg.png", width=60)
    st.title("🎬 Bollywood GraphRAG")
    st.caption("Knowledge Graph × LLM")
    st.divider()

    page = st.radio(
        "Navigate",
        ["💬 Chat", "🔍 Explore", "🎬 Movies", "📊 Stats"],
        label_visibility="collapsed",
    )

    st.divider()
    st.subheader("Chat Settings")
    top_k = st.slider("Starting nodes (top_k)", 1, 6, 3,
                      help="How many graph nodes to use as context anchors")
    hops  = st.slider("Traversal depth (hops)", 1, 3, 2,
                      help="How many relationship hops to follow from each node")

    st.divider()
    # Health check
    health = api_get("/health")
    if health:
        st.success(f"✓ Graph: {health['node_count']} nodes")
    else:
        st.error("✗ API unreachable")


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: Chat
# ─────────────────────────────────────────────────────────────────────────────

if page == "💬 Chat":
    st.header("💬 Ask Anything About Bollywood")
    st.caption("Powered by a Neo4j knowledge graph + GPT-4o | Graph facts, zero hallucination")

    # Initialise session state for conversation history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Suggested starter questions
    with st.expander("✨ Suggested questions", expanded=True):
        suggestions = [
            "Which films did Aamir Khan and AR Rahman work on together?",
            "Which Bollywood directors have won both Filmfare and National Awards?",
            "What are all the films produced by Yash Raj Films starring Shah Rukh Khan?",
            "Which actors have worked under both Rajkumar Hirani and Sanjay Leela Bhansali?",
            "Which films in the graph have crossed 500 crore at the box office?",
            "Tell me about the career of Deepika Padukone based on graph data.",
        ]
        cols = st.columns(2)
        for i, s in enumerate(suggestions):
            if cols[i % 2].button(s, use_container_width=True, key=f"sug_{i}"):
                st.session_state.pending_question = s

    st.divider()

    # Render conversation history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant" and "nodes" in msg:
                with st.expander("📍 Graph nodes used as context", expanded=False):
                    for node in msg["nodes"]:
                        score_pct = int(node["score"] * 100)
                        st.markdown(
                            f'<span class="entity-chip">{node["label"]}</span> '
                            f'**{node["name"]}** — {score_pct}% match',
                            unsafe_allow_html=True,
                        )

    # Handle suggestion button clicks
    pending = st.session_state.pop("pending_question", None)

    # Chat input
    user_input = st.chat_input("Ask about Bollywood films, actors, directors...")
    question = pending or user_input

    if question:
        # Show user message
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        # Get answer from API
        with st.chat_message("assistant"):
            with st.spinner("Searching the knowledge graph..."):
                result = api_post("/ask", {
                    "question": question,
                    "top_k": top_k,
                    "hops":  hops,
                })

            if result:
                st.markdown(result["answer"])

                with st.expander("📍 Graph nodes used as context", expanded=False):
                    for node in result["retrieved_nodes"]:
                        score_pct = int(node["score"] * 100)
                        st.markdown(
                            f'<span class="entity-chip">{node["label"]}</span> '
                            f'**{node["name"]}** — {score_pct}% match',
                            unsafe_allow_html=True,
                        )

                with st.expander("🕸️ Raw graph context", expanded=False):
                    st.code(result["context_preview"] + "\n...", language="text")

                st.session_state.messages.append({
                    "role":    "assistant",
                    "content": result["answer"],
                    "nodes":   result["retrieved_nodes"],
                })
            else:
                st.error("Could not get a response. Please check the API connection.")

    if st.session_state.messages:
        if st.button("🗑️ Clear conversation", type="secondary"):
            st.session_state.messages = []
            st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: Explore
# ─────────────────────────────────────────────────────────────────────────────

elif page == "🔍 Explore":
    st.header("🔍 Explore the Knowledge Graph")

    col1, col2 = st.columns([2, 1])
    with col1:
        entity_name = st.text_input("Entity name", placeholder="e.g. Shah Rukh Khan, Dangal, AR Rahman")
    with col2:
        entity_label = st.selectbox("Type", ["Person", "Movie", "ProductionHouse", "Award"])

    explore_hops = st.slider("Traversal depth", 1, 3, 2)

    if st.button("🔍 Explore", type="primary") and entity_name:
        with st.spinner("Traversing graph..."):
            result = api_get(
                f"/graph/{entity_name}",
                {"label": entity_label, "hops": explore_hops}
            )

        if result:
            st.subheader(f"Neighbourhood of: {entity_name}")
            st.code(result["context"], language="text")

    st.divider()
    st.subheader("🔎 Similarity Search")
    search_q = st.text_input("Search by topic or keyword", placeholder="e.g. cricket, revenge story, music")
    search_label = st.selectbox("Restrict to type", ["(all)", "Movie", "Person", "ProductionHouse", "Award"])

    if st.button("Search") and search_q:
        params = {"q": search_q, "top_k": 8}
        if search_label != "(all)":
            params["label"] = search_label

        results = api_get("/search", params)
        if results:
            st.subheader(f"Top matches for: '{search_q}'")
            for r in results["results"]:
                score_pct = int(r["score"] * 100)
                col_a, col_b, col_c = st.columns([3, 1, 2])
                col_a.write(f"**{r['name']}**")
                col_b.write(f"`{r['label']}`")
                col_c.progress(r["score"], text=f"{score_pct}%")


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: Movies
# ─────────────────────────────────────────────────────────────────────────────

elif page == "🎬 Movies":
    st.header("🎬 Bollywood Films in the Graph")

    data = api_get("/movies", {"limit": 50})
    if data:
        movies = data["movies"]

        # Filters
        col1, col2 = st.columns(2)
        genres    = sorted(set(m["genre"] for m in movies if m["genre"]))
        selected_genres = col1.multiselect("Filter by genre", genres)
        min_crore = col2.number_input("Minimum box office (₹ crore)", value=0, step=50)

        filtered = [
            m for m in movies
            if (not selected_genres or m["genre"] in selected_genres)
            and (m["crore"] or 0) >= min_crore
        ]

        st.caption(f"Showing {len(filtered)} films")

        for m in filtered:
            crore = m["crore"] or 0
            with st.expander(f"🎬 **{m['title']}** ({m['year']}) — ₹{crore:.0f} Cr"):
                col_a, col_b = st.columns(2)
                col_a.write(f"**Genre:** {m['genre']}")
                col_b.write(f"**Box Office:** ₹{crore:.0f} crore")

                if st.button("Show graph context", key=f"btn_{m['title']}"):
                    result = api_get(f"/graph/{m['title']}", {"label": "Movie", "hops": 2})
                    if result:
                        st.code(result["context"], language="text")


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: Stats
# ─────────────────────────────────────────────────────────────────────────────

elif page == "📊 Stats":
    st.header("📊 Knowledge Graph Statistics")

    data = api_get("/stats")
    if data:
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Node Counts")
            total_nodes = sum(r["count"] for r in data["nodes"])
            st.metric("Total Nodes", total_nodes)
            for row in data["nodes"]:
                st.progress(row["count"] / max(total_nodes, 1),
                            text=f"{row['label']}: {row['count']}")

        with col2:
            st.subheader("Relationship Counts")
            total_rels = sum(r["count"] for r in data["relationships"])
            st.metric("Total Relationships", total_rels)
            for row in data["relationships"]:
                st.progress(row["count"] / max(total_rels, 1),
                            text=f"{row['rel_type']}: {row['count']}")

    st.divider()
    st.subheader("🔬 Try a Raw Cypher Query")
    st.caption("Read-only queries only (MATCH / RETURN)")

    default_q = "MATCH (p:Person)-[:DIRECTED]->(m:Movie) RETURN p.name AS Director, m.title AS Movie ORDER BY p.name LIMIT 15"
    cypher_input = st.text_area("Cypher query", value=default_q, height=80)

    if st.button("▶ Run Query", type="primary"):
        result = api_post("/cypher", {"query": cypher_input})
        if result:
            st.caption(f"{result['count']} rows returned")
            st.dataframe(result["results"], use_container_width=True)
