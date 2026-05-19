# Autonomous Shortform Content Engine

An AI-powered media automation pipeline that discovers trends, generates scripts, synthesizes voiceovers, renders 9:16 vertical videos, and posts them to social media autonomously.

---

## Prerequisites

Before you begin, ensure you have the following installed:

*   **Python 3.12+**
*   **PostgreSQL** (Database)
*   **Redis** (Message Broker for Celery)
*   **FFmpeg** (Required for video rendering)
*   **ImageMagick** (Optional, required for MoviePy TextClips)

---

## Installation

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/your-repo/autonomous-shortform-engine.git
    cd autonomous-shortform-engine
    ```

2.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Setup Environment Variables:**
    ```bash
    cp .env.example .env
    ```
    Populate your `.env` with the following keys:
    *   `OPENAI_API_KEY`: For workflow planning and scriptwriting.
    *   `GEMINI_API_KEY`: For trend research and discovery.
    *   `ELEVENLABS_API_KEY`: For high-quality voice synthesis.
    *   `ZERNIO_API_KEY` & `ZERNIO_TIKTOK_ACCOUNT_ID`: For TikTok publishing.
    *   `DATABASE_URL`: Your PostgreSQL connection string.

---

## Database Setup

Initialize your database schema using Alembic:

```bash
# Generate the initial migration
alembic revision --autogenerate -m "initial_schema"

# Apply the migration to your database
alembic upgrade head
```

---

## Running the Engine (Local Testing)

The system requires three processes running simultaneously. It is recommended to use three separate terminal windows:

### 1. Start the API & Dashboard
Serves the control panel at `http://localhost:8000`.
```bash
uvicorn src.api.main:app --reload
```

### 2. Start the Celery Worker
The "muscle" that executes the actual tasks (Scraping, TTS, Rendering).
```bash
export PYTHONPATH=$PYTHONPATH:.
celery -A src.core.celery_app worker -Q orchestrator_queue --loglevel=info
```

### 3. Start the Celery Beat (Autonomous Heartbeat)
The "brain" that checks for pending tasks and triggers the dispatcher every 30 seconds.
```bash
export PYTHONPATH=$PYTHONPATH:.
celery -A src.core.celery_app beat --loglevel=info
```

---

## Testing the Workflow

1.  **Access the Dashboard:** Open `http://localhost:8000` in your browser.
2.  **Submit a Goal:** In the "New Goal" input, type a high-level directive:
    > *"Find a trending AI tool for software productivity and post a viral TikTok video about it."*
3.  **Monitor the Plan:**
    *   The `OrchestratorPlanner` will generate a 5-step DAG of tasks.
    *   Click **"Details"** on the new workflow to see the tasks in `PENDING` state.
4.  **Watch the Execution:**
    *   Every 30 seconds, the Beat process will trigger the dispatcher.
    *   The Worker will pick up tasks sequentially.
    *   You will see JSON data (scripts, audio paths, video paths) being injected from one task into the next.
5.  **Verify Output:**
    *   **Audio:** Check `storage/media/` for generated `.mp3` files.
    *   **Video:** Check `storage/media/final/` for the completed `.mp4` video.
    *   **Social:** If Zernio is configured, the video will be pushed to your TikTok account.

---

## Project Structure

*   `src/orchestrator`: AI Planning logic (GPT-4).
*   `src/tasks`: Background execution and task dispatching.
*   `src/tools`: Individual execution units (Gemini Research, ElevenLabs TTS, FFmpeg Rendering).
*   `src/api`: FastAPI dashboard and routes.
*   `src/models`: Database schemas (Workflows, Tasks, Analytics).
*   `storage/media`: Local storage for all generated content assets.
