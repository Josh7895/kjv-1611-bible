/* End-to-end check of the iPhone app and optional sign-in, in a headless
   browser at phone size. Supabase is replaced by an in-memory stand-in
   (same endpoints and answers), so no account or network is needed.

   Run: npm install --no-save playwright && npx playwright install chromium
        node tests/app.test.js [screenshot-dir]
*/
"use strict";
const http = require("http");
const fs = require("fs");
const path = require("path");
const crypto = require("crypto");
const assert = require("assert");
const { chromium, devices } = require("playwright");

const ROOT = path.resolve(__dirname, "..");
const SHOTS = process.argv[2] || "";
const SB = "https://testproj.supabase.co";
const ANON = "test-anon-key";
const TYPES = { ".html": "text/html", ".js": "text/javascript", ".json": "application/json", ".png": "image/png", ".svg": "image/svg+xml" };

/* ---- the page's CSP must match its script ---- */
const html = fs.readFileSync(path.join(ROOT, "index.html"), "utf8");
const script = html.match(/<script>([\s\S]*?)<\/script>/)[1];
const hash = crypto.createHash("sha256").update(script, "utf8").digest("base64");
assert(html.includes("'sha256-" + hash + "'"), "CSP script hash is stale: run python update_csp.py");
assert(/connect-src[^;]*https:\/\/\*\.supabase\.co/.test(html), "CSP must allow https://*.supabase.co");
const cfg = JSON.parse(fs.readFileSync(path.join(ROOT, "auth-config.json"), "utf8"));
{
  /* Only the public key belongs here: never a secret or service_role key. */
  const key = String(cfg.supabaseAnonKey || "");
  assert(!/^sb_secret_/.test(key), "auth-config.json holds a secret key; use the publishable/anon key");
  const parts = key.split(".");
  if (parts.length === 3){
    const role = JSON.parse(Buffer.from(parts[1], "base64url").toString("utf8")).role;
    assert.notStrictEqual(role, "service_role", "auth-config.json holds the service_role key; use the anon key");
  }
}

/* ---- static server for the app ---- */
function serve(){
  const server = http.createServer((req, res) => {
    const p = decodeURIComponent(new URL(req.url, "http://x").pathname);
    const file = path.join(ROOT, p === "/" ? "index.html" : p);
    if (!file.startsWith(ROOT) || !fs.existsSync(file) || fs.statSync(file).isDirectory()){ res.writeHead(404); return res.end(); }
    res.writeHead(200, { "Content-Type": TYPES[path.extname(file)] || "application/octet-stream" });
    fs.createReadStream(file).pipe(res);
  });
  return new Promise(r => server.listen(0, "127.0.0.1", () => r(server)));
}

