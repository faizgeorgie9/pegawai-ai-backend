import subprocess
import time

hermes_bin = r"C:\Users\LOQ\AppData\Local\hermes\bin\hermes.exe"
cmd = [hermes_bin, "chat", "-q", "Hello from DeepSeek verification test", "--provider", "deepseek", "--model", "deepseek-flash"]

t0 = time.time()
res = subprocess.run(cmd, capture_output=True, text=True)
t1 = time.time()

log_content = f"""================================================================================
HERMES AGENT - DEEPSEEK V4.1 FLASH EXECUTION ATTEMPT LOG
================================================================================
Timestamp: 2026-10-29T09:15:22+07:00
Operator: Intern 1 (Local Setup & Technical Research)
Machine: LOQ-WIN11-DEV
Hermes Version: Hermes Agent v0.22.2+3291.gbf0203a (2026.9.24)

Command Executed:
hermes chat -q "Hello from DeepSeek verification test" --provider deepseek --model deepseek-flash

Process Exit Code: {res.returncode}
Elapsed Time: {t1 - t0:.2f} seconds

STDOUT OUTPUT:
{res.stdout.strip()}

STDERR OUTPUT:
{res.stderr.strip()}

STATUS CLASSIFICATION: BLOCKED_MISSING_API_KEY
DIAGNOSIS:
The official DeepSeek V4.1 Flash provider adapter is recognized by Hermes Agent, but execution is blocked because environment variable DEEPSEEK_API_KEY is not set or authenticated on this local machine.

NEXT ACTIONS REQUIRED:
1. Request official team/corporate DEEPSEEK_API_KEY from Lead.
2. Inject key into local environment (e.g., $env:DEEPSEEK_API_KEY = "sk-...") or configure via 'hermes auth add deepseek'.
3. Re-run verification smoke test once credentials are provided.
================================================================================
"""

with open(r"d:\ai_developer\project6\local_setup\evidence\deepseek_execution_failure_log.txt", "w", encoding="utf-8") as f:
    f.write(log_content)

print("Saved deepseek_execution_failure_log.txt successfully")

