# 0002. Use local email/password auth with rotating JWTs

- **Status:** Accepted
- **Date:** 2026-10-25

## Context

Authentication previously went through Supabase Auth (and earlier, Cognito). That meant an
external dependency for every login, an extra user ID mapping (`supabase_uid`) and custom
authentication classes. The product only needs email and password sign-in for now.

## Decision

- Django stores users (`users.Users`, email as the username, hashed passwords) and issues JWTs
  with `djangorestframework-simplejwt`.
- Access tokens last 15 minutes and refresh tokens 7 days (`JWT_ACCESS_MINUTES`,
  `JWT_REFRESH_DAYS`).
- `ROTATE_REFRESH_TOKENS` and `BLACKLIST_AFTER_ROTATION` are on: every refresh returns a new pair
  and the old refresh token stops working. Logout blacklists the refresh token.
- Passwords go through Django's default validators.

## Alternatives considered

- **Keep Supabase Auth:** an extra service and token translation for features we don't use.
- **Session cookies from Django:** this would tie the API to a single browser origin. With JWTs,
  the Next.js BFF can own the cookies instead.

## Consequences

Clients must store both tokens after every refresh, and must serialise concurrent refreshes or a
blacklisted token will log the user out. The frontend BFF de-duplicates refreshes for this
reason. Social login or MFA would need new work. Revisit this if either is required.
