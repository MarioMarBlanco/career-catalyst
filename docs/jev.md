# Jev API Reference

Local working reference for TypeSafe AI's Jev model through Vercel AI Gateway.
Sources were reviewed on 2026-09-25. This file is intentionally compressed;
the linked vendor documentation remains authoritative when APIs change.

## Identity and mental model

- Jev is TypeSafe AI's flagship System One decision model, not a chat model,
  coding agent, or text generator.
- It evaluates one `state` against one or more typed, bounded questions and
  returns structured answers that application code can branch on.
- Questions in one request are independent and evaluated in parallel against
  the same state. An array is one state, not a batch of unrelated states.
- Keep deterministic workflow, authorization, side effects, and control flow
  in code. Use Jev for narrow judgments over unstructured or mixed data.
- Type-safe output does not mean semantically correct output. Validate against
  labeled examples and send uncertain or high-risk cases to review.

## Vercel model and limits

Gateway model ID: `typesafe-ai/jev`

Current TypeSafe model details from the vendor model page:

- Versioned model: `jev-1.13.0`; aliases: `jev-latest` and `jev-preview`.
- `jev-latest` is stable and moves when a release ships. Pin a version when
  thresholds must remain reproducible; log the response `model` field.
- Context: 64k tokens per request and 32k tokens for state plus the longest
  question.
- Input is text only: string, JSON object, or JSON array. Preprocess images,
  audio, video, and binary data into text or structured fields.
- Vercel lists approximately `$0.042 / 1M` input tokens and no output-token
  charge. Verify current pricing before budgeting.
- TypeSafe currently lists 250,000 tokens/second and 1,200 requests/minute;
  limits can change dynamically.
- English is currently the strongest language. Test other languages on real
  data before relying on them.

## Authentication and routes

### Preferred Vercel AI SDK path

Use AI SDK 7 or later. In a linked Vercel project, `vercel env pull` provides a
local `VERCEL_OIDC_TOKEN`; Vercel deployments receive the token automatically.
Local OIDC tokens expire after about 12 hours, so refresh them after a 401.

```bash
npm install ai@latest
vercel link
vercel env pull
```

Plain Gateway model strings resolve through AI Gateway:

```ts
import { experimental_evaluate as evaluate } from "ai";

const result = await evaluate({
  model: "typesafe-ai/jev",
  state: "The support agent issued a full refund to the customer.",
  questions: {
    refunded: {
      type: "boolean",
      instructions: "Was a refund issued?",
    },
  },
});
```

For explicit provider configuration:

```bash
npm install @ai-sdk/gateway
```

```ts
import { gateway } from "@ai-sdk/gateway";
import { experimental_evaluate as evaluate } from "ai";

const result = await evaluate({
  model: gateway.evaluationModel("typesafe-ai/jev"),
  state: "I was charged twice. Please refund the duplicate.",
  questions: {
    requestsRefund: {
      type: "boolean",
      instructions: "Is the customer requesting money back?",
    },
  },
});
```

AI SDK string IDs use `AI_GATEWAY_API_KEY` when supplied, or Vercel OIDC when
configured. Do not put keys in source control. The existing Copilot setup uses
`COPILOT_PROVIDER_*` variables and the coding-agent base URL; that config is
separate from the AI SDK evaluation API.

### Native Gateway HTTP API

Evaluation is not available through the OpenAI-compatible, Anthropic-
compatible, or Cohere-compatible Gateway endpoints. Use the native endpoint:

```http
POST https://ai-gateway.vercel.sh/v1/evaluate
Authorization: Bearer $AI_GATEWAY_API_KEY
Content-Type: application/json
```

Request body uses `model`, `state`, and `questions`. Optional Gateway options:

```json
{
  "providerOptions": {
    "gateway": {
      "zeroDataRetention": true,
      "only": ["typesafe-ai"]
    }
  }
}
```

The response includes `model`, `answers`, `usage`, and Gateway routing/cost
metadata. Do not log request state if it contains sensitive data.

### Python without an SDK

Python is fully supported. It can call the native Gateway endpoint with any
HTTP client; no AI SDK or TypeScript is required. For the existing Vercel
Gateway setup, use the Gateway key and Gateway model ID:

