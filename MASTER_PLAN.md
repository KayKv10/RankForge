# Project Master Plan: RankForge - Competitive Gaming Analytics Platform

## Executive Summary

RankForge is a modern, game-agnostic rating and matchmaking system designed to track player performance across any competitive format (1v1, 1vN, MvN). The project serves dual purposes: providing a fun, competitive experience for tracking performance among friends, and functioning as a portfolio showcase demonstrating expertise across mathematics, data science, software development, and frontend skills.

The project currently has a **solid backend foundation** with a fully functional FastAPI application, complete Glicko-2 rating implementation, flexible data models supporting any game format, and comprehensive test coverage. The backend API is production-ready for basic match recording and rating calculations. However, the project is missing critical components: **no frontend exists**, **no matchmaking algorithm is implemented**, **no leaderboard/analytics endpoints are available**, and the matchmaking algorithm (using skill distribution superposition and simulated annealing) exists only as a concept.

The path to MVP completion requires approximately **150-200 hours of development** across four major phases: backend API completion, frontend development, matchmaking implementation, and polish/documentation. At 3-6 hours per week, this translates to roughly 6-12 months of dedicated work. This plan prioritizes delivering value incrementally, with each phase producing a functional improvement to the system.

---

## Current State Assessment

### What's Implemented

**Backend Infrastructure (Production-Ready)**
- FastAPI async web application with automatic OpenAPI documentation
- SQLAlchemy 2.0 ORM with async support (aiosqlite for development, PostgreSQL-ready)
- Alembic database migrations for schema versioning
- Clean separation of concerns: API routes, schemas, services, models

**Data Models (Complete)**
- `Player` - Unique person across all games
- `Game` - Defines competitive game structure with pluggable rating strategy
- `GameProfile` - Player's rating and stats for a specific game (flexible JSON fields)
- `Match` - Single instance of a game with contextual metadata
- `MatchParticipant` - Links players to matches with outcomes and rating history

**API Endpoints (13 Endpoints)**
- Players: Full CRUD (POST, GET list, GET single, PUT, DELETE)
- Games: Full CRUD (POST, GET list, GET single, PUT, DELETE)
- Matches: Create, Read list, Read single, Delete

**Rating System**
- Complete Glicko-2 implementation ([glicko2_engine.py](src/rankforge/rating/glicko2_engine.py))
- Based on Mark Glickman's paper with proper mathematical implementation
- Supports binary (win/loss) and ranked outcomes
- Team-based calculations with proper opponent aggregation
- Historical rating tracking (before/after each match)

**Code Quality Infrastructure**
- Pre-commit hooks with Ruff (linting/formatting) and Mypy (type checking)
- Comprehensive test suite (~1,200 lines across 7 test modules)
- Async-first testing with pytest-asyncio
- In-memory test database with transactional isolation

**Data Import System**
- 24+ data import scripts for real-world match history (Pickleball, Tennis, Padel)
- Demonstrates API usage patterns and real data structures

### What's In Progress

- **Rating Strategy Dispatcher**: Architecture exists for multiple rating engines; currently routes to Glicko-2 or dummy engine based on game's `rating_strategy` field
- **Match History Tracking**: Basic structure in place (rating_info_before, rating_info_change), but no dedicated history retrieval endpoints

### What's Missing

**Core Features Needed for MVP**
1. **Leaderboard/Rankings Endpoints** - No endpoints to retrieve sorted player rankings by game
2. **Player Statistics Endpoints** - No endpoints for win/loss records, match history per player
3. **Game Profile Retrieval** - No endpoints to get all players' ratings for a specific game
4. **Matchmaking System** - Zero implementation; this is the novel algorithm (distribution superposition + simulated annealing)
5. **Frontend Application** - No frontend code exists whatsoever
6. **User Authentication** - No auth system (acceptable for friends-only use, but needed for public deployment)

**Infrastructure Gaps**
1. **No production deployment configuration** - No Dockerfile, docker-compose, or cloud deployment manifests
2. **No environment configuration** - Empty `.env` file, hardcoded SQLite database path
3. **No API rate limiting or security hardening**
4. **No monitoring, logging, or health check endpoints**

**Documentation/Testing Gaps**
1. **No API usage examples** - README covers setup but not how to use the API
2. **No architecture documentation** - No diagrams or detailed system explanations
3. **No user guide** - No documentation for end users
4. **Limited integration tests** - Most tests are unit/service level, fewer end-to-end API tests

### Technical Debt & Refactoring Needs

1. **Import Scripts Cleanup** - 24 versions of pickleball import script should be consolidated into a single configurable importer
2. **Database URL Hardcoding** - Currently hardcoded in [session.py](src/rankforge/db/session.py); should use environment variables
3. **Error Handling Consistency** - Some edge cases (e.g., non-competitive matches) have TODO comments rather than proper error handling
4. **Pydantic Schema Expansion** - Current schemas don't expose rating info in player responses; need GameProfile schemas for leaderboard use
5. **Type Annotations** - Some function parameters lack full type hints
6. **Test Coverage for Glicko-2** - Mathematical edge cases (very high/low RD, extreme rating differences) need more test coverage

