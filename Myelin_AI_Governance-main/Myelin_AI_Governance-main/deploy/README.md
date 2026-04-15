# Myelin Deployment Without Docker

This repository can be deployed with Git plus a process manager.

## Windows flow

1. Clone the repo
2. Run `deploy/scripts/bootstrap_agent.ps1`
3. Configure `agent/.env`
4. Start the agent from `agent/` with the virtualenv Python

To update later:

```powershell
deploy/scripts/pull_and_restart.ps1
```

## Linux flow

1. Clone the repo to a fixed path such as `/opt/myelin/Myelin_AI_Governance-main`
2. Create a virtual environment and install dependencies
3. Configure `agent/.env`
4. Copy `deploy/systemd/myelin-agent.service` into `/etc/systemd/system/`
5. Adjust paths and user values in the service file
6. Run:

```bash
sudo systemctl daemon-reload
sudo systemctl enable myelin-agent
sudo systemctl start myelin-agent
```

## Operational endpoints

If `MYELIN_OPERATIONAL_TOKEN` is set, include this header for ops routes:

```text
X-Myelin-Ops-Token: your-token
```

Protected routes:

- `/incidents/recent`
- `/metrics`