```python
import os

import requests

response = requests.post(
  "https://ai-gateway.vercel.sh/v1/evaluate",
  headers={
    "Authorization": f"Bearer {os.environ['COPILOT_PROVIDER_API_KEY']}",
    "Content-Type": "application/json",
  },
  json={
    "model": "typesafe-ai/jev",
    "state": "The customer was charged twice and asks for a refund.",
    "questions": {
      "needsRefund": {
        "type": "boolean",
        "instructions": "Is the customer requesting a refund?",
      },
    },
  },
)
response.raise_for_status()
print(response.json()["answers"])
```

Install the only dependency used by this example with `python -m pip install
requests`. In a fresh shell, load the Vercel variables first with `source
~/.zshrc`, or provide the key through your normal secret-management system.

Do not confuse this with TypeSafe's optional direct Python SDK. The direct SDK
uses `TYPESAFE_API_KEY`, the TypeSafe endpoint
`https://api.typesafe.ai/v1/systemone`, model IDs such as `jev-latest`, and the
TypeSafe primitive name `noul` instead of Gateway's `boolean`. Use the native
Gateway HTTP request above when this project should remain routed through
Vercel AI Gateway.

### Direct TypeSafe API

The direct vendor API is a different surface:

```http
POST https://api.typesafe.ai/v1/systemone
Authorization: Bearer $TYPESAFE_API_KEY
Content-Type: application/json
```

It uses TypeSafe model IDs such as `jev-latest` and TypeSafe primitive names.
Use this only when intentionally integrating TypeSafe directly, not for the
Gateway integration in this project.

## Question types

All questions have an application-chosen ID, `type`, and `instructions`.
Question IDs are returned as keys but are not sent to the model. Instructions
and criteria may be strings, objects, or arrays of JSON-compatible values.

### Choice: one option from a set

Use for routing, category, intent, language, or any unordered finite set.
`criteria` is a nonempty map of option keys to descriptions; up to 255 options.
Include `other`, `unknown`, or `insufficient_evidence` when the list may not
cover the input.

```ts
department: {
  type: "choice",
  instructions: "Which team should handle this ticket?",
  criteria: {
    billing: "Charges, invoices, and refunds",
    technical: "Bugs, outages, and integrations",
    other: "Does not fit the other teams",
  },
}
```

Gateway answer:

```ts
{
  type: "choice",
  choice: "billing",
  probabilities: { billing: 0.88, technical: 0.08, other: 0.04 },
}
```

The selected option has the highest probability. Choice distributions are
optional in generic AI SDK evaluation providers, but native Jev supplies them.

### Score: position on an ordered rubric

Use for severity, urgency, quality, frustration, or another spectrum. `criteria`
is an ordered array of 2 to 10 descriptive levels, indexed from zero. Describe
observable situations, not vague numbers such as `low`, `medium`, `high`.

```ts
severity: {
  type: "score",
  instructions: "How severe is the issue?",
  criteria: [
    "Cosmetic; no impact to functionality",
    "Broken or degraded; a workaround exists",
    "Blocking; no workaround exists",
  ],
}
```

Answer fields include `score`, optional `probabilities` keyed by string level
indices, and `legend`. The score is the probability-weighted mean, so it may
be fractional. A score of `1.0` does not distinguish a concentrated level 1
from a split distribution across levels 0 and 2; inspect the distribution.

### Boolean / Noul: probability a statement is true

In Vercel AI SDK, use `type: "boolean"` and read `probability`. In TypeSafe's
direct API and SDK, the equivalent primitive is `type: "noul"` and the answer
field is `noul`.

```ts
requestsRefund: {
  type: "boolean",
  instructions: "Is the customer asking for money back?",
  criteria: {
    true: "Directly asks for a refund or credit.",
    false: "Does not ask for money back.",
  },
}
```

`1` is a strong yes, `0` a strong no, and `0.5` uncertainty. This is not a
degree or confidence score. There is no separate confidence field for a
boolean/Noul answer.

## State and question design

- Prefer a focused structured object with only evidence needed by the current
  questions. Include timestamps and preserve uncertain observations as such.
- Separate evidence in `state` from the judgment in `instructions`.
- For nested state, explicitly name fields with backticked paths such as
  ``Does `ticket.messages[0].text` request a refund?``.
- Ask one atomic judgment per question. Split compound questions and combine
  answers with deterministic code or weighted formulas.
- Ask all questions that use the same state in one request, including
  speculative questions whose answers only matter on some paths. They run in
  parallel; a second request is justified only when the first answer is needed
  to construct new state, fetch data, or choose later options.
- Use structured instruction/criteria objects when similar options are confused;
  fields such as `what`, `not_for`, and `examples` are ordinary labels, not
  reserved API keywords.
