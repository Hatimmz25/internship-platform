# InternshipRadar AI

## 1. Project Overview and Objectives
InternshipRadar AI is a production-grade web application designed to periodically collect PFE (End-of-Studies) and internship listings from permitted websites across Europe, focusing specifically on:
* Artificial Intelligence, Machine Learning, and Deep Learning
* Data Science and Data Engineering
* NLP and Large Language Models (LLMs)
* Computer Vision and Applied AI Research

The system automatically detects new offers, deduplicates records, matches them against student preferences using a deterministic ranking engine, and dispatches email alerts.

## 2. Architecture Diagram
```mermaid
graph TD
    Client[Next.js Frontend / Admin UI] -->|HTTPS / REST API| API[FastAPI Backend]
    
    subgraph Storage & Caching
        DB[(PostgreSQL Database)]
        Redis[(Redis Cache & Task Broker)]
    end

    subgraph Async Background Engine
        Beat[Celery Beat Scheduler] -->|Enqueues Scheduled Tasks| Redis
        Worker[Celery Workers] <-->|Processes Jobs / Fetches Tasks| Redis
        Worker -->|Reads / Writes Offers & Logs| DB
        Worker -->|Sends Notifications| EmailService[Email Service Interface]
        API -->|Triggers Manual Scraping / Jobs| Redis
    end

    subgraph Scraping Infrastructure
        Worker -->|Executes Spiders| Scrapy[Scrapy Framework Engine]
        Scrapy -->|Rate-Limited / Respectful Requests| Targets[Target Websites / APIs / RSS]
    end

    API <--> DB
    API <--> Redis
    EmailService -->|Delivers Alerts| UserEmail[Subscriber Inbox]

    3. Technology Stack and RationaleFrontend: Next.js 14, TypeScript, Tailwind CSS (Modern, responsive, fast server-side rendering).Backend REST API: FastAPI (High-performance asynchronous Python API with automatic Swagger/OpenAPI docs).Scraping Subsystem: Scrapy (Robust, rate-limited web crawling framework with built-in pipeline support).Database & ORM: PostgreSQL 15 & SQLAlchemy 2.x with Alembic migrations (Reliable relational data integrity and structured schema evolution).Background Processing: Celery & Redis (Scalable asynchronous task distribution and distributed locking).Scheduling: Celery Beat (Authoritative single-clock periodic task scheduler).Email Provider Interface: Interchangeable adapter supporting SMTP, Resend, and a Development Console fallback.4. Repository StructurePlaintextinternship-platform/
├── backend/                  # FastAPI application, models, schemas, tasks, migrations
│   ├── app/
│   │   ├── api/v1/           # REST endpoints (auth, offers, preferences, admin)
│   │   ├── core/             # Config, database session, celery app, redis locks
│   │   ├── models/           # SQLAlchemy ORM models
│   │   ├── services/         # Ingestion, matching, and email provider services
│   │   └── tasks/            # Celery scraping, matching, and notification tasks
│   ├── alembic/              # Database migration scripts
│   └── tests/                # Pytest test suite
├── scraper/                  # Scrapy project, spiders, items, pipelines, and offline fixtures
│   └── internship_scraper/
│       ├── spiders/          # Source-specific feed/HTML spiders
│       └── tests/            # Fixture-based unit tests
├── frontend/                 # Next.js TypeScript application
│   └── src/app/              # Pages, components, and layout views
├── docker-compose.yml        # Infrastructure service orchestration
├── .env.example              # Environment variable template
└── README.md                 # Project documentation
5. PrerequisitesDocker and Docker Compose (v2.0+)Python 3.11+ (if running tests locally outside containers)Node.js 18+ (if running frontend locally outside containers)6. Environment ConfigurationCopy the template and configure your local settings:Bashcp .env.example .env
7. Installation and Startup CommandsLaunch all containerized services:Bashdocker compose up -d --build
8. Database Migration InstructionsApply pending Alembic migrations inside the backend container:Bashdocker compose exec backend alembic upgrade head
9. How to Run TestsExecute the full pytest suite inside the backend container:Bashdocker compose exec backend pytest
10. How to Configure a Permitted SourceAdministrators can register or update scraping sources via the database seed script or the /api/v1/admin/sources REST endpoint. Spiders strictly respect robots.txt and download delays.11. How to Run a Scrape ManuallyTrigger an out-of-band scrape via the Celery task runner or admin API:Bashdocker compose exec backend python -c "from app.tasks.scraping_tasks import scrape_source_task; scrape_source_task.delay(1)"
12. How to Configure Email NotificationsSet EMAIL_PROVIDER=resend or EMAIL_PROVIDER=smtp in your .env file along with credentials. In development, leave it unconfigured to default to the safe Console Provider (no real emails sent).13. How to Create a Subscriber and PreferencesUse the /api/v1/auth/register endpoint or the database seed script (python -m app.db.seed) to create a subscriber account and default preference profile.14. How to Inspect Logs and Troubleshoot ErrorsView backend API logs: docker compose logs -f backendView worker execution logs: docker compose logs -f workerView scheduler ticks: docker compose logs -f beat15. Known Limitations and Future ImprovementsLive scraping sources require ongoing maintenance due to target DOM changes; current testing relies heavily on RSS feeds and offline XML fixtures.Advanced semantic embedding matching is architected via an optional interface but defaults to a deterministic keyword/skill scoring engine.
---

## 2. Environment Configuration (`.env.example`)

```env
# Application Settings
PROJECT_NAME=InternshipRadar AI
ENVIRONMENT=development
DEBUG=true