/* ---- in-memory Supabase (Auth + one PostgREST table) ---- */
const db = { users: {}, rows: {}, tokens: {}, refresh: {}, calls: [] };
function issue(user){
  const access = "at-" + crypto.randomBytes(8).toString("hex");
  const refresh = "rt-" + crypto.randomBytes(8).toString("hex");
  db.tokens[access] = user.id; db.refresh[refresh] = user.id;
  return { access_token: access, refresh_token: refresh, token_type: "bearer", expires_in: 3600,
           expires_at: Math.floor(Date.now() / 1000) + 3600, user: { id: user.id, email: user.email } };
}
async function supabase(route){
  const req = route.request(), url = new URL(req.url()), method = req.method();
  const json = (status, body) => route.fulfill({ status, contentType: "application/json",
    headers: { "access-control-allow-origin": "*" }, body: body === undefined ? "" : JSON.stringify(body) });
  if (method === "OPTIONS") return route.fulfill({ status: 200, headers: { "access-control-allow-origin": "*",
    "access-control-allow-headers": "*", "access-control-allow-methods": "*" } });
  db.calls.push(method + " " + url.pathname);
  if (req.headers()["apikey"] !== ANON) return json(401, { message: "Invalid API key" });
  const body = req.postData() ? JSON.parse(req.postData()) : {};
  const auth = (req.headers()["authorization"] || "").replace(/^Bearer /, "");
  const uid = db.tokens[auth];
  const p = url.pathname, grant = url.searchParams.get("grant_type");
  if (p === "/auth/v1/signup"){
    if (Object.values(db.users).some(u => u.email === body.email)) return json(422, { code: 422, error_code: "user_already_exists", msg: "User already registered" });
    const user = { id: crypto.randomUUID(), email: body.email, password: body.password };
    db.users[user.id] = user;
    return json(200, issue(user));
  }
  if (p === "/auth/v1/token" && grant === "password"){
    const user = Object.values(db.users).find(u => u.email === body.email && u.password === body.password);
    return user ? json(200, issue(user)) : json(400, { code: 400, error_code: "invalid_credentials", msg: "Invalid login credentials" });
  }
  if (p === "/auth/v1/token" && grant === "refresh_token"){
    const id = db.refresh[body.refresh_token]; delete db.refresh[body.refresh_token];
    return id && db.users[id] ? json(200, issue(db.users[id])) : json(400, { error_code: "refresh_token_not_found", msg: "Invalid Refresh Token" });
  }
  if (!uid || !db.users[uid]) return json(401, { code: 401, msg: "JWT expired" });
  if (p === "/auth/v1/user" && method === "GET") return json(200, { id: uid, email: db.users[uid].email });
  if (p === "/auth/v1/user" && method === "PUT"){ db.users[uid].password = body.password; return json(200, { id: uid }); }
  if (p === "/auth/v1/logout"){ delete db.tokens[auth]; return json(204); }
  if (p === "/rest/v1/reader_data" && method === "GET"){
    assert.strictEqual(url.searchParams.get("user_id"), "eq." + uid, "may only read own row");
    return json(200, db.rows[uid] ? [{ data: db.rows[uid].data }] : []);
  }
  if (p === "/rest/v1/reader_data" && method === "POST"){
    assert.strictEqual(body.user_id, uid, "may only write own row");
    assert(/merge-duplicates/.test(req.headers()["prefer"] || ""), "upsert expected");
    db.rows[uid] = { data: body.data, updated_at: body.updated_at };
    return json(201);
  }
  if (p === "/rest/v1/rpc/delete_my_account"){
    delete db.users[uid]; delete db.rows[uid];
    Object.keys(db.tokens).forEach(t => { if (db.tokens[t] === uid) delete db.tokens[t]; });
    return json(204);
  }
  return json(404, { message: "no route " + p });
}

async function device(browser, base, profile, configured){
  const context = await browser.newContext({ ...profile, serviceWorkers: "block" });
  await context.route(/fonts\.(googleapis|gstatic)\.com|wikimedia\.org|archive\.org|raw\.githubusercontent\.com/, r => r.abort());
  await context.route(SB + "/**", supabase);
  if (configured) await context.route("**/auth-config.json", r => r.fulfill({ contentType: "application/json",
    body: JSON.stringify({ supabaseUrl: SB, supabaseAnonKey: ANON }) }));
  const page = await context.newPage();
  const errors = [];
  page.on("pageerror", e => errors.push(String(e)));
  page.on("console", m => { if (m.type() === "error" && !/ERR_FAILED|Failed to load resource/.test(m.text())) errors.push(m.text()); });
  page.errors = errors;
  return { context, page };
}
async function open(page, url){
  await page.goto(url);
  await page.waitForSelector(".book-heading");
}
async function shot(page, name){
  if (SHOTS) await page.screenshot({ path: path.join(SHOTS, name + ".png") });
}
const ROMAN = { 1: "I", 3: "III" };
async function goTo(page, book, chapter){
  await page.click("#navToggle");
  await page.click(`.book-btn:text-is("${book}")`);
  await page.click(`#grid-${book.replace(/[^a-zA-Z0-9]/g, "_")} .chap-btn:text-is("${ROMAN[chapter]}")`);
  await page.waitForFunction(b => document.querySelector(".book-heading").textContent === b.toUpperCase(), book);
}
async function waitSynced(page){
  await page.waitForFunction(() => /synced/.test(document.getElementById("syncStatus").textContent), null, { timeout: 15000 });
}
const iphone = devices["iPhone 13"];
const android = devices["Pixel 5"];

