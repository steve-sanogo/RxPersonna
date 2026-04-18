# Character Interaction Network Extraction from the *Foundation* Corpus

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![NLP](https://img.shields.io/badge/NLP-SpaCy%20%7C%20Flair-green)
![Hybrid AI](https://img.shields.io/badge/Approach-Hybrid%20AI-orange)
![Score](https://img.shields.io/badge/F1--Score-0.66-brightgreen)
[![Live Demo](https://img.shields.io/badge/Live%20Demo-foundation--graph.pages.dev-cyan?logo=cloudflare)](https://53c4d986.foundation-graph.pages.dev/)

## Project Overview

This project investigates how **structured social interaction networks** can be automatically extracted from literary texts using a **hybrid Natural Language Processing pipeline** combining neural models and symbolic rules.

The objective is to transform raw narrative text from Isaac Asimov's *Foundation* corpus into **signed knowledge graphs of character interactions**, where edges represent semantic relations such as *alliance*, *hostility*, or *neutral interaction*.

The project was developed as part of the course **Analyse et Modélisation de Systèmes (AMS)**.

---

## Research Motivation

Narrative texts contain complex relational information that cannot be captured by simple co-occurrence networks.

Key challenges include:

- **Alias resolution** (e.g., multiple references to the same character)
- **Implicit relations expressed through verbs and dialogue**
- **Context-dependent polarity of interactions**

To address these challenges, the project explores a **hybrid pipeline combining statistical NLP models with symbolic reasoning rules**.

---

## Methodology

The pipeline follows a multi-stage architecture:

### 1. Named Entity Recognition

Character mentions are extracted using two complementary NER models:

- **SpaCy** (`fr_core_news_md`)
- **Flair** (`flair/ner-french`)

Combining both models improves recall for fictional entities and uncommon names present in the corpus.

### 2. Contextual Entity Filtering

A semantic filter evaluates each PER candidate by analyzing verbs and adjectives in a local context window. Entities associated with non-human verbs (e.g., *orbiter*, *briller*) are deprioritized. This complements the static blacklist.

### 3. Alias Resolution

To merge different references to the same character, a symbolic alias resolution module is applied:

- **Jaccard similarity on token sets** with family-name safeguard
- **Minimal alias dictionary** (18 entries for cases without shared tokens)
- **Canonical protection** to prevent incorrect merges (e.g., father/son)

### 4. Graph Construction

Co-occurrences are computed within a sliding window and used to build a graph where:

- Nodes represent characters
- Edges represent interactions weighted by co-occurrence frequency
- Isolated nodes (degree 0) are pruned before export

### 5. Graph-based Disambiguation

A structural analysis module computes **Jaccard similarity on node neighborhoods** to detect potential unresolved aliases and suspicious nodes.

### 6. Polarity Analysis

Two methods are available, selectable via configuration:

- **Chapter-level ternary polarity** (main method): for each sentence containing a polarized verb and two characters, a signal (*ami* / *ennemi*) is assigned. Final label per pair is determined by majority vote.
- **Legacy composite polarity** (perspective): continuous score combining SVO events, dialogue weighting, affiliations, and co-occurrence signal. Retained as a methodological evolution path.

Graphs are exported in **GraphML format**.

---

## Results

Applied to a **37-chapter subset of the Foundation corpus**, the system produced:

- **249 character nodes**
- **360 interaction edges**
- **28 non-neutral polarity labels** (19 *ennemi*, 9 *ami*)
- **F1-score: 0.66 on the course benchmark leaderboard** (up from 0.57 baseline)

---

## Repository Structure

```
├── config.py                # Global parameters and blacklists
├── main.py                  # Main pipeline execution (Orchestrator)
├── preprocessor.py          # Text cleaning and segmentation
├── ner_engine.py            # Hybrid NER (SpaCy + Flair)
├── polarity_analyzer.py     # Relationship scoring engine (SVO logic)
├── extraction_rules.py      # Linguistic modulation (Negation, Modals)
├── resource_manager.py      # Dynamic JSON lexicon loader
├── context_entity_filter.py # Statistical filtering of false positives
├── graph_builder.py         # NetworkX construction and GraphML export
│
├── docs/                    # PROJECT DOCUMENTATION & REPORTS
│   ├── 00_research_project_presentation.pdf
│   ├── 01_research_project_summary.pdf
│   ├── 02_pipeline_documentation.pdf
│   └── AMS_Project_Testing_Report.xlsx
│
├── experiences/             # SCIENTIFIC EVALUATION
│   └── experimentations.py  # Sensitivity analysis and window-size tests
│
├── utils/                   # VISUALIZATION & DATA TOOLS
│   ├── scripts/             # Static Python plotting (Matplotlib)
│   └── visual/              # Interactive Web Viewer (D3.js)
│
├── tests/                   # UNIT & INTEGRATION TESTS
└── data/                    # Corpus (raw) and generated outputs
```

---

## Tools and Libraries

- Python 3.8+
- SpaCy (`fr_core_news_md`)
- Flair (`ner-french`)
- NetworkX
- Pandas

---

## Installation

```bash
# Clone the repository
git clone https://github.com/steve-sanogo/RxPersonna.git
cd RxPersonna

# Install Python dependencies
pip install -r requirements.txt

# Download the French SpaCy model (required)
python -m spacy download fr_core_news_md
```

## Configuration

Key parameters in `config.py`:

| Parameter | Value | Description |
|---|---|---|
| `POLARITY_METHOD` | `"chapter_3labels"` | Ternary polarity per chapter (main) |
| `USE_CONTEXT_FILTER` | `True` | Contextual entity filtering |
| `USE_GRAPH_DISAMBIG` | `False` | Structural graph disambiguation (experimental) |
| `WINDOW_SIZE` | `20` | Co-occurrence window (tokens) |

---
## Visualization & Analysis Tools

The project provides two ways to explore the extracted networks: **Static Python plots** and an **Interactive Web Viewer**.

### 1. Static Visualizations (Python)
Use `visualize_polarity.py` to generate high-resolution plots with sentiment-coded edges.

| Scope | Command | Description |
| :--- | :--- | :--- |
| **Global** | `python utils/scripts/visualize_polarity.py all` | View the entire merged network. |
| **Chapter** | `python utils/scripts/visualize_polarity.py lca3` | Focus on a specific chapter. |
| **Ego-Graph** | `python utils/scripts/visualize_polarity.py all --ego "Hari"` | Focus on one character and their neighbors. |
| **Save** | `python utils/scripts/visualize_polarity.py lca3 --save` | Export as PNG to `./data/images/final`. |

### 2. Interactive Web Viewer (D3.js) — Live Deployment

A fully deployed version of the interactive viewer is publicly accessible at:

> **[https://53c4d986.foundation-graph.pages.dev/](https://53c4d986.foundation-graph.pages.dev/)**

The viewer offers two modes:

- **Explorer** — Navigate the character network chapter by chapter, with zoom, drag, and hover tooltips showing polarity statistics per character.
- **Ask the Graph** — Query the network in natural language (French or English) using a rule-based NLP parser grounded in the extracted graph data.

To run it locally from the repository:

1. **Data Preparation**: Run `python utils/visual/merge.py`. This script converts the CSV submission into a JSON format compatible with the web viewer.
2. **Update**: The script generates/updates the data constant used by the viewer.
3. **Launch**: Open `utils/visual/graph_viewer.html` in any web browser to explore the interactive "Foundation Universe" map.

### Visual Legend
- 🟢 **Green**: Positive interaction / Alliance.
- 🔴 **Red**: Negative interaction / Hostility.
- ⚪ **Grey**: Neutral interaction / Co-occurrence.
- **Node Size**: Proportional to the character's importance (degree).
- **Edge Width**: Proportional to interaction frequency (weight).


## Authors & Contributions
- **Steve B. SANOGO** (M1 IA)  
  *Lead Architect & Core Developer* - Conception de l'architecture modulaire et du pipeline hybride.
  - Developed the NER engines (Flair/SpaCy) and the semantic polarity analyzer.
  - Implemented the graph disambiguation logic and the experimental testing framework.


- **Malika GHILAS** (M1 ILSEN)  
  *Software Engineer & Integration* - Support à l'intégration des modules et maintenance du code.
  - Developed the interactive Web visualization interface (D3.js).
  - Assisted with technical documentation and the preparation of test datasets.

## Copyright & License

**Copyright © 2026 Steve. SANOGO & Malika GHILAS. All rights reserved.**

### Academic Use
This project was developed within the framework of the **Master 1 Computer Science program at Avignon Université (CERI)**. 

* **Permissions**: The source code, documentation, and research reports contained in this repository are available for academic review and grading by the teaching staff of Avignon Université.
* **Restrictions**: No part of this project may be reproduced, distributed, or transmitted in any form or by any means for commercial purposes without the prior written permission of the Lead Architect (**Steve B. SANOGO**).
* **Citation**: Any use of the methodology, the polarity formula, or the interactive viewer in subsequent research must properly cite this repository and its authors using the reference below.

### How to Cite

**BibTeX**

```bibtex
@misc{sanogo_ghilas_2026_rxpersonna,
  author       = {Sanogo, Steve B. and Ghilas, Malika},
  title        = {{RxPersonna}: Hybrid NLP Pipeline for Character Interaction
                  Network Extraction from the \textit{Foundation} Corpus},
  year         = {2026},
  institution  = {Avignon Université, Master 1 Intelligence Artificielle (CERI)},
  note         = {Course project — Analyse et Modélisation de Systèmes (AMS).
                  Interactive viewer available at
                  \url{https://53c4d986.foundation-graph.pages.dev/}},
  url          = {https://github.com/steve-sanogo/RxPersonna},
}
```

**Plain text (APA-style)**

> Sanogo, S. B., & Ghilas, M. (2026). *RxPersonna: Hybrid NLP Pipeline for Character Interaction Network Extraction from the Foundation Corpus* [Course project, Analyse et Modélisation de Systèmes]. Avignon Université, Master 1 Intelligence Artificielle (CERI). Retrieved from https://github.com/steve-sanogo/RxPersonna

---
*Last Updated: April 2026*

---