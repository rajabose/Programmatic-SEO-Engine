# Data Model: Brand Authentication Portal

**Feature**: Brand Authentication Portal  
**Created**: 2026-05-17

## Entity: User

**Purpose**: Represents a platform user with authentication credentials and profile information

**Fields**:
- `id` (UUID, primary key): Unique user identifier
- `email` (String, unique, indexed): User's work email address
- `password_hash` (String): Bcrypt-hashed password (nullable for OAuth-only users)
- `name` (String): User's full name
- `google_id` (String, nullable): Google OAuth user ID
- `avatar_url` (String, nullable): Profile picture URL from OAuth provider
- `created_at` (DateTime): Account creation timestamp
- `updated_at` (DateTime): Last profile update timestamp
- `is_active` (Boolean): Account status (true=active, false=disabled)
- `email_verified` (Boolean): Email verification status

**Relationships**:
- One-to-many with Session (user has many sessions)
- Many-to-one with BrandAccount (user belongs to one brand account)

**Validation Rules**:
- Email must be valid format and unique
- Password must meet strength requirements (min 8 chars, uppercase, lowercase, number, special char)
- Name required (min 2 chars)
- Google ID unique if present

**State Transitions**:
- Created → Email Verified → Active
- Active → Disabled (admin action)

---

## Entity: BrandAccount

**Purpose**: Represents a D2C brand entity with associated users and generated content

**Fields**:
- `id` (UUID, primary key): Unique brand account identifier
- `name` (String): Brand/company name
- `slug` (String, unique, indexed): URL-friendly brand identifier
- `created_at` (DateTime): Account creation timestamp
- `updated_at` (DateTime): Last update timestamp
- `is_active` (Boolean): Account status

**Relationships**:
- One-to-many with User (brand has many users)
- One-to-many with GeneratedPage (brand has many generated pages)

**Validation Rules**:
- Name required (min 2 chars)
- Slug must be unique and URL-safe
- Slug auto-generated from name if not provided

**State Transitions**:
- Created → Active
- Active → Suspended (admin action)

---

## Entity: GeneratedPage

**Purpose**: Represents SEO/AEO content generated for a brand account with status tracking

**Fields**:
- `id` (UUID, primary key): Unique page identifier
- `brand_account_id` (UUID, foreign key): Associated brand account
- `title` (String): Page title
- `slug` (String, unique): URL slug
- `status` (Enum): Draft, Review Pending, Approved, Published
- `content` (Text, nullable): Page content (HTML or markdown)
- `seo_score` (Integer, nullable): SEO score (0-100)
- `created_at` (DateTime): Page creation timestamp
- `updated_at` (DateTime): Last update timestamp
- `published_at` (DateTime, nullable): Publication timestamp

**Relationships**:
- Many-to-one with BrandAccount (page belongs to one brand account)

**Validation Rules**:
- Title required (min 5 chars)
- Slug must be unique
- Status must be valid enum value
- SEO score between 0-100 if present

**State Transitions**:
- Draft → Review Pending → Approved → Published
- Any state → Draft (revision requested)

---

## Entity: Session

**Purpose**: Represents an active user authentication session with expiration and metadata

**Fields**:
- `id` (UUID, primary key): Unique session identifier
- `user_id` (UUID, foreign key): Associated user
- `token` (String, unique, indexed): Session token (JWT or random string)
- `ip_address` (String, nullable): Client IP address
- `user_agent` (String, nullable): Client user agent string
- `created_at` (DateTime): Session creation timestamp
- `expires_at` (DateTime): Session expiration timestamp
- `last_activity_at` (DateTime): Last user activity timestamp
- `is_active` (Boolean): Session status

**Relationships**:
- Many-to-one with User (session belongs to one user)

**Validation Rules**:
- Token must be unique
- Expires at must be after created at
- IP address and user agent optional but recommended for security

**State Transitions**:
- Created → Active → Expired
- Active → Revoked (logout or security event)

---

## Entity: OTPCode

**Purpose**: Represents a one-time authentication code with expiration, usage tracking, and email association

**Fields**:
- `id` (UUID, primary key): Unique OTP identifier
- `email` (String, indexed): User's email address
- `code` (String): 6-digit numeric code
- `attempts` (Integer): Number of failed attempts
- `created_at` (DateTime): OTP creation timestamp
- `expires_at` (DateTime): OTP expiration timestamp
- `used_at` (DateTime, nullable): Timestamp when code was successfully used
- `is_used` (Boolean): Whether code has been used

**Relationships**:
- None (standalone entity)

**Validation Rules**:
- Email must be valid format
- Code must be exactly 6 digits
- Expires at typically 10 minutes after created at
- Max attempts typically 5 before blocking

**State Transitions**:
- Created → Used (successful authentication)
- Created → Expired (time limit exceeded)
- Created → Blocked (max attempts exceeded)

---

## Entity: PasswordResetToken

**Purpose**: Represents a secure token for password reset flow with expiration and user association

**Fields**:
- `id` (UUID, primary key): Unique token identifier
- `user_id` (UUID, foreign key): Associated user
- `token` (String, unique, indexed): Secure random token
- `created_at` (DateTime): Token creation timestamp
- `expires_at` (DateTime): Token expiration timestamp
- `used_at` (DateTime, nullable): Timestamp when token was used
- `is_used` (Boolean): Whether token has been used

**Relationships**:
- Many-to-one with User (token belongs to one user)

**Validation Rules**:
- Token must be unique and cryptographically secure
- Expires at typically 1 hour after created at
- Token invalid after use

**State Transitions**:
- Created → Used (password reset completed)
- Created → Expired (time limit exceeded)
