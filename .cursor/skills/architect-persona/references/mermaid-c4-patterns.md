# Mermaid C4 Diagram Patterns

Copy-paste starting points for the most common diagram types.

---

## C4 Context Diagram

```mermaid
C4Context
  title System Context — <System Name>

  Person(user, "User", "A description of the user")
  System(system, "<System Name>", "What the system does")
  System_Ext(extSystem, "<External System>", "Third-party or external service")

  Rel(user, system, "Uses", "HTTPS")
  Rel(system, extSystem, "Calls", "REST/JSON")
```

---

## C4 Container Diagram

```mermaid
C4Container
  title Container Diagram — <System Name>

  Person(user, "User")

  System_Boundary(sys, "<System Name>") {
    Container(webApp, "Web App", "Node.js / Express", "Handles HTTP requests")
    Container(db, "Database", "PostgreSQL", "Stores application data")
    Container(worker, "Background Worker", "Node.js", "Processes async jobs")
  }

  System_Ext(googleApi, "Google Calendar API", "Manages calendar events")

  Rel(user, webApp, "Uses", "HTTPS")
  Rel(webApp, db, "Reads/writes", "SQL")
  Rel(webApp, worker, "Enqueues jobs", "Redis queue")
  Rel(worker, googleApi, "Calls", "REST/JSON + OAuth 2.0")
```

---

## C4 Component Diagram

```mermaid
C4Component
  title Component Diagram — Web App

  Container_Boundary(webApp, "Web App") {
    Component(router, "Router", "Express Router", "Routes HTTP requests")
    Component(authAdapter, "Auth Adapter", "TypeScript class", "Handles Google OAuth 2.0 flow")
    Component(calendarAdapter, "Calendar Adapter", "TypeScript class", "Wraps Google Calendar API")
    Component(domain, "Domain Service", "TypeScript class", "Core business logic")
  }

  Rel(router, authAdapter, "Delegates auth", "function call")
  Rel(router, domain, "Invokes", "function call")
  Rel(domain, calendarAdapter, "Uses port", "interface")
```

---

## Sequence Diagram — OAuth 2.0 Flow

```mermaid
sequenceDiagram
  actor User
  participant App as Node.js App
  participant Google as Google OAuth 2.0

  User->>App: GET /auth/google
  App->>Google: Redirect to consent screen (client_id, scopes)
  Google-->>User: Show consent screen
  User->>Google: Grant permission
  Google-->>App: Redirect to /auth/callback?code=...
  App->>Google: POST /token (code, client_secret)
  Google-->>App: access_token + refresh_token
  App-->>User: Session established
```

---

## Sequence Diagram — Calendar API Integration

```mermaid
sequenceDiagram
  participant App as Node.js App
  participant Auth as Auth Adapter
  participant Cal as Calendar Adapter
  participant GCal as Google Calendar API

  App->>Auth: getValidToken(userId)
  Auth-->>App: accessToken (refreshed if expired)
  App->>Cal: createEvent(eventData, accessToken)
  Cal->>GCal: POST /calendars/primary/events
  GCal-->>Cal: 200 OK { event }
  Cal-->>App: EventId
```

---

## Tips

- Keep each diagram to **one level of zoom** — don't mix C4 levels.
- Label every arrow with **what** is exchanged and **how** (protocol/format).
- Use `System_Ext` for anything you don't own or deploy.
- For complex flows, prefer sequence diagrams over component diagrams.