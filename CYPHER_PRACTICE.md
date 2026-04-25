# Cypher Query Practice — Bollywood Knowledge Graph

A hands-on guide to exploring the Bollywood graph with Neo4j's Cypher query language.
Open **http://localhost:7474** in your browser (user: `neo4j`, password: `bollywood2024!`),
paste any query into the editor, and hit **Ctrl+Enter** to run it.

Each section introduces a new Cypher concept. Work through them in order.

---

## Part 1 — The Basics: Finding Nodes

### 1.1 See everything in the graph (careful on large graphs!)

```cypher
MATCH (n)
RETURN n
LIMIT 25
```

**What's happening:**
- `MATCH (n)` — find any node and call it `n`. No label filter means all node types.
- `RETURN n` — return the full node object. Neo4j Browser renders it as a graph.
- `LIMIT 25` — safety cap. Never run `MATCH (n) RETURN n` without a limit on a large graph.

---

### 1.2 Find all movies

```cypher
MATCH (m:Movie)
RETURN m.title, m.year, m.genre, m.box_office_crore
ORDER BY m.year
```

**What's happening:**
- `(m:Movie)` — the `:Movie` label narrows the search to Movie nodes only.
- `m.title`, `m.year` etc. — dot notation to access specific properties.
- `ORDER BY m.year` — sort results ascending by release year.

---

### 1.3 Find all people and their professions

```cypher
MATCH (p:Person)
RETURN p.name, p.profession, p.hometown
ORDER BY p.profession, p.name
```

**What's happening:**
- Multiple `ORDER BY` fields work like SQL — sort by profession first, then name alphabetically within each profession.

---

### 1.4 Find a specific person by name

```cypher
MATCH (p:Person {name: "Shah Rukh Khan"})
RETURN p
```

**What's happening:**
- `{name: "Shah Rukh Khan"}` inside the node pattern is an inline property filter. Equivalent to adding `WHERE p.name = "Shah Rukh Khan"`.

> **Try changing the name** to `Aamir Khan`, `AR Rahman`, or `Zoya Akhtar` and re-run.

---

### 1.5 Count nodes by type

```cypher
MATCH (n)
RETURN labels(n)[0] AS NodeType, count(n) AS Total
ORDER BY Total DESC
```

**What's happening:**
- `labels(n)` returns a list of all labels on the node (a node can have multiple).
- `[0]` gets the first label from that list.
- `count(n)` aggregates — Neo4j groups by `NodeType` automatically.

---

## Part 2 — Filtering with WHERE

### 2.1 Movies with box office above 500 crore

```cypher
MATCH (m:Movie)
WHERE m.box_office_crore > 500
RETURN m.title, m.year, m.box_office_crore
ORDER BY m.box_office_crore DESC
```

**What's happening:**
- `WHERE` clauses let you filter on any property, including numeric comparisons.
- `DESC` reverses the sort order — highest box office at the top.

---

### 2.2 Actors born in the 1960s

```cypher
MATCH (p:Person)
WHERE p.born >= 1960 AND p.born < 1970
RETURN p.name, p.born, p.profession
ORDER BY p.born
```

**What's happening:**
- `AND` combines multiple conditions. You can also use `OR` and `NOT`.

---

### 2.3 Search for a partial name (case-insensitive)

```cypher
MATCH (p:Person)
WHERE toLower(p.name) CONTAINS "khan"
RETURN p.name, p.profession
```

**What's happening:**
- `toLower()` converts the property to lowercase before comparison.
- `CONTAINS` is a substring match — you don't need the exact name.
- Also useful: `STARTS WITH`, `ENDS WITH`.

---

### 2.4 Movies of a specific genre

```cypher
MATCH (m:Movie)
WHERE m.genre IN ["Comedy Drama", "Sports Biopic", "Historical Drama"]
RETURN m.title, m.genre, m.year
ORDER BY m.genre
```

**What's happening:**
- `IN [...]` is the Cypher equivalent of SQL's `WHERE genre IN (...)`. Checks if the value is in a list.

---

