# Turning on sign-in (about 10 minutes, free)

The app works fully without this. Sign-in only adds syncing: bookmarks,
notes, reading place and settings follow you between your iPhone, tablet
and computer. It uses [Supabase](https://supabase.com) (free plan is plenty).

## 1. Create the Supabase project

1. Go to <https://supabase.com>, sign up, and click **New project**.
   Any name (e.g. `kjv-bible`), pick a database password (keep it to
   yourself, the app never needs it), choose the region nearest you.
2. Wait for it to finish setting up (a minute or two).

## 2. Create the table

1. In the left menu open **SQL Editor**, click **New query**.
2. Paste everything from [`supabase/schema.sql`](supabase/schema.sql) and click **Run**.
   It creates one private table where each person can only see their own row,
   plus a "delete my account" function.

## 3. Tell Supabase where the app lives

**Authentication → URL Configuration**:

- **Site URL**: `https://josh7895.github.io/kjv-1611-bible/`
  (or wherever you host the app)
- **Redirect URLs**: add the same address.

This is where the "confirm your email" and "reset password" links send people.

## 4. Put the public keys in the app

**Project Settings → API** (or **API Keys**) shows two things you need:

- **Project URL**, like `https://abcdefghijkl.supabase.co`
- The **anon public** key (or the **publishable** key, starting `sb_publishable_`)

Open [`auth-config.json`](auth-config.json) on GitHub, click the pencil, and fill them in:

```json
{
  "supabaseUrl": "https://abcdefghijkl.supabase.co",
  "supabaseAnonKey": "eyJhbGciOi...your anon key..."
}
```

Commit. Within a minute or two the Account button in the app offers
Sign In and Create Account.

These two values are meant to be public: the table rules from step 2 are
what keep everyone's data private. **Never** put the `service_role` key or
a `sb_secret_` key in this file or anywhere in the app (the automated test
refuses them).

## Good to know

- **Email confirmation** is on by default: new accounts get an email link
  first. On iPhone, a home-screen app opens that link in Safari; after it
  says you're confirmed, go back to the app and tap Sign In.
- Supabase's built-in email sender only sends a few emails per hour. That's
  fine for a family; for more people, add your own email service under
  **Authentication → Emails → SMTP Settings**, or turn off **Confirm email**
  under **Authentication → Sign In / Providers → Email**.
- The app only talks to `*.supabase.co` addresses (its security policy
  blocks everything else), so a custom Supabase domain would need
  `update_csp.py` changed too.
