# SkillSwap Specification

Source: `problem.md` (requirements R1–R5). This spec adds only the decisions
needed to implement and test those requirements. Anything not listed here is
out of scope.

## Overview

SkillSwap is a small local web app. A user creates a profile, lists the
services they offer and the services they want, and sees the other users they
could trade with.

## Decisions

- **Stack:** Python with Flask, server-rendered HTML (Jinja templates), and no
  JavaScript framework. Tests use pytest.
- **Storage:** one JSON file (default `data.json`). The path is configurable so
  tests can use a temporary file.
- **Current profile:** taken from the URL (`/profile/<id>`). There are no
  logins, passwords, sessions, or cookies.
- **Service comparison:** two services are the same when they are equal after
  normalization, which means trimming the ends, collapsing internal whitespace
  to one space, and lowercasing. Substrings do not match: `"logo"` does not
  match `"logo design"`.
- **Single user at a time:** there is no concurrency handling or file locking.

## Requirements

### R1. Create or choose a profile

- A user can create a profile by entering a name.
- Names are trimmed. A blank name is rejected with an error message.
- Names must be unique, ignoring case and extra whitespace. A duplicate name is
  rejected with an error message.
- Each profile gets a unique id.
- The home page (`/`) shows a form to create a profile and a list of all
  existing profiles. Choosing one opens that profile's page.
- Requesting a profile id that does not exist returns 404.

### R2. Add offered and wanted services

- The profile page has one form to add a service the user **offers** and
  another to add a service they **want**.
- Each submission adds one service as free text.
- A blank service is rejected with an error message.
- Adding a service that already exists in the same list (after normalization)
  is ignored, so it is stored only once.
- Services are stored as the user typed them, trimmed. They are normalized
  only when compared.
- The profile page shows the user's current offers and wants.

### R3. Show matches

- For the current profile A, another profile B is a **match** when both of
  these are true:
  1. B offers at least one service that A wants.
  2. B wants at least one service that A offers.
- A profile never matches itself.
- A profile with no offers or no wants has no matches.
- The profile page lists every match. Each match shows:
  - B's name.
  - The services B offers that A wants.
  - The services B wants that A offers.
- If there are no matches, the page says so.

### R4. Persistence

- All profiles and their services are saved to the JSON file after every
  change.
- When the app starts, it loads that file, so data is still there after a
  restart.
- If the file does not exist, the app starts with no profiles and does not
  crash.
- File format:

  ```json
  {
    "profiles": [
      {"id": "1", "name": "Ana", "offers": ["Logo design"], "wants": ["Tax help"]}
    ]
  }
  ```

### R5. Runs locally in a browser

- The app starts with one command (`uv run python -m skillswap`) and serves
  pages at `http://127.0.0.1:5000`.
- The user does everything through a web browser.

## Pages and routes

| Method | Path                    | Purpose                                          |
|--------|-------------------------|--------------------------------------------------|
| GET    | `/`                     | Create-profile form and list of existing profiles |
| POST   | `/profiles`             | Create a profile, then redirect to its page      |
| GET    | `/profile/<id>`         | Show offers, wants, add forms, and matches       |
| POST   | `/profile/<id>/offers`  | Add an offered service, then redirect back       |
| POST   | `/profile/<id>/wants`   | Add a wanted service, then redirect back         |

## Visual design

This section covers presentation only. It does not change R1–R5, the routes,
form field names, validation, or stored data, and all existing tests must keep
passing.

### Look and feel

- A modern, clean service-marketplace look with a dark theme.
- Colors are defined once as CSS custom properties:

  | Token         | Value     | Use                                        |
  |---------------|-----------|--------------------------------------------|
  | `--bg`        | `#0f172a` | Page background (navy)                     |
  | `--surface`   | `#1e293b` | Header, cards, and panels (charcoal)       |
  | `--border`    | `#334155` | Card and input borders                     |
  | `--text`      | `#e2e8f0` | Main text                                  |
  | `--muted`     | `#94a3b8` | Secondary text, labels, empty states       |
  | `--accent`    | `#14b8a6` | Buttons, links, tags, focus ring (teal)    |
  | `--accent-ink`| `#0f172a` | Text on accent-colored backgrounds         |
  | `--error`     | `#f87171` | Error messages                             |

