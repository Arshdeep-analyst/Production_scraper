# 🕷️ Production Scraper

A production-oriented web scraping system built with **Python, Playwright, SQLAlchemy, MySQL, Pydantic Settings, and a layered architecture**.

The project focuses on building a reliable and maintainable scraping pipeline rather than a simple one-off scraper.

Currently, the system is implemented for **Myntra**, where it discovers and collects product data through Myntra's internal search API and stores normalized products in MySQL.

---

## 🚀 Project Overview

The goal of this project is to build a reusable scraping architecture that can:

- Establish a real browser session
- Discover and consume website APIs
- Handle JavaScript-heavy websites
- Scrape large product datasets
- Normalize website-specific data
- Persist structured data into MySQL
- Separate scraping, normalization, orchestration, and persistence concerns
- Handle failures without bringing down the entire scraping run
- Provide a foundation for adding more e-commerce platforms

The current implementation successfully handles thousands of Myntra products in a single scraping run.

---

# 🏗️ Architecture

```text
                         ┌──────────────────────┐
                         │      Orchestrator    │
                         │     myntra.py        │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │   Browser Session    │
                         │      Playwright      │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │    Myntra Client     │
                         │      API Layer       │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │     Raw Products    │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │      Normalizer      │
                         │   Myntra → Schema    │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │   Product Pipeline   │
                         │     SQLAlchemy       │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │        MySQL         │
                         │   client_products    │
                         └──────────────────────┘


🔍 Scraping Strategy

Instead of relying exclusively on HTML parsing, this project uses Myntra's underlying search API.

The scraper establishes a real Chromium browser session first:

Chromium
   ↓
Myntra homepage
   ↓
Browser session established
   ↓
Browser API context
   ↓
Myntra internal API

This approach allows the scraper to work with the same backend API used by the website.

🌐 Browser Session

Playwright is used to establish the initial browser session.

browser = playwright.chromium.launch(
    headless=False
)


browser_context = browser.new_context(
    user_agent=USER_AGENT
)


page = browser_context.new_page()


page.goto(
    "https://www.myntra.com/",
    wait_until="domcontentloaded"
)


api_context = browser_context.request

The API context belongs to the browser context, allowing requests to be made using the established browser session.

📡 Myntra API Client

The MyntraClient is responsible for communication with Myntra's backend API.

Responsibilities include:

Searching products
Fetching brand facets
Handling pagination
Applying brand filters
Handling price sorting
Collecting raw API responses
Deduplicating products
Handling request failures

Example endpoint pattern:

/gateway/v4/search/{query}

Example parameters:

sort=price_asc
rawQuery=korean pants
rows=50
o=0
plaEnabled=true
xdEnabled=false
isFacet=true
p=1
pincode=144002
📊 Large Result Set Handling

During development, a limitation was discovered in Myntra's pagination behavior.

A single search/filter path cannot reliably expose an unlimited number of products.

To work around this, the scraper uses brand-based partitioning.

Example:

"korean pants"
      │
      ▼
Brand Facet
      │
      ├── Brand A → 20 products
      ├── Brand B → 150 products
      ├── Brand C → 420 products
      ├── Brand D → 800 products
      │
      ▼
Scrape each brand independently

For brands below the safe pagination limit:

price_asc

is used.

For brands exceeding the safe limit:

price_asc
+
price_desc

are used and the results are merged and deduplicated.

This allows the scraper to collect significantly more products than a single search pagination path would allow.

🧹 Normalization Layer

Raw data from different websites should not directly enter the database.

The project therefore contains a dedicated normalization layer.

Myntra API response
        ↓
MyntraNormalizer
        ↓
Normalized Product Schema
        ↓
Database Pipeline

The normalizer converts website-specific fields into the project's common product structure.

Example:

{
    "source_site": "myntra",
    "title": "...",
    "description": "...",
    "price": 659,
    "stock": 284,
    "product_url": "...",
    "source_product_id": "...",
    "brand": "ZYVRA",
    "image_url": "...",
    "rating": 0,
    "currency": "INR",
    "country_of_origin": None
}

This makes it possible to eventually support additional websites without changing the database layer.

🗄️ Database Layer

The project uses:

MySQL
SQLAlchemy ORM
PyMySQL

The database layer is separated into:

db/
├── base.py
├── connection.py
├── init_db.py
└── models.py
Connection

connection.py manages:

MySQL connection
SQLAlchemy engine
Session factory
Connection health checking
Models

models.py contains the SQLAlchemy database models.

The primary product table is:

client_products
📦 Product Schema

The product model currently contains fields such as:

Field	Description
id	Internal database ID
source_site	Website the product came from
title	Product title
description	Product description
price	Product price
stock	Available stock
product_url	Product page URL
source_product_id	Original website product ID
brand	Product brand
image_url	Product image
rating	Product rating
currency	Currency
country_of_origin	Country information
created_at	Creation timestamp
updated_at	Last update timestamp
🔄 Product Pipeline

The persistence layer is responsible for saving normalized products.

Normalized Product
        ↓
ProductPipeline
        ↓
SQLAlchemy Session
        ↓
MySQL

Example:

pipeline = ProductPipeline(session)


pipeline.process(
    normalized_product
)

The pipeline is intentionally separated from the scraper so that database logic does not become coupled to scraping logic.

🎯 Orchestration

The orchestrator coordinates the complete workflow.

Current flow:

run_myntra()
      │
      ├── Launch browser
      │
      ├── Establish Myntra session
      │
      ├── Create API client
      │
      ├── Scrape products
      │
      ├── Normalize products
      │
      ├── Save products
      │
      └── Close browser

Example:

uv run python -m orchestrators.myntra
📁 Project Structure
Production_Scraper/
│
├── api/
│
├── config/
│   └── settings.py
│
├── db/
│   ├── base.py
│   ├── connection.py
│   ├── init_db.py
│   └── models.py
│
├── orchestrators/
│   └── myntra.py
│
├── pipeline/
│   └── product_pipeline.py
│
├── scraper/
│   ├── clients/
│   │   └── myntra.py
│   │
│   └── normalizer/
│       └── myntra.py
│
├── tests/
│   ├── pipelinetest.py
│   └── pipeline_tune.py
│
├── .env
├── .gitignore
├── pyproject.toml
└── README.md
⚙️ Tech Stack
Technology	Purpose
Python	Core programming language
Playwright	Browser automation and API session
SQLAlchemy	ORM and database abstraction
PyMySQL	MySQL driver
MySQL	Persistent storage
Pydantic Settings	Configuration management
uv	Python environment and dependency management
Git	Version control
🔐 Configuration

Create a .env file in the project root.

MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=production_scraper


USE_PROXY=False


PROXY_PROVIDER=
PROXY_HOST=
PROXY_PORT=
PROXY_USERNAME=
PROXY_PASSWORD=

The .env file is intentionally excluded from Git.

Never commit credentials or API keys to the repository.

🛠️ Installation

Clone the repository:

git clone https://github.com/Arshdeep-analyst/Product-Scraper.git

Navigate into the project:

cd Production_Scraper

Install dependencies:

uv sync

Install Playwright browsers:

uv run playwright install

Create the MySQL database:

CREATE DATABASE production_scraper;

Initialize database tables:
uv run python -m db.init_db

▶️ Running the Scraper
Run the Myntra orchestrator:
uv run python -m orchestrators.myntra

The orchestrator will:

Launch Chromium
Open Myntra
Establish a browser session
Create an API request context
Search for products
Fetch brand facets
Scrape products
Normalize product data
Store products in MySQL
🧪 Testing

Database connectivity can be tested using the existing tests.

Example:

uv run python -m tests.pipelinetest

Pipeline testing:

uv run python -m tests.pipeline_tune
⚡ Performance Considerations

The project has two major performance areas:

1. Scraping

Currently the largest bottleneck.

Myntra API
    ↓
Network requests
    ↓
Pagination
    ↓
Brand partitioning

Future improvements include:

Controlled concurrent requests
Async API requests
Connection reuse
Retry strategies
Exponential backoff
Better request scheduling
2. Database

Database writes have been optimized using batch processing experiments.

The target architecture is:

50-100 products
       ↓
Batch INSERT
       ↓
COMMIT

Rather than:

Product
   ↓
INSERT
   ↓
COMMIT


Product
   ↓
INSERT
   ↓
COMMIT

Batch processing significantly reduces transaction overhead.

🛡️ Error Handling

The scraper is designed to handle failures at multiple layers.

Potential failures include:

HTTP errors
API request failures
Connection resets
Missing product fields
Invalid database values
MySQL errors
Browser/session failures

The architecture separates these concerns so that a failure in one layer does not require rewriting the entire system.

🧠 Engineering Lessons

This project was built as a learning exercise in production-oriented scraping architecture.

Major lessons include:

Reverse engineering APIs

Instead of immediately parsing HTML:

Website
   ↓
Inspect network requests
   ↓
Find backend API
   ↓
Understand request parameters
   ↓
Reproduce API requests
Browser sessions

A browser can be used to establish a legitimate session and then the associated request context can communicate with backend APIs.

Pagination limitations

Real-world scraping often requires more than simply:

for page in range(...):
    scrape(page)

Backend limitations sometimes require partitioning strategies.

Normalization

Website-specific data should be converted into a common schema before entering the database.

Separation of concerns

The scraper should not know how the database works.

The database should not know how Myntra works.

The normalizer should bridge the two.

🚧 Current Limitations

This project is still under active development.

Current limitations include:

Myntra-specific implementation
Sequential scraping in parts of the workflow
Browser session dependency
Scraping performance can be improved
Database batch failure recovery is still being refined
No production job queue yet
No monitoring/observability system yet
No distributed workers yet
🔮 Future Improvements

Planned improvements include:

Scraping
Async/concurrent request processing
Controlled concurrency
Retry and exponential backoff
Better request scheduling
Proxy rotation
More robust session management
Database
Robust batch transaction handling
Upsert support
Duplicate prevention
Database indexing
Connection pool tuning
Architecture
Abstract scraper interface
Multiple marketplace implementations
Worker architecture
Job queue
Scheduler
Monitoring
Structured logging

Potential future architecture:

                    Scheduler
                       │
                       ▼
                    Job Queue
                       │
              ┌────────┴────────┐
              ▼                 ▼
          Worker 1           Worker 2
              │                 │
              ▼                 ▼
          Scraper             Scraper
              │                 │
              └────────┬────────┘
                       ▼
                  Normalizer
                       │
                       ▼
                  Data Pipeline
                       │
                       ▼
                     MySQL
📈 Current Results

The current Myntra implementation has successfully demonstrated scraping approximately 3,000 products in a single run, followed by normalization and persistence into MySQL.

Example run:

==================================================
✅ Myntra pipeline completed
==================================================
📦 Raw products: 2983
🔄 Normalized products: 2983
💾 Saved products: ...
==================================================

The exact number of saved products may vary depending on product data quality and database constraints.

📚 What This Project Demonstrates

This project demonstrates practical experience with:

Web scraping
API reverse engineering
Playwright
Browser automation
API request reproduction
Pagination strategies
Data normalization
SQLAlchemy
MySQL
Database transactions
Configuration management
Error handling
Modular architecture
Orchestration
Performance optimization
Production-oriented scraping design
👨‍💻 Author

Arsh

Focused on:

Web Scraping
Data Extraction
Python Automation
API Reverse Engineering
Scraping Infrastructure
Data Pipelines
⭐ Project Status

Active Development

The current focus is improving scraping performance, reliability, concurrency, and production-level database processing.


