# Implementation Plan: Brand Authentication Portal

**Branch**: `main` | **Date**: 2026-05-17 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/speckit.specify`

## Summary

Build a lightweight but premium onboarding and authentication portal for an AI-powered D2C brand agency platform. The MVP includes a hero landing page, user signup (email/password + Google OAuth), sign-in (email/password + Google OAuth + OTP), protected dashboard with mock data, and password recovery. Built using Streamlit for rapid frontend development and FastAPI for backend authentication services, with PostgreSQL for data persistence.

## Technical Context

**Language/Version**: Python 3.10+  
**Primary Dependencies**: Streamlit, FastAPI, SQLAlchemy, Alembic, python-jose, passlib, Authlib, psycopg2-binary  
**Storage**: PostgreSQL  
**Testing**: pytest  
**Target Platform**: Web (responsive, mobile-friendly)  
**Project Type**: Web application (frontend + backend)  
**Performance Goals**: Landing page <3s load, dashboard <2s load, 1000 concurrent users  
**Constraints**: SSL/TLS required, session timeout configurable, rate limiting for OTP  
**Scale/Scope**: MVP for rapid launch, modular architecture for future SaaS migration

## Constitution Check

**GATE**: PASSED - No violations found

This feature aligns with constitution principles:
- Python 3.10+ as core language ✓
- Mobile-first templates ✓
- Page load time <2s for dashboard ✓
- Quality gates before deployment ✓
- Modular architecture for future scalability ✓

## Project Structure

### Documentation (this feature)

```text
.specify/features/brand-auth-portal/
├── plan.md              # This file
├── research.md          # Technology decisions
├── data-model.md        # Entity definitions
├── quickstart.md        # Integration scenarios
├── contracts/           # API contracts
│   └── api-endpoints.md
└── tasks.md             # Implementation tasks (to be generated)
```

### Source Code (repository root)

```text
brand-auth-portal/
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── landing.py
│   │   │   ├── signup.py
│   │   │   ├── signin.py
│   │   │   └── dashboard.py
│   │   ├── components/
│   │   │   ├── auth.py
│   │   │   └── ui.py
│   │   └── config.py
│   ├── requirements.txt
│   └── .streamlit/config.toml
├── backend/
│   ├── src/
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   ├── brand_account.py
│   │   │   ├── generated_page.py
│   │   │   ├── session.py
│   │   │   ├── otp_code.py
│   │   │   └── password_reset_token.py
│   │   ├── services/
│   │   │   ├── auth_service.py
│   │   │   ├── email_service.py
│   │   │   └── session_service.py
│   │   ├── api/
│   │   │   ├── v1/
│   │   │   │   ├── endpoints/
│   │   │   │   │   ├── auth.py
│   │   │   │   │   ├── users.py
│   │   │   │   │   ├── brand_accounts.py
│   │   │   │   │   └── pages.py
│   │   │   │   └── router.py
│   │   ├── database.py
│   │   ├── config.py
│   │   └── main.py
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   └── conftest.py
│   ├── requirements.txt
│   └── alembic/
└── shared/
    ├── schemas/
    │   ├── user.py
    │   └── auth.py
    └── utils/
        ├── security.py
        └── validators.py
