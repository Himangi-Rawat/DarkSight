# 🕵️ DarkSight
### AI-Powered E-Commerce Manipulation Intelligence Platform

> An end-to-end analytics platform that detects, classifies, and visualizes deceptive e-commerce dark patterns using web scraping, rule-based NLP, and interactive analytics. The project is developed with reference to India's CCPA Guidelines for Prevention and Regulation of Dark Patterns (2023).

![Python](https://img.shields.io/badge/Python-3.13-blue?style=flat-square)
![Dashboard](https://img.shields.io/badge/Dashboard-Streamlit-FF4B4B?style=flat-square)
![Platforms](https://img.shields.io/badge/Platforms-4-orange?style=flat-square)
![Products](https://img.shields.io/badge/Products%20Analysed-1534-green?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)

---

# 📌 Project Overview

Dark patterns are deceptive UI/UX techniques that influence consumer decisions through misleading interfaces, fake urgency messages, inflated discounts, hidden costs, and manipulative pricing strategies.

Following the release of the **CCPA Guidelines for Prevention and Regulation of Dark Patterns (2023)**, identifying such practices at scale has become increasingly important.

**DarkSight** automates this process by collecting product information from multiple Indian e-commerce platforms, detecting common dark patterns using a rule-based NLP engine, computing a platform-level Manipulation Index, and presenting the results through an interactive analytics dashboard.

---

# 🎯 Objectives

- Scrape product information from major Indian e-commerce websites.
- Detect common dark patterns automatically.
- Measure manipulation intensity using a weighted scoring system.
- Compare platforms using analytics and visualizations.
- Provide an interactive dashboard for exploratory analysis.

---

# ✨ Features

- Multi-platform web scraping
- Automated dark pattern detection
- Rule-based NLP classification
- Manipulation Index calculation
- Interactive Streamlit dashboard
- Platform comparison
- Exploratory Data Analysis
- Searchable product explorer

---

# 📊 Dataset Summary

| Metric | Value |
|---------|------:|
| Platforms Analysed | 4 |
| Products Analysed | 1,534 |
| Dark Pattern Categories | 6 |
| Visualizations | 9 |
| Dashboard | Streamlit |

---

# 📈 Key Findings

**Within the collected dataset:**

- **64.5%** of analysed products were flagged with at least one detected dark pattern.
- The analysed Amazon India dataset showed the highest **Manipulation Index (36.3/100)** among the sampled platforms.
- **32.3%** of products contained extreme discount claims (70%+).
- **18.3%** contained urgency or scarcity messaging.
- **25.0%** showed misleading pricing where the current price was greater than or equal to the displayed original price.

> **Note:** These findings are based solely on the sampled dataset collected during this project and should not be interpreted as a comprehensive evaluation of any platform.

---

# 🚨 Dark Pattern Taxonomy

| Pattern | Description |
|----------|-------------|
| Fake Urgency | Scarcity messages such as "Only 2 left!" or "Selling Fast" |
| Extreme Discount | Discount claims exceeding 70% |
| Misleading Price | Current price greater than or equal to original price |
| Inflated Discount | Displayed discount percentage exceeds actual savings |
| Bait Discount | Discounts below 5% promoted as major offers |
| Drip Pricing | Hidden or additional charges embedded in product information |

---

# 🏆 Manipulation Index

The **Manipulation Index (MI)** is a weighted metric (0–100) developed for this project to estimate the relative prevalence and severity of detected dark patterns within the sampled dataset.

| Platform | Manipulation Index |
|----------|-------------------:|
| Amazon India | 36.3 |
| Flipkart | 19.6 |
| Myntra | 10.9 |
| Ajio | 9.5 |

### Scoring Weights

| Pattern | Weight |
|---------|-------:|
| Fake Urgency | 25 |
| Extreme Discount | 20 |
| Inflated Discount | 20 |
| Misleading Price | 15 |
| Bait Discount | 10 |
| Drip Pricing | 10 |

---

# 🏗️ System Architecture

```
E-Commerce Websites
        │
        ▼
 Selenium Web Scrapers
        │
        ▼
   Raw Product Data
        │
        ▼
 Data Cleaning & ETL
        │
        ▼
 Rule-Based NLP Engine
        │
        ▼
 Dark Pattern Detection
        │
        ▼
 Manipulation Index Engine
        │
        ▼
 Exploratory Data Analysis
        │
        ▼
 Streamlit Dashboard
```

---

# 📂 Project Structure

```
DarkSight/
│
├── scraper/
│   ├── scrape_flipkart.py
│   ├── scrape_amazon.py
│   ├── scrape_myntra.py
│   ├── scrape_ajio.py
│   └── data/
│       ├── amazon_raw.csv
│       ├── flipkart_raw.csv
│       ├── myntra_raw.csv
│       ├── ajio_raw.csv
│       ├── master_dataset.csv
│       ├── classified_dataset.csv
│       └── manipulation_scores.csv
│
├── classifier/
│   └── dark_pattern_tagger.py
│
├── analytics/
│   ├── analysis.py
│   └── charts/
│
├── dashboard/
│   └── app.py
│
├── requirements.txt
├── .gitignore
└── README.md
```

---

# ⚙️ Technology Stack

| Layer | Technology |
|---------|------------|
| Programming Language | Python 3.13 |
| Web Scraping | Selenium, BeautifulSoup4 |
| Data Processing | Pandas, NumPy |
| Pattern Detection | Rule-Based NLP (Regex + Heuristics) |
| Data Visualization | Plotly, Matplotlib, Seaborn |
| Dashboard | Streamlit |
| Storage | CSV Pipeline |

---

# 🚀 Installation

## Clone Repository

```bash
git clone https://github.com/Himangi-Rawat/DarkSight.git
cd DarkSight
```

## Create Virtual Environment

```bash
python -m venv venv
```

### Windows

```bash
venv\Scripts\activate
```

### Linux / Mac

```bash
source venv/bin/activate
```

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

# ▶️ Running the Project

### Run Web Scrapers

```bash
python scraper/scrape_flipkart.py
python scraper/scrape_amazon.py
python scraper/scrape_myntra.py
python scraper/scrape_ajio.py
```

### Clean Data

```bash
python scraper/data/clean_data.py
```

### Detect Dark Patterns

```bash
python classifier/dark_pattern_tagger.py
```

### Generate Analytics

```bash
python analytics/analysis.py
```

### Launch Dashboard

```bash
streamlit run dashboard/app.py
```

Open:

```
http://localhost:8501
```

---

# 📊 Dashboard Features

- KPI Overview
- Manipulation Index Leaderboard
- Platform Comparison
- Pattern Distribution
- Heatmaps
- Discount Analysis
- Product Category Analysis
- Interactive Product Explorer
- Dashboard Filters

---

# 🧠 Detection Methodology

The current implementation uses a **rule-based NLP engine** that combines regular expressions and heuristic rules to identify six categories of dark patterns.

The pipeline consists of:

1. Product scraping
2. Data cleaning
3. Pattern detection
4. Score calculation
5. Analytics generation
6. Interactive visualization

---

# 📚 Regulatory Context

This project references publicly available regulatory guidance, including:

- **India – CCPA Guidelines for Prevention and Regulation of Dark Patterns (2023)**
- **EU Digital Services Act (DSA)**
- **US Federal Trade Commission (FTC) publications on deceptive design**

The implementation is intended for educational and research purposes and is not an official compliance assessment tool.

---

# ⚠️ Dataset Limitations

- Results are based on the sampled products collected during the project period.
- Product listings change frequently.
- Detection currently relies on rule-based heuristics.
- The Manipulation Index is a project-specific analytical metric and should not be interpreted as a regulatory or legal assessment of any platform.

---

# 🛣️ Future Work

- Transformer-based NLP Classifier (BERT)
- GenAI Complaint Generator
- Conversational Analytics Chatbot
- Price Manipulation Prediction
- Automated Scheduled Scraping
- Cloud Deployment
- Real-time Monitoring
- Database Integration

---

# 👩‍💻 My Contributions

- Designed the complete project architecture
- Developed Selenium-based web scrapers
- Built the ETL and preprocessing pipeline
- Implemented the rule-based dark pattern detection engine
- Designed the Manipulation Index scoring methodology
- Performed exploratory data analysis
- Developed the interactive Streamlit dashboard
- Prepared project documentation

---

# 📄 License

This project is licensed under the MIT License.

---

# 👩‍💻 Author

**Himangi Rawat**

B.Tech Computer Science & Engineering  
Jaypee Institute of Information Technology, Noida

GitHub: https://github.com/Himangi-Rawat

---

<div align="center">

### ⭐ Built to expose manipulation. Powered by data.

</div>
