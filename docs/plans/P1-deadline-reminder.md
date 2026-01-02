# P1: Deadline Reminders

> **Priority**: P1 (Core Experience)
> **Status**: `NOT_STARTED`
> **Progress**: 0%
> **Last Updated**: 2026-01-03

---

## Overview

Implement a notification system to remind users of upcoming opportunity deadlines, preventing missed applications.

---

## Why This Matters

- **User Pain Point**: Startup teams are busy, easy to forget deadlines
- **Direct Value**: Preventing one missed opportunity = huge user value
- **Engagement**: Regular touchpoints keep users active

---

## Notification Types

### 1. Deadline Approaching

Notify when opportunities in user's pipeline/bookmarks have upcoming deadlines:

| Timing | Priority | Message |
|--------|----------|---------|
| 7 days before | Low | "ETH Denver deadline in 1 week" |
| 3 days before | Medium | "ETH Denver deadline in 3 days" |
| 1 day before | High | "ETH Denver deadline tomorrow!" |
| Day of | Urgent | "ETH Denver deadline TODAY" |

### 2. New High-Match Opportunity

Notify when a new opportunity is added that scores highly for user:

| Condition | Message |
|-----------|---------|
| Score > 85% | "New opportunity! ETH Denver matches your profile" |
| Score > 90% | "Hot match! YC W26 is perfect for you" |

### 3. Pipeline Stage Reminders

Remind to take action on stalled pipeline items:

| Condition | Message |
|-----------|---------|
| In "Preparing" > 7 days | "Still preparing for ETH Denver? Need help?" |
| In "Submitted" no update > 14 days | "Any updates on your YC application?" |

---

## Notification Channels

### Phase 1: Email

- Most reliable, works for all users
- Use SendGrid or similar
- Daily digest or immediate based on preference

### Phase 2: In-App

- Notification bell in header
- Unread count badge
- Notification center panel

### Phase 3 (Future): Push/SMS

- Browser push notifications
- SMS for urgent deadlines (opt-in)

---

## User Preferences

```python
class NotificationPreferences:
    # Email
    email_enabled: bool = True
    email_frequency: Literal["immediate", "daily_digest", "weekly_digest"] = "daily_digest"

    # Deadline reminders
    deadline_7_days: bool = True
    deadline_3_days: bool = True
    deadline_1_day: bool = True
    deadline_day_of: bool = True

    # Other notifications
    new_high_match: bool = True
    new_high_match_threshold: int = 85  # Minimum score %

    pipeline_stalled: bool = True
    pipeline_stalled_days: int = 7

    # Quiet hours (for future push)
    quiet_hours_start: str | None  # "22:00"
    quiet_hours_end: str | None    # "08:00"
```

---

## Technical Architecture

```
┌─────────────────────────────────────────────────────┐
│                Notification System                   │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌──────────────────────────────────────────────┐   │
│  │           Scheduled Jobs (Cron)               │   │
│  │  • Check deadlines (daily)                    │   │
│  │  • Check new matches (hourly)                 │   │
│  │  • Check stalled pipelines (daily)            │   │
│  └─────────────────────┬────────────────────────┘   │
│                        │                             │
│              ┌─────────▼─────────┐                   │
│              │  Notification     │                   │
│              │  Generator        │                   │
│              └─────────┬─────────┘                   │
│                        │                             │
│              ┌─────────▼─────────┐                   │
│              │  User Preference  │                   │
│              │  Filter           │                   │
│              └─────────┬─────────┘                   │
│                        │                             │
│         ┌──────────────┼──────────────┐              │
│         │              │              │              │
│  ┌──────▼──────┐ ┌─────▼─────┐ ┌─────▼─────┐       │
│  │   Email     │ │  In-App   │ │   Push    │       │
│  │   Sender    │ │  Store    │ │  (Future) │       │
│  └─────────────┘ └───────────┘ └───────────┘       │
│                                                      │
└──────────────────────────────────────────────────────┘
```

---

## Data Models

### Notification

```python
class Notification(Document):
    user_id: ObjectId
    type: Literal[
        "deadline_reminder",
        "new_match",
        "pipeline_reminder",
        "system"
    ]

    # Content
    title: str
    message: str
    action_url: str | None       # Deep link

    # Related entities
    opportunity_id: ObjectId | None
    pipeline_id: ObjectId | None

    # Status
    read: bool = False
    sent_email: bool = False
    sent_push: bool = False

    # Timing
    created_at: datetime
    read_at: datetime | None
```

---

## API Endpoints

```python
# Notifications
GET    /api/v1/notifications              # List notifications
GET    /api/v1/notifications/unread-count # Unread count
POST   /api/v1/notifications/{id}/read    # Mark as read
POST   /api/v1/notifications/read-all     # Mark all read

# Preferences
GET    /api/v1/notifications/preferences  # Get preferences
PUT    /api/v1/notifications/preferences  # Update preferences
```

---

## Email Templates

### Deadline Reminder

```
Subject: [Deadline in 3 days] ETH Denver 2026

Hi {name},

Just a reminder that ETH Denver 2026 has a deadline in 3 days (Feb 28, 2026).

Quick Stats:
• Prize Pool: $50,000
• Your Match Score: 87%
• Status: Preparing

[Continue Application] [View Details]

---
You're receiving this because you added this to your pipeline.
[Manage notification preferences]
```

### Daily Digest

```
Subject: Your OpportunityRadar Daily Digest

Hi {name},

Here's what's happening with your opportunities:

📅 UPCOMING DEADLINES
• ETH Denver - 3 days left
• Gitcoin GG21 - 1 week left

🆕 NEW MATCHES
• YC W26 Batch (92% match)
• Techstars NYC (85% match)

📊 YOUR PIPELINE
• 3 opportunities in progress
• 1 needs attention

[Go to Dashboard]
```

---

## Implementation Tasks

### Phase 1: Backend Foundation

- [ ] Create Notification model
- [ ] Create NotificationPreferences model
- [ ] Add notification preferences to Profile
- [ ] Implement notification CRUD API
- [ ] Create notification service

### Phase 2: Scheduled Jobs

- [ ] Set up job scheduler (APScheduler or Celery)
- [ ] Implement deadline check job
- [ ] Implement new match check job
- [ ] Implement stalled pipeline check job

### Phase 3: Email Integration

- [ ] Set up email service (SendGrid)
- [ ] Create email templates
- [ ] Implement immediate email sender
- [ ] Implement daily digest aggregation

### Phase 4: Frontend In-App

- [ ] Add notification bell to header
- [ ] Create notification dropdown/panel
- [ ] Implement unread count badge
- [ ] Add notification preferences page

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Email open rate | > 40% |
| Click-through rate | > 15% |
| Deadline miss rate | < 10% |
| Notification preference set | > 50% of users |

---

## Dependencies

- P0: Opportunity Crawler (need opportunities with deadlines)
- P1: Team Profile (for user preferences)

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-03 | Initial plan created |