---

## Project Architecture

### Technology Stack

**Backend:**
| Component | Technology | Purpose |
|-----------|------------|---------|
| Framework | FastAPI | Async REST API |
| ORM | SQLAlchemy 2.0 | Database abstraction |
| Migrations | Alembic | Schema version control |
| Validation | Pydantic | Request/response schemas |
| Server | Uvicorn | ASGI application server |
| Dev Database | SQLite + aiosqlite | Development persistence |
| Prod Database | PostgreSQL | Production persistence (planned) |

**Frontend (Proposed):**
| Component | Technology | Rationale |
|-----------|------------|-----------|
| Framework | React | Industry standard, excellent ecosystem |
| Language | TypeScript | Type safety, better DX |
| Build Tool | Vite | Fast development, modern bundling |
| Styling | Tailwind CSS | Rapid prototyping, utility-first |
| State | React Query + Zustand | Server state + client state |
| Charts | Recharts | React-native charting library |
| HTTP | Axios | Clean API client |

**Infrastructure (Proposed):**
| Component | Technology | Rationale |
|-----------|------------|-----------|
| Containerization | Docker | Consistent deployments |
| Hosting | Railway / Render | Simple PaaS with free tiers |
| CI/CD | GitHub Actions | Integrated with repository |
| Monitoring | Sentry (free tier) | Error tracking |

### System Components

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React)                            │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────────────┐ │
│  │   Match   │  │ Leaderbd  │  │  Player   │  │   Matchmaking     │ │
│  │  Entry    │  │   View    │  │  Stats    │  │    Interface      │ │
│  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘  └─────────┬─────────┘ │
└────────┼──────────────┼──────────────┼──────────────────┼───────────┘
         │              │              │                  │
         └──────────────┼──────────────┼──────────────────┘
                        │              │
                   HTTP/REST API
                        │              │
┌───────────────────────┴──────────────┴──────────────────────────────┐
│                        BACKEND (FastAPI)                            │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                      API Layer (/api/)                        │  │
│  │   /players  │  /games  │  /matches  │  /leaderboard*  │ ...  │  │
│  └───────────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                   Service Layer (/services/)                  │  │
│  │   match_service  │  matchmaking_service*  │  analytics*       │  │
│  └───────────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                    Rating Layer (/rating/)                    │  │
│  │     glicko2_engine  │  dummy_engine  │  (future: ML models)   │  │
│  └───────────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                   Data Layer (/db/)                           │  │
│  │   Player  │  Game  │  GameProfile  │  Match  │  Participant   │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                          ┌──────┴──────┐
                          │  Database   │
                          │ PostgreSQL  │
                          └─────────────┘

* = Not yet implemented
```

### Data Flow for Key Operations

**Recording a Match:**
```
User → Frontend Form → POST /matches/ → match_service.process_new_match()
  → Create Match + MatchParticipant records
  → get_or_create_game_profile() for each player
  → Store rating_info_before
  → Commit to DB
  → Dispatch to rating engine (glicko2_engine.update_ratings_for_match)
  → Calculate new ratings per Glicko-2 algorithm
  → Update GameProfile.rating_info
  → Store rating_info_change
  → Return complete Match object → Frontend displays result
```

**Matchmaking (Planned):**
```
User → Select players + constraints → POST /matchmaking/generate
  → Fetch all players' GameProfiles for selected game
  → Create skill distributions per player (Gaussian from rating + RD)
  → Generate possible team configurations
  → Evaluate each configuration:
    → Superposition team distributions
    → Calculate fairness score (overlap of team distributions)
  → Simulated annealing optimization
    → Start with random configuration
    → Perturb and accept/reject based on temperature schedule
  → Return top N configurations → Frontend displays options