```

**Structure Decision**: Separated frontend (Streamlit) and backend (FastAPI) directories with shared schemas and utilities. This provides clear separation of concerns while allowing future migration to production SaaS architecture.

## Implementation Phases

### Phase 1 — Setup (Week 1)

**Goal**: Project initialization, development environment setup, and basic infrastructure

**Tasks**:
- Initialize frontend and backend projects
- Set up PostgreSQL database
- Configure environment variables
- Set up development tools (pre-commit, linting)
- Create basic project structure

**Exit Criteria**: Both frontend and backend can run locally, database connection successful

---

### Phase 2 — User Story 1: Hero Landing Page (Priority: P1) 🎯 MVP

**Goal**: Public landing page with hero section, product explanation, and CTAs

**Independent Test**: Visit landing page URL, verify all sections render, CTAs redirect correctly

**Tasks**:
- Create landing page layout in Streamlit
- Implement hero section with headline and CTAs
- Add product explanation section
- Add workflow visualization
- Add social proof placeholders
- Implement responsive design
- Add dark/light mode toggle
- Performance optimization (load <3s)

**Exit Criteria**: Landing page loads in <3s, all CTAs functional, responsive on mobile

---

### Phase 3 — User Story 2: User Sign Up (Priority: P1) 🎯 MVP

**Goal**: User can create account with email/password or Google OAuth

**Independent Test**: Complete signup flow with valid credentials, account created, redirected to dashboard

**Tasks**:
- Create User and BrandAccount models
- Implement email validation
- Implement password hashing and validation
- Create signup API endpoint
- Implement Google OAuth integration
- Create signup page in Streamlit
- Add form validation
- Implement duplicate email check
- Add terms acceptance validation

**Exit Criteria**: User can signup with email/password and Google OAuth, account created successfully

---

### Phase 4 — User Story 3: User Sign In (Priority: P1) 🎯 MVP

**Goal**: User can sign in with email/password, Google OAuth, or OTP

**Independent Test**: Sign in with valid credentials, session created, redirected to dashboard with personalized welcome

**Tasks**:
- Create Session model
- Implement session management service
- Create signin API endpoint
- Implement OTP generation and validation
- Create OTP API endpoints
- Create signin page in Streamlit
- Add Google OAuth sign-in
- Add OTP sign-in flow
- Implement forgot password link
- Add personalized welcome message

**Exit Criteria**: User can sign in with all three methods, session created, dashboard accessible

---

### Phase 5 — User Story 4: Protected Dashboard (Priority: P1) 🎯 MVP

**Goal**: Authenticated users can view dashboard with brand account and generated pages

**Independent Test**: Sign in and access dashboard, verify brand account name and page list displayed

**Tasks**:
- Create GeneratedPage model
- Implement route protection middleware
- Create dashboard page in Streamlit
- Display brand account information
- Display generated pages list with status badges
- Implement empty state
- Add mock data for MVP
- Implement session timeout
- Add sign-out functionality
- Performance optimization (load <2s)

**Exit Criteria**: Dashboard displays brand account and pages, protected routes redirect to login

---

### Phase 6 — User Story 5: OTP Authentication (Priority: P2)

**Goal**: Passwordless authentication via email OTP

**Independent Test**: Request OTP, receive code, authenticate successfully

**Tasks**:
- Create OTPCode model
- Implement OTP generation service
- Implement email service integration
- Add rate limiting for OTP requests
- Implement OTP expiration
- Add max attempt blocking
- Create OTP request API endpoint
- Create OTP verification API endpoint
- Add OTP sign-in UI

**Exit Criteria**: OTP sent within 10s, valid codes authenticate user, expired/blocked codes rejected

---

### Phase 7 — User Story 6: Password Recovery (Priority: P2)

**Goal**: Users can reset password via secure email flow

**Independent Test**: Request reset, receive link, set new password, sign in successfully

**Tasks**:
- Create PasswordResetToken model
- Implement token generation service
- Create password reset request API endpoint
- Create password reset confirm API endpoint
- Add token expiration
- Implement password reset page in Streamlit
- Add password strength validation
- Send reset email

**Exit Criteria**: Reset link sent within 10s, valid tokens allow password reset, expired tokens rejected

---

### Phase 8 — Polish & Cross-Cutting Concerns

**Goal**: Production-ready features, testing, documentation

**Tasks**:
- Add comprehensive error handling
- Implement logging
- Add input sanitization
- Write unit tests
- Write integration tests
- Add API documentation
- Create deployment guide
- Security audit
- Performance testing
- Mobile testing

**Exit Criteria**: All tests passing, documentation complete, security review passed

---

## Stack Reference

| Layer | Choice | Rationale |
|-------|--------|-----------|
| Frontend | Streamlit | Rapid MVP development, Python-based, responsive |
| Backend API | FastAPI | Fast, async, auto-docs, Python ecosystem |
| Database | PostgreSQL | Robust, relational, aligns with existing stack |
| ORM | SQLAlchemy | Python standard, mature, migration support |
| Auth | Custom + Google OAuth | Full control, cost-effective, modular |
| Email | SendGrid/AWS SES | Reliable, good deliverability, API-based |
| Session | Database + Redis | Persistent, fast lookup, scalable |
| Testing | pytest | Python standard, async support |

---

## Risks

| Risk | Mitigation |
|------|-----------|
| Streamlit limitations for complex UI | Modular design allows migration to Next.js |
| Google OAuth configuration complexity | Detailed setup guide, test environment |
| Email deliverability issues | Use reputable provider, domain verification |
| Session management complexity | Use proven patterns, Redis caching |
| Security vulnerabilities | Security audit, input validation, rate limiting |
| Performance issues with Streamlit | Optimize components, lazy loading, caching |
| Database migration issues | Use Alembic, test migrations thoroughly |
