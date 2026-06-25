# Quickstart: Brand Authentication Portal

**Feature**: Brand Authentication Portal  
**Created**: 2026-05-17

## Happy Path: User Signup and Dashboard Access

1. **Visit Landing Page**
   - User navigates to platform URL
   - Landing page loads with hero section, product explanation, and CTAs
   - User clicks "Sign Up" button

2. **Complete Signup**
   - User enters name, work email, password, and brand name
   - User accepts terms and conditions
   - User submits form
   - Account is created in database
   - User is redirected to dashboard

3. **View Dashboard**
   - Dashboard loads with personalized welcome message
   - Brand account name is displayed
   - Mock generated pages list is shown with status badges
   - Empty state message if no pages exist

## Happy Path: User Sign In

1. **Visit Login Page**
   - User navigates to platform URL
   - User clicks "Sign In" button

2. **Authenticate**
   - User enters email and password
   - User submits form
   - Credentials are validated
   - Session is created
   - User is redirected to dashboard

3. **View Dashboard**
   - Dashboard loads with personalized welcome message
   - Brand account name is displayed
   - Generated pages list is shown

## Happy Path: Google OAuth Sign In

1. **Visit Login Page**
   - User navigates to platform URL
   - User clicks "Continue with Google"

2. **OAuth Flow**
   - User is redirected to Google OAuth consent screen
   - User authorizes the application
   - Google redirects back with authorization code
   - User profile is retrieved from Google
   - Account is created if new, or existing account is linked
   - Session is created
   - User is redirected to dashboard

## Happy Path: OTP Authentication

1. **Request OTP**
   - User on login page clicks "Sign in with OTP"
   - User enters email address
   - System generates 6-digit code
   - System sends code via email
   - User sees OTP input field

2. **Enter OTP**
   - User receives email with code
   - User enters code in input field
   - System validates code
   - Session is created
   - User is redirected to dashboard

## Happy Path: Password Recovery

1. **Initiate Reset**
   - User on login page clicks "Forgot password"
   - User enters email address
   - System generates secure reset token
   - System sends reset link via email

2. **Reset Password**
   - User clicks reset link in email
   - User is taken to password reset page
   - User enters new password
   - System validates password strength
   - Password is updated in database
   - User is redirected to login page

## Key Error Conditions

### Invalid Email Format
- User enters invalid email during signup
- System displays error message
- No account is created

### Duplicate Email
- User attempts to sign up with existing email
- System displays duplicate account error
- User is prompted to sign in instead

### Weak Password
- User enters weak password during signup
- System displays password strength requirements
- User must enter stronger password

### Invalid Credentials
- User enters incorrect email/password during sign in
- System displays authentication error
- User can retry or use password recovery

### Expired OTP
- User enters expired OTP code
- System displays expiration error
- User must request new OTP

### Max OTP Attempts
- User exceeds maximum failed OTP attempts
- System temporarily blocks OTP requests
- User must wait or use alternative authentication method

### Expired Reset Token
- User clicks expired password reset link
- System displays expiration error
- User must request new reset link

## Integration with Other Features

### Content Generation API
- Dashboard will eventually fetch generated pages from backend content generation API
- For MVP, mock data is used
- Future integration: Replace mock data with API calls to existing backend systems

### Google OAuth Configuration
- Requires Google Cloud Console project setup
- OAuth 2.0 credentials (client ID, client secret)
- Redirect URI configuration
- Scopes: email, profile

### Email Service Integration
- Requires SendGrid or AWS SES account
- API key configuration
- Email templates for OTP and password reset
- Domain verification for deliverability

## Protected Routes

All routes except landing page, signup, and login require authentication:
- `/dashboard` - Protected, redirects to login if not authenticated
- `/profile` - Protected, redirects to login if not authenticated
- `/settings` - Protected, redirects to login if not authenticated

## Session Management

- Sessions expire after configurable timeout (default: 24 hours)
- Session is refreshed on user activity
- User can manually sign out, which invalidates session
- Concurrent sessions allowed (user can be logged in on multiple devices)

## Mobile Responsiveness

- All pages are responsive and functional on mobile devices
- Touch-friendly UI elements
- Optimized for mobile viewport widths
- Fast loading on mobile networks