```

---

## Development Roadmap

### Phase 0: Foundation & Cleanup
**Goal:** Establish solid foundation, clean up technical debt, and set up for productive development

**Tasks:**

| Task | Hours | Priority |
|------|-------|----------|
| Consolidate import scripts into single configurable importer | 3-4 | Medium |
| Externalize database URL to environment variables | 1 | High |
| Add proper error handling for edge cases (replace TODO comments) | 2-3 | High |
| Create GameProfile Pydantic schemas for API responses | 2-3 | High |
| Add leaderboard endpoint: `GET /games/{game_id}/leaderboard` | 3-4 | High |
| Add player stats endpoint: `GET /players/{player_id}/stats` | 3-4 | High |
| Add match history endpoint: `GET /players/{player_id}/matches` | 2-3 | Medium |
| Add health check endpoint: `GET /health` | 0.5 | Medium |
| Increase Glicko-2 test coverage for edge cases | 3-4 | Medium |
| Set up Docker development environment | 3-4 | Medium |

**Estimated Total:** 23-30 hours (5-10 weeks at 3-6 hrs/week)

**Completion Criteria:**
- [ ] All environment configuration externalized
- [ ] Zero TODO comments in production code
- [ ] Leaderboard and player stats endpoints functional
- [ ] API fully documented in OpenAPI spec
- [ ] Docker development environment works end-to-end
- [ ] Test coverage > 85%

---

### Phase 1: Matchmaking Algorithm Implementation
**Goal:** Implement the novel matchmaking algorithm that makes this project unique

**Tasks:**

| Task | Hours | Priority |
|------|-------|----------|
| Design matchmaking service interface and schemas | 3-4 | High |
| Implement skill distribution modeling (Gaussian from rating + RD) | 4-5 | High |
| Implement team distribution superposition | 4-5 | High |
| Implement fairness scoring function (distribution overlap) | 3-4 | High |
| Implement configuration space enumeration for small N | 3-4 | Medium |
| Implement simulated annealing optimizer | 6-8 | High |
| Add matchmaking endpoint: `POST /matchmaking/generate` | 3-4 | High |
| Add constraints handling (player preferences, must-play-together, etc.) | 4-5 | Medium |
| Write comprehensive tests for matchmaking | 5-6 | High |
| Document algorithm with mathematical notation | 3-4 | Medium |

**Estimated Total:** 39-49 hours (8-16 weeks at 3-6 hrs/week)

**Completion Criteria:**
- [ ] Matchmaking generates balanced teams for 4-12 players
- [ ] Fairness score accurately reflects team balance
- [ ] Algorithm handles constraints (exclude players, force teammates)
- [ ] Performance: <2 seconds for 12 players
- [ ] Algorithm documented with examples

---

### Phase 2: Frontend Development
**Goal:** Build user-facing interface for core features

**Tasks:**

| Task | Hours | Priority |
|------|-------|----------|
| Set up React + TypeScript + Vite project structure | 2-3 | High |
| Configure Tailwind CSS and design system | 2-3 | High |
| Create API client with Axios and types from OpenAPI | 3-4 | High |
| Build navigation and layout components | 3-4 | High |
| Build Match Entry form (select game, players, outcomes) | 6-8 | High |
| Build Leaderboard view (sortable table with ratings/stats) | 5-6 | High |
| Build Player Profile page (stats, match history, rating graph) | 6-8 | High |
| Build Matchmaking interface (player selection, generate teams) | 8-10 | High |
| Build Game Selection/Management page | 3-4 | Medium |
| Implement responsive design for mobile | 4-5 | Medium |
| Add loading states, error handling, toast notifications | 3-4 | Medium |
| Build rating history chart (line chart over time) | 4-5 | Medium |

**Estimated Total:** 50-64 hours (10-21 weeks at 3-6 hrs/week)

**Completion Criteria:**
- [ ] All four core user flows functional (record match, view leaderboard, create teams, view stats)
- [ ] Responsive design works on mobile devices
- [ ] Loading and error states properly handled
- [ ] No console errors in production build

---

### Phase 3: Integration, Polish & Deployment
**Goal:** Connect all pieces, deploy to production, and prepare for public use

**Tasks:**

| Task | Hours | Priority |
|------|-------|----------|
| Create production Docker configuration (multi-stage build) | 3-4 | High |
| Set up PostgreSQL for production | 2-3 | High |
| Configure CORS and security headers | 2 | High |
| Deploy backend to Railway/Render | 3-4 | High |
| Deploy frontend to Vercel/Netlify | 2-3 | High |
| Set up CI/CD with GitHub Actions (test + deploy) | 4-5 | High |
| Configure environment variables for production | 2 | High |
| Add error tracking with Sentry | 2 | Medium |
| Performance testing and optimization | 4-5 | Medium |
| Mobile PWA configuration (installable) | 3-4 | Low |
| Add basic analytics (match counts, active users) | 2-3 | Low |

**Estimated Total:** 30-38 hours (6-13 weeks at 3-6 hrs/week)

**Completion Criteria:**
- [ ] Application deployed and accessible via public URL
- [ ] CI/CD pipeline runs tests and deploys on merge to main
- [ ] Zero downtime deployments configured
- [ ] Error tracking operational
- [ ] Performance benchmarks met (<200ms API response times)

---

### Phase 4: Documentation & Open Source Preparation
**Goal:** Make project accessible and professional for public release

**Tasks:**

| Task | Hours | Priority |
|------|-------|----------|
| Write comprehensive README with screenshots | 3-4 | High |
| Create installation and setup guide | 2-3 | High |
| Document API with examples and use cases | 3-4 | High |
| Write architecture documentation with diagrams | 3-4 | High |
| Create CONTRIBUTING.md with guidelines | 2 | Medium |
| Add CODE_OF_CONDUCT.md | 0.5 | Medium |
| Create issue and PR templates | 1 | Medium |
| Write algorithm documentation (the "paper") | 5-6 | High |
| Create demo video or GIF walkthrough | 2-3 | Medium |
| Write blog post / case study for portfolio | 4-5 | Medium |
| Optimize GitHub repository presentation | 2 | Medium |

**Estimated Total:** 28-35 hours (5-12 weeks at 3-6 hrs/week)

**Completion Criteria:**
- [ ] New contributor can set up project in <15 minutes
- [ ] API fully documented with examples
- [ ] Algorithm explained clearly for technical and non-technical audiences
- [ ] Repository has professional presentation (README, badges, etc.)

---

## MVP Definition

### Core Features (Must Have)

1. **Match Recording**
   - Select game from dropdown
   - Select players from list or add new
   - Assign players to teams
   - Record outcome (win/loss or ranks)
   - Automatic rating calculation on submit
   - Display rating changes after submission

2. **Leaderboard Display**
   - View all players ranked by rating for a game
   - Show rating, rating deviation, matches played
   - Sortable columns
   - Filter by game

3. **Matchmaking Generation**
   - Select active players for a session
   - Generate balanced team configurations
   - Display fairness score for each option
   - Accept configuration or regenerate

4. **Player Statistics**
   - View individual player profile
   - Show win/loss record per game
   - Display rating history graph
   - List recent matches

### User Flows

**1. Recording a Match:**
```
1. User opens app → Dashboard
2. Click "Record Match" button
3. Select game (e.g., "Pickleball")
4. If new players: click "Add Player" → enter name → save
5. Drag/drop or select players into Team 1 and Team 2
6. Select winner (Team 1 / Team 2 / Draw)
7. Optionally add score and notes
8. Click "Submit Match"
9. View rating changes for all participants
10. Confirm or record another match
```

**2. Viewing Leaderboard:**
```
1. User opens app → Dashboard
2. Click "Leaderboards" in navigation
3. Select game from dropdown
4. View sorted list of players by rating
5. Click column headers to sort by other metrics
6. Click player name to view profile
```

**3. Creating Balanced Teams:**
```
1. User opens app → Dashboard
2. Click "Matchmaking" in navigation
3. Select game
4. Check boxes next to available players (e.g., 8 players)
5. Set constraints (optional): "Keep X and Y together"
6. Click "Generate Teams"
7. View 3-5 suggested configurations with fairness scores
8. Click "Use This" to copy or start match
```

**4. Analyzing Player Stats:**
```
1. Click player name from leaderboard or search
2. View profile page with:
   - Rating summary across games
   - Win/loss pie chart
   - Rating over time line chart
   - Recent match list with ratings before/after