- One system font stack, with clear heading sizes and comfortable line
  spacing.
- All styling lives in one stylesheet. There is no CSS framework and no
  JavaScript.

### Layout

- Content sits in a centered column (about 56rem maximum width) with
  comfortable padding and consistent spacing between sections.
- A simple header appears on every page with the **SkillSwap** name on the
  left and a **Home** link on the right. Both lead to `/`.
- Error messages appear in a clearly visible box at the top of the content,
  in the error color.

### Home page (`/`)

In this order:

1. **Introduction:** the SkillSwap name and a short sentence explaining that
   it helps people trade services they offer for services they need.
2. **Create a profile:** a panel with a labelled name input and a Create
   button.
3. **Existing profiles:** a grid of cards, one per profile. Each card shows
   the profile name and links to that profile's page. The whole card is
   clickable.
   - When there are none, the empty state reads "No profiles yet."

### Profile page (`/profile/<id>`)

- The profile name is the page heading.
- Three clearly separated sections, each in its own panel:
  1. **Services Offered:** the user's offers as tags (pills), followed by a
     labelled input and an "Add offer" button.
  2. **Services Wanted:** the user's wants as tags, followed by a labelled
     input and an "Add want" button.
  3. **Matches:** one card per match, showing:
     - the matched profile's name,
     - "They offer what you want:" followed by those services as tags,
     - "They want what you offer:" followed by those services as tags.
- Empty states stay clear: "No services offered yet.", "No services wanted
  yet.", and "No matches yet."

### Components

- **Tags (pills):** small rounded labels with an accent outline or tinted
  background, used for every list of services.
- **Cards:** surface background, subtle border, rounded corners, and
  consistent padding. Clickable cards show a hover and focus state.
- **Forms:** every input has a visible `<label>` connected to it. Inputs have
  a dark background, a visible border, and padding. All buttons share one
  style: accent background, accent-ink text, rounded corners, and hover and
  focus states.

### Accessibility

- Text and background colors meet WCAG AA contrast (at least 4.5:1 for normal
  text).
- Every link, button, and input shows a visible keyboard focus outline in the
  accent color (`:focus-visible`).
- Color is never the only way information is shown. Sections have headings,
  and errors have text.

### Responsive behavior

- The layout works from desktop widths down to about 360px wide.
- On wide windows, profile cards and match cards show in a multi-column grid.
  On narrow windows they stack in one column.
- On narrow windows, form inputs and buttons fill the available width, and
  nothing scrolls horizontally.

## Out of scope

The following are not required by R1–R5 and will not be built:

- Deleting or editing profiles or services
- Login, passwords, or accounts
- Messaging, ratings, payments, or contacting matches
- Search or filtering
- Profile photos or avatars
- Substring, fuzzy, or category-based matching
- Multi-user or networked deployment, and databases other than the JSON file

## Acceptance tests

- **R1:**
  - Creating a profile makes it appear on `/`.
  - `GET /profile/<id>` returns 200 and shows the name.
  - A blank name is rejected.
  - A duplicate name in different case is rejected.
  - An unknown id returns 404.
- **R2:**
  - An added offer is stored in the offers list and shown on the page.
  - An added want is stored in the wants list and shown on the page.
  - A blank service is rejected.
  - A repeated service in different case or spacing is stored once.
- **R3:**
  - A mutual match is listed with the correct matching services.
  - A match in one direction only is not listed.
  - A profile never matches itself.
  - A profile with no services has no matches.
  - Variants in case and spacing match, and a substring does not.
  - The profile page shows the matches.
- **R4:**
  - Data written by one app instance is visible to a new instance that uses
    the same file.
  - A missing file gives an empty app without crashing.
- **R5:**
  - The app factory creates an app, and `GET /` returns 200 with HTML.
  - Opening the app in a real browser is checked by hand.