## Part 3 — Relationships: The Core of Graph Queries

This is where graph databases shine. In SQL you'd need JOINs; in Cypher the relationship is part of the pattern.

### 3.1 All films Aamir Khan acted in

```cypher
MATCH (p:Person {name: "Aamir Khan"})-[:ACTED_IN]->(m:Movie)
RETURN m.title, m.year, m.box_office_crore
ORDER BY m.year
```

**What's happening:**
- `(p)-[:ACTED_IN]->(m)` — find a path where `p` has an `ACTED_IN` relationship pointing to `m`.
- The arrow direction `->` matters. `ACTED_IN` goes from Person to Movie.
- `:ACTED_IN` is the relationship type filter.

**Pattern anatomy:**
```
(p:Person {name: "Aamir Khan"}) - [:ACTED_IN] -> (m:Movie)
  ↑ start node                    ↑ relationship    ↑ end node
```

---

### 3.2 Include relationship properties

```cypher
MATCH (p:Person {name: "Shah Rukh Khan"})-[r:ACTED_IN]->(m:Movie)
RETURN m.title, r.character AS character_played, r.lead_role AS is_lead
ORDER BY m.year
```

**What's happening:**
- `[r:ACTED_IN]` — give the relationship a variable name `r`.
- `r.character`, `r.lead_role` — access properties stored on the relationship itself (not just the nodes).

---

### 3.3 Who directed what

```cypher
MATCH (d:Person)-[:DIRECTED]->(m:Movie)
RETURN d.name AS Director, collect(m.title) AS Films_Directed
ORDER BY size(Films_Directed) DESC
```

**What's happening:**
- `collect(m.title)` — aggregation function that gathers all movie titles into a list per director.
- `size(...)` — returns the length of a list. Used here to sort directors by number of films.

---

### 3.4 Both actors AND director of a film

```cypher
MATCH (director:Person)-[:DIRECTED]->(m:Movie {title: "3 Idiots"})<-[:ACTED_IN]-(actor:Person)
RETURN director.name AS Director, collect(actor.name) AS Cast
```

**What's happening:**
- The pattern follows two relationship paths to the same movie node `m`.
- `<-[:ACTED_IN]-` — the arrow points **into** `actor`, meaning ACTED_IN goes FROM actor TO movie.
- The result is the director and a list of all actors in that one query.

> **Try changing the title** to `"Dangal"`, `"Gully Boy"`, or `"Bajirao Mastani"`.

---

### 3.5 Find the music composer for a film

```cypher
MATCH (c:Person)-[:COMPOSED_MUSIC_FOR]->(m:Movie)
RETURN m.title, c.name AS Composer
ORDER BY m.year
```

---

### 3.6 Which production house made which films

```cypher
MATCH (ph:ProductionHouse)-[:PRODUCED]->(m:Movie)
RETURN ph.name AS Studio, m.title AS Film, m.year AS Year
ORDER BY ph.name, m.year
```

---

## Part 4 — Multi-Hop Traversal: Connecting the Dots

This is the real advantage of a graph database. No JOINs — just follow the path.

### 4.1 Movies produced by Yash Raj Films starring Shah Rukh Khan

```cypher
MATCH (ph:ProductionHouse {name: "Yash Raj Films"})-[:PRODUCED]->(m:Movie)<-[:ACTED_IN]-(p:Person {name: "Shah Rukh Khan"})
RETURN m.title, m.year, m.box_office_crore
ORDER BY m.year
```

**What's happening:**
- This pattern has THREE nodes connected by TWO relationships.
- Read it aloud: "Find a ProductionHouse named Yash Raj Films that PRODUCED a Movie that Shah Rukh Khan ACTED_IN."
- Neo4j traverses both relationships in one query — no JOIN needed.

---

### 4.2 Which composers have worked with Aamir Khan productions?

```cypher
MATCH (ph:ProductionHouse {name: "Aamir Khan Productions"})-[:PRODUCED]->(m:Movie)<-[:COMPOSED_MUSIC_FOR]-(c:Person)
RETURN DISTINCT c.name AS Composer, collect(m.title) AS Films
```

