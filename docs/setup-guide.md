# Setup Guide

## Prerequisites
- Git
- GitHub account
- IBM Bob installed and an IBMid
- Python 3.11 or newer
- Windows, macOS, or Linux

IBM Bob's getting-started guide says to download Bob from `bob.ibm.com/download`, create/sign in with an IBMid, and use Agent/Ask/Plan modes for implementation, questions, and planning.

## 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/bob-ai-hackathon-YOUR_TEAM.git
cd bob-ai-hackathon-YOUR_TEAM
```

## 2. Create a virtual environment
Windows PowerShell:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 3. Install dependencies
```bash
pip install -r src/requirements.txt
```

## 4. Run the app
```bash
streamlit run src/app.py
```

Open the local URL shown by Streamlit, usually `http://localhost:8501`.

## 5. Verify Signal Detection
- Open **Signal Detection**.
- Click **Load demo data**.
- Confirm the table appears.
- Click **Run signal detection**.
- Confirm PRR and flag columns appear.
- Download the CSV report.

## 6. Verify Submission Readiness
- Open **Submission Readiness**.
- Click **Load demo CTD outline**.
- Click **Check readiness**.
- Confirm module scores and missing-section table appear.
- Download the gap report.

## Environment variables
None are required for the offline prototype. If you add external services later, document every variable in `src/.env.example` and never commit `.env`.

## Troubleshooting

| Error | Fix |
|---|---|
| `python` not found | Install Python and reopen the terminal |
| `streamlit` not found | Activate `.venv`, then run `pip install -r src/requirements.txt` |
| Port 8501 busy | Run `streamlit run src/app.py --server.port 8502` |
| PowerShell blocks activation | Run `Set-ExecutionPolicy -Scope Process Bypass` and activate again |
| CSV validation error | Ensure columns are exactly `drug,event` or use the demo dataset |

## Clean-machine test
Create a new terminal, clone the repo, create a fresh `.venv`, install requirements, and follow this document from step 1 without using any files outside the repository.
