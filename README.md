# RankForge

A modern, full-stack rating and matchmaking system designed to handle any competitive game. RankForge provides a flexible architecture for tracking player ratings, match histories, and generating balanced teams for any number of players and team structures.

## Core Features

-   **Game Agnostic:** The unified database schema is designed to handle a wide variety of games, from 1v1 win/loss scenarios to complex team-based, multi-outcome formats.
-   **Modern Tech Stack:** Built with a professional, asynchronous Python backend using FastAPI and SQLAlchemy 2.0.
-   **Flexible Rating System:** The architecture supports multiple rating algorithms, allowing each game to have its own custom logic (e.g., Glicko-2, Elo).
-   **Automated Quality Checks:** The development environment is configured with Ruff and Mypy, enforced by pre-commit hooks to ensure high-quality, consistent code.
-   **Database Migrations:** Uses Alembic to manage database schema changes in a safe and reproducible way.

## Tech Stack

-   **Backend:** [FastAPI](https://fastapi.tiangolo.com/)
-   **Database ORM:** [SQLAlchemy 2.0](https://www.sqlalchemy.org/) (Async with `aiosqlite`)
-   **Database Migrations:** [Alembic](https://alembic.sqlalchemy.org/)
-   **Linting & Formatting:** [Ruff](https://github.com/astral-sh/ruff)
-   **Type Checking:** [Mypy](http://mypy-lang.org/)
-   **Planned Database:** [PostgreSQL](https://www.postgresql.org/) (using SQLite for initial development)

---

## Getting Started

Follow these instructions to set up the development environment and run the application locally.

### Prerequisites

-   Python 3.10+
-   [Git](https://git-scm.com/)

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/RankForge.git
cd RankForge
```

### 2. Set Up the Virtual Environment

It is highly recommended to use a virtual environment to manage project dependencies.

**On Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**On macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

The project uses `pyproject.toml` to define its dependencies. Install the project in "editable" mode along with the development tools:

```bash
pip install --upgrade pip
pip install -e .[dev]
```

### 4. Set Up Pre-commit Hooks

This will install the pre-commit hooks, which automatically check and format your code before each commit.

```bash
pre-commit install
```

### 5. Initialize the Database

The project uses Alembic to manage the database schema. The following commands will create the initial SQLite database file (`rankforge.db`) and set up the necessary tables.

_Note: If you make changes to the models in `src/rankforge/db/models.py`, you will need to generate a new migration._

**Create the initial migration (only needed if one doesn't exist):**
```bash
# This command compares the models with the database and generates a migration script.
alembic revision --autogenerate -m "Create initial database tables"
```

**Apply the migration to create the database tables:**
```bash
# This command runs the migration scripts to update the database.
alembic upgrade head
```
After this step, you will see a `rankforge.db` file in the root of the project.

### 6. Run the Application

The application is served using Uvicorn. The `--reload` flag enables hot-reloading for development.

```bash
uvicorn rankforge.main:app --reload --app-dir src
```

The API will now be available at [http://127.0.0.1:8000](http://127.0.0.1:8000).

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