3. Click on match to see full match details
```

### Technical Requirements

**Performance:**
- API response time < 200ms for all endpoints
- Matchmaking for 12 players < 2 seconds
- Frontend initial load < 3 seconds
- Smooth animations at 60fps

**Security:**
- Input validation on all endpoints
- SQL injection prevention (ORM handles this)
- XSS prevention in frontend
- CORS configured for production domains only

**Scalability:**
- Support 1,000+ matches in database
- Support 100+ players across games
- Async architecture ready for concurrent requests

**Code Quality:**
- All code passes Ruff linting
- All code passes Mypy type checking
- Test coverage > 80%
- No critical security vulnerabilities

---

## Post-MVP Feature Roadmap

### Near-term Enhancements (Next 3-6 months post-MVP)

**Tier 1: High-Priority Extensions**

1. **Match Editing/Correction**
   - Value: Fix data entry mistakes without deleting matches
   - Complexity: Medium (need to recalculate affected ratings)
   - Estimated effort: 8-10 hours

2. **Rating History API**
   - Value: Power frontend graphs, enable analytics
   - Complexity: Low (query existing data differently)
   - Estimated effort: 4-6 hours

3. **Bulk Match Import UI**
   - Value: Onboard historical data easily
   - Complexity: Medium (CSV parsing, validation UI)
   - Estimated effort: 10-12 hours

4. **Game Configuration UI**
   - Value: Non-technical users can add games
   - Complexity: Low (CRUD form)
   - Estimated effort: 4-5 hours

**Tier 2: Medium-Priority Additions**

5. **Player Aliases/Nicknames**
   - Value: Handle players known by multiple names
   - Complexity: Low
   - Estimated effort: 3-4 hours

6. **Match Comments/Notes**
   - Value: Add context to matches
   - Complexity: Low
   - Estimated effort: 2-3 hours

7. **Rating Predictions**
   - Value: "What if" scenarios before matches
   - Complexity: Medium
   - Estimated effort: 6-8 hours

8. **Export to CSV/JSON**
   - Value: Data portability, analysis in other tools
   - Complexity: Low
   - Estimated effort: 3-4 hours

### Long-term Vision (6+ months)

**Experimental Features:**

1. **ML-Enhanced Rating System**
   - Replace traditional "expectation of win" calculations with ML models
   - Experiment with architectures:
     - Random Forest on feature-engineered match data
     - MLPs on player rating vectors
     - Attention mechanisms for player interaction modeling
     - LLMs for contextual understanding (ambitious)
   - Compare ML predictions vs. Glicko-2 expected outcomes
   - Measure: Does ML improve fairness prediction accuracy?
   - Estimated effort: 40-60 hours for initial prototype

2. **Advanced Matchmaking**
   - Refine distribution superposition with learned parameters
   - Add user-configurable optimization objectives
   - Explore multi-objective optimization (fairness + fun factor)
   - Consider fatigue/variety constraints
   - Estimated effort: 20-30 hours

3. **Social Features**
   - Friend lists and groups
   - Match challenges between players
   - Achievement badges
   - Estimated effort: 30-40 hours

4. **Tournament Mode**
   - Bracket generation (single/double elimination, round robin)
   - Tournament ratings separate from ladder ratings
   - Seeding based on current ratings
   - Estimated effort: 40-50 hours

**Platform Expansion:**

5. **Mobile Native App** (React Native)
   - Value: Better mobile UX, offline support
   - Complexity: High
   - Estimated effort: 80-100 hours

6. **Discord Bot Integration**
   - Record matches via slash commands
   - View leaderboards in Discord
   - Matchmaking via reactions
   - Estimated effort: 20-25 hours

7. **Multi-tenant Support**
   - Separate instances for different friend groups/organizations
   - Admin roles and permissions
   - Estimated effort: 30-40 hours

---

## Technical Implementation Details

### Rating System Architecture

**Current Implementation: Glicko-2**

Located in [glicko2_engine.py](src/rankforge/rating/glicko2_engine.py), the implementation follows Mark Glickman's paper exactly:

```python
@dataclass
class Glicko2Rating:
    mu: float = 1500.0      # Rating (skill estimate)
    phi: float = 350.0      # Rating Deviation (uncertainty)
    sigma: float = 0.06     # Volatility (consistency)
