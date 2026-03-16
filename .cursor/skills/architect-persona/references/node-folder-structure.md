# Node.js / TypeScript Project Structure

**Based on Hexagonal Architecture (Ports & Adapters)**

---

## Recommended Folder Structure

```
my-project/
├── src/
│   ├── domain/                  # Pure business logic — no framework, no I/O
│   │   ├── entities/            # Core domain objects (plain TypeScript classes)
│   │   ├── services/            # Domain services (orchestrate entities)
│   │   └── errors/              # Domain-specific error types
│   │
│   ├── ports/                   # Interfaces (contracts) the domain depends on
│   │   ├── outbound/            # What the domain needs from the outside world
│   │   │   ├── CalendarPort.ts  # e.g. interface CalendarPort { createEvent(...) }
│   │   │   └── AuthPort.ts
│   │   └── inbound/             # How the outside world drives the domain
│   │       └── EventUseCases.ts
│   │
│   ├── adapters/                # Concrete implementations of ports
│   │   ├── google/
│   │   │   ├── GoogleCalendarAdapter.ts
│   │   │   └── GoogleOAuthAdapter.ts
│   │   ├── puppeteer/
│   │   │   └── PuppeteerAdapter.ts
│   │   └── persistence/
│   │       └── PostgresAdapter.ts
│   │
│   ├── app/                     # Application layer — wires domain + adapters
│   │   ├── container.ts         # Dependency injection / composition root
│   │   └── usecases/            # Use case implementations (thin orchestrators)
│   │
│   ├── api/                     # Delivery mechanism — HTTP, CLI, etc.
│   │   ├── routes/
│   │   ├── middleware/
│   │   └── server.ts
│   │
│   └── config/                  # Env config, constants
│       └── index.ts
│
├── test/
│   ├── unit/                    # Tests for domain/ — no mocks of external services needed
│   ├── integration/             # Tests for adapters (real or containerised services)
│   └── e2e/                     # End-to-end (Puppeteer, Supertest, etc.)
│
├── docs/
│   └── adr/                     # Architecture Decision Records
│       ├── README.md            # ADR index
│       └── 0001-hexagonal.md
│
├── .env.example
├── tsconfig.json
├── package.json
└── README.md
```

---

## Key Rules

| Rule | Why |
|------|-----|
| `domain/` has **zero** imports from `adapters/` or `api/` | Domain must be testable in isolation |
| Adapters implement interfaces defined in `ports/` | Swap without touching domain |
| `container.ts` is the only place that `new`s adapters | Single composition root, easy to swap |
| All env config accessed via `config/index.ts` | Never `process.env` scattered through code |
| Test files mirror `src/` structure | Easy to find tests for any module |

---

## Dependency Direction

```
api/ → app/ → domain/
                ↑
          ports/ (interfaces)
                ↑
          adapters/ (implement ports)
```

The domain **never** depends on adapters. Adapters depend on ports (interfaces). The app layer wires them together.

---

## Google OAuth 2.0 + Calendar API Adapter Pattern

```typescript
// ports/outbound/CalendarPort.ts
export interface CalendarPort {
  createEvent(event: CalendarEvent, userId: string): Promise<string>;
  listEvents(userId: string, from: Date, to: Date): Promise<CalendarEvent[]>;
}

// adapters/google/GoogleCalendarAdapter.ts
import { CalendarPort } from '../../ports/outbound/CalendarPort';

export class GoogleCalendarAdapter implements CalendarPort {
  constructor(private readonly authAdapter: AuthPort) {}

  async createEvent(event: CalendarEvent, userId: string): Promise<string> {
    const token = await this.authAdapter.getValidToken(userId);
    // Call Google Calendar API with token...
  }
}
```

---

## tsconfig.json — Recommended Base

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "lib": ["ES2020"],
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "baseUrl": ".",
    "paths": {
      "@domain/*": ["src/domain/*"],
      "@ports/*": ["src/ports/*"],
      "@adapters/*": ["src/adapters/*"],
      "@app/*": ["src/app/*"]
    }
  },
  "include": ["src"],
  "exclude": ["node_modules", "dist", "test"]
}
```