# The App Store version

The free home-screen app (see README) is the main way to use this Bible on
an iPhone. This file covers the optional App Store version: the same app
wrapped as a native iPhone app with [Capacitor](https://capacitorjs.com).

**No Mac is needed.** The `iPhone app build` workflow builds it on GitHub's
cloud Macs. Every pull request and every change to `master` already builds
it, opens it in an iPhone simulator, and saves a screenshot (Actions tab ->
the run -> Artifacts). Only *signing and uploading* need Apple's paid
developer account.

## 1. Join the Apple Developer Program

<https://developer.apple.com/programs/enroll/> ($99 a year). Approval can
take a day or two. Then note your **Team ID**: developer.apple.com ->
Account -> Membership details.

## 2. Create the app record

1. <https://developer.apple.com/account/resources/identifiers/list> -> **+** ->
   App IDs -> App -> Explicit Bundle ID: `com.josh7895.kjv1611bible`,
   description `1611 Bible`. No extra capabilities needed.
2. <https://appstoreconnect.apple.com> -> Apps -> **+** -> New App: iOS, name
   (must be unique on the store, e.g. "1611 Bible – KJV"), language English,
   the bundle ID above, any SKU (e.g. `kjv1611`).

## 3. Make an App Store Connect API key (lets GitHub sign and upload)

App Store Connect -> Users and Access -> Integrations -> App Store Connect
API -> Team Keys -> **+**. Access: **Admin** (needed so GitHub can create the
signing certificate for you). Download the `.p8` file (Apple only lets you
download it once) and note the **Key ID** and the **Issuer ID** shown above
the list.

## 4. Add four secrets to GitHub (never paste these in chat)

GitHub -> this repository -> Settings -> Secrets and variables -> Actions ->
**New repository secret**, four times:

| Name | Value |
| --- | --- |
| `APPLE_TEAM_ID` | Your Team ID from step 1 (10 characters) |
| `ASC_KEY_ID` | The API key's Key ID |
| `ASC_ISSUER_ID` | The Issuer ID (a long id with dashes) |
| `ASC_KEY_P8` | The whole contents of the `.p8` file, including the `BEGIN`/`END` lines |

## 5. Upload a build

GitHub -> Actions -> **iPhone app build** -> Run workflow -> tick **upload**
-> Run. About 15–20 minutes later the build shows in App Store Connect ->
TestFlight. Install Apple's **TestFlight** app on your iPhone, add yourself
as an internal tester, and you can use the real app before anyone else.

## 6. Submit for review

In App Store Connect fill in the listing: description, keywords, category
(Reference or Books), age rating, screenshots (the 6.9" iPhone size), and
the privacy policy URL:
`https://github.com/Josh7895/kjv-1611-bible/blob/master/PRIVACY.md`.
For App Privacy, declare **Email address** and **User content (notes,
bookmarks)**, linked to the user, used for app functionality, not tracking.
If sign-in is on, give the reviewer a test email and password under App
Review Information.

Things Apple checks that this app already handles: accounts can be deleted
inside the app (Account -> Delete my account), email sign-in needs no "Sign
in with Apple", and no tracking. Apple sometimes rejects apps it sees as "just
a website" (guideline 4.2). The built-in offline Bible, notes, narration and
sync help, but approval isn't guaranteed, and the home-screen app keeps
working either way.

## Updating the app later

Web changes reach the website straight away; the App Store app only changes
when you run the workflow with **upload** again and submit the new build.
Locally (any computer with Node 22): `npm ci && npm run ios:sync` copies the
web app into `ios/`.