```

**Key Algorithm Steps:**
1. Convert to Glicko-2 scale (divide by 173.7178)
2. Compute estimated variance `v`
3. Compute estimated improvement `delta`
4. Determine new volatility `sigma'` via bisection method
5. Update rating deviation to pre-rating period value
6. Update rating and rating deviation
7. Convert back to Glicko scale

**Score Calculation:**
- Binary outcomes: win=1.0, loss=0.0, draw=0.5
- Ranked outcomes: normalized by (numOpponents - (rank-1)) / numOpponents
- Each player rated against all opponents on opposing teams

**Extension Points:**
- New rating engines implement `update_ratings_for_match(db, match)` function
- Game's `rating_strategy` field routes to appropriate engine
- Engines can be hot-swapped without schema changes

### Matchmaking Algorithm (Planned)

**Core Concept: Skill Distribution Superposition**

Each player's skill is modeled as a Gaussian distribution:
```
Player_i ~ N(μ_i, σ_i)
where μ = rating, σ = rating_deviation
```

A team's skill is the sum of player skills (superposition):
```
Team ~ N(Σμ_i, √(Σσ_i²))
```

**Fairness Scoring:**

The fairness of a matchup is the probability that teams are evenly matched, calculated as the overlap of team distributions:
```
Fairness = P(|Team1 - Team2| < threshold)
         = area under min(pdf_Team1_wins, pdf_Team2_wins)
```

Higher overlap = more uncertain outcome = more balanced match.

**Simulated Annealing Optimization:**

For N players forming M teams:
1. Initialize random valid configuration
2. Set temperature T = T_max
3. While T > T_min:
   - Perturb: swap two random players between teams
   - Calculate ΔFairness
   - If improved: accept
   - If worse: accept with probability exp(ΔFairness/T)
   - Cool: T = T * cooling_rate
4. Return best configuration found

**Configuration:**
```python
DEFAULT_MATCHMAKING_CONFIG = {
    "T_max": 1.0,
    "T_min": 0.001,
    "cooling_rate": 0.99,
    "iterations_per_temp": 10,
    "num_results": 5,  # Return top N configurations
}
```

### Data Models

