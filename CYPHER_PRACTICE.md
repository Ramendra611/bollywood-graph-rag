# Cypher Query Practice — Bollywood Knowledge Graph

A fully self-contained lab. By the end of this document you will have a live
Neo4j graph database running locally, loaded with Bollywood data, and you will
have written queries that cover every major Cypher concept.

---

Built as part of **Codeverra** — helping you learn coding, DSA, data science, and AI the right way.  
https://codeverra.com

---

## Table of Contents

1. [What is Neo4j and Cypher?](#1-what-is-neo4j-and-cypher)
2. [Start Neo4j with Docker](#2-start-neo4j-with-docker)
3. [Open the Neo4j Browser](#3-open-the-neo4j-browser)
4. [The Data Model — what we are building](#4-the-data-model)
5. [Load the data — run these in Neo4j Browser](#5-load-the-data)
6. [Part 1 — Finding nodes](#part-1--finding-nodes)
7. [Part 2 — Filtering with WHERE](#part-2--filtering-with-where)
8. [Part 3 — Relationships](#part-3--relationships)
9. [Part 4 — Multi-hop traversal](#part-4--multi-hop-traversal)
10. [Part 5 — Aggregation](#part-5--aggregation)
11. [Part 6 — Graph-specific features](#part-6--graph-specific-features)
12. [Part 7 — Writing and modifying data](#part-7--writing-and-modifying-data)
13. [Part 8 — Challenge queries](#part-8--challenge-queries)
14. [Cypher cheat sheet](#cypher-cheat-sheet)

---

## 1. What is Neo4j and Cypher?

### Neo4j

Neo4j is a **graph database**. Instead of storing data in rows and tables (like SQL), it stores data as:

- **Nodes** — entities, like a Person or a Movie
- **Relationships** — named, directed connections between nodes, like ACTED_IN or DIRECTED
- **Properties** — key-value pairs attached to both nodes and relationships

This model is built for questions that involve connections:
*"Who worked with who?", "What are all the films connected to this director through two hops?"*
In SQL these require multiple JOINs. In Neo4j you draw the pattern and the database finds it.

```
(Shah Rukh Khan) -[:ACTED_IN]-> (Dangal) -[:WON]-> (National Award)
     Person               Movie                  Award
```

### Cypher

Cypher is Neo4j's query language. It is designed to look like ASCII art of the graph pattern you are searching for.

```cypher
MATCH (p:Person)-[:ACTED_IN]->(m:Movie)
RETURN p.name, m.title
```

Read it aloud: *"Find a Person that has an ACTED_IN relationship to a Movie, return their name and the movie title."*

---

## 2. Start Neo4j with Docker

You need Docker Desktop installed and running. Open a terminal and run:

```bash
docker run -d \
  --name bollywood_neo4j \
  -p 7474:7474 \
  -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/bollywood2024! \
  neo4j:5.18.0
```

**What each flag does:**

| Flag | Purpose |
|---|---|
| `-d` | Run in the background (detached mode) |
| `--name bollywood_neo4j` | Give the container a memorable name |
| `-p 7474:7474` | Map port 7474 on your machine to port 7474 in the container — this is the browser UI |
| `-p 7687:7687` | Map port 7687 — this is the Bolt protocol used by drivers and the browser to run queries |
| `-e NEO4J_AUTH=neo4j/bollywood2024!` | Set the username (`neo4j`) and password (`bollywood2024!`) |
| `neo4j:5.18.0` | The official Neo4j image from Docker Hub, version 5.18 |

Wait about 15 seconds for Neo4j to start, then verify:

```bash
docker logs bollywood_neo4j | grep "Started"
```

You should see a line like: `Remote interface available at http://localhost:7474/`

**To stop the container later:**
```bash
docker stop bollywood_neo4j
```

**To start it again:**
```bash
docker start bollywood_neo4j
```

**Important — your data is safe when you stop and restart.** Docker containers persist their data between stop/start cycles. Only running `docker rm bollywood_neo4j` (delete the container) would erase the data.

---

## 3. Open the Neo4j Browser

Go to **http://localhost:7474** in your browser.

- **Username:** `neo4j`
- **Password:** `bollywood2024!`

You will see the Neo4j Browser — a web-based query editor. There is a text field at the top where you paste Cypher queries and press **Ctrl+Enter** (Mac: **Cmd+Enter**) to run them.

Results are shown as a visual graph when you return full nodes, or as a table when you return specific properties.

---

## 4. The Data Model

Before loading anything, understand what we are building.

### Node types (labels)

| Label | What it represents | Key properties |
|---|---|---|
| `Person` | Actor, director, or music composer | `name`, `born`, `profession`, `hometown` |
| `Movie` | A Bollywood film | `title`, `year`, `genre`, `box_office_crore`, `description` |
| `ProductionHouse` | Film studio | `name`, `founded`, `founder`, `hq` |
| `Award` | A film award | `name`, `category`, `year` |

### Relationship types

```
(Person)          -[:ACTED_IN {character, lead_role}]->  (Movie)
(Person)          -[:DIRECTED]->                         (Movie)
(Person)          -[:COMPOSED_MUSIC_FOR]->               (Movie)
(Person)          -[:WON]->                              (Award)
(Movie)           -[:WON]->                              (Award)
(ProductionHouse) -[:PRODUCED]->                         (Movie)
```

### Visual diagram

```
                    ┌─────────────┐
                    │   Person    │
                    │  (Actor /   │
                    │  Director / │
                    │  Composer)  │
                    └──────┬──────┘
                           │
         ┌─────────────────┼──────────────────────┐
         │                 │                      │
    ACTED_IN           DIRECTED          COMPOSED_MUSIC_FOR
         │                 │                      │
         ▼                 ▼                      ▼
    ┌──────────┐     ┌──────────┐          ┌──────────┐
    │  Movie   │◄────│  Movie   │          │  Movie   │
    └────┬─────┘     └──────────┘          └──────────┘
         │
    ┌────┴──────────────────────────────┐
    │                                   │
   WON                              PRODUCED (by)
    │                                   │
    ▼                                   ▲
┌──────────┐                   ┌─────────────────┐
│  Award   │                   │ ProductionHouse  │
└──────────┘                   └─────────────────┘
```

---

## 5. Load the Data

Paste each block into the Neo4j Browser and run it. You can run the entire section at once or block by block.

### 5.1 Create uniqueness constraints

Constraints prevent duplicate nodes and speed up lookups. Run this first.

```cypher
CREATE CONSTRAINT person_name  IF NOT EXISTS FOR (p:Person)          REQUIRE p.name  IS UNIQUE;
CREATE CONSTRAINT movie_title  IF NOT EXISTS FOR (m:Movie)           REQUIRE m.title IS UNIQUE;
CREATE CONSTRAINT prodhouse    IF NOT EXISTS FOR (p:ProductionHouse) REQUIRE p.name  IS UNIQUE;
CREATE CONSTRAINT award_name   IF NOT EXISTS FOR (a:Award)           REQUIRE a.name  IS UNIQUE;
```

`MERGE` (used below) will use these constraints as indexes — making every upsert fast.

---

### 5.2 Create Person nodes

`MERGE` means: create the node if it does not exist, or match the existing one. Safe to re-run.

```cypher
// Actors
MERGE (n:Person {name: "Shah Rukh Khan"})      SET n.born = 1965, n.profession = "Actor",           n.hometown = "Delhi";
MERGE (n:Person {name: "Aamir Khan"})           SET n.born = 1965, n.profession = "Actor-Director",  n.hometown = "Mumbai";
MERGE (n:Person {name: "Salman Khan"})          SET n.born = 1965, n.profession = "Actor",           n.hometown = "Mumbai";
MERGE (n:Person {name: "Amitabh Bachchan"})    SET n.born = 1942, n.profession = "Actor",           n.hometown = "Allahabad";
MERGE (n:Person {name: "Hrithik Roshan"})       SET n.born = 1974, n.profession = "Actor",           n.hometown = "Mumbai";
MERGE (n:Person {name: "Ranveer Singh"})        SET n.born = 1985, n.profession = "Actor",           n.hometown = "Mumbai";
MERGE (n:Person {name: "Ranbir Kapoor"})        SET n.born = 1982, n.profession = "Actor",           n.hometown = "Mumbai";
MERGE (n:Person {name: "Deepika Padukone"})    SET n.born = 1986, n.profession = "Actor",           n.hometown = "Bengaluru";
MERGE (n:Person {name: "Alia Bhatt"})           SET n.born = 1993, n.profession = "Actor",           n.hometown = "Mumbai";
MERGE (n:Person {name: "Priyanka Chopra"})     SET n.born = 1982, n.profession = "Actor",           n.hometown = "Jamshedpur";
MERGE (n:Person {name: "Kajol"})                SET n.born = 1974, n.profession = "Actor",           n.hometown = "Mumbai";
MERGE (n:Person {name: "Madhuri Dixit"})        SET n.born = 1967, n.profession = "Actor",           n.hometown = "Pune";
MERGE (n:Person {name: "Aishwarya Rai"})       SET n.born = 1973, n.profession = "Actor",           n.hometown = "Mangaluru";
MERGE (n:Person {name: "Taapsee Pannu"})       SET n.born = 1987, n.profession = "Actor",           n.hometown = "Delhi";
MERGE (n:Person {name: "Nawazuddin Siddiqui"}) SET n.born = 1974, n.profession = "Actor",           n.hometown = "Budhana, UP";
MERGE (n:Person {name: "Irrfan Khan"})          SET n.born = 1967, n.profession = "Actor",           n.hometown = "Jaipur";
MERGE (n:Person {name: "Sunny Deol"})           SET n.born = 1956, n.profession = "Actor",           n.hometown = "Sahnewal, Punjab";
MERGE (n:Person {name: "Rani Mukerji"})         SET n.born = 1978, n.profession = "Actor",           n.hometown = "Kolkata";

// Directors
MERGE (n:Person {name: "Rajkumar Hirani"})     SET n.born = 1962, n.profession = "Director",          n.hometown = "Nagpur";
MERGE (n:Person {name: "Zoya Akhtar"})          SET n.born = 1972, n.profession = "Director",          n.hometown = "Mumbai";
MERGE (n:Person {name: "Sanjay Leela Bhansali"})SET n.born = 1963, n.profession = "Director",          n.hometown = "Mumbai";
MERGE (n:Person {name: "Karan Johar"})          SET n.born = 1972, n.profession = "Director-Producer", n.hometown = "Mumbai";
MERGE (n:Person {name: "Aditya Chopra"})       SET n.born = 1971, n.profession = "Director-Producer", n.hometown = "Mumbai";
MERGE (n:Person {name: "Farhan Akhtar"})        SET n.born = 1974, n.profession = "Director-Actor",   n.hometown = "Mumbai";
MERGE (n:Person {name: "Nitesh Tiwari"})        SET n.born = 1973, n.profession = "Director",          n.hometown = "Itarsi, MP";
MERGE (n:Person {name: "Ashutosh Gowariker"})  SET n.born = 1964, n.profession = "Director",          n.hometown = "Mumbai";
MERGE (n:Person {name: "Imtiaz Ali"})           SET n.born = 1971, n.profession = "Director",          n.hometown = "Jamshedpur";
MERGE (n:Person {name: "Kabir Khan"})           SET n.born = 1971, n.profession = "Director",          n.hometown = "Delhi";
MERGE (n:Person {name: "Farah Khan"})           SET n.born = 1965, n.profession = "Director",          n.hometown = "Mumbai";
MERGE (n:Person {name: "Rohit Shetty"})         SET n.born = 1973, n.profession = "Director",          n.hometown = "Mumbai";
MERGE (n:Person {name: "Anurag Kashyap"})       SET n.born = 1972, n.profession = "Director",          n.hometown = "Gorakhpur, UP";
MERGE (n:Person {name: "Anurag Basu"})          SET n.born = 1974, n.profession = "Director",          n.hometown = "Kolkata";
MERGE (n:Person {name: "Siddharth Anand"})      SET n.born = 1975, n.profession = "Director",          n.hometown = "Mumbai";

// Music composers
MERGE (n:Person {name: "AR Rahman"})            SET n.born = 1967, n.profession = "Music Composer",  n.hometown = "Chennai";
MERGE (n:Person {name: "Shankar-Ehsaan-Loy"})  SET n.born = 1965, n.profession = "Music Composer",  n.hometown = "Mumbai";
MERGE (n:Person {name: "Pritam Chakraborty"})  SET n.born = 1971, n.profession = "Music Composer",  n.hometown = "Kolkata";
MERGE (n:Person {name: "Vishal-Shekhar"})      SET n.born = 1977, n.profession = "Music Composer",  n.hometown = "Mumbai";
MERGE (n:Person {name: "Amit Trivedi"})         SET n.born = 1979, n.profession = "Music Composer",  n.hometown = "Varanasi";
MERGE (n:Person {name: "Ismail Darbar"})        SET n.born = 1967, n.profession = "Music Composer",  n.hometown = "Mumbai";
```

---

### 5.3 Create Movie nodes

```cypher
MERGE (m:Movie {title: "Dilwale Dulhania Le Jayenge"})
SET m.year = 1995, m.genre = "Romance", m.box_office_crore = 102.0,
    m.description = "A young man and woman fall in love on a trip to Europe, but must overcome family opposition to be together.";

MERGE (m:Movie {title: "Lagaan"})
SET m.year = 2001, m.genre = "Historical Drama", m.box_office_crore = 65.0,
    m.description = "Villagers in 19th-century India challenge British colonisers to a cricket match to avoid paying taxes.";

MERGE (m:Movie {title: "Dil Chahta Hai"})
SET m.year = 2001, m.genre = "Coming-of-age Drama", m.box_office_crore = 34.0,
    m.description = "Three inseparable friends navigate love, career and life after college.";

MERGE (m:Movie {title: "Devdas"})
SET m.year = 2002, m.genre = "Tragedy Romance", m.box_office_crore = 52.0,
    m.description = "A young man is unable to marry his childhood love and descends into alcoholism.";

MERGE (m:Movie {title: "Rang De Basanti"})
SET m.year = 2006, m.genre = "Drama", m.box_office_crore = 95.0,
    m.description = "A British filmmaker casts Indian youth to play freedom fighters and the parallels transform their lives.";

MERGE (m:Movie {title: "Taare Zameen Par"})
SET m.year = 2007, m.genre = "Drama", m.box_office_crore = 93.0,
    m.description = "A dyslexic child's life is transformed when a caring teacher recognises his condition and nurtures his talent.";

MERGE (m:Movie {title: "Om Shanti Om"})
SET m.year = 2007, m.genre = "Drama", m.box_office_crore = 201.0,
    m.description = "A junior artist falls in love with a film star in the 1970s and is reborn to take revenge in the 2000s.";

MERGE (m:Movie {title: "Ghajini"})
SET m.year = 2008, m.genre = "Action Thriller", m.box_office_crore = 243.0,
    m.description = "A man with short-term memory loss hunts for the killer of his girlfriend.";

MERGE (m:Movie {title: "3 Idiots"})
SET m.year = 2009, m.genre = "Comedy Drama", m.box_office_crore = 460.0,
    m.description = "Two friends search for their long-lost third companion while reliving their college days and the philosophy of their inspiring teacher.";

MERGE (m:Movie {title: "My Name Is Khan"})
SET m.year = 2010, m.genre = "Drama", m.box_office_crore = 200.0,
    m.description = "A Muslim man with Asperger syndrome embarks on a journey to meet the US President after post-9/11 discrimination.";

MERGE (m:Movie {title: "Zindagi Na Milegi Dobara"})
SET m.year = 2011, m.genre = "Adventure Drama", m.box_office_crore = 153.0,
    m.description = "Three childhood friends go on a road trip through Spain that changes their perspectives on life and love.";

MERGE (m:Movie {title: "Barfi!"})
SET m.year = 2012, m.genre = "Comedy Drama", m.box_office_crore = 120.0,
    m.description = "A deaf-mute man falls in love with two women in 1970s Darjeeling.";

MERGE (m:Movie {title: "Gangs of Wasseypur"})
SET m.year = 2012, m.genre = "Crime Drama", m.box_office_crore = 56.0,
    m.description = "A multi-generational saga of coal mine mafia, revenge, and power in Dhanbad.";

MERGE (m:Movie {title: "Chennai Express"})
SET m.year = 2013, m.genre = "Action Comedy", m.box_office_crore = 423.0,
    m.description = "A Mumbai man on a train to Rameswaram gets entangled with a Tamil girl and her gangster father.";

MERGE (m:Movie {title: "PK"})
SET m.year = 2014, m.genre = "Satire Comedy", m.box_office_crore = 832.0,
    m.description = "An alien stranded on Earth questions religious practices while searching for his remote control to return home.";

MERGE (m:Movie {title: "Bajrangi Bhaijaan"})
SET m.year = 2015, m.genre = "Drama", m.box_office_crore = 969.0,
    m.description = "A devoted devotee of Hanuman helps a mute Pakistani girl return to her family across the border.";

MERGE (m:Movie {title: "Bajirao Mastani"})
SET m.year = 2015, m.genre = "Historical Romance", m.box_office_crore = 355.0,
    m.description = "The love story of Maratha warrior Peshwa Bajirao and his second wife Mastani.";

MERGE (m:Movie {title: "Dangal"})
SET m.year = 2016, m.genre = "Sports Biopic", m.box_office_crore = 2024.0,
    m.description = "The real story of Mahavir Singh Phogat who trains his daughters to become world-class wrestlers.";

MERGE (m:Movie {title: "Raees"})
SET m.year = 2017, m.genre = "Crime Drama", m.box_office_crore = 193.0,
    m.description = "A bootlegger in Gujarat rises to power while being chased by a relentless police officer.";

MERGE (m:Movie {title: "Gully Boy"})
SET m.year = 2019, m.genre = "Musical Drama", m.box_office_crore = 247.0,
    m.description = "A young man from the Dharavi slums discovers hip-hop as a vehicle for expressing his struggles and dreams.";

MERGE (m:Movie {title: "War"})
SET m.year = 2019, m.genre = "Action Thriller", m.box_office_crore = 475.0,
    m.description = "An Indian soldier is assigned to eliminate his former mentor who has gone rogue.";

MERGE (m:Movie {title: "Brahmastra Part One: Shiva"})
SET m.year = 2022, m.genre = "Fantasy Action", m.box_office_crore = 431.0,
    m.description = "A young man discovers he has a mystical connection to fire as he searches for an ancient superweapon.";

MERGE (m:Movie {title: "Pathaan"})
SET m.year = 2023, m.genre = "Action Spy", m.box_office_crore = 1050.0,
    m.description = "An exiled Indian spy must stop a private army from launching a devastating attack on India.";

MERGE (m:Movie {title: "Jawan"})
SET m.year = 2023, m.genre = "Action Thriller", m.box_office_crore = 1160.0,
    m.description = "A prison warden with a dark past recruits women inmates to expose corrupt officials.";

MERGE (m:Movie {title: "Animal"})
SET m.year = 2023, m.genre = "Action Crime", m.box_office_crore = 900.0,
    m.description = "A man's obsessive devotion to his estranged father spirals into violence when his father is targeted.";
```

---

### 5.4 Create ProductionHouse nodes

```cypher
MERGE (n:ProductionHouse {name: "Yash Raj Films"})          SET n.founded = 1970, n.founder = "Yash Chopra",          n.hq = "Mumbai";
MERGE (n:ProductionHouse {name: "Dharma Productions"})      SET n.founded = 1976, n.founder = "Yash Johar",           n.hq = "Mumbai";
MERGE (n:ProductionHouse {name: "Excel Entertainment"})     SET n.founded = 2001, n.founder = "Farhan Akhtar",        n.hq = "Mumbai";
MERGE (n:ProductionHouse {name: "Vinod Chopra Films"})      SET n.founded = 1987, n.founder = "Vidhu Vinod Chopra",   n.hq = "Mumbai";
MERGE (n:ProductionHouse {name: "Aamir Khan Productions"})  SET n.founded = 1999, n.founder = "Aamir Khan",           n.hq = "Mumbai";
MERGE (n:ProductionHouse {name: "Red Chillies Entertainment"}) SET n.founded = 2002, n.founder = "Shah Rukh Khan",   n.hq = "Mumbai";
MERGE (n:ProductionHouse {name: "Nadiadwala Grandson"})     SET n.founded = 1948, n.founder = "S.N. Nadiadwala",      n.hq = "Mumbai";
MERGE (n:ProductionHouse {name: "T-Series Films"})          SET n.founded = 1983, n.founder = "Gulshan Kumar",        n.hq = "Noida";
```

---

### 5.5 Create Award nodes

```cypher
MERGE (a:Award {name: "Filmfare Best Film 1996"})               SET a.category = "Filmfare",  a.year = 1996;
MERGE (a:Award {name: "Filmfare Best Film 2002"})               SET a.category = "Filmfare",  a.year = 2002;
MERGE (a:Award {name: "Filmfare Best Film 2009"})               SET a.category = "Filmfare",  a.year = 2009;
MERGE (a:Award {name: "Filmfare Best Film 2010"})               SET a.category = "Filmfare",  a.year = 2010;
MERGE (a:Award {name: "Filmfare Best Film 2017"})               SET a.category = "Filmfare",  a.year = 2017;
MERGE (a:Award {name: "Filmfare Best Film 2020"})               SET a.category = "Filmfare",  a.year = 2020;
MERGE (a:Award {name: "National Award Best Film 2001"})         SET a.category = "National",  a.year = 2001;
MERGE (a:Award {name: "National Award Best Film 2002"})         SET a.category = "National",  a.year = 2002;
MERGE (a:Award {name: "National Award Best Film 2007"})         SET a.category = "National",  a.year = 2007;
MERGE (a:Award {name: "National Award Best Film 2017"})         SET a.category = "National",  a.year = 2017;
MERGE (a:Award {name: "Filmfare Best Actor SRK 1996"})          SET a.category = "Filmfare",  a.year = 1996;
MERGE (a:Award {name: "Filmfare Best Actor SRK 2005"})          SET a.category = "Filmfare",  a.year = 2005;
MERGE (a:Award {name: "Filmfare Best Actor Aamir 2009"})        SET a.category = "Filmfare",  a.year = 2009;
MERGE (a:Award {name: "Filmfare Best Actor Hrithik 2020"})      SET a.category = "Filmfare",  a.year = 2020;
MERGE (a:Award {name: "Filmfare Best Actor Ranveer 2016"})      SET a.category = "Filmfare",  a.year = 2016;
MERGE (a:Award {name: "Filmfare Best Actress Deepika 2016"})    SET a.category = "Filmfare",  a.year = 2016;
MERGE (a:Award {name: "Filmfare Best Actress Alia 2020"})       SET a.category = "Filmfare",  a.year = 2020;
MERGE (a:Award {name: "Filmfare Best Director RKH 2010"})       SET a.category = "Filmfare",  a.year = 2010;
MERGE (a:Award {name: "Filmfare Best Director Zoya 2012"})      SET a.category = "Filmfare",  a.year = 2012;
MERGE (a:Award {name: "National Award Best Music AR Rahman 2002"}) SET a.category = "National", a.year = 2002;
MERGE (a:Award {name: "Oscar Best Original Score AR Rahman 2009"}) SET a.category = "Oscar",   a.year = 2009;
MERGE (a:Award {name: "National Award Best Actor Nawaz 2013"})  SET a.category = "National",  a.year = 2013;
MERGE (a:Award {name: "Padma Shri Shah Rukh Khan"})             SET a.category = "Civilian",  a.year = 2005;
MERGE (a:Award {name: "Padma Bhushan Amitabh Bachchan"})        SET a.category = "Civilian",  a.year = 2015;
MERGE (a:Award {name: "Padma Vibhushan Amitabh Bachchan"})      SET a.category = "Civilian",  a.year = 2024;
```

---

### 5.6 Create ACTED_IN relationships

```cypher
MATCH (p:Person {name: "Shah Rukh Khan"}),    (m:Movie {title: "Dilwale Dulhania Le Jayenge"}) MERGE (p)-[:ACTED_IN {character: "Raj Malhotra",              lead_role: true}]->(m);
MATCH (p:Person {name: "Kajol"}),             (m:Movie {title: "Dilwale Dulhania Le Jayenge"}) MERGE (p)-[:ACTED_IN {character: "Simran Singh",              lead_role: true}]->(m);
MATCH (p:Person {name: "Aamir Khan"}),        (m:Movie {title: "Lagaan"})                       MERGE (p)-[:ACTED_IN {character: "Bhuvan",                    lead_role: true}]->(m);
MATCH (p:Person {name: "Aamir Khan"}),        (m:Movie {title: "Dil Chahta Hai"})               MERGE (p)-[:ACTED_IN {character: "Akash",                     lead_role: true}]->(m);
MATCH (p:Person {name: "Aamir Khan"}),        (m:Movie {title: "Taare Zameen Par"})             MERGE (p)-[:ACTED_IN {character: "Ram Shankar Nikumbh",       lead_role: true}]->(m);
MATCH (p:Person {name: "Aamir Khan"}),        (m:Movie {title: "Ghajini"})                      MERGE (p)-[:ACTED_IN {character: "Sanjay Singhania",          lead_role: true}]->(m);
MATCH (p:Person {name: "Aamir Khan"}),        (m:Movie {title: "3 Idiots"})                     MERGE (p)-[:ACTED_IN {character: "Rancho",                    lead_role: true}]->(m);
MATCH (p:Person {name: "Aamir Khan"}),        (m:Movie {title: "PK"})                           MERGE (p)-[:ACTED_IN {character: "PK",                        lead_role: true}]->(m);
MATCH (p:Person {name: "Aamir Khan"}),        (m:Movie {title: "Dangal"})                       MERGE (p)-[:ACTED_IN {character: "Mahavir Singh Phogat",      lead_role: true}]->(m);
MATCH (p:Person {name: "Shah Rukh Khan"}),    (m:Movie {title: "Om Shanti Om"})                 MERGE (p)-[:ACTED_IN {character: "Om Kapoor / Om Makhija",    lead_role: true}]->(m);
MATCH (p:Person {name: "Deepika Padukone"}),  (m:Movie {title: "Om Shanti Om"})                 MERGE (p)-[:ACTED_IN {character: "Shantipriya / Sandy",       lead_role: true}]->(m);
MATCH (p:Person {name: "Shah Rukh Khan"}),    (m:Movie {title: "My Name Is Khan"})              MERGE (p)-[:ACTED_IN {character: "Rizwan Khan",               lead_role: true}]->(m);
MATCH (p:Person {name: "Shah Rukh Khan"}),    (m:Movie {title: "Chennai Express"})              MERGE (p)-[:ACTED_IN {character: "Rahul Mithaiwala",          lead_role: true}]->(m);
MATCH (p:Person {name: "Shah Rukh Khan"}),    (m:Movie {title: "Raees"})                        MERGE (p)-[:ACTED_IN {character: "Raees Alam",                lead_role: true}]->(m);
MATCH (p:Person {name: "Shah Rukh Khan"}),    (m:Movie {title: "Pathaan"})                      MERGE (p)-[:ACTED_IN {character: "Pathaan",                   lead_role: true}]->(m);
MATCH (p:Person {name: "Shah Rukh Khan"}),    (m:Movie {title: "Jawan"})                        MERGE (p)-[:ACTED_IN {character: "Azad / Vikram Rathore",     lead_role: true}]->(m);
MATCH (p:Person {name: "Deepika Padukone"}),  (m:Movie {title: "Pathaan"})                      MERGE (p)-[:ACTED_IN {character: "Rubina Mohsin",             lead_role: true}]->(m);
MATCH (p:Person {name: "Salman Khan"}),       (m:Movie {title: "Bajrangi Bhaijaan"})            MERGE (p)-[:ACTED_IN {character: "Pawan Kumar Chaturvedi",    lead_role: true}]->(m);
MATCH (p:Person {name: "Hrithik Roshan"}),    (m:Movie {title: "War"})                          MERGE (p)-[:ACTED_IN {character: "Khalid",                    lead_role: true}]->(m);
MATCH (p:Person {name: "Ranveer Singh"}),     (m:Movie {title: "Gully Boy"})                    MERGE (p)-[:ACTED_IN {character: "Murad Ahmed",               lead_role: true}]->(m);
MATCH (p:Person {name: "Alia Bhatt"}),        (m:Movie {title: "Gully Boy"})                    MERGE (p)-[:ACTED_IN {character: "Safeena",                   lead_role: true}]->(m);
MATCH (p:Person {name: "Ranveer Singh"}),     (m:Movie {title: "Bajirao Mastani"})              MERGE (p)-[:ACTED_IN {character: "Peshwa Bajirao",            lead_role: true}]->(m);
MATCH (p:Person {name: "Deepika Padukone"}),  (m:Movie {title: "Bajirao Mastani"})              MERGE (p)-[:ACTED_IN {character: "Mastani",                   lead_role: true}]->(m);
MATCH (p:Person {name: "Ranbir Kapoor"}),     (m:Movie {title: "Barfi!"})                       MERGE (p)-[:ACTED_IN {character: "Barfi",                     lead_role: true}]->(m);
MATCH (p:Person {name: "Priyanka Chopra"}),   (m:Movie {title: "Barfi!"})                       MERGE (p)-[:ACTED_IN {character: "Shruti",                    lead_role: true}]->(m);
MATCH (p:Person {name: "Ranbir Kapoor"}),     (m:Movie {title: "Brahmastra Part One: Shiva"})   MERGE (p)-[:ACTED_IN {character: "Shiva",                     lead_role: true}]->(m);
MATCH (p:Person {name: "Alia Bhatt"}),        (m:Movie {title: "Brahmastra Part One: Shiva"})   MERGE (p)-[:ACTED_IN {character: "Isha",                      lead_role: true}]->(m);
MATCH (p:Person {name: "Amitabh Bachchan"}),  (m:Movie {title: "Brahmastra Part One: Shiva"})   MERGE (p)-[:ACTED_IN {character: "Guru",                      lead_role: false}]->(m);
MATCH (p:Person {name: "Shah Rukh Khan"}),    (m:Movie {title: "Devdas"})                       MERGE (p)-[:ACTED_IN {character: "Devdas Mukherjee",          lead_role: true}]->(m);
MATCH (p:Person {name: "Aishwarya Rai"}),     (m:Movie {title: "Devdas"})                       MERGE (p)-[:ACTED_IN {character: "Paro",                      lead_role: true}]->(m);
MATCH (p:Person {name: "Madhuri Dixit"}),     (m:Movie {title: "Devdas"})                       MERGE (p)-[:ACTED_IN {character: "Chandramukhi",              lead_role: true}]->(m);
MATCH (p:Person {name: "Amitabh Bachchan"}),  (m:Movie {title: "Devdas"})                       MERGE (p)-[:ACTED_IN {character: "Chunilal",                  lead_role: false}]->(m);
MATCH (p:Person {name: "Hrithik Roshan"}),    (m:Movie {title: "Zindagi Na Milegi Dobara"})     MERGE (p)-[:ACTED_IN {character: "Arjun Saluja",              lead_role: true}]->(m);
MATCH (p:Person {name: "Farhan Akhtar"}),     (m:Movie {title: "Zindagi Na Milegi Dobara"})     MERGE (p)-[:ACTED_IN {character: "Imraan",                    lead_role: true}]->(m);
MATCH (p:Person {name: "Irrfan Khan"}),       (m:Movie {title: "Rang De Basanti"})              MERGE (p)-[:ACTED_IN {character: "DJ",                        lead_role: true}]->(m);
MATCH (p:Person {name: "Nawazuddin Siddiqui"}),(m:Movie {title: "Gangs of Wasseypur"})          MERGE (p)-[:ACTED_IN {character: "Faizal Khan",               lead_role: true}]->(m);
MATCH (p:Person {name: "Ranbir Kapoor"}),     (m:Movie {title: "Animal"})                       MERGE (p)-[:ACTED_IN {character: "Ranvijay Singh",            lead_role: true}]->(m);
MATCH (p:Person {name: "Taapsee Pannu"}),     (m:Movie {title: "Raees"})                        MERGE (p)-[:ACTED_IN {character: "Aasiya",                    lead_role: true}]->(m);
```

---

### 5.7 Create DIRECTED relationships

```cypher
MATCH (d:Person {name: "Aditya Chopra"}),        (m:Movie {title: "Dilwale Dulhania Le Jayenge"}) MERGE (d)-[:DIRECTED]->(m);
MATCH (d:Person {name: "Ashutosh Gowariker"}),   (m:Movie {title: "Lagaan"})                       MERGE (d)-[:DIRECTED]->(m);
MATCH (d:Person {name: "Farhan Akhtar"}),         (m:Movie {title: "Dil Chahta Hai"})               MERGE (d)-[:DIRECTED]->(m);
MATCH (d:Person {name: "Sanjay Leela Bhansali"}), (m:Movie {title: "Devdas"})                       MERGE (d)-[:DIRECTED]->(m);
MATCH (d:Person {name: "Sanjay Leela Bhansali"}), (m:Movie {title: "Bajirao Mastani"})              MERGE (d)-[:DIRECTED]->(m);
MATCH (d:Person {name: "Aamir Khan"}),            (m:Movie {title: "Taare Zameen Par"})             MERGE (d)-[:DIRECTED]->(m);
MATCH (d:Person {name: "Farah Khan"}),            (m:Movie {title: "Om Shanti Om"})                 MERGE (d)-[:DIRECTED]->(m);
MATCH (d:Person {name: "Rajkumar Hirani"}),       (m:Movie {title: "3 Idiots"})                     MERGE (d)-[:DIRECTED]->(m);
MATCH (d:Person {name: "Rajkumar Hirani"}),       (m:Movie {title: "PK"})                           MERGE (d)-[:DIRECTED]->(m);
MATCH (d:Person {name: "Karan Johar"}),           (m:Movie {title: "My Name Is Khan"})              MERGE (d)-[:DIRECTED]->(m);
MATCH (d:Person {name: "Rohit Shetty"}),          (m:Movie {title: "Chennai Express"})              MERGE (d)-[:DIRECTED]->(m);
MATCH (d:Person {name: "Zoya Akhtar"}),           (m:Movie {title: "Zindagi Na Milegi Dobara"})     MERGE (d)-[:DIRECTED]->(m);
MATCH (d:Person {name: "Zoya Akhtar"}),           (m:Movie {title: "Gully Boy"})                    MERGE (d)-[:DIRECTED]->(m);
MATCH (d:Person {name: "Anurag Kashyap"}),        (m:Movie {title: "Gangs of Wasseypur"})           MERGE (d)-[:DIRECTED]->(m);
MATCH (d:Person {name: "Anurag Basu"}),           (m:Movie {title: "Barfi!"})                       MERGE (d)-[:DIRECTED]->(m);
MATCH (d:Person {name: "Kabir Khan"}),            (m:Movie {title: "Bajrangi Bhaijaan"})            MERGE (d)-[:DIRECTED]->(m);
MATCH (d:Person {name: "Nitesh Tiwari"}),         (m:Movie {title: "Dangal"})                       MERGE (d)-[:DIRECTED]->(m);
MATCH (d:Person {name: "Siddharth Anand"}),       (m:Movie {title: "War"})                          MERGE (d)-[:DIRECTED]->(m);
MATCH (d:Person {name: "Siddharth Anand"}),       (m:Movie {title: "Pathaan"})                      MERGE (d)-[:DIRECTED]->(m);
MATCH (d:Person {name: "Siddharth Anand"}),       (m:Movie {title: "Jawan"})                        MERGE (d)-[:DIRECTED]->(m);
MATCH (d:Person {name: "Ranbir Kapoor"}),         (m:Movie {title: "Animal"})                       MERGE (d)-[:DIRECTED]->(m);
```

> **Note:** Yes, Ranbir Kapoor directed Animal in this dataset — this intentionally creates an actor-director case you can query in Part 6.

---

### 5.8 Create COMPOSED_MUSIC_FOR relationships

```cypher
MATCH (c:Person {name: "AR Rahman"}),           (m:Movie {title: "Lagaan"})                   MERGE (c)-[:COMPOSED_MUSIC_FOR]->(m);
MATCH (c:Person {name: "AR Rahman"}),           (m:Movie {title: "Rang De Basanti"})           MERGE (c)-[:COMPOSED_MUSIC_FOR]->(m);
MATCH (c:Person {name: "AR Rahman"}),           (m:Movie {title: "Ghajini"})                   MERGE (c)-[:COMPOSED_MUSIC_FOR]->(m);
MATCH (c:Person {name: "Shankar-Ehsaan-Loy"}),  (m:Movie {title: "Dil Chahta Hai"})            MERGE (c)-[:COMPOSED_MUSIC_FOR]->(m);
MATCH (c:Person {name: "Shankar-Ehsaan-Loy"}),  (m:Movie {title: "Zindagi Na Milegi Dobara"}) MERGE (c)-[:COMPOSED_MUSIC_FOR]->(m);
MATCH (c:Person {name: "Shankar-Ehsaan-Loy"}),  (m:Movie {title: "My Name Is Khan"})           MERGE (c)-[:COMPOSED_MUSIC_FOR]->(m);
MATCH (c:Person {name: "Ismail Darbar"}),        (m:Movie {title: "Devdas"})                    MERGE (c)-[:COMPOSED_MUSIC_FOR]->(m);
MATCH (c:Person {name: "Ismail Darbar"}),        (m:Movie {title: "Bajirao Mastani"})           MERGE (c)-[:COMPOSED_MUSIC_FOR]->(m);
MATCH (c:Person {name: "Vishal-Shekhar"}),       (m:Movie {title: "Om Shanti Om"})              MERGE (c)-[:COMPOSED_MUSIC_FOR]->(m);
MATCH (c:Person {name: "Vishal-Shekhar"}),       (m:Movie {title: "Pathaan"})                   MERGE (c)-[:COMPOSED_MUSIC_FOR]->(m);
MATCH (c:Person {name: "Vishal-Shekhar"}),       (m:Movie {title: "Jawan"})                     MERGE (c)-[:COMPOSED_MUSIC_FOR]->(m);
MATCH (c:Person {name: "Pritam Chakraborty"}),  (m:Movie {title: "Barfi!"})                    MERGE (c)-[:COMPOSED_MUSIC_FOR]->(m);
MATCH (c:Person {name: "Pritam Chakraborty"}),  (m:Movie {title: "Brahmastra Part One: Shiva"})MERGE (c)-[:COMPOSED_MUSIC_FOR]->(m);
MATCH (c:Person {name: "Pritam Chakraborty"}),  (m:Movie {title: "Chennai Express"})            MERGE (c)-[:COMPOSED_MUSIC_FOR]->(m);
MATCH (c:Person {name: "Pritam Chakraborty"}),  (m:Movie {title: "3 Idiots"})                  MERGE (c)-[:COMPOSED_MUSIC_FOR]->(m);
MATCH (c:Person {name: "Amit Trivedi"}),         (m:Movie {title: "Gully Boy"})                 MERGE (c)-[:COMPOSED_MUSIC_FOR]->(m);
```

---

### 5.9 Create PRODUCED relationships

```cypher
MATCH (ph:ProductionHouse {name: "Yash Raj Films"}),          (m:Movie {title: "Dilwale Dulhania Le Jayenge"}) MERGE (ph)-[:PRODUCED]->(m);
MATCH (ph:ProductionHouse {name: "Yash Raj Films"}),          (m:Movie {title: "War"})                         MERGE (ph)-[:PRODUCED]->(m);
MATCH (ph:ProductionHouse {name: "Yash Raj Films"}),          (m:Movie {title: "Pathaan"})                      MERGE (ph)-[:PRODUCED]->(m);
MATCH (ph:ProductionHouse {name: "Yash Raj Films"}),          (m:Movie {title: "Jawan"})                        MERGE (ph)-[:PRODUCED]->(m);
MATCH (ph:ProductionHouse {name: "Dharma Productions"}),      (m:Movie {title: "My Name Is Khan"})              MERGE (ph)-[:PRODUCED]->(m);
MATCH (ph:ProductionHouse {name: "Dharma Productions"}),      (m:Movie {title: "Brahmastra Part One: Shiva"})   MERGE (ph)-[:PRODUCED]->(m);
MATCH (ph:ProductionHouse {name: "Excel Entertainment"}),     (m:Movie {title: "Dil Chahta Hai"})               MERGE (ph)-[:PRODUCED]->(m);
MATCH (ph:ProductionHouse {name: "Excel Entertainment"}),     (m:Movie {title: "Zindagi Na Milegi Dobara"})     MERGE (ph)-[:PRODUCED]->(m);
MATCH (ph:ProductionHouse {name: "Excel Entertainment"}),     (m:Movie {title: "Gully Boy"})                    MERGE (ph)-[:PRODUCED]->(m);
MATCH (ph:ProductionHouse {name: "Aamir Khan Productions"}),  (m:Movie {title: "Lagaan"})                       MERGE (ph)-[:PRODUCED]->(m);
MATCH (ph:ProductionHouse {name: "Aamir Khan Productions"}),  (m:Movie {title: "Taare Zameen Par"})             MERGE (ph)-[:PRODUCED]->(m);
MATCH (ph:ProductionHouse {name: "Aamir Khan Productions"}),  (m:Movie {title: "3 Idiots"})                     MERGE (ph)-[:PRODUCED]->(m);
MATCH (ph:ProductionHouse {name: "Aamir Khan Productions"}),  (m:Movie {title: "PK"})                           MERGE (ph)-[:PRODUCED]->(m);
MATCH (ph:ProductionHouse {name: "Aamir Khan Productions"}),  (m:Movie {title: "Dangal"})                       MERGE (ph)-[:PRODUCED]->(m);
MATCH (ph:ProductionHouse {name: "Vinod Chopra Films"}),      (m:Movie {title: "3 Idiots"})                     MERGE (ph)-[:PRODUCED]->(m);
MATCH (ph:ProductionHouse {name: "Red Chillies Entertainment"}),(m:Movie {title: "Om Shanti Om"})               MERGE (ph)-[:PRODUCED]->(m);
MATCH (ph:ProductionHouse {name: "Nadiadwala Grandson"}),     (m:Movie {title: "Chennai Express"})              MERGE (ph)-[:PRODUCED]->(m);
MATCH (ph:ProductionHouse {name: "Nadiadwala Grandson"}),     (m:Movie {title: "Bajrangi Bhaijaan"})            MERGE (ph)-[:PRODUCED]->(m);
```

---

### 5.10 Create WON relationships

```cypher
// Movie awards
MATCH (m:Movie {title: "Dilwale Dulhania Le Jayenge"}), (a:Award {name: "Filmfare Best Film 1996"})          MERGE (m)-[:WON]->(a);
MATCH (m:Movie {title: "Devdas"}),                       (a:Award {name: "Filmfare Best Film 2002"})          MERGE (m)-[:WON]->(a);
MATCH (m:Movie {title: "Lagaan"}),                       (a:Award {name: "National Award Best Film 2002"})    MERGE (m)-[:WON]->(a);
MATCH (m:Movie {title: "Rang De Basanti"}),              (a:Award {name: "National Award Best Film 2007"})    MERGE (m)-[:WON]->(a);
MATCH (m:Movie {title: "3 Idiots"}),                     (a:Award {name: "Filmfare Best Film 2010"})          MERGE (m)-[:WON]->(a);
MATCH (m:Movie {title: "Dangal"}),                       (a:Award {name: "National Award Best Film 2017"})    MERGE (m)-[:WON]->(a);
MATCH (m:Movie {title: "Gully Boy"}),                    (a:Award {name: "Filmfare Best Film 2020"})          MERGE (m)-[:WON]->(a);

// Personal awards
MATCH (p:Person {name: "Shah Rukh Khan"}),       (a:Award {name: "Filmfare Best Actor SRK 1996"})             MERGE (p)-[:WON]->(a);
MATCH (p:Person {name: "Shah Rukh Khan"}),       (a:Award {name: "Filmfare Best Actor SRK 2005"})             MERGE (p)-[:WON]->(a);
MATCH (p:Person {name: "Shah Rukh Khan"}),       (a:Award {name: "Padma Shri Shah Rukh Khan"})                MERGE (p)-[:WON]->(a);
MATCH (p:Person {name: "Aamir Khan"}),           (a:Award {name: "Filmfare Best Actor Aamir 2009"})           MERGE (p)-[:WON]->(a);
MATCH (p:Person {name: "Hrithik Roshan"}),       (a:Award {name: "Filmfare Best Actor Hrithik 2020"})         MERGE (p)-[:WON]->(a);
MATCH (p:Person {name: "Ranveer Singh"}),        (a:Award {name: "Filmfare Best Actor Ranveer 2016"})         MERGE (p)-[:WON]->(a);
MATCH (p:Person {name: "Deepika Padukone"}),     (a:Award {name: "Filmfare Best Actress Deepika 2016"})       MERGE (p)-[:WON]->(a);
MATCH (p:Person {name: "Alia Bhatt"}),           (a:Award {name: "Filmfare Best Actress Alia 2020"})          MERGE (p)-[:WON]->(a);
MATCH (p:Person {name: "Rajkumar Hirani"}),      (a:Award {name: "Filmfare Best Director RKH 2010"})          MERGE (p)-[:WON]->(a);
MATCH (p:Person {name: "Zoya Akhtar"}),          (a:Award {name: "Filmfare Best Director Zoya 2012"})         MERGE (p)-[:WON]->(a);
MATCH (p:Person {name: "AR Rahman"}),            (a:Award {name: "National Award Best Music AR Rahman 2002"}) MERGE (p)-[:WON]->(a);
MATCH (p:Person {name: "AR Rahman"}),            (a:Award {name: "Oscar Best Original Score AR Rahman 2009"}) MERGE (p)-[:WON]->(a);
MATCH (p:Person {name: "Nawazuddin Siddiqui"}),  (a:Award {name: "National Award Best Actor Nawaz 2013"})     MERGE (p)-[:WON]->(a);
MATCH (p:Person {name: "Amitabh Bachchan"}),     (a:Award {name: "Padma Bhushan Amitabh Bachchan"})           MERGE (p)-[:WON]->(a);
MATCH (p:Person {name: "Amitabh Bachchan"}),     (a:Award {name: "Padma Vibhushan Amitabh Bachchan"})         MERGE (p)-[:WON]->(a);
```

---

### 5.11 Verify the data loaded correctly

Run this to see a count of everything in the graph:

```cypher
MATCH (n)
RETURN labels(n)[0] AS NodeType, count(n) AS Count
ORDER BY Count DESC
```

Expected output:

| NodeType | Count |
|---|---|
| Person | 41 |
| Award | 25 |
| Movie | 25 |
| ProductionHouse | 8 |

```cypher
MATCH ()-[r]->()
RETURN type(r) AS RelationshipType, count(r) AS Count
ORDER BY Count DESC
```

Expected output:

| RelationshipType | Count |
|---|---|
| ACTED_IN | 38 |
| DIRECTED | 21 |
| WON | 22 |
| PRODUCED | 18 |
| COMPOSED_MUSIC_FOR | 16 |

If your counts match, you are ready for the practice queries.

---

## Part 1 — Finding Nodes

### 1.1 See a sample of everything in the graph

```cypher
MATCH (n)
RETURN n
LIMIT 25
```

**What's happening:**
- `MATCH (n)` — find any node. No label filter means all types are returned.
- `RETURN n` — return the full node object. Neo4j Browser renders it as a clickable visual graph.
- `LIMIT 25` — always use a limit when browsing. On large graphs, no limit can return millions of rows.

---

### 1.2 Find all movies, sorted by release year

```cypher
MATCH (m:Movie)
RETURN m.title, m.year, m.genre, m.box_office_crore
ORDER BY m.year
```

**What's happening:**
- `(m:Movie)` — the `:Movie` after the colon is a **label filter**. Only Movie nodes are matched.
- `m.title`, `m.year` — dot notation to read specific properties from the node.
- `ORDER BY m.year` — sort ascending by year. Add `DESC` to reverse.

---

### 1.3 Find all people grouped by profession

```cypher
MATCH (p:Person)
RETURN p.profession, collect(p.name) AS People
ORDER BY p.profession
```

**What's happening:**
- `collect(p.name)` — an aggregation function that gathers all names into a list, grouped by profession.
- The result is one row per profession, with a list of names.

---

### 1.4 Find a specific person by exact name

```cypher
MATCH (p:Person {name: "Shah Rukh Khan"})
RETURN p
```

**What's happening:**
- `{name: "Shah Rukh Khan"}` inside the node pattern is an **inline property filter**.
- It is exactly equivalent to: `MATCH (p:Person) WHERE p.name = "Shah Rukh Khan"`.
- The inline style is shorter and preferred when filtering on the identifier property.

> Try changing the name to `"Aamir Khan"`, `"AR Rahman"`, or `"Zoya Akhtar"`.

---

### 1.5 Count all nodes by type

```cypher
MATCH (n)
RETURN labels(n)[0] AS NodeType, count(n) AS Total
ORDER BY Total DESC
```

**What's happening:**
- `labels(n)` returns a **list** of all labels on the node (nodes can have multiple labels).
- `[0]` gets the first element of that list.
- `count(n)` counts the number of nodes per group. The grouping happens automatically on the non-aggregated field (`NodeType`).

---

## Part 2 — Filtering with WHERE

### 2.1 Movies that crossed 500 crore box office

```cypher
MATCH (m:Movie)
WHERE m.box_office_crore > 500
RETURN m.title, m.year, m.box_office_crore
ORDER BY m.box_office_crore DESC
```

**What's happening:**
- `WHERE` lets you filter on any property using standard comparison operators: `>`, `<`, `>=`, `<=`, `=`, `<>`.
- `DESC` reverses the sort — highest box office first.

---

### 2.2 Actors born in the 1960s

```cypher
MATCH (p:Person)
WHERE p.born >= 1960 AND p.born < 1970
RETURN p.name, p.born, p.profession
ORDER BY p.born
```

**What's happening:**
- `AND` combines conditions — both must be true for the row to be returned.
- You can also use `OR` (either condition true) and `NOT` (invert a condition).

---

### 2.3 Search by partial name (case-insensitive)

```cypher
MATCH (p:Person)
WHERE toLower(p.name) CONTAINS "khan"
RETURN p.name, p.profession
```

**What's happening:**
- `toLower()` converts the value to lowercase before comparison, making the search case-insensitive.
- `CONTAINS` is a substring match — the search term can appear anywhere in the string.
- Other string operators: `STARTS WITH "A"`, `ENDS WITH "r"`.

---

### 2.4 Filter using a list of values

```cypher
MATCH (m:Movie)
WHERE m.genre IN ["Comedy Drama", "Sports Biopic", "Historical Drama"]
RETURN m.title, m.genre, m.year
ORDER BY m.genre, m.year
```

**What's happening:**
- `IN [...]` checks if the property value appears anywhere in the given list.
- This is the Cypher equivalent of SQL's `WHERE genre IN ('Comedy Drama', 'Sports Biopic', ...)`.

---

### 2.5 Filter on NULL — find nodes missing a property

```cypher
MATCH (m:Movie)
WHERE m.box_office_crore IS NULL OR m.box_office_crore = 0
RETURN m.title, m.year
```

**What's happening:**
- `IS NULL` tests for a missing property. In Neo4j, if you never set a property on a node, it simply does not exist (it is not stored as null).
- This is useful for data quality checks.

---

## Part 3 — Relationships

This is the core strength of a graph database.

### Pattern anatomy

```
(p:Person {name: "Aamir Khan"}) -[:ACTED_IN]-> (m:Movie)
 ↑ start node                    ↑ relationship   ↑ end node
 with label and filter           with type filter
```

The arrow direction `->` matters and must match how the relationship was created.

---

### 3.1 All films a person acted in

```cypher
MATCH (p:Person {name: "Aamir Khan"})-[:ACTED_IN]->(m:Movie)
RETURN m.title, m.year, m.box_office_crore
ORDER BY m.year
```

> Try with: `"Shah Rukh Khan"`, `"Deepika Padukone"`, `"Ranveer Singh"`.

---

### 3.2 Read properties stored on the relationship itself

```cypher
MATCH (p:Person {name: "Shah Rukh Khan"})-[r:ACTED_IN]->(m:Movie)
RETURN m.title, r.character AS character_played, r.lead_role AS is_lead_role
ORDER BY m.year
```

**What's happening:**
- `[r:ACTED_IN]` — assigning a variable `r` to the relationship lets you access its properties.
- `r.character` and `r.lead_role` are properties stored directly on the ACTED_IN edge, not on any node.

---

### 3.3 Who directed which films

```cypher
MATCH (d:Person)-[:DIRECTED]->(m:Movie)
RETURN d.name AS Director, collect(m.title) AS Films
ORDER BY size(Films) DESC
```

**What's happening:**
- `collect(m.title)` gathers all movie titles into a list per director.
- `size(Films)` returns the length of the collected list — used here to sort most prolific directors first.

---

### 3.4 Both the director AND cast of a specific film in one query

```cypher
MATCH (director:Person)-[:DIRECTED]->(m:Movie {title: "3 Idiots"})<-[:ACTED_IN]-(actor:Person)
RETURN director.name AS Director, collect(actor.name) AS Cast
```

**What's happening:**
- Two relationship paths meet at the same Movie node `m`.
- `<-[:ACTED_IN]-` — the arrow points **into** `actor`, because ACTED_IN goes FROM actor TO movie. Reading against the arrow finds who pointed to this node.
- One query, two hops, both pieces of information returned together.

> Try with `"Devdas"`, `"Gully Boy"`, `"Bajirao Mastani"`.

---

### 3.5 Find the music composer for every film

```cypher
MATCH (c:Person)-[:COMPOSED_MUSIC_FOR]->(m:Movie)
RETURN c.name AS Composer, collect(m.title) AS Films
ORDER BY c.name
```

---

### 3.6 Which studio produced which films

```cypher
MATCH (ph:ProductionHouse)-[:PRODUCED]->(m:Movie)
RETURN ph.name AS Studio, m.title AS Film, m.year AS Year
ORDER BY ph.name, m.year
```

---

## Part 4 — Multi-hop Traversal

Graph databases are built for following paths across multiple nodes. No JOINs — you just extend the pattern.

### 4.1 Films produced by Yash Raj Films starring Shah Rukh Khan

```cypher
MATCH (ph:ProductionHouse {name: "Yash Raj Films"})
      -[:PRODUCED]->(m:Movie)
      <-[:ACTED_IN]-(p:Person {name: "Shah Rukh Khan"})
RETURN m.title, m.year, m.box_office_crore
ORDER BY m.year
```

**What's happening:**
- Three nodes, two relationships, one pattern. Neo4j traverses both edges simultaneously.
- Read it: *"A ProductionHouse named Yash Raj that PRODUCED a Movie that Shah Rukh Khan ACTED_IN."*
- In SQL this would require a JOIN across three tables.

---

### 4.2 Which composers have worked with Aamir Khan Productions?

```cypher
MATCH (ph:ProductionHouse {name: "Aamir Khan Productions"})
      -[:PRODUCED]->(m:Movie)
      <-[:COMPOSED_MUSIC_FOR]-(c:Person)
RETURN c.name AS Composer, collect(m.title) AS Films
```

**What's happening:**
- Path: ProductionHouse → Movie ← Person (composer).
- Both `->` and `<-` are used in the same pattern — the direction follows how each relationship was originally created.

---

### 4.3 Awards won by films that AR Rahman scored

```cypher
MATCH (ar:Person {name: "AR Rahman"})
      -[:COMPOSED_MUSIC_FOR]->(m:Movie)
      -[:WON]->(a:Award)
RETURN m.title AS Film, a.name AS Award, a.category AS Category
ORDER BY a.year
```

**What's happening:**
- A three-hop chain: Person → Movie → Award.
- This answers a question that would need two JOINs in SQL, using a single readable pattern in Cypher.

---

### 4.4 Actors directed by Rajkumar Hirani who also worked with AR Rahman

```cypher
MATCH (rk:Person {name: "Rajkumar Hirani"})-[:DIRECTED]->(m1:Movie)<-[:ACTED_IN]-(actor:Person)
MATCH (ar:Person {name: "AR Rahman"})-[:COMPOSED_MUSIC_FOR]->(m2:Movie)<-[:ACTED_IN]-(actor)
RETURN DISTINCT actor.name AS Actor,
       collect(DISTINCT m1.title) AS Hirani_Films,
       collect(DISTINCT m2.title) AS AR_Rahman_Films
```

**What's happening:**
- Two separate `MATCH` clauses. The variable `actor` appears in both — Neo4j only returns actors who satisfy BOTH patterns simultaneously.
- This is a **graph intersection** — finding nodes that exist at the junction of two independent paths.

---

### 4.5 Everyone connected to Dangal within 2 hops

```cypher
MATCH (m:Movie {title: "Dangal"})-[*1..2]-(connected)
RETURN DISTINCT labels(connected)[0] AS Type,
       coalesce(connected.name, connected.title) AS Entity
ORDER BY Type, Entity
```

**What's happening:**
- `[*1..2]` — variable-length path. Walk between 1 and 2 relationship steps from the start node, in **any direction**.
- This is called **variable-length traversal** and has no direct SQL equivalent.
- `coalesce(a, b)` — returns `a` if it is not null, otherwise `b`. Handles the fact that Person and ProductionHouse nodes have `name` while Movie nodes have `title`.

---

## Part 5 — Aggregation

### 5.1 Total box office per production house

```cypher
MATCH (ph:ProductionHouse)-[:PRODUCED]->(m:Movie)
WHERE m.box_office_crore > 0
RETURN ph.name AS Studio,
       count(m)                            AS Films,
       sum(m.box_office_crore)             AS Total_Crore,
       round(avg(m.box_office_crore))      AS Avg_Per_Film
ORDER BY Total_Crore DESC
```

**What's happening:**
- `count()`, `sum()`, `avg()` work like SQL aggregate functions.
- `round()` removes decimal places.
- Results are automatically grouped by `ph.name` — the one non-aggregated field in the RETURN.

---

### 5.2 Awards won per person

```cypher
MATCH (p:Person)-[:WON]->(a:Award)
RETURN p.name AS Person, count(a) AS Awards_Won
ORDER BY Awards_Won DESC
```

---

### 5.3 Most prolific actors by film count

```cypher
MATCH (p:Person)-[:ACTED_IN]->(m:Movie)
RETURN p.name AS Actor, count(m) AS Films_Acted_In
ORDER BY Films_Acted_In DESC
LIMIT 10
```

---

### 5.4 Average box office by genre

```cypher
MATCH (m:Movie)
WHERE m.box_office_crore > 0
RETURN m.genre                         AS Genre,
       count(m)                         AS Film_Count,
       round(avg(m.box_office_crore))   AS Avg_Box_Office_Crore
ORDER BY Avg_Box_Office_Crore DESC
```

---

### 5.5 The WITH clause — filtering after aggregation

`WHERE` can only filter on raw properties. To filter on the result of an aggregation (like "directors with more than 2 films"), use `WITH`:

```cypher
MATCH (d:Person)-[:DIRECTED]->(m:Movie)
WITH d, count(m) AS film_count
WHERE film_count >= 2
RETURN d.name AS Director, film_count
ORDER BY film_count DESC
```

**What's happening:**
- `WITH` is like a pipe — it passes results from the first part of the query into the second.
- `WHERE film_count >= 2` filters on the aggregated value, which was computed in the `WITH`.
- Think of `WITH` as the Cypher equivalent of a SQL subquery or CTE.

---

## Part 6 — Graph-Specific Features

These have no direct SQL equivalent. They are unique to graph databases.

### 6.1 Shortest path between two people

```cypher
MATCH path = shortestPath(
    (a:Person {name: "Shah Rukh Khan"})-[*]-(b:Person {name: "AR Rahman"})
)
RETURN [n IN nodes(path) | coalesce(n.name, n.title)] AS Path,
       length(path) AS Hops
```

**What's happening:**
- `shortestPath(...)` is a built-in Neo4j algorithm. It finds the minimum-hop route between two nodes.
- `[*]` — any relationship type, any direction, any number of hops.
- `nodes(path)` — returns the list of nodes along the path.
- `[n IN nodes(path) | coalesce(n.name, n.title)]` — a **list comprehension**: for each node in the path, extract its name or title.

> Try other pairs: `"Deepika Padukone"` → `"Rajkumar Hirani"`, `"Salman Khan"` → `"Zoya Akhtar"`.

---

### 6.2 Directors who also acted in their own films

```cypher
MATCH (p:Person)-[:DIRECTED]->(m:Movie)<-[:ACTED_IN]-(p)
RETURN p.name AS Person, collect(m.title) AS Self_Directed_Films
```

**What's happening:**
- The same variable `p` is used at **both ends** of the pattern.
- This means "find a person who DIRECTED a movie AND ACTED_IN that same movie."
- In SQL this would require a self-join. In Cypher it is a natural part of the pattern.

---

### 6.3 Variable-length paths — everyone reachable from Aamir Khan in 2 hops

```cypher
MATCH (start:Person {name: "Aamir Khan"})-[*1..2]->(neighbor)
RETURN DISTINCT labels(neighbor)[0] AS Type,
       coalesce(neighbor.name, neighbor.title) AS Entity
ORDER BY Type, Entity
```

**What's happening:**
- `[*1..2]` — follow between 1 and 2 relationship hops.
- This returns every node reachable from Aamir Khan by following directed relationships outward.
- Compare `[*1..1]` (direct connections only) vs `[*1..3]` (3-hop neighbourhood).

---

### 6.4 Find the most connected nodes (high-degree hubs)

```cypher
MATCH (n)
WITH n, size([(n)--() | 1]) AS degree
WHERE degree > 5
RETURN labels(n)[0] AS Type,
       coalesce(n.name, n.title) AS Entity,
       degree
ORDER BY degree DESC
```

**What's happening:**
- `(n)--()` matches any relationship in either direction.
- `[(n)--() | 1]` is a **pattern comprehension** — it creates a list of `1` for every match. `size()` counts the list.
- This efficiently counts the total degree (in + out connections) of each node.

---

### 6.5 All relationships between two specific nodes

```cypher
MATCH (srk:Person {name: "Shah Rukh Khan"})-[r]-(m)
RETURN type(r) AS Relationship,
       coalesce(m.name, m.title) AS ConnectedTo,
       labels(m)[0] AS ConnectedType
ORDER BY type(r)
```

**What's happening:**
- `[r]` without a type label matches **any** relationship.
- `type(r)` returns the relationship type as a string.
- This is useful for exploring what connections a node has without already knowing the relationship types.

---

## Part 7 — Writing and Modifying Data

### 7.1 CREATE — always makes a new node

```cypher
CREATE (m:Movie {
    title: "Dil Dhadakne Do",
    year: 2015,
    genre: "Drama",
    box_office_crore: 108.0,
    description: "A wealthy Indian family goes on a cruise and family secrets unravel."
})
RETURN m
```

**What's happening:**
- `CREATE` creates a new node unconditionally — even if a node with the same properties exists, it creates another one.
- Use `MERGE` (below) when you want to avoid duplicates.

---

### 7.2 MERGE — the safe upsert (create or match)

```cypher
MERGE (p:Person {name: "Zoya Akhtar"})
ON CREATE SET p.born = 1972, p.profession = "Director", p.hometown = "Mumbai"
ON MATCH  SET p.profession = "Director-Producer"
RETURN p
```

**What's happening:**
- `MERGE` checks first: does a Person named "Zoya Akhtar" already exist?
  - **If no:** creates a new node and runs `ON CREATE SET`.
  - **If yes:** finds the existing node and runs `ON MATCH SET`.
- This is the safe, idempotent way to write data. The loader in this project uses `MERGE` everywhere so it can be re-run without creating duplicates.

---

### 7.3 Add a relationship between two existing nodes

```cypher
MATCH (p:Person {name: "Zoya Akhtar"})
MATCH (m:Movie  {title: "Dil Dhadakne Do"})
MERGE (p)-[:DIRECTED]->(m)
RETURN p, m
```

**What's happening:**
- Always `MATCH` the nodes first before connecting them.
- `MERGE` on the relationship prevents creating a duplicate edge if the relationship already exists.
- If either MATCH returns nothing (node not found), the MERGE is silently skipped.

---

### 7.4 Update a property on an existing node

```cypher
MATCH (m:Movie {title: "Dangal"})
SET m.streaming_platform = "Disney+ Hotstar",
    m.language = "Hindi"
RETURN m.title, m.streaming_platform, m.language
```

**What's happening:**
- `SET` adds or updates one or more properties.
- If `streaming_platform` did not exist before, it is created.
- To update many properties at once: `SET m += {key: value, key2: value2}` (the `+=` merges without overwriting existing properties not in the map).

---

### 7.5 Remove a property

```cypher
MATCH (m:Movie {title: "Dangal"})
REMOVE m.streaming_platform
RETURN m
```

**What's happening:**
- `REMOVE` deletes a property from a node. The property key is gone — it is not set to null.
- `REMOVE` also works on labels: `REMOVE n:OldLabel`.

---

### 7.6 Delete a node and all its relationships

```cypher
MATCH (m:Movie {title: "Dil Dhadakne Do"})
DETACH DELETE m
```

**What's happening:**
- `DELETE` alone fails if the node has any relationships.
- `DETACH DELETE` removes all relationships connected to the node first, then deletes the node itself.
- **This is permanent.** Neo4j has no ROLLBACK by default. Double-check your MATCH before deleting.

---

## Part 8 — Challenge Queries

Write these yourself before expanding the answers.

**Challenge 1**  
Find all films where the same person both directed and acted. Return their name and the film(s).

**Challenge 2**  
List every actor and the total combined box office of all films they acted in. Order by highest total.

**Challenge 3**  
Find the music composer who has worked with the most distinct production houses. Trace the path: Composer → COMPOSED_MUSIC_FOR → Movie ← PRODUCED — ProductionHouse.

**Challenge 4**  
Find all National Award winning films and return the film title, year, and all actors who appeared in it.

**Challenge 5**  
Who is the person with the highest combined degree (most total relationships of any type)?

---

<details>
<summary>Challenge Answers — expand after trying</summary>

**Challenge 1:**
```cypher
MATCH (p:Person)-[:DIRECTED]->(m:Movie)<-[:ACTED_IN]-(p)
RETURN p.name AS Person, collect(m.title) AS Films
```

**Challenge 2:**
```cypher
MATCH (p:Person)-[:ACTED_IN]->(m:Movie)
WHERE m.box_office_crore > 0
RETURN p.name AS Actor, sum(m.box_office_crore) AS Total_Box_Office_Crore
ORDER BY Total_Box_Office_Crore DESC
```

**Challenge 3:**
```cypher
MATCH (c:Person)-[:COMPOSED_MUSIC_FOR]->(m:Movie)<-[:PRODUCED]-(ph:ProductionHouse)
RETURN c.name AS Composer, count(DISTINCT ph) AS Distinct_Studios
ORDER BY Distinct_Studios DESC
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
MATCH (n)
WITH n, size([(n)--() | 1]) AS degree
RETURN labels(n)[0] AS Type,
       coalesce(n.name, n.title) AS Entity,
       degree
ORDER BY degree DESC
LIMIT 10
```

</details>

---

## Cypher Cheat Sheet

```
─────────────────────────────────────────────────────────────────
READING DATA
─────────────────────────────────────────────────────────────────
MATCH (n:Label)                          -- find nodes by label
MATCH (n:Label {prop: "value"})          -- inline property filter
MATCH (n:Label) WHERE n.prop > 100       -- WHERE filter
MATCH (a)-[:REL]->(b)                    -- directional relationship
MATCH (a)-[:REL]-(b)                     -- any direction
MATCH (a)-[*1..3]->(b)                   -- variable-length path
MATCH path = shortestPath((a)-[*]-(b))   -- shortest path algorithm
RETURN n, n.prop, labels(n), type(r)
ORDER BY n.prop DESC
LIMIT 10
SKIP 20                                  -- pagination

─────────────────────────────────────────────────────────────────
AGGREGATION
─────────────────────────────────────────────────────────────────
count(n)           -- count rows
sum(n.prop)        -- sum numeric values
avg(n.prop)        -- average
min(n.prop)        -- minimum
max(n.prop)        -- maximum
collect(n.prop)    -- gather into a list
DISTINCT           -- deduplicate

─────────────────────────────────────────────────────────────────
FILTERING AFTER AGGREGATION
─────────────────────────────────────────────────────────────────
MATCH (d)-[:DIRECTED]->(m)
WITH d, count(m) AS films
WHERE films > 2
RETURN d.name, films

─────────────────────────────────────────────────────────────────
WRITING DATA
─────────────────────────────────────────────────────────────────
CREATE (n:Label {prop: value})           -- always creates new
MERGE  (n:Label {prop: value})           -- create or match
  ON CREATE SET n.x = 1
  ON MATCH  SET n.x = 2
SET    n.prop = value                    -- update property
SET    n += {prop: value, prop2: val2}   -- batch update
REMOVE n.prop                            -- delete a property
REMOVE n:Label                           -- remove a label
DELETE n                                 -- delete (fails if has rels)
DETACH DELETE n                          -- delete + all its rels

─────────────────────────────────────────────────────────────────
USEFUL FUNCTIONS
─────────────────────────────────────────────────────────────────
labels(n)                    -- list of node labels
type(r)                      -- relationship type as string
coalesce(a, b, c)            -- first non-null value
toLower(str) / toUpper(str)  -- string case
toString(n) / toInteger(s)   -- type conversion
size(list)                   -- length of a list
nodes(path)                  -- list of nodes in a path
relationships(path)          -- list of rels in a path
length(path)                 -- number of hops in a path
round(n) / ceil(n) / floor(n)-- numeric rounding
```

---

*Open Neo4j Browser at http://localhost:7474 to run all queries.*
*Username: `neo4j` — Password: `bollywood2024!`*

---
**Codeverra** — A learning platform to master coding, data science, DSA, and AI. Learn more at: https://codeverra.com
