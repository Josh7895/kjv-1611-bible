/* Checks that every chapter of every book has a story picture, that each
   picture's drawing exists in art/scenes/, that the service worker stores
   exactly those drawings, and that the page's CSP hash is current.
   Run:  node tools/check_pictures.js */
var fs = require("fs");
var path = require("path");
var crypto = require("crypto");
var vm = require("vm");

var root = path.join(__dirname, "..");
var html = fs.readFileSync(path.join(root, "index.html"), "utf8");
var errors = [];

var block = /var PICTURES = \{[\s\S]*?\n\};/.exec(html);
if (!block) { console.error("PICTURES not found in index.html"); process.exit(1); }
var sandbox = {};
vm.runInNewContext(block[0] + "\nthis.PICTURES = PICTURES;", sandbox);
var PICTURES = sandbox.PICTURES;

var bible = JSON.parse(fs.readFileSync(path.join(root, "data", "kjv.json"), "utf8"));
var used = {}, chapters = 0;
bible.books.forEach(function (b) {
  var name = b.englishName || b.book;
  var lines = PICTURES[name];
  if (!lines) { errors.push("no pictures for " + name); return; }
  var last = 0;
  lines.forEach(function (line) {
    var m = /^(\d+) (\S+) (.+)$/.exec(line);
    if (!m) { errors.push(name + ": bad line " + JSON.stringify(line)); return; }
    var ch = Number(m[1]);
    if (ch <= last) errors.push(name + ": chapter " + ch + " out of order");
    if (ch > b.chapters.length) errors.push(name + ": chapter " + ch + " does not exist");
    last = ch;
    used[m[2]] = true;
    if (!fs.existsSync(path.join(root, "art", "scenes", m[2] + ".svg")))
      errors.push(name + " " + ch + ": missing art/scenes/" + m[2] + ".svg");
  });
  if (!/^1 /.test(lines[0] || "")) errors.push(name + ": chapter 1 has no picture");
  chapters += b.chapters.length;
});
Object.keys(PICTURES).forEach(function (name) {
  if (!bible.books.some(function (b) { return (b.englishName || b.book) === name; }))
    errors.push("PICTURES names unknown book " + name);
});

var files = fs.readdirSync(path.join(root, "art", "scenes"))
  .filter(function (f) { return /\.svg$/.test(f); }).map(function (f) { return f.slice(0, -4); }).sort();
files.forEach(function (f) { if (!used[f]) errors.push("art/scenes/" + f + ".svg is never used"); });

var sw = fs.readFileSync(path.join(root, "service-worker.js"), "utf8");
var swList = /var SCENES = (\[[\s\S]*?\]);/.exec(sw);
var scenes = swList ? JSON.parse(swList[1]).sort() : [];
if (JSON.stringify(scenes) !== JSON.stringify(files))
  errors.push("service-worker.js SCENES does not match art/scenes/");

var scripts = html.match(/<script>([\s\S]*?)<\/script>/g) || [];
if (scripts.length === 1) {
  var body = scripts[0].slice(8, -9);
  var hash = crypto.createHash("sha256").update(body, "utf8").digest("base64");
  if (html.indexOf("'sha256-" + hash + "'") === -1) errors.push("CSP script hash is stale: run python update_csp.py");
} else errors.push("expected exactly one inline <script>");

if (errors.length) { errors.forEach(function (e) { console.error("FAIL " + e); }); process.exit(1); }
console.log("OK: " + chapters + " chapters, " + files.length + " drawings, all covered");
