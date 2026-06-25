# Configuration

re-agent is configured via `re-agent.yaml`, environment variables, and CLI flags.

## Priority Order

CLI flags > Environment variables > YAML config > Defaults

## Environment Variables

| Variable | Maps to |
|----------|---------|
| `RE_AGENT_LLM_PROVIDER` | `llm.provider` |
| `RE_AGENT_LLM_API_KEY` | `llm.api_key` |
| `RE_AGENT_LLM_MODEL` | `llm.model` |
| `RE_AGENT_LLM_BASE_URL` | `llm.base_url` |
| `RE_AGENT_BEDROCK` | `llm.use_bedrock` |
| `RE_AGENT_LLM_AWS_REGION` | `llm.aws_region` |
| `RE_AGENT_BACKEND_CLI_PATH` | `backend.cli_path` |
| `RE_AGENT_BACKEND_TIMEOUT` | `backend.timeout_s` |

## LLM Config

```yaml
llm:
  provider: "claude"        # claude | openai | openai-compat | codex
  model: "us.anthropic.claude-opus-4-6-v1"  # Bedrock inference profile (default)
  use_bedrock: true         # false -> direct Anthropic / OpenAI-compatible API
  aws_region: null          # Bedrock region; falls back to AWS_REGION
  api_key: null             # direct mode only
  base_url: null            # direct mode only
  max_tokens: 4096
  temperature: 0.0
  timeout_s: 1800
```

Notes:

- `claude` defaults to AWS Bedrock (`use_bedrock: true`) with the `us.anthropic.claude-opus-4-6-v1` inference profile, reading AWS credentials from the standard chain. Set `use_bedrock: false` to use the direct Anthropic API (`ANTHROPIC_API_KEY`)
- `openai` and `openai-compat` use the OpenAI-compatible chat completions provider and typically read `OPENAI_API_KEY`
- `codex` uses the local `codex` CLI and ChatGPT login credentials instead of an API key

## Project Profile

The `project_profile` section makes re-agent work across different RE projects:

```yaml
project_profile:
  hook_patterns:
    - 'RH_ScopedInstall\s*\(\s*(\w+)\s*,\s*(0x[0-9A-Fa-f]+)'
  stub_markers: ["NOTSA_UNREACHABLE"]
  stub_call_prefix: "plugin::Call"
  source_root: "./source/game_sa"
  source_extensions: [".cpp", ".h", ".hpp"]
```

## Parity Config

```yaml
parity:
  enabled: true
  call_count_warn_diff: 3
  inline_wrapper_autoskip: false
```

## Orchestrator Config

```yaml
orchestrator:
  max_review_rounds: 4
  max_functions_per_class: 10
  objective_verifier_enabled: true
  objective_call_count_tolerance: 3
  objective_control_flow_tolerance: 2
```