**Entity Relationship Diagram:**
```
┌─────────────┐     ┌─────────────┐     ┌─────────────────┐
│   Player    │     │    Game     │     │   GameProfile   │
├─────────────┤     ├─────────────┤     ├─────────────────┤
│ id (PK)     │───┐ │ id (PK)     │───┐ │ id (PK)         │
│ name        │   │ │ name        │   │ │ player_id (FK)  │←─┐
│ created_at  │   │ │ rating_strat│   └→│ game_id (FK)    │  │
└─────────────┘   │ │ description │     │ rating_info{}   │  │
                  │ └─────────────┘     │ stats{}         │  │
                  │                     └─────────────────┘  │
                  │                              ↑           │
                  │     ┌──────────────────────┐ │           │
                  │     │       Match          │ │           │
                  │     ├──────────────────────┤ │           │
                  │     │ id (PK)              │ │           │
                  │     │ game_id (FK)         │─┘           │
                  │     │ played_at            │             │
                  │     │ match_metadata{}     │             │
                  │     └──────────────────────┘             │
                  │              │                           │
                  │              ↓                           │
                  │     ┌──────────────────────┐             │
                  └────→│  MatchParticipant    │─────────────┘
                        ├──────────────────────┤
                        │ id (PK)              │
                        │ match_id (FK)        │
                        │ player_id (FK)       │
                        │ team_id              │
                        │ outcome{}            │
                        │ rating_info_before{} │
                        │ rating_info_change{} │
                        └──────────────────────┘
```

**JSON Field Schemas:**

`GameProfile.rating_info`:
```json
{
  "rating": 1500.0,
  "rd": 350.0,
  "vol": 0.06
}
```

`GameProfile.stats`:
```json
{
  "matches_played": 42,
  "wins": 25,
  "losses": 17,
  "win_rate": 0.595
}
```

`MatchParticipant.outcome`:
```json
// Binary
{"result": "win"}  // or "loss", "draw"

// Ranked
{"rank": 1}  // 1st place

// Scored
{"result": "win", "score": 11, "opponent_score": 8}
```

`Match.match_metadata`:
```json
{
  "type": "Official Pickleball Rules",
  "final_score": "11-8",
  "source": "Historical Import 2025-11-09"
}
```

### API Design

**RESTful Conventions:**
- Resource-based URLs: `/players`, `/games`, `/matches`
- HTTP methods: GET (read), POST (create), PUT (update), DELETE (remove)
- Status codes: 200 (success), 201 (created), 204 (no content), 404 (not found)
- JSON request/response bodies

**Current Endpoints:**
```
Players:
  POST   /players/                Create player
  GET    /players/                List all players
  GET    /players/{id}            Get single player
  PUT    /players/{id}            Update player
  DELETE /players/{id}            Delete player

Games:
  POST   /games/                  Create game
  GET    /games/                  List all games
  GET    /games/{id}              Get single game
  PUT    /games/{id}              Update game
  DELETE /games/{id}              Delete game

Matches:
  POST   /matches/                Create match (triggers rating calc)
  GET    /matches/                List all matches
  GET    /matches/{id}            Get single match
  DELETE /matches/{id}            Delete match
```

**Planned Endpoints:**
```
Leaderboard:
  GET    /games/{id}/leaderboard  Get ranked players for game
         ?sort=rating|wins|winrate
         ?limit=50

Player Stats:
  GET    /players/{id}/stats      Get player statistics
  GET    /players/{id}/matches    Get player's match history
         ?game_id=1&limit=20

Matchmaking:
  POST   /matchmaking/generate    Generate balanced teams
         Body: {game_id, player_ids[], constraints?}
         Response: [{teams: [[id...], [id...]], fairness: 0.95}, ...]

Health:
  GET    /health                  Health check for monitoring
```

---

## Development Guidelines

### Code Quality Standards

**Testing Requirements:**
- Unit tests for all business logic functions
- Integration tests for API endpoints
- Test coverage target: >80%
- All async code tested with pytest-asyncio
- Use in-memory SQLite for test isolation

**Documentation Standards:**
- Docstrings for all public functions/classes
- Type hints on all function signatures
- Complex algorithms explained in comments
- README updated for new features

**Code Review Process:**
- All changes via pull request
- At least one review before merge (even for solo development - use self-review checklist)
- CI must pass before merge
- Squash merge for clean history

**Linting/Formatting:**
- Ruff for linting (E, F, I rules)
- Ruff for formatting (88 char line length, double quotes)
- Mypy for type checking (strict mode)
- Pre-commit hooks enforce on every commit

### Git Workflow

**Branching Strategy:**
```
main (protected)
  └── feature/matchmaking-algorithm
  └── feature/frontend-leaderboard
  └── fix/rating-edge-case
  └── docs/api-examples
```

**Branch Naming:**
- `feature/` - New functionality
- `fix/` - Bug fixes
- `refactor/` - Code improvements without behavior change
- `docs/` - Documentation only
- `chore/` - Maintenance (dependencies, CI, etc.)

**Commit Message Convention:**
```
type(scope): short description

Longer explanation if needed.

Closes #123
```

Types: feat, fix, docs, refactor, test, chore

**PR Requirements:**
- Descriptive title and description
- Link to related issue(s)
- Screenshots for UI changes
- Test coverage maintained or improved
- No linting/type errors

### Production Readiness Checklist

