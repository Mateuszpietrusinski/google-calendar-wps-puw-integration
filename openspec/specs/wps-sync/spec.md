## ADDED Requirements

### Requirement: WPS authentication via JWT bearer
The WPS connector SHALL authenticate by POSTing to `https://wpsapi.ahe.lodz.pl/api/Profil/zaloguj` with WPS credentials and extracting `access_token` (JWT) from the response. The student's `StudentID` SHALL be decoded from the JWT payload field `id`.

#### Scenario: Successful authentication
- **WHEN** valid WPS credentials are in `.env`
- **THEN** a JWT bearer token and `StudentID` are obtained and used on all subsequent WPS API calls

#### Scenario: Invalid credentials
- **WHEN** WPS credentials are invalid
- **THEN** the sync cycle is aborted for this source, an error is logged: `AuthError: WPS login failed — check WPS_USERNAME / WPS_PASSWORD in .env`, and no calendar changes are made

#### Scenario: WPS connector disabled when credentials absent
- **WHEN** `WPS_USERNAME` or `WPS_PASSWORD` is absent from `.env`
- **THEN** the WPS connector is not initialised and no WPS sync jobs are registered

---

### Requirement: Proactive JWT refresh before expiry
The WPS connector SHALL check `exp - now < 5 minutes` before each API call. If true, it SHALL silently re-authenticate using credentials from config before proceeding.

#### Scenario: Token refreshed proactively
- **WHEN** the JWT expiry is within 5 minutes of the current time
- **THEN** the connector re-authenticates before making the timetable API call, without any error or interruption to the sync cycle

---

### Requirement: Fetch current semester timetable
The WPS connector SHALL fetch the full zjazd timetable using `GET /api/PlanyZajec/GETPlanSzczegolowy` with `CzyNieaktywnePlany=0`, `StudentID` from JWT, and `DataOd`/`DataDo` bounds for the current academic semester.

Semester bounds SHALL be auto-detected from the min/max `DataOD`/`DataDO` values in a prior API response. Students MAY override bounds via `WPS_SEMESTER_FROM` / `WPS_SEMESTER_TO` in `.env`.

#### Scenario: Semester bounds auto-detected
- **WHEN** no `WPS_SEMESTER_FROM` / `WPS_SEMESTER_TO` are set and the API returns timetable entries
- **THEN** the connector uses the earliest `DataOD` and latest `DataDO` from the response as semester bounds on subsequent calls

#### Scenario: Semester bounds overridden via .env
- **WHEN** `WPS_SEMESTER_FROM=2026-02-01` and `WPS_SEMESTER_TO=2026-06-30` are set
- **THEN** these dates are used as `DataOd`/`DataDo` regardless of the API response

---

### Requirement: WPS event mapping to CalendarEvent
Each `WpsPlanSzczegolowy` entry SHALL be mapped to a `CalendarEvent` as follows:
- **Title:** `"{PNazwa} — {TypZajec}"` (e.g. `"Programowanie obiektowe 1 — Laboratorium"`)
- **Start/End:** `DataOD` / `DataDO` (ISO datetime, CET-aware, `Europe/Warsaw`)
- **Description (on-site):** Room `SalaNumer`, address `SalaAdres`, teachers from `Dydaktyk[].ImieNazwisko`
- **Description (webinar):** `"Online (Webinar)"`, teachers from `Dydaktyk[].ImieNazwisko`

#### Scenario: On-site class mapped with room details
- **WHEN** a WPS entry has `Webinar=false` with `SalaNumer="101"` and `SalaAdres="ul. Sterlinga 26"`
- **THEN** the `CalendarEvent.description` contains both the room number and address

#### Scenario: Webinar class mapped without room
- **WHEN** a WPS entry has `Webinar=true` (and `SalaNumer=null`, `SalaAdres=null`)
- **THEN** the `CalendarEvent.description` contains `"Online (Webinar)"` and does not reference a room

---

### Requirement: WPS change detection via field checksum
The WPS connector SHALL compute a checksum as `MD5(DataOD + DataDO + SalaNumer + SalaAdres + ",".join(sorted(d.ImieNazwisko for d in Dydaktyk)))` for each entry. The sync engine SHALL detect an update when the fetched checksum differs from the stored checksum.

#### Scenario: Room change detected as update
- **WHEN** a WPS entry previously had `SalaNumer="101"` and now has `SalaNumer="203"`
- **THEN** the checksum differs and `compute_diff` includes the entry in `SyncPlan.to_update`

---

### Requirement: WPS deletion detection
A timetable entry previously synced (present in `state.json`) but absent from the current API response SHALL be included in `SyncPlan.to_delete`.

#### Scenario: Cancelled class deleted from calendar
- **WHEN** an `IDPlanZajecPoz` is in `state.json` but not returned by the current semester fetch
- **THEN** the corresponding Google Calendar event is deleted
