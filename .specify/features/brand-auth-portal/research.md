# Research: Brand Authentication Portal

**Feature**: Brand Authentication Portal  
**Created**: 2026-05-17

## Decision: Frontend Framework

**Chosen**: Streamlit

**Rationale**: 
- Rapid MVP development with minimal boilerplate
- Built-in authentication state management
- Responsive design out of the box
- Python-based, aligns with existing tech stack
- Easy to deploy and maintain
- Sufficient for MVP scope (landing page, signup, login, dashboard)

**Alternatives Considered**:
- Next.js: More production-ready but requires JavaScript/TypeScript expertise and longer setup time
- Gradio: Similar to Streamlit but more focused on ML demos, less suitable for SaaS authentication flows
- Pure FastAPI + Jinja2: More control but requires more frontend development effort

## Decision: Backend Framework

**Chosen**: FastAPI (for authentication API endpoints if needed beyond Streamlit)

**Rationale**:
- Python-based, aligns with constitution requirement
- Fast performance with async support
- Automatic API documentation
- Easy integration with Streamlit
- Scalable for future production migration
- Strong authentication library ecosystem (python-jose, passlib, etc.)

**Alternatives Considered**:
- Flask: Simpler but less modern features and slower performance
- Django: Too heavyweight for MVP authentication needs
- Pure Streamlit: May be sufficient for MVP but FastAPI provides better separation of concerns

## Decision: Database

**Chosen**: PostgreSQL

**Rationale**:
- Robust relational database with strong data integrity
- Supports JSON fields for flexible schema
- Excellent for user authentication and session management
- Aligns with existing landing-page-generation feature
- Strong ecosystem and tooling
- Production-ready for future SaaS migration

**Alternatives Considered**:
- SQLite: Too simple for production-scale authentication
- MongoDB: Good for flexible schemas but overkill for MVP
- Redis: Good for caching but not suitable as primary data store

## Decision: Authentication Provider

**Chosen**: Custom implementation with Google OAuth integration

**Rationale**:
- Full control over user data and authentication flow
- Google OAuth via Authlib or python-social-auth
- Cost-effective for MVP (no per-user fees)
- Modular design allows future migration to managed auth (Clerk, Auth0)
- Aligns with spec requirements (email/password, Google OAuth, OTP)

**Alternatives Considered**:
- Clerk: Excellent managed auth but adds cost and dependency
- Auth0: Enterprise-grade but overkill for MVP
- Firebase Auth: Good but adds Google platform dependency
- Supabase Auth: Good option but PostgreSQL already chosen

## Decision: Email Service

**Chosen**: SendGrid or AWS SES

**Rationale**:
- Reliable transactional email delivery
- Good deliverability rates
- Easy API integration
- Cost-effective for MVP volume
- Supports OTP and password reset flows

**Alternatives Considered**:
- SMTP self-hosted: Too complex and poor deliverability
- Mailgun: Good alternative to SendGrid
- Postmark: Excellent but higher cost

## Decision: Session Management

**Chosen**: Database-backed sessions with Redis caching

**Rationale**:
- Persistent sessions across server restarts
- Redis caching for fast session lookup
- Supports concurrent session handling
- Easy to implement session timeout
- Scalable for production

**Alternatives Considered**:
- JWT-only: Stateless but harder to invalidate sessions
- Pure database: Slower performance
- Pure Redis: Fast but data loss on restart

## Decision: Project Structure

**Chosen**: Monorepo with separated frontend/backend directories

**Rationale**:
- Clear separation of concerns
- Easy to migrate to microservices later
- Streamlit frontend in `frontend/` directory
- FastAPI backend in `backend/` directory
- Shared models and utilities in `shared/` directory
- Aligns with plan template Option 2

**Alternatives Considered**:
- Single directory: Too messy for growing codebase
- Separate repositories: Overkill for MVP
- Monolithic Streamlit-only: Limits future scalability
