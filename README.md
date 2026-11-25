# Workspace Python Environments

This workspace provides two Python environments for different use cases.

- **`py3.10-exercises/cd14715-claude-code-classroom/`** → Runs in the system Python 3.10 (no activation needed)

- **`py3.13-exercises-and-project/`** → Must run in the Python 3.13 virtual environment (`source /voc/data/py313-venv/bin/activate`)

**Quick Reference**

| Task | Command |
|------|---------|
| Use system Python (3.10) | `python` (default) |
| Activate Python 3.13 | `source /voc/data/py313-venv/bin/activate` |
| Deactivate Python 3.13 | `deactivate` |
| Check Python version | `python --version` |
| Run Python 3.13 exercises | Activate venv, then run exercise commands |
| Run Python 3.10 exercises | Use default Python without activation |


> ⚠️ **IMPORTANT: Use the correct Python environment for each folder:**

## 1. System Python (Python 3.10)

The default system Python is version 3.10 with a comprehensive set of data science and ML packages pre-installed.

**Usage:**
```bash
python --version
# Python 3.10.x

# Run a script
python your_script.py
```

### 1.1. Python 3.10 Exercises (`py3.10-exercises/cd14715-claude-code-classroom/`)

**Use the default system Python 3.10 for this folder.**

This folder contains exercises designed to run with Python 3.10 and covers Claude Code classroom topics.

**To run exercises with Python 3.10:**
```bash
# 1. Use the default system Python (no activation needed)
python --version  # Should show Python 3.10.x

# 2. Navigate to an exercise folder
cd py3.10-exercises/cd14715-claude-code-classroom/

# 3. Run the exercise with Python 3.10
python your_script.py
```

### 1.2. Installed Packages - System Python (3.10)
See full list in: `py3.10-exercises/requirements.txt`

Includes:
- TensorFlow, PyTorch, Keras
- pandas, numpy, scikit-learn
- langchain, openai, anthropic
- jupyter, matplotlib, seaborn
- And many more data science packages


## 2. Python 3.13 Virtual Environment

A Python 3.13 virtual environment is available with modern tooling packages (anthropic, pytest, mypy, ruff, etc.).

**To activate the Python 3.13 environment:**
```bash
source /voc/data/py313-venv/bin/activate
```

After activation, your prompt will change to show `(py313-venv)` and Python commands will use version 3.13:
```bash
python --version
# Python 3.13.18
```

**To deactivate and return to system Python:**
```bash
deactivate
```


### 2.1. Python 3.13 Exercises and Project (`py3.13-exercises-and-project/`)

**Use Python 3.13 environment for this folder.**

This folder contains:
- **Exercises**: Progressive tutorials on building advanced AI systems with Claude
  - Build a Claims Intake Agent with a stop_reason-Driven Loop
  - Engineer a Long-Conversation Context Strategy for a Retail Support Copilot
  - Configure Claude Code for a Multi-Surface Monorepo Team
  - Build a Multi-Shift Quality Monitoring System with Claude Orchestration

- **Project (Capstone)**: A hands-on integrative project called "Harness Engineering with Claude and Claude Code"
  - Build and run the four completed systems from the course exercises
  - Verify implementations and capture artifacts
  - Write an evidence-grounded reflection brief analyzing architectural decisions

**Each exercise has:**
- `starter/` folder: Fill-in-the-blank exercises for learning
- `solution/` folder: Completed reference implementation

**To run exercises/project with Python 3.13:**
```bash
# 1. Activate the Python 3.13 environment
source /voc/data/py313-venv/bin/activate

# 2. Navigate to an exercise starter folder
cd py3.13-exercises-and-project/Build\ a\ Claims\ Intake\ Agent\ with\ a\ stop_reason-Driven\ Loop/exercises/01-loop/starter

# 3. Run the exercise (example command)
python -m claims_intake.run --all

# 4. When done, deactivate the environment
deactivate
```


### 2.2. Python 3.13 Virtual Environment Packages
See full list in: `py3.13-exercises-and-project/requirements.py313-venv.txt`

Includes:
- anthropic (Claude SDK)
- pydantic
- pytest, mypy, ruff (dev tools)
- uv (fast Python package manager)