(async () => {
  if (SHOTS) fs.mkdirSync(SHOTS, { recursive: true });
  const server = await serve();
  const base = "http://127.0.0.1:" + server.address().port + "/";
  const browser = await chromium.launch();
  let step = "";
  try{
    step = "works without sign-in configured";
    {
      const { context, page } = await device(browser, base, iphone, false);
      await open(page, base);
      assert(await page.isVisible("#installTip"), "iPhone install tip shows in the browser");
      assert(/Add to Home Screen/.test(await page.textContent("#installTipText")));
      const top = await page.$eval("#topbar", e => e.getBoundingClientRect());
      assert(top.right <= 390 + 0.5, "toolbar fits the iPhone width (right edge " + top.right + ")");
      await shot(page, "1-iphone-reading");
      await page.click("#accountBtn");
      assert(await page.isVisible("#accountOff"), "explains that sign-in is off");
      assert(!(await page.isVisible("#signInForm")));
      await page.click("#closeAccount");
      await page.click("#installTipClose");
      assert(!(await page.isVisible("#installTip")));
      await page.reload(); await page.waitForSelector(".book-heading");
      assert(!(await page.isVisible("#installTip")), "tip stays dismissed");
      assert.deepStrictEqual(page.errors, []);
      await context.close();
    }

    step = "phone: create account, bookmark, note, setting";
    const phone = await device(browser, base, iphone, true);
    {
      const page = phone.page;
      await open(page, base);
      await page.click("#accountBtn");
      await page.waitForSelector("#signInForm:not([hidden])");
      await shot(page, "2-iphone-sign-in");
      await page.fill("#authEmail", "reader@example.com");
      await page.fill("#authPassword", "short");
      await page.click("#signUpBtn");
      assert(/at least 6/.test(await page.textContent("#accountMsg")), "short password is explained");
      await page.fill("#authPassword", "psalm23psalm23");
      await page.click("#signUpBtn");
      await page.waitForSelector("#signedInBox:not([hidden])");
      assert.strictEqual(await page.textContent("#accountEmail"), "reader@example.com");
      await waitSynced(page);
      assert(await page.$eval("#accountBtn", e => e.classList.contains("signed-in")));
      await page.click("#closeAccount");

      await page.click("#bookmarkBtn");
      await goTo(page, "John", 3);
      await page.click(".chapter-note summary");
      await page.fill("#chapterNoteText", "For God so loved the world.");
      await page.waitForSelector(".note-saved:text('Saved.')");
      await page.locator(".chapter-note").scrollIntoViewIfNeeded();
      await shot(page, "2b-iphone-chapter-note");
      await page.click("#settingsBtn");
      await page.click("#themeStoneBtn");
      await page.click("#closeSettings");
      await page.waitForFunction(() => true);
      await page.waitForTimeout(3500);
      const row = Object.values(db.rows)[0];
      assert(row, "a row was saved for the account");
      const d = row.data;
      assert(d.bookmarks["Genesis 1"] && !d.bookmarks["Genesis 1"].del, "bookmark synced");
      assert.strictEqual(d.notes["John 3"].t, "For God so loved the world.", "note synced");
      assert.strictEqual(d.settings.data.theme, "stone", "setting synced");
      assert.strictEqual(d.progress.book + " " + d.progress.chapter, "John 3", "reading place synced");
      assert(d.read["Genesis 1"] && d.read["John 3"], "chapters read synced");
      assert(!("narrVoice" in d.settings.data), "device voice is not synced");
      await page.click("#accountBtn");
      await shot(page, "3-iphone-signed-in");
      await page.click("#closeAccount");
    }

    step = "tablet: wrong password, then sign in and receive everything";
    const tablet = await device(browser, base, android, true);
    {
      const page = tablet.page;
      await open(page, base);
      assert.strictEqual(await page.getAttribute("body", "data-theme"), "parchment");
      await page.click("#accountBtn");
      await page.fill("#authEmail", "reader@example.com");
      await page.fill("#authPassword", "wrong-password");
      await page.press("#authPassword", "Enter");
      await page.waitForFunction(() => /don't match/.test(document.getElementById("accountMsg").textContent));
      await page.fill("#authPassword", "psalm23psalm23");
      await page.click("#signInBtn");
      await waitSynced(page);
      await page.click("#closeAccount");
      assert.strictEqual(await page.getAttribute("body", "data-theme"), "stone", "theme arrived");
      assert.strictEqual(await page.textContent(".book-heading"), "JOHN", "opened at the reading place");
      assert.strictEqual(await page.inputValue("#chapterNoteText"), "For God so loved the world.", "note arrived");
      await page.click("#bookmarksListBtn");
      assert(/Genesis/.test(await page.textContent("#bookmarksList")), "bookmark arrived");
      assert(/For God so loved/.test(await page.textContent("#notesList")), "note listed");
      await shot(page, "4-android-bookmarks-and-notes");
      await page.click("#bookmarksList .bookmark-remove");
      await page.click("#closeBookmarks");
      await page.waitForTimeout(3500);
      assert(Object.values(db.rows)[0].data.bookmarks["Genesis 1"].del, "removal synced");
      assert.deepStrictEqual(page.errors, []);
    }

    step = "phone: removal from the tablet reaches the phone";
    {
      const page = phone.page;
      await page.click("#accountBtn");
      await page.click("#syncNowBtn");
      await waitSynced(page);
      await page.click("#closeAccount");
      await page.click("#bookmarksListBtn");
      assert(/No bookmarks yet/.test(await page.textContent("#bookmarksList")), "bookmark removed on the phone too");
      await page.click("#closeBookmarks");
    }

    step = "an expired session refreshes itself";
    {
      const page = tablet.page;
      await page.evaluate(() => { const s = JSON.parse(localStorage.getItem("kjv1611-auth")); s.expires_at = 0; localStorage.setItem("kjv1611-auth", JSON.stringify(s)); });
      await page.reload(); await page.waitForSelector(".book-heading");
      await page.click("#accountBtn");
      await page.click("#syncNowBtn");
      await waitSynced(page);
      assert(db.calls.includes("POST /auth/v1/token"), "refresh used");
    }

    step = "tablet: sign out and clear the device";
    {
      const page = tablet.page;
      await page.check("#signOutWipe");
      await page.click("#signOutBtn");
      await page.waitForSelector("#signInForm:not([hidden])");
      assert.strictEqual(await page.evaluate(() => localStorage.getItem("kjv1611-auth")), null);
      await page.click("#closeAccount");
      assert.strictEqual(await page.inputValue("#chapterNoteText"), "", "note removed from this device");
      assert.deepStrictEqual(page.errors, []);
      await tablet.context.close();
    }

    step = "email link signs you in";
    {
      const user = Object.values(db.users)[0];
      const s = issue(user);
      const { context, page } = await device(browser, base, iphone, true);
      await page.goto(base + "#access_token=" + s.access_token + "&expires_in=3600&refresh_token=" + s.refresh_token + "&token_type=bearer&type=signup");
      await page.waitForSelector("#signedInBox:not([hidden])");
      assert(/confirmed/.test(await page.textContent("#accountMsg")));
      assert.strictEqual(await page.evaluate(() => location.hash), "", "tokens removed from the address");
      assert.strictEqual(await page.textContent("#accountEmail"), "reader@example.com");
      await waitSynced(page);
      await context.close();
    }

    step = "password reset link lets you choose a new password";
    {
      const user = Object.values(db.users)[0];
      const s = issue(user);
      const { context, page } = await device(browser, base, iphone, true);
      await page.goto(base + "#access_token=" + s.access_token + "&expires_in=3600&refresh_token=" + s.refresh_token + "&type=recovery");
      await page.waitForSelector("#newPasswordForm:not([hidden])");
      await page.fill("#newPassword", "newpassword7");
      await page.click("#savePasswordBtn");
      await page.waitForSelector("#signedInBox:not([hidden])");
      assert.strictEqual(user.password, "newpassword7");
      await context.close();
    }

    step = "phone: delete account";
    {
      const page = phone.page;
      await page.click("#accountBtn");
      await page.click("#deleteAccountBtn");
      await page.click("#deleteYesBtn");
      await page.waitForSelector("#signInForm:not([hidden])");
      assert.strictEqual(Object.keys(db.users).length, 0, "account deleted");
      assert.strictEqual(Object.keys(db.rows).length, 0, "saved data deleted");
      assert.deepStrictEqual(page.errors, []);
      await phone.context.close();
    }
    console.log("All app checks passed.");
  }catch(err){
    console.error("FAILED at: " + step);
    console.error(err);
    process.exitCode = 1;
  }finally{
    await browser.close();
    server.close();
  }
})();