- [ ] Comprehensive test coverage (>80%)
- [ ] API documentation (OpenAPI/Swagger) - auto-generated by FastAPI
- [ ] User documentation (README, guides)
- [ ] Deployment automation (CI/CD)
- [ ] Monitoring and logging (Sentry, structured logs)
- [ ] Security audit completed (OWASP top 10 review)
- [ ] Performance benchmarks met (<200ms API, <3s frontend load)
- [ ] Accessibility standards met (WCAG 2.1 AA for frontend)
- [ ] Mobile responsive design
- [ ] Error handling covers all edge cases
- [ ] Database migrations tested on production-like data
- [ ] Rollback procedure documented

---

## Open Source Considerations

### Repository Setup

**Files to Create:**
- [x] LICENSE (MIT - already present)
- [x] README.md (needs expansion)
- [ ] CONTRIBUTING.md
- [ ] CODE_OF_CONDUCT.md
- [ ] .github/ISSUE_TEMPLATE/bug_report.md
- [ ] .github/ISSUE_TEMPLATE/feature_request.md
- [ ] .github/PULL_REQUEST_TEMPLATE.md
- [ ] .github/workflows/ci.yml
- [ ] .github/FUNDING.yml (optional)

### Documentation Requirements

**Installation Guide:**
- Prerequisites (Python, Node.js, Docker)
- Step-by-step setup for development
- Environment variable reference
- Database initialization
- Running tests

**Configuration Guide:**
- All environment variables explained
- Rating engine configuration
- Matchmaking algorithm parameters
- Production vs. development settings

**API Documentation:**
- OpenAPI spec (auto-generated)
- Example requests/responses
- Authentication (if added)
- Rate limits (if added)

**Architecture Documentation:**
- System overview diagram
- Database schema
- Rating algorithm explanation
- Matchmaking algorithm paper

**User Guide:**
- Recording matches
- Understanding ratings
- Using matchmaking
- Viewing statistics

**Developer Guide:**
- Project structure
- Adding new rating engines
- Adding new API endpoints
- Testing strategies

### Community Building

**Strategies for Attracting Contributors:**
1. Well-labeled "good first issue" tags
2. Clear CONTRIBUTING.md with setup instructions
3. Responsive to issues and PRs
4. Recognition in README for contributors
5. Detailed issue descriptions with context

**GitHub Profile Optimization:**
- Detailed "About" section with live demo link
- Topics/tags: rating-system, matchmaking, fastapi, react, glicko2, sports-analytics
- Social preview image (screenshot or logo)
- Pinned on profile

**Portfolio Presentation:**
- Featured in GitHub profile README
- Deployed demo with sample data
- Blog post explaining the project
- Video walkthrough of features

---

## Timeline & Milestones

### Realistic Schedule (3-6 hours/week)

| Phase | Duration | Hours | Target Completion |
|-------|----------|-------|-------------------|
| Phase 0: Foundation | 5-10 weeks | 23-30 | Week 10 |
| Phase 1: Matchmaking | 8-16 weeks | 39-49 | Week 26 |
| Phase 2: Frontend | 10-21 weeks | 50-64 | Week 47 |
| Phase 3: Deployment | 6-13 weeks | 30-38 | Week 60 |
| Phase 4: Documentation | 5-12 weeks | 28-35 | Week 72 |

**Total: ~170-216 hours over 12-18 months**

*Note: Phases can overlap. For example, documentation can start during Phase 2.*

### Key Milestones

1. **Backend API Complete** - End of Phase 0
   - All planned endpoints functional
   - Leaderboard and stats available
   - Docker development environment working

2. **Matchmaking MVP** - End of Phase 1
   - Algorithm generates balanced teams
   - API endpoint available
   - Algorithm documented

3. **Frontend Alpha** - Mid-Phase 2
   - Match recording works end-to-end
   - Leaderboard displays correctly
   - Deployed to staging environment

4. **Full MVP** - End of Phase 2
   - All four user flows complete
   - Responsive design working
   - Ready for friend group testing

5. **Production Launch** - End of Phase 3
   - Deployed to production
   - CI/CD pipeline operational
   - Error tracking in place

6. **Open Source Ready** - End of Phase 4
   - Comprehensive documentation
   - Contributor-friendly repository
   - Portfolio presentation complete

### Contingency Planning

**Buffer Time:**
- Each phase includes ~20% buffer in estimates
- Phase 3 and 4 can be compressed if behind schedule
- MVP can be redefined to ship faster

**Risk Mitigation:**

| Risk | Impact | Mitigation |
|------|--------|------------|
| Matchmaking algorithm complexity | High | Start simple, iterate |
| Frontend learning curve | Medium | Follow tutorials, use component libraries |
| Deployment issues | Medium | Use PaaS (Railway/Render) to minimize DevOps |
| Scope creep | High | Strict MVP definition, defer features |
| Burnout | High | Sustainable 3-6 hrs/week, celebrate milestones |

---

## Success Metrics

### Project Completion Criteria

