# God Mode Infrastructure & Scaling Specification

## Current State

- Single Mac mini running:
  - Docker Desktop
  - Tailscale
  - api, hud, postgres, redis, qdrant containers
- `gmup`:
  - Starts everything + autopilot
- Existing HUD:
  - Canonical dashboard until explicitly replaced.

## Scaling Goals

- Add more nodes (cloud or local) that:
  - Run copies of the same stack.
  - Share:
    - Code
    - Config
    - Tasks
    - Memory (where appropriate).
- Maintain a single logical “God Mode” view via the HUD and/or its successor.

## Node Types

- Control Node:
  - Current Mac mini.
  - Hosts central tasks/roadmap and primary DB.
  - Hosts the canonical HUD.

- Worker Nodes:
  - Additional machines/servers.
  - Run subsets of agents (heavy jobs, scraping, content generation).
  - Host specialized services (GPU inference, scraping, media rendering).

## Infrastructure Topology (Future State)

- **Local inference cluster** – control node + GPU worker(s) connected via Tailscale. Hosts orchestrator, vector DB, graph DB, Redis/queues.
- **Cloud training cluster** – distributed GPUs/TPUs (DeepSpeed/Megatron) for pre-training/fine-tuning multilingual models.
- **Data layer** – Postgres (transactions), Qdrant/Milvus/FAISS (embeddings), Neo4j (knowledge graph).
- **Inference services** – stateless API pods, caching tiers, load balancers, autoscaling rules.
- **Message bus** – Redis/NATS/Kafka for inter-agent communication and task queues.
- **Monitoring/logging** – Prometheus/Grafana/Loki (or similar) to trace agent lifecycles end-to-end.

## Minimal Initial Plan

- Phase 1:
  - Keep Mac mini as sole control node.
  - Document how a worker would:
    - Pull latest code (git).
    - Get env/keys (manual for now).
    - Connect via Tailscale.

- Phase 2:
  - Centralize:
    - Tasks in a DB.
    - Logs in a shared store.

- Phase 3:
  - Auto-register new nodes:
    - On startup, node reports to control node.
    - Gets assigned tasks.

## Deployment Pipeline (Target)

1. Provision infra (K8s clusters or bare-metal nodes) with secure networking + IAM.
2. Containerize services; use docker compose locally, Helm/manifests for production deployments.
3. Orchestrate vector DB, graph DB, inference pods, queues; configure autoscaling policies.
4. Run CI/CD (GitHub Actions) with tests, build artifacts, blue/green rollouts, and health checks.
5. Offer appliance tier (pre-configured Mac mini) that automatically joins the mesh via Tailscale.

## Agent Deployment & Scaling

- Persistent agents run as long-lived pods pinned to specific nodes.
- Dynamic/burst agents spin up via serverless containers or short-lived pods triggered by the scheduler.
- Scheduler considers agent skill tags, queue depth, and node load before dispatching.
- Agents authenticate to memory/tools using short-lived scoped credentials.

## Security Considerations (High-Level)

- Do not expose raw Docker ports to the public internet.
- Use Tailscale for node-to-node communication.
- Keep secrets out of git (use env / .env / secret store).
- Limit which nodes can modify which parts of the system.

## Existing HUD vs Future Interfaces

- The existing HUD is the primary interface for infra visibility.
- If new desktop/mobile/frontends are built:
  - They should rely on the same backend API and model of the world.
  - Old HUD can be deprecated only after new interfaces are fully functional and documented.

## Agent Responsibilities

- Read this spec when planning infra tasks.
- Propose:
  - Scripts for bootstrapping a new worker node.
  - DB schema for multi-node task tracking (future).
- Implement incremental, safe changes versus big-bang rewrites.

## AUTOGEN: Autonomous Growth Behavior

As new nodes are added in the future:

- They should pull the same design docs and roadmap so they inherit:
  - Knowledge of streams.
  - HUD/API structure.
  - Self-improvement logic.
- Control node (Mac mini for now) remains the canonical source for:
  - tasks/roadmap.jsonl
  - central ledger (if DB-based)
  - core design_docs/

Agents working on infra must:
- Ensure that any scaling scripts respect security rules (no public DB exposure).
- Document bootstrap steps for new nodes.
