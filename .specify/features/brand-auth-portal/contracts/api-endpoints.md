# API Contracts: Brand Authentication Portal

**Feature**: Brand Authentication Portal  
**Created**: 2026-05-17

## Authentication Endpoints

### POST /api/v1/auth/signup
Create new user account with email/password

### POST /api/v1/auth/signin
Authenticate with email/password

### POST /api/v1/auth/google
Authenticate via Google OAuth

### POST /api/v1/auth/otp/request
Request OTP code

### POST /api/v1/auth/otp/verify
Verify OTP and create session

### POST /api/v1/auth/password-reset/request
Request password reset link

### POST /api/v1/auth/password-reset/confirm
Reset password with token

### POST /api/v1/auth/signout
Invalidate session

## User Endpoints

### GET /api/v1/users/me
Get current user profile

### PUT /api/v1/users/me
Update user profile

## Brand Account Endpoints

### GET /api/v1/brand-accounts/me
Get current brand account

## Generated Pages Endpoints

### GET /api/v1/pages
List generated pages (with status filter)

### GET /api/v1/pages/{page_id}
Get page details

## Authentication
All protected endpoints use `Authorization: Bearer {session_token}` header.
