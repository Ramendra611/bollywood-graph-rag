# src/loader.py
# ─────────────────────────────────────────────────────────────────────────────
# Sets up the ontology constraints and loads the complete Bollywood dataset
# into Neo4j. Safe to run multiple times — all writes use MERGE (upsert).
# ─────────────────────────────────────────────────────────────────────────────

from db import Neo4jConnection
from data.bollywood_data import (
    PEOPLE, PRODUCTION_HOUSES, MOVIES, AWARDS,
    ACTED_IN, DIRECTED, COMPOSED_MUSIC_FOR, PRODUCED_BY, WON_AWARDS,
)


# ─────────────────────────────────────────────────────────────────────────────
# STEP 1: Constraints
# ─────────────────────────────────────────────────────────────────────────────

CONSTRAINTS = [
    "CREATE CONSTRAINT bw_person  IF NOT EXISTS FOR (p:Person)          REQUIRE p.name  IS UNIQUE",
    "CREATE CONSTRAINT bw_movie   IF NOT EXISTS FOR (m:Movie)           REQUIRE m.title IS UNIQUE",
    "CREATE CONSTRAINT bw_prod    IF NOT EXISTS FOR (p:ProductionHouse) REQUIRE p.name  IS UNIQUE",
    "CREATE CONSTRAINT bw_award   IF NOT EXISTS FOR (a:Award)           REQUIRE a.name  IS UNIQUE",
]


def setup_constraints(db: Neo4jConnection) -> None:
    print("  Setting up ontology constraints...")
    for c in CONSTRAINTS:
        db.write(c)
    print("  ✓ Constraints active")


# ─────────────────────────────────────────────────────────────────────────────
# STEP 2: Nodes
# ─────────────────────────────────────────────────────────────────────────────

def load_people(db: Neo4jConnection) -> None:
    for p in PEOPLE:
        db.write("""
            MERGE (n:Person {name: $name})
            SET n.born = $born, n.profession = $profession, n.hometown = $hometown
        """, p)
    print(f"  ✓ {len(PEOPLE)} Person nodes")


def load_movies(db: Neo4jConnection) -> None:
    for m in MOVIES:
        db.write("""
            MERGE (n:Movie {title: $title})
            SET n.year = $year, n.genre = $genre, n.language = $language,
                n.box_office_crore = $box_office_crore,
                n.description = $description
        """, m)
    print(f"  ✓ {len(MOVIES)} Movie nodes")


def load_production_houses(db: Neo4jConnection) -> None:
    for ph in PRODUCTION_HOUSES:
        db.write("""
            MERGE (n:ProductionHouse {name: $name})
            SET n.founded = $founded, n.founder = $founder, n.hq = $hq
        """, ph)
    print(f"  ✓ {len(PRODUCTION_HOUSES)} ProductionHouse nodes")


def load_awards(db: Neo4jConnection) -> None:
    for a in AWARDS:
        db.write("""
            MERGE (n:Award {name: $name})
            SET n.category = $category, n.year = $year
        """, a)
    print(f"  ✓ {len(AWARDS)} Award nodes")


# ─────────────────────────────────────────────────────────────────────────────
# STEP 3: Relationships
# ─────────────────────────────────────────────────────────────────────────────

def load_acted_in(db: Neo4jConnection) -> None:
    for actor, movie, character, lead in ACTED_IN:
        db.write("""
            MATCH (p:Person {name: $actor})
            MATCH (m:Movie  {title: $movie})
            MERGE (p)-[r:ACTED_IN]->(m)
            SET r.character = $character, r.lead_role = $lead
        """, {"actor": actor, "movie": movie, "character": character, "lead": lead})
    print(f"  ✓ {len(ACTED_IN)} ACTED_IN relationships")


def load_directed(db: Neo4jConnection) -> None:
    created = 0
    for director, movie in DIRECTED:
        # Auto-create director node if not already in PEOPLE (e.g. Farah Khan)
        db.write("MERGE (p:Person {name: $name})", {"name": director})
        db.write("""
            MATCH (p:Person {name: $director})
            MATCH (m:Movie  {title: $movie})
            MERGE (p)-[:DIRECTED]->(m)
        """, {"director": director, "movie": movie})
        created += 1
    print(f"  ✓ {created} DIRECTED relationships")


def load_composed(db: Neo4jConnection) -> None:
    for composer, movie in COMPOSED_MUSIC_FOR:
        db.write("MERGE (p:Person {name: $name})", {"name": composer})
        db.write("""
            MATCH (p:Person {name: $composer})
            MATCH (m:Movie  {title: $movie})
            MERGE (p)-[:COMPOSED_MUSIC_FOR]->(m)
        """, {"composer": composer, "movie": movie})
    print(f"  ✓ {len(COMPOSED_MUSIC_FOR)} COMPOSED_MUSIC_FOR relationships")


def load_produced_by(db: Neo4jConnection) -> None:
    for house, movie in PRODUCED_BY:
        db.write("""
            MATCH (ph:ProductionHouse {name: $house})
            MATCH (m:Movie            {title: $movie})
            MERGE (ph)-[:PRODUCED]->(m)
        """, {"house": house, "movie": movie})
    print(f"  ✓ {len(PRODUCED_BY)} PRODUCED relationships")


def load_won_awards(db: Neo4jConnection) -> None:
    for entity, entity_type, award in WON_AWARDS:
        if entity_type == "person":
            db.write("""
                MATCH (p:Person {name: $entity})
                MATCH (a:Award  {name: $award})
                MERGE (p)-[:WON]->(a)
            """, {"entity": entity, "award": award})
        else:
            db.write("""
                MATCH (m:Movie {title: $entity})
                MATCH (a:Award {name:  $award})
                MERGE (m)-[:WON]->(a)
            """, {"entity": entity, "award": award})
    print(f"  ✓ {len(WON_AWARDS)} WON relationships")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def load_all(db: Neo4jConnection, clear_first: bool = False) -> None:
    if clear_first:
        print("  Clearing existing data...")
        db.write("MATCH (n) DETACH DELETE n")

    print("\n[1/2] Loading nodes...")
    setup_constraints(db)
    load_people(db)
    load_movies(db)
    load_production_houses(db)
    load_awards(db)

    print("\n[2/2] Loading relationships...")
    load_acted_in(db)
    load_directed(db)
    load_composed(db)
    load_produced_by(db)
    load_won_awards(db)

    # Summary
    summary = db.read("""
        MATCH (n) RETURN labels(n)[0] AS Label, count(n) AS Count
        ORDER BY Count DESC
    """)
    rel_count = db.read("MATCH ()-[r]->() RETURN count(r) AS total")[0]["total"]

    print("\n─── Graph Summary ───────────────────────────────────")
    for row in summary:
        print(f"  {row['Label']:<20} {row['Count']} nodes")
    print(f"  {'Relationships':<20} {rel_count}")
    print("─────────────────────────────────────────────────────")


if __name__ == "__main__":
    with Neo4jConnection() as db:
        load_all(db, clear_first=True)
        print("\n✓ Bollywood Knowledge Graph loaded.")
        print("  Open http://localhost:7474 to explore visually.")
