import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ENV_ROOT = os.environ.get("GODMODE_REPO_ROOT")
REPO_ROOT = Path(ENV_ROOT).resolve() if ENV_ROOT else SCRIPT_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from api.agent_shell import GodModeAgent  # noqa: E402

def main():
    goal = (
        "Analyze this repository and list all missing pieces required to fully "
        "implement the God Mode system as designed, including agents, HUD wiring, "
        "memory backends, and revenue modules."
    )
    agent = GodModeAgent(goal=goal, repo_root=str(REPO_ROOT))
    result = agent.run()
    print("\\nFINAL RESULT:\\n")
    print(result)

if __name__ == "__main__":
    main()