**What's happening:**
- `DISTINCT` on the RETURN removes duplicates if a composer worked on multiple films from the same house.
- The path goes: ProductionHouse → Movie ← Person (composer). The arrow directions match how data was loaded.

---

### 4.3 Awards won by films that AR Rahman scored

```cypher
MATCH (ar:Person {name: "AR Rahman"})-[:COMPOSED_MUSIC_FOR]->(m:Movie)-[:WON]->(a:Award)
RETURN m.title AS Film, a.name AS Award, a.category AS Category
ORDER BY a.year
```

**What's happening:**
- Three hops: Person → Movie → Award.
- This is a chain of relationships — a path through three node types in one query.

---

### 4.4 Actors who were directed by Rajkumar Hirani AND also worked with AR Rahman

```cypher
MATCH (rk:Person {name: "Rajkumar Hirani"})-[:DIRECTED]->(m1:Movie)<-[:ACTED_IN]-(actor:Person)
MATCH (ar:Person {name: "AR Rahman"})-[:COMPOSED_MUSIC_FOR]->(m2:Movie)<-[:ACTED_IN]-(actor)
RETURN DISTINCT actor.name AS Actor, collect(DISTINCT m1.title) AS Hirani_Films, collect(DISTINCT m2.title) AS AR_Films
```

**What's happening:**
- Two separate `MATCH` clauses — both must be satisfied. The `actor` variable is shared between them, so Neo4j only returns actors who appear in BOTH patterns.
- This is a graph intersection — very natural in Cypher, painful in SQL.

---

## Part 5 — Aggregation and Statistics

### 5.1 Total box office per production house

```cypher
MATCH (ph:ProductionHouse)-[:PRODUCED]->(m:Movie)
RETURN ph.name AS Studio,
       count(m) AS Films_Count,
       sum(m.box_office_crore) AS Total_Box_Office_Crore,
       round(avg(m.box_office_crore)) AS Avg_Per_Film
ORDER BY Total_Box_Office_Crore DESC
```

**What's happening:**
- `count()`, `sum()`, `avg()` work exactly like SQL aggregate functions.
- `round()` removes decimal places.
- Results are automatically grouped by `ph.name` since it's the non-aggregated field.

---

### 5.2 How many awards has each person won?

```cypher
MATCH (p:Person)-[:WON]->(a:Award)
RETURN p.name AS Person, count(a) AS Awards_Won
ORDER BY Awards_Won DESC
```

---

### 5.3 Most prolific actors by film count

```cypher
MATCH (p:Person)-[:ACTED_IN]->(m:Movie)
RETURN p.name AS Actor, count(m) AS Films
ORDER BY Films DESC
LIMIT 10
```

---

### 5.4 Average box office by genre

```cypher
MATCH (m:Movie)
WHERE m.box_office_crore > 0
RETURN m.genre AS Genre,
       count(m) AS Film_Count,
       round(avg(m.box_office_crore)) AS Avg_Box_Office
ORDER BY Avg_Box_Office DESC
```

---

## Part 6 — Graph-Specific Features

These have no direct equivalent in SQL. They are unique to graph databases.

### 6.1 Shortest path between two people

```cypher
MATCH path = shortestPath(
    (a:Person {name: "Shah Rukh Khan"})-[*]-(b:Person {name: "AR Rahman"})
)
RETURN [n IN nodes(path) | coalesce(n.name, n.title)] AS Path,
       length(path) AS Hops
```

**What's happening:**
- `shortestPath(...)` is a built-in graph algorithm that finds the fewest-hop path between two nodes.
- `[*]` means "any number of hops, any relationship type, either direction."
- `[n IN nodes(path) | coalesce(n.name, n.title)]` — list comprehension that extracts the name or title from each node along the path.
- `coalesce(a, b)` returns `a` if it's not null, otherwise `b` — handles the fact that Movies have `title` while Persons have `name`.

> **Try different pairs:** `"Deepika Padukone"` to `"Rajkumar Hirani"`, or `"Salman Khan"` to `"Zoya Akhtar"`.