- [ ] All MVP features implemented and tested
- [ ] Production deployment successful and stable
- [ ] Documentation complete and accessible
- [ ] Code quality standards met (>80% coverage, no linting errors)
- [ ] Repository ready for public consumption
- [ ] At least one full end-to-end usage session with friends

### Portfolio/Resume Impact

**Resume Bullet Point:**
> Designed and built RankForge, a full-stack rating and matchmaking platform using FastAPI, React, PostgreSQL, and TypeScript. Implemented Glicko-2 algorithm and novel matchmaking system using skill distribution superposition and simulated annealing. Deployed as open-source with comprehensive documentation.

**LinkedIn Presentation:**
- Featured project with live demo link
- Skills highlighted: Python, TypeScript, React, FastAPI, Algorithm Design, Data Science
- Engagement through posts about development journey

**GitHub Profile:**
- Pinned repository with star count
- Active commit history showing consistency
- Professional README with screenshots

**Technical Interview Material:**
- Algorithm design decisions
- System architecture trade-offs
- Testing strategies
- Production deployment experience

### User Engagement Goals

**Friend Group Adoption:**
- Target: 5-10 active users among friends
- Target: 20+ matches recorded per month
- Target: Weekly matchmaking usage for game nights

**Feature Adoption:**
- 100% of matches recorded through app (vs. manual tracking)
- 80%+ of sessions use matchmaking feature
- Players check leaderboard at least weekly

---

## Resources & References

### Technical Resources

**Rating Systems:**
- [Glicko-2 Paper (Glickman)](http://www.glicko.net/glicko/glicko2.pdf)
- [Wikipedia: Glicko Rating System](https://en.wikipedia.org/wiki/Glicko_rating_system)
- [TrueSkill Paper (Microsoft)](https://www.microsoft.com/en-us/research/publication/trueskill-a-bayesian-skill-rating-system/)

**FastAPI:**
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0 Tutorial](https://docs.sqlalchemy.org/en/20/tutorial/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)

**React/Frontend:**
- [React Documentation](https://react.dev/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [React Query Documentation](https://tanstack.com/query/latest)
- [Vite Documentation](https://vitejs.dev/guide/)

**Deployment:**
- [Railway Documentation](https://docs.railway.app/)
- [Render Documentation](https://render.com/docs)
- [Docker Documentation](https://docs.docker.com/)

### Similar Projects

- [openskill.js](https://github.com/philihp/openskill.js) - Rating library implementing Weng-Lin model
- [lichess.org](https://github.com/lichess-org/lila) - Open source chess platform with Glicko-2
- [trueskill](https://github.com/sublee/trueskill) - Python implementation of TrueSkill
- [ratings](https://github.com/atomicjolt/ratings) - Multi-algorithm rating library

### Tools & Services

**Development:**
- [VS Code](https://code.visualstudio.com/) - Editor
- [Insomnia](https://insomnia.rest/) / [Postman](https://www.postman.com/) - API testing
- [TablePlus](https://tableplus.com/) - Database GUI

**Deployment:**
- [Railway](https://railway.app/) - Backend hosting (free tier available)
- [Render](https://render.com/) - Alternative backend hosting
- [Vercel](https://vercel.com/) - Frontend hosting
- [Netlify](https://www.netlify.com/) - Alternative frontend hosting
- [Supabase](https://supabase.com/) - Managed PostgreSQL (free tier)

**CI/CD:**
- [GitHub Actions](https://github.com/features/actions) - CI/CD pipelines

**Monitoring:**
- [Sentry](https://sentry.io/) - Error tracking (free tier)

---

## Next Immediate Actions

Start here. These are the first tasks to tackle in order:

1. **Externalize Database Configuration** (1 hour)
   - Move database URL from [session.py](src/rankforge/db/session.py) to environment variable
   - Update `.env.example` with required variables
   - Test with both SQLite and PostgreSQL connection strings

2. **Add Leaderboard Endpoint** (3-4 hours)
   - Create `GET /games/{game_id}/leaderboard` endpoint
   - Return players sorted by rating with GameProfile info
   - Add Pydantic schema for leaderboard response
   - Write integration tests

3. **Add Player Stats Endpoint** (3-4 hours)
   - Create `GET /players/{player_id}/stats` endpoint
   - Aggregate win/loss/match counts per game
   - Include rating info per game
   - Write integration tests

4. **Set Up Docker Development** (3-4 hours)
   - Create Dockerfile for backend
   - Create docker-compose.yml with app + PostgreSQL
   - Document docker development workflow in README

5. **Begin Matchmaking Design Document** (3-4 hours)
   - Write out algorithm specification
   - Define API contract for matchmaking endpoint
   - Create service interface and schemas
   - This becomes the foundation for Phase 1

---

**Document Version:** 1.0
**Last Updated:** 2025-12-19
**Next Review:** After Phase 0 completion

---

*This document should be treated as a living plan. Review and update after each phase completion or when priorities change significantly.*
