/* Copies the web app into www/, the folder Capacitor packs into the iPhone
   app. The website itself is served straight from the repository root;
   www/ is only a build output (ignored by git). Run: node tools/build-www.js */
"use strict";
const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const OUT = path.join(ROOT, "www");
const FILES = ["index.html", "manifest.json", "service-worker.js", "auth-config.json"];
const DIRS = ["data", "icons", "art"]; /* art/ arrives with the story pictures PR */

fs.rmSync(OUT, { recursive: true, force: true });
fs.mkdirSync(OUT);
FILES.forEach(f => fs.copyFileSync(path.join(ROOT, f), path.join(OUT, f)));
DIRS.forEach(d => {
  if (fs.existsSync(path.join(ROOT, d))) fs.cpSync(path.join(ROOT, d), path.join(OUT, d), { recursive: true });
});
console.log("www/ ready: " + FILES.concat(DIRS.filter(d => fs.existsSync(path.join(ROOT, d)))).join(", "));
