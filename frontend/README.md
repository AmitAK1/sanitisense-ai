# SanitiSense AI — Frontend

## Owner: Person A (Frontend Developer)

## Tech Stack
- React 18 + Next.js 14 + TypeScript
- Tailwind CSS + shadcn/ui
- Leaflet.js (maps)
- Recharts (analytics charts)

## Setup
```bash
cd frontend
npm install
npm run dev
```
Opens at http://localhost:3000

## Pages to Build

### 1. `/` — Landing Page (Role Selector)
- 3 big buttons: "I'm a Citizen", "I'm a Worker", "Authority Dashboard"
- Simple, clean, mobile-responsive

### 2. `/citizen` — Citizen Report View
- Big camera button (use `<input type="file" accept="image/*" capture="camera">`)
- Voice record button (use MediaRecorder API)
- Submit button
- After submit: show ticket ID + AI classification result
- **Zero text input required** — icon-based, big touch targets

### 3. `/worker` — Worker Task View
- List of tasks with color-coded severity badges (red/yellow/green)
- Click task → see before photo + AI analysis + location
- "Complete Task" button → opens camera for after-photo
- Shows AI validation result (approved/rejected + waste reduction %)

### 4. `/dashboard` — Authority Dashboard
- Interactive map (react-leaflet) with colored markers
- Stat cards: Total Reports, Pending, Completed, Avg Resolution Time
- Epidemic Risk Panel: shows AI-generated health advisory text
- Simple bar/line chart (Recharts)

## API Integration
The API base URL will be provided as an environment variable:
```
NEXT_PUBLIC_API_URL=https://xxxxx.execute-api.us-east-1.amazonaws.com/prod
```

### API Endpoints (Person B builds these):
- `POST /reports` — submit new report (photo + location)
- `GET /reports` — list all reports
- `GET /reports/{ticket_id}` — get single report
- `POST /tasks/{task_id}/complete` — submit after-photo
- `GET /tasks` — list worker tasks
- `GET /dashboard/stats` — get dashboard statistics
- `GET /dashboard/epidemic` — get AI epidemic advisory

## Design Guidelines
- Mobile-first (citizen/worker views used on phones)
- Big buttons (min 48x48px touch targets)
- Color coding: Red = High severity, Yellow = Medium, Green = Low
- Minimal text — use icons
- Works on Android Chrome (8.0+)