---

### 6.2 All paths up to 3 hops from a node (variable-length traversal)

```cypher
MATCH (start:Person {name: "Aamir Khan"})-[*1..2]->(neighbor)
RETURN DISTINCT labels(neighbor)[0] AS Type,
       coalesce(neighbor.name, neighbor.title) AS Entity
ORDER BY Type
```

**What's happening:**
- `[*1..2]` — walk between 1 and 2 hops. The range is `[*min..max]`.
- This is variable-length path matching — impossible to express cleanly in SQL without recursive CTEs.
- Returns every distinct node reachable from Aamir Khan within 2 hops.

---

### 6.3 Directors who also acted in their own films

```cypher
MATCH (p:Person)-[:DIRECTED]->(m:Movie)<-[:ACTED_IN]-(p)
RETURN p.name AS Person, collect(m.title) AS Self_Directed_Films
```

**What's happening:**
- The same variable `p` appears at both ends of the pattern.
- This means "find a person who has BOTH a DIRECTED and an ACTED_IN relationship to the same movie."
- Cypher handles this naturally — in SQL you'd need a self-join subquery.

---

### 6.4 Nodes with more than 3 connections (high-degree nodes)

```cypher
MATCH (n)
WHERE (n)--() 
WITH n, size([(n)--() | 1]) AS degree
WHERE degree > 3
RETURN labels(n)[0] AS Type,
       coalesce(n.name, n.title) AS Entity,
       degree
ORDER BY degree DESC
```

**What's happening:**
- `(n)--()` matches any relationship in either direction.
- `size([...| 1])` counts the number of matching patterns (a pattern comprehension trick for degree).
- This finds the most "connected" nodes — useful for finding hubs in the graph.

---

### 6.5 Find all awards won by movies, not people

```cypher
MATCH (m:Movie)-[:WON]->(a:Award)
RETURN m.title AS Film, a.name AS Award, a.category AS Category, a.year AS Year
ORDER BY a.year
```

**What's happening:**
- Both `Movie` and `Person` nodes can have a `WON` relationship to `Award`.
- By specifying `(m:Movie)` we filter to only movie-level awards, excluding personal awards.

---

## Part 7 — Writing and Modifying Data (Advanced)

Run these in Neo4j Browser but think of them as learning exercises — the loader handles real data loading.

### 7.1 Add a new movie (CREATE)

```cypher
CREATE (m:Movie {
    title: "Dil Dhadakne Do",
    year: 2015,
    genre: "Drama",
    box_office_crore: 108.0,
    description: "A wealthy Indian family goes on a cruise, and family secrets unravel."
})
RETURN m
```

**What's happening:**
- `CREATE` always creates a new node — even if one with the same properties exists. Use `MERGE` to avoid duplicates.

---

### 7.2 MERGE vs CREATE — add a node safely

```cypher
MERGE (p:Person {name: "Priyanka Chopra Jonas"})
ON CREATE SET p.born = 1982, p.profession = "Actor", p.hometown = "Jamshedpur"
ON MATCH  SET p.profession = "Actor-Producer"
RETURN p
```

**What's happening:**
- `MERGE` checks if the node exists first.
- `ON CREATE SET` — runs only if a new node was created.
- `ON MATCH SET` — runs only if an existing node was matched.
- This is the safe, idempotent way to write data.

---

### 7.3 Add a relationship between two existing nodes

```cypher
MATCH (p:Person {name: "Zoya Akhtar"})
MATCH (m:Movie  {title: "Dil Chahta Hai"})
MERGE (p)-[:DIRECTED]->(m)
RETURN p, m
```

**What's happening:**
- Always `MATCH` the nodes first before creating the relationship — never assume they exist.
- `MERGE` on the relationship prevents duplicate edges.

---

### 7.4 Update a property on an existing node

```cypher
MATCH (m:Movie {title: "Dangal"})
SET m.streaming_platform = "Disney+ Hotstar"
RETURN m.title, m.streaming_platform
```

