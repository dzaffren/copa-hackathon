# Three-Tier Model Configuration

**Ticket:** TBD
**Type:** Technical — Infrastructure

Adds two new model deployment configuration options so that each stage of the Arm G finding pipeline can be directed to the right-sized model. Currently every processing step — from extracting a topic phrase to scanning an entire document — is forced through the same large, expensive model. This story introduces separate configuration for the extraction step (small, fast model) and the per-pair judgment step (mid-tier model), while leaving the existing large-model configuration in place for the whole-document coverage step. This is the prerequisite for Story 2, which wires up the full pipeline.

## Motivation

**Current state:** The engine has a single model deployment setting that all processing steps share. There is no way to route a lightweight topic-extraction task to a small model and reserve the large model for the one step — whole-document coverage reasoning — that genuinely needs it. All three stages of the future Arm G pipeline would be forced through the large model even though two of the three stages do not require deep reasoning at all.

**Desired state:** Three independent model deployment settings exist in the engine configuration — one for topic extraction (small/fast), one for per-pair batched judgment (mid-tier), and the existing one for whole-document coverage reasoning (large). Each setting has a safe, sensible default so the pipeline works out of the box without any manual environment setup. Any operator can override any or all three by setting the corresponding configuration value in their environment.

**Trigger:** Story 2 (the Arm G pipeline) cannot be built without a way to direct different pipeline stages to different models. This configuration work is the explicit dependency listed in the epic's story index.

## Scope

- **In scope:**
  - A new configuration setting for the axis extraction stage, with a default model name appropriate for a small, fast extraction task
  - A new configuration setting for the per-pair batched judgment stage, with a default model name appropriate for a mid-tier reasoning task
  - Both new settings follow the same pattern as the three existing deployment settings already present in the engine configuration
  - Both new settings are documented alongside the existing deployment settings, including what each one is used for and what the default value is
  - The existing large-model deployment setting remains unchanged and continues to serve as the default for the whole-document coverage stage

- **Out of scope:**
  - Any change to how model calls are actually made (that is Story 2)
  - Any cost tracking, token counting, or usage reporting
  - Changing or replacing the existing deployment settings for the parser, the finder/critic, or the copilot
  - Any frontend changes

## Goals

- Any operator can configure the extraction and judgment stages independently by setting two new environment variables, with no change required to any other setting.
- All three existing deployment settings continue to work exactly as before — no existing behavior changes.
- The two new settings have sensible defaults so the pipeline operates correctly on a fresh install with no environment configuration.
- The new settings are described clearly enough that an operator reading the configuration file understands which pipeline stage each one governs and why a given model tier is appropriate.

## Non-Goals

- Validating that the configured model names are reachable or correctly spelled — that is a runtime concern.
- Surfacing the configured model names in any user interface.
- Building a mechanism to switch between models at analysis time based on document size or any other signal.
- Adding configuration for any stage beyond the three covered by this story.

## Success Criteria

- An environment with only the extraction variable set uses that model for axis extraction and falls back to the mid-tier default for judgment.
- An environment with only the judgment variable set uses that model for per-pair judgment and falls back to the small-model default for extraction.
- An environment with neither new variable set still operates correctly using the built-in defaults for both stages.
- An environment with both new variables set uses the configured model for each respective stage.
- The existing large-model deployment variable continues to govern the whole-document coverage stage regardless of what the two new variables are set to.
- No existing functionality — clause parsing, the finder/critic loop, the drafting copilot — changes behavior in any environment, regardless of whether the new variables are set.

## Acceptance Criteria

### Scenario: Extraction model uses the configured value when the variable is set

```gherkin
Given the extraction deployment variable is set to "gpt-4o-mini"
  And the judgment deployment variable is not set
When the engine configuration is loaded
Then the extraction stage is directed to "gpt-4o-mini"
  And the judgment stage falls back to the mid-tier default
  And the whole-document coverage stage is directed to the existing large-model deployment value
```

### Scenario: Judgment model uses the configured value when the variable is set

```gherkin
Given the judgment deployment variable is set to "claude-sonnet-5"
  And the extraction deployment variable is not set
When the engine configuration is loaded
Then the judgment stage is directed to "claude-sonnet-5"
  And the extraction stage falls back to the small-model default
  And the whole-document coverage stage is directed to the existing large-model deployment value
```

### Scenario: Both new variables unset — defaults take effect

```gherkin
Given neither the extraction deployment variable nor the judgment deployment variable is set
When the engine configuration is loaded
Then the extraction stage is directed to the built-in small-model default
  And the judgment stage is directed to the built-in mid-tier default
  And the whole-document coverage stage is directed to the existing large-model deployment value
```

### Scenario: All three coverage-pipeline variables set simultaneously

```gherkin
Given the extraction deployment variable is set to "gpt-4o-mini"
  And the judgment deployment variable is set to "claude-sonnet-5"
  And the existing large-model deployment variable is set to "claude-opus-4-8"
When the engine configuration is loaded
Then the extraction stage is directed to "gpt-4o-mini"
  And the judgment stage is directed to "claude-sonnet-5"
  And the whole-document coverage stage is directed to "claude-opus-4-8"
```

### Scenario Outline: Existing deployment settings are unaffected regardless of new variable state

```gherkin
Given the existing <existing_variable> is set to <existing_value>
  And the new extraction and judgment deployment variables are <new_var_state>
When the engine configuration is loaded
Then <existing_variable> resolves to <existing_value>
  And no other deployment setting changes
```

Examples:
| existing_variable | existing_value | new_var_state |
| finder/critic deployment variable | claude-opus-4-8 | both set |
| finder/critic deployment variable | claude-opus-4-8 | neither set |
| copilot deployment variable | claude-sonnet-5 | both set |
| copilot deployment variable | claude-sonnet-5 | neither set |

### Scenario: New variables are documented alongside existing deployment settings

```gherkin
Given a developer reads the engine configuration module
When they look at the deployment settings section
Then they can see the extraction deployment variable, its default value, and a plain-language description of which pipeline stage it governs
  And they can see the judgment deployment variable, its default value, and a plain-language description of which pipeline stage it governs
  And the two new entries appear alongside — not mixed into — the three existing deployment settings
```

## Constraints

- **Backwards compatibility:** Full. No existing configuration variable changes name, default value, or behavior. Any deployment that does not set the new variables continues to work identically.
- **Downtime:** None required. Configuration changes take effect on the next process start.
- **Compliance:** The model deployment names are read from the environment and never committed to the repository — consistent with the existing pattern for all sensitive credentials and deployment names.
- **Rollback:** Trivially reversible by removing the two new environment variables; the engine falls back to the defaults and no downstream behavior is affected.

## Dependencies

- No other story or external dependency is required before this work begins.
- Story 2 (Arm G finding pipeline) depends on this story being complete before it can route pipeline stages to the correct models.

## Open Questions

- [ ] What are the exact default model names for the extraction and judgment stages? — **Deferred (non-blocking):** The default names will be chosen during implementation based on what is available in the shared Azure AI Foundry resource. The pattern (small/fast for extraction, mid-tier for judgment) is fixed; the specific deployment name strings are an operational detail. Candidates from the existing resource are `gpt-4o-mini` for extraction and `claude-sonnet-5` for judgment, matching the pattern already set by `PARSER_DEPLOYMENT` and `COPILOT_DEPLOYMENT`.