- Use a Score for an ordered spectrum, Choice for discrete alternatives, and
  boolean/Noul for one proposition. Do not use a boolean as a proxy for degree.

## Confidence, probabilities, and policy

- Choice and Score expose a probability distribution and TypeSafe confidence.
  Confidence summarizes how concentrated the distribution is; it is not the
  selected option's probability and is not a correctness guarantee.
- Boolean probability means P(true), not confidence in a generated answer.
- Probabilities are not guaranteed calibrated for an individual input. Evaluate
  labeled examples from this domain before setting thresholds.
- Use three application paths: high confidence can act automatically, medium
  confidence can request confirmation or review, and low confidence should not
  guess.
- Threshold by action risk, not globally by model. Read-only actions can use a
  lower bar; destructive actions, refunds, permissions, production changes,
  and external messages need a higher bar or human approval.
- Classification is not authorization. Jev can identify a refund request or a
  destructive tool call; code and policy must decide whether it is permitted.

Example Gateway routing guard:

```ts
const answer = result.answers.department;
const probability = answer.probabilities?.[answer.choice] ?? 0;
const confidence = result.providerMetadata?.typesafe?.confidence?.department ?? 0;

if (confidence < 0.6 || probability < 0.7) {
  return { action: "human-review", reason: "ambiguous department" };
}

return { action: "assign", queue: answer.choice };
```

Treat Choice/Score distributions as optional in portable AI SDK code. Jev's
native response includes them, but another evaluation provider may not.

## Validation and operational behavior

- AI SDK evaluation is experimental and can change in patch releases.
- Successful calls return an answer for every question; there is no partial
  success or automatic model substitution.
- Unsupported question types fail the whole call with
  `Experimental_EvaluationUnsupportedQuestionTypeError`.
- Invalid inputs use `InvalidArgumentError`; malformed provider answers use
  `InvalidResponseDataError`.
- AI SDK retries transient provider failures with `maxRetries: 2` by default.
  Use `abortSignal` for cancellation, `headers` for headers, and
  `providerOptions` for provider-specific settings.
- Native TypeSafe HTTP statuses: `401` invalid/missing key, `422` invalid
  request, `429` rate limit, `529` temporary overload. Use exponential backoff;
  official SDKs honor retry behavior and `retry-after` where available.
- Jev does not stream, batch unrelated states, perform multilabel classification,
  generate prose, or accept media directly.
- Rounded distributions may sum to `0.99` rather than exactly `1`; do not
  renormalize native answers. Read any returned rounding metadata.

## Testing strategy

Keep policy and threshold tests offline. AI SDK provides
`Experimental_EvaluationMockModelV4` from `ai/test`; inject it as the model into
the function that calls `evaluate`. Test clear, boundary, low-probability, and
missing-confidence cases. Separately evaluate real labeled examples to decide
whether the thresholds are appropriate.

## Minimal native HTTP smoke test

```bash
curl https://ai-gateway.vercel.sh/v1/evaluate \
  -H "Authorization: Bearer $AI_GATEWAY_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "typesafe-ai/jev",
    "state": "The support agent issued a full refund.",
    "questions": {
      "refunded": {
        "type": "boolean",
        "instructions": "Was a refund issued?"
      }
    }
  }'
```

## Official references

- Vercel overview: https://vercel.com/i/what-is-jev
- Gateway evaluation: https://vercel.com/docs/ai-gateway/modalities/evaluation
- Gateway quickstart: https://vercel.com/docs/ai-gateway/getting-started/evaluation
- Vercel AI SDK evaluation: https://ai-sdk.dev/docs/ai-sdk-core/evaluation
- Vercel Jev guide: https://vercel.com/kb/guide/typesafe-jev-and-ai-sdk
- TypeSafe introduction: https://docs.typesafe.ai/introduction
- TypeSafe System One: https://docs.typesafe.ai/concepts/system-one
- TypeSafe build guidance: https://docs.typesafe.ai/concepts/how-to-build-with-system-one
- TypeSafe state: https://docs.typesafe.ai/concepts/state
- TypeSafe primitives: https://docs.typesafe.ai/primitives
- TypeSafe API: https://docs.typesafe.ai/api
- TypeSafe confidence: https://docs.typesafe.ai/confidence
- TypeSafe models and limits: https://docs.typesafe.ai/models
- TypeSafe documentation index: https://docs.typesafe.ai/llms.txt