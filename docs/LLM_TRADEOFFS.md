# LLM selection and trade-offs

## Current position

The default application path uses a deterministic parser for synthetic rows, which keeps the local demo simple and predictable. An optional Ollama agreement-extraction provider is wired behind `LLM_PROVIDER=ollama`; no Ollama runtime or model weights are installed by this repository, and the provider has not been run or quality-evaluated yet. The local environment template names `qwen3.5:4b` as the candidate model.

For a first local candidate, use **Ollama + Qwen3.5 4B quantized** as a quality/performance experiment. Ollama currently lists Qwen3.5 family variants including 4B and 9B; the listed 4B package is roughly 3.3–4.0 GB. The local machine has a 4 GB NVIDIA GTX 1050, so that model is at the edge of VRAM capacity and may have to run partly or entirely on CPU. The 9B candidate is listed around 6.6–7.6 GB and does not fit in 4 GB VRAM. These package sizes do not include all runtime/context overhead, so actual speed and fit must be measured. [Ollama Qwen3.5 model listing](https://ollama.com/library/qwen3.5)

This is a **candidate to evaluate**, not a claim that it is “very good” at legal contract extraction for Apollo's documents. No model benchmark against representative Apollo contracts exists yet. The model's self-reported confidence must not be treated as a calibrated probability.

## Why start with Qwen3.5 4B locally

- It is an open-weights model family currently distributed through Ollama with local text/image input and multiple sizes. [Ollama model page](https://ollama.com/library/qwen3.5)
- The 4B quantized option is the smallest plausible candidate for the present 4 GB GPU. It may still run poorly due to memory overhead; CPU inference is a fallback if system RAM is sufficient.
- Ollama offers a local HTTP API, which can be placed behind a small extraction-provider function and kept out of pricing/billing business logic.
- The 9B sibling is an optional comparison only if CPU/RAM performance is acceptable or a stronger local GPU becomes available.

## Candidate alternatives considered

| Option | Strength | Cost/risk for this MVP | Decision |
|---|---|---|---|
| Deterministic tagged parser | No model download, fast, predictable, easy to inspect. | Only recognizes the generated marker format; cannot understand ordinary contract prose. | Keep as default and fallback. |
| Qwen3.5 4B quantized through Ollama | Local and small among current candidate variants; can be called over local HTTP. | GPU memory is tight, quality unknown for these contracts, CPU may be slow. | First candidate to evaluate, not yet enabled by default. |
| Qwen3.5 9B quantized through Ollama | Larger model may follow longer/legal instructions better than a 4B candidate. | Listed package exceeds current 4 GB GPU; CPU speed and RAM availability are unknown. | Compare only if local hardware supports it. |
| Mistral Small 4 | Apache 2.0, multimodal and document understanding capability; official docs list a 256k context. [Mistral Small 4 announcement](https://mistral.ai/news/mistral-small-4/), [model docs](https://docs.mistral.ai/models/mistral-small-4-0-26-03) | 119B parameters (6.5B active) is far too large for this GPU; local quantized runtime setup would be heavier. | Do not choose for the current local demo machine. Consider hosted or stronger deployment only if policy permits. |
| Cloud model/API | Better hardware and potentially stronger extraction. | Sends contract data outside the workstation; adds credential, privacy, cost, and network requirements. | Not selected; requires explicit data handling approval. |

Model release and availability change. Recheck model cards, license, quantization, and runtime support before downloading or deploying any weights.

## Proposed integration boundary

1. Keep PDF text extraction as a separate step. Use `pypdf` for selectable text; OCR is a separate later provider.
2. Pass page-tagged text to the configured provider. The current Ollama call requests JSON mode and gives the model a field contract in its prompt; Ollama also documents a `format` JSON Schema option, which can replace JSON mode when the chosen model/runtime is validated. [Ollama structured output API](https://github.com/ollama/ollama/blob/main/docs/capabilities/structured-outputs.mdx)
3. Ask for each field's value, exact evidence quote, page number, and missing/ambiguous state. Avoid asking the model to approve or activate pricing.
4. Current checks require the response shape, known or `UNKNOWN` service code, allowed stream/charge type, non-negative numeric amount when supplied, valid page number, and an evidence quote found verbatim on that page. Add deeper cross-field/type validation before relying on the path.
5. Store provider/model/version plus raw evidence and reviewed values for traceability. Treat extracted fields as drafts until Structuring reviews them and Finance completes the separate approval workflow.
6. If the model is not available, fails, times out, or returns invalid JSON/evidence, show an understandable error. Synthetic parsing remains the default; do not silently mark arbitrary prose as successfully extracted.

The extraction provider should be a small function/module, selected from config, not a new microservice or orchestration framework. An Ollama HTTP client can use Python's standard library; no extra dependency is necessary for a first local prototype.

## Evaluation needed before choosing a default

The current marker PDFs do not adequately test legal-document understanding. Create additional synthetic agreements in ordinary prose with varied layouts and clauses. Have a human label expected values and source passages. Measure exact field match, date/rate normalization, false extraction when a term is absent, evidence quote validity, and latency. Include examples with conflicting clauses, amendments, range/tier pricing, and ambiguous phrasing. Keep a human-review gate regardless of the score.

Do not install or download model weights automatically when a user runs the app. Model download is a separate, explicit setup step because it may require several gigabytes and local storage.
