# src/data/bollywood_data.py
# ─────────────────────────────────────────────────────────────────────────────
# Complete dataset for the Bollywood Knowledge Graph.
#
# This module defines all entities and relationships that will be loaded into
# Neo4j. The data covers Hindi cinema from 1995–2024, including iconic films,
# major actors, celebrated directors, legendary music composers, production
# houses, and a selection of Filmfare and National Awards.
#
# Ontology:
#   Nodes:  Person, Movie, ProductionHouse, Award, MusicAlbum
#   Edges:  ACTED_IN, DIRECTED, COMPOSED_MUSIC_FOR, PRODUCED, WON,
#           WORKED_WITH, RELEASED_BY
# ─────────────────────────────────────────────────────────────────────────────


# ─────────────────────────────────────────────────────────────────────────────
# PEOPLE
# ─────────────────────────────────────────────────────────────────────────────

PEOPLE = [
    # Actors
    {"name": "Shah Rukh Khan",      "born": 1965, "profession": "Actor",           "hometown": "Delhi"},
    {"name": "Aamir Khan",           "born": 1965, "profession": "Actor-Director",  "hometown": "Mumbai"},
    {"name": "Salman Khan",          "born": 1965, "profession": "Actor",           "hometown": "Mumbai"},
    {"name": "Amitabh Bachchan",    "born": 1942, "profession": "Actor",           "hometown": "Allahabad"},
    {"name": "Hrithik Roshan",       "born": 1974, "profession": "Actor",           "hometown": "Mumbai"},
    {"name": "Ranveer Singh",        "born": 1985, "profession": "Actor",           "hometown": "Mumbai"},
    {"name": "Ranbir Kapoor",        "born": 1982, "profession": "Actor",           "hometown": "Mumbai"},
    {"name": "Deepika Padukone",    "born": 1986, "profession": "Actor",           "hometown": "Bengaluru"},
    {"name": "Alia Bhatt",           "born": 1993, "profession": "Actor",           "hometown": "Mumbai"},
    {"name": "Priyanka Chopra",     "born": 1982, "profession": "Actor",           "hometown": "Jamshedpur"},
    {"name": "Kajol",                "born": 1974, "profession": "Actor",           "hometown": "Mumbai"},
    {"name": "Madhuri Dixit",        "born": 1967, "profession": "Actor",           "hometown": "Pune"},
    {"name": "Aishwarya Rai",       "born": 1973, "profession": "Actor",           "hometown": "Mangaluru"},
    {"name": "Taapsee Pannu",       "born": 1987, "profession": "Actor",           "hometown": "Delhi"},
    {"name": "Nawazuddin Siddiqui", "born": 1974, "profession": "Actor",           "hometown": "Budhana, UP"},
    {"name": "Irrfan Khan",          "born": 1967, "profession": "Actor",           "hometown": "Jaipur"},
    {"name": "Sunny Deol",           "born": 1956, "profession": "Actor",           "hometown": "Sahnewal, Punjab"},
    {"name": "Rani Mukerji",         "born": 1978, "profession": "Actor",           "hometown": "Kolkata"},

    # Directors
    {"name": "Rajkumar Hirani",     "born": 1962, "profession": "Director",        "hometown": "Nagpur"},
    {"name": "Zoya Akhtar",          "born": 1972, "profession": "Director",        "hometown": "Mumbai"},
    {"name": "Sanjay Leela Bhansali","born": 1963, "profession": "Director",        "hometown": "Mumbai"},
    {"name": "Karan Johar",          "born": 1972, "profession": "Director-Producer","hometown": "Mumbai"},
    {"name": "Aditya Chopra",       "born": 1971, "profession": "Director-Producer","hometown": "Mumbai"},
    {"name": "Farhan Akhtar",        "born": 1974, "profession": "Director-Actor",  "hometown": "Mumbai"},
    {"name": "Nitesh Tiwari",        "born": 1973, "profession": "Director",        "hometown": "Itarsi, MP"},
    {"name": "Ashutosh Gowariker",  "born": 1964, "profession": "Director",        "hometown": "Mumbai"},
    {"name": "Imtiaz Ali",           "born": 1971, "profession": "Director",        "hometown": "Jamshedpur"},
    {"name": "Vikramaditya Motwane","born": 1977, "profession": "Director",        "hometown": "Mumbai"},
    {"name": "Kabir Khan",           "born": 1971, "profession": "Director",        "hometown": "Delhi"},

    # Music composers
    {"name": "AR Rahman",            "born": 1967, "profession": "Music Composer",  "hometown": "Chennai"},
    {"name": "Shankar-Ehsaan-Loy",  "born": 1965, "profession": "Music Composer",  "hometown": "Mumbai"},
    {"name": "Pritam Chakraborty",  "born": 1971, "profession": "Music Composer",  "hometown": "Kolkata"},
    {"name": "Vishal-Shekhar",      "born": 1977, "profession": "Music Composer",  "hometown": "Mumbai"},
    {"name": "Amit Trivedi",         "born": 1979, "profession": "Music Composer",  "hometown": "Varanasi"},
]


