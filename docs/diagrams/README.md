# Architecture diagrams

Mermaid sources (`.mmd`) and rendered PNGs for the Insurance Customer 360 blueprint.

| Diagram | Source | PNG |
| --- | --- | --- |
| Runtime architecture (CAI AMP, warehouse, app, LLM) | [runtime-architecture.mmd](runtime-architecture.mmd) | [runtime-architecture.png](runtime-architecture.png) |
| Logical request flows (REST + SSE paths) | [logical-request-flows.mmd](logical-request-flows.mmd) | [logical-request-flows.png](logical-request-flows.png) |

Regenerate PNGs after editing `.mmd` files:

```bash
npx -y @mermaid-js/mermaid-cli@11 -i docs/diagrams/runtime-architecture.mmd -o docs/diagrams/runtime-architecture.png -b transparent
npx -y @mermaid-js/mermaid-cli@11 -i docs/diagrams/logical-request-flows.mmd -o docs/diagrams/logical-request-flows.png -b transparent
```

Requires Node.js and outbound network for the first `npx` download.