**What's happening:**
- `SET` adds or updates a property. If `streaming_platform` didn't exist before, it's created.
- `SET m += {key: value, key2: value2}` is the batch version for updating multiple properties.

---

### 7.5 Delete a node and all its relationships

```cypher
MATCH (m:Movie {title: "Dil Dhadakne Do"})
DETACH DELETE m
```

**What's happening:**
- `DELETE` alone fails if the node has relationships.
- `DETACH DELETE` removes all relationships connected to the node first, then deletes the node.
- **Be careful** — this is permanent. There is no ROLLBACK by default.

---

## Part 8 — Challenge Queries

Try these without looking at the answers first. Each uses concepts from the sections above.

**Challenge 1:** Find all films where the director is also listed as an actor (hint: same person node, two different relationship types to the same movie).

**Challenge 2:** List every person and the total box office of all films they acted in, ordered by highest total.

**Challenge 3:** Find the music composer who has worked with the most different production houses (trace the path: Composer → COMPOSED_MUSIC_FOR → Movie ← PRODUCED — ProductionHouse).

**Challenge 4:** Find all National Award winning films and return the film title, year, and all actors who appeared in it.

**Challenge 5:** Which two people in the graph are connected by the shortest path? (Hint: you'll need to try different pairs or think about who might be very well-connected.)

---

<details>
<summary>Challenge Answers (expand after trying)</summary>

**Challenge 1:**
```cypher
MATCH (p:Person)-[:DIRECTED]->(m:Movie)<-[:ACTED_IN]-(p)
RETURN p.name, collect(m.title) AS Films
```

**Challenge 2:**
```cypher
MATCH (p:Person)-[:ACTED_IN]->(m:Movie)
WHERE m.box_office_crore > 0
RETURN p.name AS Actor, sum(m.box_office_crore) AS Total_Box_Office
ORDER BY Total_Box_Office DESC
```

**Challenge 3:**
```cypher
MATCH (c:Person)-[:COMPOSED_MUSIC_FOR]->(m:Movie)<-[:PRODUCED]-(ph:ProductionHouse)
RETURN c.name AS Composer, count(DISTINCT ph) AS Production_Houses
ORDER BY Production_Houses DESC
LIMIT 5
```

**Challenge 4:**
```cypher
MATCH (m:Movie)-[:WON]->(a:Award {category: "National"})
MATCH (m)<-[:ACTED_IN]-(actor:Person)
RETURN m.title AS Film, m.year AS Year, collect(actor.name) AS Cast
ORDER BY m.year
```

**Challenge 5:**
```cypher
MATCH (a:Person), (b:Person)
WHERE a.name < b.name
MATCH path = shortestPath((a)-[*]-(b))
RETURN a.name, b.name, length(path) AS Hops
ORDER BY Hops ASC
LIMIT 5
```

</details>

---

## Quick Reference — Cypher Syntax Cheat Sheet

```cypher
-- Find nodes
MATCH (n:Label {property: "value"}) RETURN n

-- Find relationships
MATCH (a)-[:REL_TYPE]->(b) RETURN a, b

-- Filter
WHERE n.property > 100 AND n.other CONTAINS "text"

-- Aggregate
count(n)   sum(n.prop)   avg(n.prop)   collect(n.prop)

-- Sort and limit
ORDER BY n.prop DESC   LIMIT 10

-- Variable-length path
(a)-[*1..3]->(b)          -- 1 to 3 hops
shortestPath((a)-[*]-(b)) -- fewest hops, any direction

-- Write
CREATE (n:Label {prop: value})
MERGE  (n:Label {prop: value})
SET    n.prop = value
DETACH DELETE n

-- Useful functions
labels(n)            -- list of labels on a node
type(r)              -- type name of a relationship
coalesce(a, b)       -- first non-null value
toLower(str)         -- lowercase
size(list)           -- length of a list
collect(x)           -- aggregate values into a list
DISTINCT             -- deduplicate
```

---

*Run all queries at http://localhost:7474 — Neo4j Browser renders results as a visual graph when you RETURN full nodes, or as a table when you RETURN specific properties.*
