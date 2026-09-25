# Cost Model

Pricing assumptions were checked on 2026-09-25 against official provider pages. Prices vary by region, billing account, free tier, and future provider changes; billing export remains the source of truth.

## Per-generation AI estimate

The production model is Gemini 2.5 Flash on Vertex AI. Current public list pricing for standard requests up to 200K input tokens is USD 0.30 per million input tokens and USD 2.50 per million output tokens. `gemini-embedding-001` online embeddings are approximately USD 0.000025 per 1,000 input characters. Sources: [Vertex AI generative pricing](https://cloud.google.com/vertex-ai/generative-ai/pricing) and [Google embedding pricing announcement](https://cloud.google.com/blog/products/ai-machine-learning/google-cloud-announces-new-text-embedding-models).

No production token-usage sample has been captured, so a single defensible cost-per-success number is not yet available. Use:

```text
Gemini cost = input_tokens / 1,000,000 * $0.30
            + output_tokens / 1,000,000 * $2.50
Embedding cost ≈ query_characters / 1,000 * $0.000025
Cost per successful generation =
  (all Gemini attempts + embedding calls + allocated infrastructure cost)
  / successful persisted exercises
```

Illustrative arithmetic only: 5,000 input tokens and 2,000 output tokens in one Gemini attempt cost about USD 0.0065, excluding embedding and infrastructure. This is not a measured project average; repair attempts multiply the Gemini portion.

## Other drivers

- Pinecone: serverless read units, storage, and any minimum plan charge; inspect the project invoice because the repository does not contain billing data.
- Cloud Run backend and sandbox: vCPU-seconds, GiB-seconds, and requests. Sandbox compilation/execution increases active compute time.
- Redis: Memorystore provisioned capacity, charged independently of request volume.
- PostgreSQL/Supabase: database plan, compute, storage, and egress.
- Artifact Registry, logging, monitoring, and network egress can add smaller operational costs.

The application should record model, call count, latency, retry count, and provider usage metadata when the SDK exposes it without logging prompts or generated private content. Billing-account access is required to reconcile estimates with actual spend.
