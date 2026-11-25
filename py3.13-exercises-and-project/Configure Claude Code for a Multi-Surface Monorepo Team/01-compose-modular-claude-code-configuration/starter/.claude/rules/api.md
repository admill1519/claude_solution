---
description: Conventions for Node.js API handlers and middleware
paths:
  - "src/api/**/*"
---

# API handler rules

Loads when editing any file under `src/api/`.

## Handler signature and structure

- Every handler is `async (req: Request) => Promise<{ status: number; body: any }>`.
- Never mix HTTP library calls (`.send()`, `.json()`, `.status()`) inside handlers—the framework adapter handles all HTTP I/O. This keeps handlers testable in isolation.
- Handlers import repositories by name, never `import * from`. Explicit imports enforce dependency clarity.
- Each handler should live in its own file under a path that mirrors the route: `GET /api/orders/:id` → `src/api/orders/get-by-id.ts`.

## Error handling

- All expected errors throw `ApiError(statusCode, errorCode, message)`. Do not use `Error` or generic exceptions.
- Always provide a descriptive `errorCode` (e.g., `'ORDER_NOT_FOUND'`, `'INVALID_PAYMENT_METHOD'`) so clients can distinguish errors programmatically.
- Catch-and-rethrow only when you're adding meaningful context; don't silently swallow errors.
- Use HTTP status codes strictly: `400` for validation, `401` for auth, `404` for not found, `500` only for unexpected exceptions.

## Repository boundary

- Handlers import repository functions from `src/db/<Table>Repository`, never raw SQL or query builders.
- If a handler needs data from multiple tables, compose repository calls; do not write ad-hoc joins in the handler.
- Validate request bodies via schemas in `src/api/_schemas/` before passing to repositories.