# ─────────────────────────────────────────────────────────────────────────────
# PRODUCTION HOUSES
# ─────────────────────────────────────────────────────────────────────────────

PRODUCTION_HOUSES = [
    {"name": "Yash Raj Films",          "founded": 1970, "founder": "Yash Chopra",     "hq": "Mumbai"},
    {"name": "Dharma Productions",      "founded": 1976, "founder": "Yash Johar",      "hq": "Mumbai"},
    {"name": "Excel Entertainment",     "founded": 2001, "founder": "Farhan Akhtar",   "hq": "Mumbai"},
    {"name": "Rajshri Productions",     "founded": 1947, "founder": "Tarachand Barjatya","hq": "Mumbai"},
    {"name": "Vinod Chopra Films",      "founded": 1987, "founder": "Vidhu Vinod Chopra","hq": "Mumbai"},
    {"name": "Aamir Khan Productions",  "founded": 1999, "founder": "Aamir Khan",       "hq": "Mumbai"},
    {"name": "Red Chillies Entertainment","founded": 2002,"founder": "Shah Rukh Khan",  "hq": "Mumbai"},
    {"name": "Phantom Films",           "founded": 2011, "founder": "Vikramaditya Motwane","hq": "Mumbai"},
    {"name": "Nadiadwala Grandson",     "founded": 1948, "founder": "S.N. Nadiadwala",  "hq": "Mumbai"},
    {"name": "T-Series Films",          "founded": 1983, "founder": "Gulshan Kumar",    "hq": "Noida"},
]


# ─────────────────────────────────────────────────────────────────────────────
# MOVIES
# ─────────────────────────────────────────────────────────────────────────────