# PostgreSQL Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=internship_radar
POSTGRES_SERVER=postgres
DATABASE_URL=postgresql+psycopg2://postgres:postgres@postgres:5432/internship_radar

# Redis & Celery
REDIS_URL=redis://redis:6379/0

# Security / JWT
SECRET_KEY=super-secret-development-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=11520

# Email Provider Configuration (console, smtp, or resend)
EMAIL_PROVIDER=console
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=user@example.com
SMTP_PASSWORD=secret
EMAILS_FROM_EMAIL=alerts@internshipradar.ai
RESEND_API_KEY=re_placeholder_key
3. Academic Project Report Outline & DiagramsReport OutlineIntroduction and Problem Statement: Context of PFE/end-of-studies internship hunting in Europe for AI/Data Science students; fragmentation of job boards.Functional and Non-Functional Requirements: User discovery, automated scraping, preference matching, notification workflows, scalability, and rate-limiting compliance.System Architecture: Monorepo containerization using Docker Compose, FastAPI, Next.js, Scrapy, Celery, Redis, and PostgreSQL.Database Design and Entity Relationship Diagram (ERD): Relational schema design across Users, Preferences, InternshipOffers, ScrapingSources, ScrapingRuns, and OfferMatches.Scraping Methodology and Source Selection: Ethical scraping practices, robots.txt adherence, feed parsing, and source adapters.New-Offer Detection and Deduplication: Canonical URL checking and SHA256 content fingerprinting to ensure idempotent ingestion.Subscriber Matching and Email Notification Workflow: Deterministic relevance scoring engine and abstracted email provider queueing.Implementation Details: Code modularity, database session management, and background worker safety.Testing Strategy and Actual Results: Unit tests, fixture-based spider tests, and workflow idempotency test results.Ethical, Legal, and Privacy Considerations: Terms of service compliance, avoiding CAPTCHA bypass, and data minimization.Limitations and Future Work: DOM volatility and optional LLM semantic embedding enhancements.Conclusion: Summary of achievements and project impact.Mermaid Diagrams1. System Architecture DiagramCode snippetgraph TD
    Client[Next.js Frontend] -->|REST API| API[FastAPI Backend]
    API --> DB[(PostgreSQL)]
    API --> Redis[(Redis Broker)]
    Beat[Celery Beat] -->|Schedules| Redis
    Worker[Celery Workers] <--> Redis
    Worker --> DB
    Worker --> Scrapy[Scrapy Engine]
    Scrapy --> External[Permitted Feeds / Sites]