MOVIES = [
    {
        "title": "Dilwale Dulhania Le Jayenge",
        "year": 1995, "genre": "Romance", "language": "Hindi",
        "box_office_crore": 102.0,
        "description": "A young man and woman fall in love on a trip to Europe, but must overcome family opposition to be together."
    },
    {
        "title": "Lagaan",
        "year": 2001, "genre": "Historical Drama", "language": "Hindi",
        "box_office_crore": 65.0,
        "description": "Villagers in 19th-century India challenge British colonisers to a cricket match to avoid paying taxes."
    },
    {
        "title": "Dil Chahta Hai",
        "year": 2001, "genre": "Coming-of-age Drama", "language": "Hindi",
        "box_office_crore": 34.0,
        "description": "Three inseparable friends navigate love, career and life after college."
    },
    {
        "title": "Devdas",
        "year": 2002, "genre": "Tragedy Romance", "language": "Hindi",
        "box_office_crore": 52.0,
        "description": "A young man is unable to marry his childhood love and descends into alcoholism."
    },
    {
        "title": "Rang De Basanti",
        "year": 2006, "genre": "Drama", "language": "Hindi",
        "box_office_crore": 95.0,
        "description": "A British filmmaker casts Indian youth to play freedom fighters and the parallels transform their lives."
    },
    {
        "title": "Taare Zameen Par",
        "year": 2007, "genre": "Drama", "language": "Hindi",
        "box_office_crore": 93.0,
        "description": "A dyslexic child's life is transformed when a caring teacher recognises his condition and nurtures his talent."
    },
    {
        "title": "Om Shanti Om",
        "year": 2007, "genre": "Drama", "language": "Hindi",
        "box_office_crore": 201.0,
        "description": "A junior artist falls in love with a film star in the 1970s and is reborn to take revenge in the 2000s."
    },
    {
        "title": "Ghajini",
        "year": 2008, "genre": "Action Thriller", "language": "Hindi",
        "box_office_crore": 243.0,
        "description": "A man with short-term memory loss hunts for the killer of his girlfriend."
    },
    {
        "title": "3 Idiots",
        "year": 2009, "genre": "Comedy Drama", "language": "Hindi",
        "box_office_crore": 460.0,
        "description": "Two friends search for their long-lost third companion while reliving their college days and the philosophy of their inspiring teacher."
    },
    {
        "title": "My Name Is Khan",
        "year": 2010, "genre": "Drama", "language": "Hindi",
        "box_office_crore": 200.0,
        "description": "A Muslim man with Asperger's syndrome embarks on a journey to meet the US President after post-9/11 discrimination."
    },
    {
        "title": "Zindagi Na Milegi Dobara",
        "year": 2011, "genre": "Adventure Drama", "language": "Hindi",
        "box_office_crore": 153.0,
        "description": "Three childhood friends go on a road trip through Spain that changes their perspectives on life and love."
    },
    {
        "title": "Barfi!",
        "year": 2012, "genre": "Comedy Drama", "language": "Hindi",
        "box_office_crore": 120.0,
        "description": "A deaf-mute man falls in love with two women in 1970s Darjeeling."
    },
    {
        "title": "Gangs of Wasseypur",
        "year": 2012, "genre": "Crime Drama", "language": "Hindi",
        "box_office_crore": 56.0,
        "description": "A multi-generational saga of coal mine mafia, revenge, and power in Dhanbad."
    },
    {
        "title": "Chennai Express",
        "year": 2013, "genre": "Action Comedy", "language": "Hindi",
        "box_office_crore": 423.0,
        "description": "A Mumbai man on a train to Rameswaram gets entangled with a Tamil girl and her gangster father."
    },
    {
        "title": "PK",
        "year": 2014, "genre": "Satire Comedy", "language": "Hindi",
        "box_office_crore": 832.0,
        "description": "An alien stranded on Earth questions religious practices while searching for his remote control to return home."
    },
    {
        "title": "Bajrangi Bhaijaan",
        "year": 2015, "genre": "Drama", "language": "Hindi",
        "box_office_crore": 969.0,
        "description": "A devoted devotee of Hanuman helps a mute Pakistani girl return to her family across the border."
    },
    {
        "title": "Bajirao Mastani",
        "year": 2015, "genre": "Historical Romance", "language": "Hindi",
        "box_office_crore": 355.0,
        "description": "The love story of Maratha warrior Peshwa Bajirao and his second wife Mastani."
    },
    {
        "title": "Dangal",
        "year": 2016, "genre": "Sports Biopic", "language": "Hindi",
        "box_office_crore": 2024.0,
        "description": "The real story of Mahavir Singh Phogat who trains his daughters to become world-class wrestlers."
    },
    {
        "title": "Raees",
        "year": 2017, "genre": "Crime Drama", "language": "Hindi",
        "box_office_crore": 193.0,
        "description": "A bootlegger in Gujarat rises to power while being chased by a relentless police officer."
    },
    {
        "title": "Gully Boy",
        "year": 2019, "genre": "Musical Drama", "language": "Hindi",
        "box_office_crore": 247.0,
        "description": "A young man from the Dharavi slums discovers hip-hop as a vehicle for expressing his struggles and dreams."
    },
    {
        "title": "War",
        "year": 2019, "genre": "Action Thriller", "language": "Hindi",
        "box_office_crore": 475.0,
        "description": "An Indian soldier is assigned to eliminate his former mentor who has gone rogue."
    },
    {
        "title": "Brahmastra Part One: Shiva",
        "year": 2022, "genre": "Fantasy Action", "language": "Hindi",
        "box_office_crore": 431.0,
        "description": "A young man discovers he has a mystical connection to fire as he searches for an ancient superweapon."
    },
    {
        "title": "Pathaan",
        "year": 2023, "genre": "Action Spy", "language": "Hindi",
        "box_office_crore": 1050.0,
        "description": "An exiled Indian spy must stop a private army from launching a devastating attack on India."
    },
    {
        "title": "Jawan",
        "year": 2023, "genre": "Action Thriller", "language": "Hindi",
        "box_office_crore": 1160.0,
        "description": "A prison warden with a dark past recruits women inmates to pull off a series of heists to expose corrupt officials."
    },
    {
        "title": "Animal",
        "year": 2023, "genre": "Action Crime", "language": "Hindi",
        "box_office_crore": 900.0,
        "description": "A man's obsessive devotion to his estranged father spirals into violence when his father is targeted."
    },
    {
        "title": "Dhurandhar",
        "year": 2025, "genre": "Espionage Thriller", "language": "Hindi",
        "box_office_crore": 0.0,
        "description": "An intelligence operative navigates a complex web of deception across international borders."
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# AWARDS
# ─────────────────────────────────────────────────────────────────────────────

AWARDS = [
    {"name": "Filmfare Best Film 1996",         "category": "Filmfare",  "year": 1996},
    {"name": "Filmfare Best Film 2002",         "category": "Filmfare",  "year": 2002},
    {"name": "Filmfare Best Film 2009",         "category": "Filmfare",  "year": 2009},
    {"name": "Filmfare Best Film 2010",         "category": "Filmfare",  "year": 2010},
    {"name": "Filmfare Best Film 2017",         "category": "Filmfare",  "year": 2017},
    {"name": "Filmfare Best Film 2020",         "category": "Filmfare",  "year": 2020},
    {"name": "National Award Best Film 2001",  "category": "National",  "year": 2001},
    {"name": "National Award Best Film 2002",  "category": "National",  "year": 2002},
    {"name": "National Award Best Film 2007",  "category": "National",  "year": 2007},
    {"name": "National Award Best Film 2017",  "category": "National",  "year": 2017},
    {"name": "Filmfare Best Actor SRK 1996",   "category": "Filmfare",  "year": 1996},
    {"name": "Filmfare Best Actor SRK 2005",   "category": "Filmfare",  "year": 2005},
    {"name": "Filmfare Best Actor Aamir 2009", "category": "Filmfare",  "year": 2009},
    {"name": "Filmfare Best Actor Hrithik 2020","category": "Filmfare", "year": 2020},
    {"name": "Filmfare Best Actor Ranveer 2016","category": "Filmfare", "year": 2016},
    {"name": "Filmfare Best Actress Deepika 2016","category":"Filmfare","year": 2016},
    {"name": "Filmfare Best Actress Alia 2020","category": "Filmfare",  "year": 2020},
    {"name": "Filmfare Best Director RKH 2010","category": "Filmfare",  "year": 2010},
    {"name": "Filmfare Best Director Zoya 2012","category":"Filmfare",  "year": 2012},
    {"name": "National Award Best Music AR Rahman 2002","category":"National","year":2002},
    {"name": "Oscar Best Original Score AR Rahman 2009","category":"Oscar","year":2009},
    {"name": "National Award Best Actor Nawaz 2013","category":"National","year":2013},
    {"name": "Padma Shri Shah Rukh Khan",       "category": "Civilian", "year": 2005},
    {"name": "Padma Bhushan Amitabh Bachchan",  "category": "Civilian", "year": 2015},
    {"name": "Padma Vibhushan Amitabh Bachchan","category": "Civilian", "year": 2024},
]


# ─────────────────────────────────────────────────────────────────────────────
# RELATIONSHIPS
# ─────────────────────────────────────────────────────────────────────────────

# (actor, movie, character_name, lead_role: bool)
ACTED_IN = [
    ("Shah Rukh Khan",    "Dilwale Dulhania Le Jayenge", "Raj Malhotra",   True),
    ("Kajol",             "Dilwale Dulhania Le Jayenge", "Simran Singh",   True),
    ("Aamir Khan",        "Lagaan",                      "Bhuvan",         True),
    ("Aamir Khan",        "Dil Chahta Hai",               "Akash",          True),
    ("Aamir Khan",        "Taare Zameen Par",             "Ram Shankar Nikumbh", True),
    ("Aamir Khan",        "Ghajini",                     "Sanjay Singhania", True),
    ("Aamir Khan",        "3 Idiots",                    "Rancho",         True),
    ("Aamir Khan",        "PK",                          "PK",             True),
    ("Aamir Khan",        "Dangal",                      "Mahavir Singh Phogat", True),
    ("Shah Rukh Khan",    "Om Shanti Om",                "Om Kapoor / Om Prakash Makhija", True),
    ("Deepika Padukone",  "Om Shanti Om",                "Shantipriya / Sandy", True),
    ("Shah Rukh Khan",    "My Name Is Khan",             "Rizwan Khan",    True),
    ("Shah Rukh Khan",    "Chennai Express",             "Rahul Mithaiwala", True),
    ("Shah Rukh Khan",    "Raees",                       "Raees Alam",     True),
    ("Shah Rukh Khan",    "Pathaan",                     "Pathaan",        True),
    ("Shah Rukh Khan",    "Jawan",                       "Azad / Vikram Rathore", True),
    ("Deepika Padukone",  "Pathaan",                     "Rubina Mohsin",  True),
    ("Salman Khan",       "Bajrangi Bhaijaan",           "Pawan Kumar Chaturvedi", True),
    ("Hrithik Roshan",    "War",                         "Khalid",         True),
    ("Tiger Shroff",      "War",                         "Kabir",          True),
    ("Ranveer Singh",     "Gully Boy",                   "Murad Ahmed",    True),
    ("Alia Bhatt",        "Gully Boy",                   "Safeena",        True),
    ("Ranveer Singh",     "Bajirao Mastani",             "Peshwa Bajirao", True),
    ("Deepika Padukone",  "Bajirao Mastani",             "Mastani",        True),
    ("Ranbir Kapoor",     "Barfi!",                      "Barfi",          True),
    ("Priyanka Chopra",   "Barfi!",                      "Shruti",         True),
    ("Ranbir Kapoor",     "Brahmastra Part One: Shiva",  "Shiva",          True),
    ("Alia Bhatt",        "Brahmastra Part One: Shiva",  "Isha",           True),
    ("Amitabh Bachchan",  "Brahmastra Part One: Shiva",  "Guru",          False),
    ("Amitabh Bachchan",  "Devdas",                      "Chunilal",      False),
    ("Shah Rukh Khan",    "Devdas",                      "Devdas Mukherjee", True),
    ("Aishwarya Rai",     "Devdas",                      "Paro",           True),
    ("Madhuri Dixit",     "Devdas",                      "Chandramukhi",   True),
    ("Hrithik Roshan",    "Zindagi Na Milegi Dobara",    "Arjun Saluja",   True),
    ("Farhan Akhtar",     "Zindagi Na Milegi Dobara",    "Imraan",         True),
    ("Irrfan Khan",       "Rang De Basanti",             "DJ",             True),
    ("Nawazuddin Siddiqui","Gangs of Wasseypur",         "Faizal Khan",    True),
    ("Ranbir Kapoor",     "Animal",                      "Ranvijay Singh", True),
    ("Taapsee Pannu",     "Raees",                       "Aasiya",         True),
]

# (director, movie)
DIRECTED = [
    ("Aditya Chopra",       "Dilwale Dulhania Le Jayenge"),
    ("Ashutosh Gowariker",  "Lagaan"),
    ("Farhan Akhtar",       "Dil Chahta Hai"),
    ("Sanjay Leela Bhansali","Devdas"),
    ("Sanjay Leela Bhansali","Bajirao Mastani"),
    ("Rakeysh Omprakash Mehra", "Rang De Basanti"),  # to be added to PEOPLE if needed
    ("Aamir Khan",           "Taare Zameen Par"),
    ("Farah Khan",           "Om Shanti Om"),
    ("A.R. Murugadoss",      "Ghajini"),
    ("Rajkumar Hirani",      "3 Idiots"),
    ("Rajkumar Hirani",      "PK"),
    ("Karan Johar",          "My Name Is Khan"),
    ("Rohit Shetty",         "Chennai Express"),
    ("Rahul Dholakia",       "Raees"),
    ("Zoya Akhtar",          "Zindagi Na Milegi Dobara"),
    ("Zoya Akhtar",          "Gully Boy"),
    ("Anurag Kashyap",       "Gangs of Wasseypur"),
    ("Anurag Basu",          "Barfi!"),
    ("Kabir Khan",           "Bajrangi Bhaijaan"),
    ("Nitesh Tiwari",        "Dangal"),
    ("Siddharth Anand",      "War"),
    ("Siddharth Anand",      "Pathaan"),
    ("Ayan Mukerji",         "Brahmastra Part One: Shiva"),
    ("Siddharth Anand",      "Jawan"),
    ("Sandeep Reddy Vanga",  "Animal"),
    ("Aditya Dhar",          "Dhurandhar"),
]

# (composer, movie)
COMPOSED_MUSIC_FOR = [
    ("AR Rahman",           "Lagaan"),
    ("AR Rahman",           "Rang De Basanti"),
    ("AR Rahman",           "Ghajini"),
    ("Shankar-Ehsaan-Loy",  "Dil Chahta Hai"),
    ("Shankar-Ehsaan-Loy",  "Zindagi Na Milegi Dobara"),
    ("Shankar-Ehsaan-Loy",  "My Name Is Khan"),
    ("Shankar-Ehsaan-Loy",  "Don"),
    ("Ismail Darbar",       "Devdas"),
    ("Ismail Darbar",       "Bajirao Mastani"),
    ("Vishal-Shekhar",      "Om Shanti Om"),
    ("Vishal-Shekhar",      "Pathaan"),
    ("Vishal-Shekhar",      "Jawan"),
    ("Pritam Chakraborty",  "Barfi!"),
    ("Pritam Chakraborty",  "Brahmastra Part One: Shiva"),
    ("Pritam Chakraborty",  "Chennai Express"),
    ("Amit Trivedi",        "Gully Boy"),
    ("Sandesh Shandilya",   "3 Idiots"),
    ("Pritam Chakraborty",  "3 Idiots"),
]

# (production_house, movie)
PRODUCED_BY = [
    ("Yash Raj Films",           "Dilwale Dulhania Le Jayenge"),
    ("Yash Raj Films",           "War"),
    ("Yash Raj Films",           "Pathaan"),
    ("Yash Raj Films",           "Jawan"),
    ("Dharma Productions",       "My Name Is Khan"),
    ("Dharma Productions",       "Brahmastra Part One: Shiva"),
    ("Excel Entertainment",      "Dil Chahta Hai"),
    ("Excel Entertainment",      "Zindagi Na Milegi Dobara"),
    ("Excel Entertainment",      "Gully Boy"),
    ("Excel Entertainment",      "Gangster"),
    ("Aamir Khan Productions",   "Lagaan"),
    ("Aamir Khan Productions",   "Taare Zameen Par"),
    ("Aamir Khan Productions",   "3 Idiots"),
    ("Aamir Khan Productions",   "PK"),
    ("Aamir Khan Productions",   "Dangal"),
    ("Vinod Chopra Films",       "3 Idiots"),
    ("Red Chillies Entertainment","Om Shanti Om"),
    ("Nadiadwala Grandson",      "Chennai Express"),
    ("Nadiadwala Grandson",      "Bajrangi Bhaijaan"),
    ("T-Series Films",           "Bajrao Mastani"),
]

# (entity_name, entity_type, award_name)
# entity_type is "person" or "movie"
WON_AWARDS = [
    ("Dilwale Dulhania Le Jayenge", "movie",  "Filmfare Best Film 1996"),
    ("Devdas",                      "movie",  "Filmfare Best Film 2002"),
    ("Lagaan",                      "movie",  "National Award Best Film 2002"),
    ("Rang De Basanti",             "movie",  "National Award Best Film 2007"),
    ("3 Idiots",                    "movie",  "Filmfare Best Film 2010"),
    ("Dangal",                      "movie",  "National Award Best Film 2017"),
    ("Gully Boy",                   "movie",  "Filmfare Best Film 2020"),
    ("Shah Rukh Khan",              "person", "Filmfare Best Actor SRK 1996"),
    ("Shah Rukh Khan",              "person", "Filmfare Best Actor SRK 2005"),
    ("Shah Rukh Khan",              "person", "Padma Shri Shah Rukh Khan"),
    ("Aamir Khan",                  "person", "Filmfare Best Actor Aamir 2009"),
    ("Hrithik Roshan",              "person", "Filmfare Best Actor Hrithik 2020"),
    ("Ranveer Singh",               "person", "Filmfare Best Actor Ranveer 2016"),
    ("Deepika Padukone",            "person", "Filmfare Best Actress Deepika 2016"),
    ("Alia Bhatt",                  "person", "Filmfare Best Actress Alia 2020"),
    ("Rajkumar Hirani",             "person", "Filmfare Best Director RKH 2010"),
    ("Zoya Akhtar",                 "person", "Filmfare Best Director Zoya 2012"),
    ("AR Rahman",                   "person", "National Award Best Music AR Rahman 2002"),
    ("AR Rahman",                   "person", "Oscar Best Original Score AR Rahman 2009"),
    ("Nawazuddin Siddiqui",         "person", "National Award Best Actor Nawaz 2013"),
    ("Amitabh Bachchan",            "person", "Padma Bhushan Amitabh Bachchan"),
    ("Amitabh Bachchan",            "person", "Padma Vibhushan Amitabh Bachchan"),
]