2. Database Relationship Diagram (ERD)Code snippeterDiagram
    USERS ||--o{ PREFERENCES : has
    USERS ||--o{ OFFER_MATCHES : receives
    SCRAPING_SOURCES ||--o{ INTERNSHIP_OFFERS : produces
    SCRAPING_SOURCES ||--o{ SCRAPING_RUNS : logs
    INTERNSHIP_OFFERS ||--o{ OFFER_MATCHES : matches
    
    USERS {
        int id PK
        string email
        string hashed_password
        string role
    }
    PREFERENCES {
        int id PK
        int user_id FK
        json preferred_countries
        json target_roles
        json skills
    }
    INTERNSHIP_OFFERS {
        int id PK
        int source_id FK
        string canonical_url
        string fingerprint
        string title
        string company
        datetime first_seen_at
        datetime last_seen_at
    }
    OFFER_MATCHES {
        int id PK
        int user_id FK
        int offer_id FK
        float score
        json breakdown
    }
    SCRAPING_SOURCES {
        int id PK
        string name
        string slug
        boolean is_active
    }
    SCRAPING_RUNS {
        int id PK
        int source_id FK
        string status
        int items_found
    }
3. New-Offer Notification Sequence DiagramCode snippetsequenceDiagram
    participant Beat as Celery Beat
    participant Worker as Celery Worker
    participant DB as PostgreSQL
    participant Matcher as Matching Engine
    participant Email as Email Provider

    Beat->>Worker: Dispatch scraping task
    Worker->>DB: Upsert offer (Idempotent check)
    alt Is New Offer
        DB-->>Worker: Return new offer ID
        Worker->>Matcher: Trigger match evaluation
        Matcher->>DB: Query subscriber preferences
        Matcher->>DB: Create OfferMatch record
        Matcher->>Email: Queue email notification task
        Email-->>Subscriber: Deliver alert (Console/SMTP/Resend)
    else Is Existing / Unchanged
        DB-->>Worker: Update last_seen_at timestamp only
        Note over Worker,Email: No duplicate match or notification created
    end
4. Final Acceptance ChecklistComponent / FeatureStatusVerification MethodDocker Compose OrchestrationImplemented & Testeddocker compose up -d starts all 6 services successfully.PostgreSQL & Alembic MigrationsImplemented & Testedalembic upgrade head applies schemas cleanly.Scrapy Scraping SubsystemImplemented & TestedVerified via offline XML fixtures and feed spiders.Idempotent Ingestion & DeduplicationImplemented & TestedSHA256 fingerprinting prevents duplicate records and alerts.Deterministic Matching EngineImplemented & TestedPytest suite validates skill overlap, PFE constraints, and scoring.Celery Background Workers & BeatImplemented & TestedDistributed Redis locking prevents scraping overlaps.Interchangeable Email ProviderImplemented & TestedSafe console fallback logs emails in development without external API keys.Next.js Frontend & REST APIImplemented (Partially Tested)FastAPI endpoints documented in Swagger (/docs); frontend UI scaffolded.5. Clean-Start & University Presentation Demonstration ScriptFollow this script step-by-step during your presentation to demonstrate the system live:Bash# Step 1: Clean start (stop and remove existing containers & volumes)
docker compose down -v

# Step 2: Build and launch all infrastructure services
docker compose up -d --build

# Step 3: Verify container health and running status
docker compose ps

# Step 4: Run database migrations
docker compose exec backend alembic upgrade head

# Step 5: Seed database with synthetic development data and subscribers
docker compose exec backend python -m app.db.seed

# Step 6: Run the automated test suite to prove system correctness
docker compose exec backend pytest -v

# Step 7: Open Swagger API Documentation in your browser
# Navigate to: http://localhost:8000/docs