// The teacher server of the Myduino lab: the Jetson agents report here and the teacher page is served from here.
// Plain Node.js, no packages. It is started by main.js (the app) or by hand:  node server.js
"use strict";
const http = require("http");
const fs = require("fs");
const os = require("os");
const path = require("path");
const crypto = require("crypto");

const PORT = 8800;
const FIRST_PORT = 8881;                       // student JupyterLab ports on a Jetson start here
const ONLINE = 20;                             // seconds without news before a Jetson counts as offline
const NAME = /^[a-z0-9_]{1,20}$/;

function clean(text) {
  return String(text ?? "").toLowerCase().replace(/[^a-z0-9_]/g, "_").replace(/^_+|_+$/g, "").slice(0, 20);
}
const pin6 = () => String(crypto.randomInt(0, 1000000)).padStart(6, "0");
const now = () => Date.now() / 1000;

function myIp() {
  for (const list of Object.values(os.networkInterfaces()))
    for (const a of list || [])
      if (a.family === "IPv4" && !a.internal && !a.address.startsWith("169.254.")) return a.address;
  return "127.0.0.1";
}

function createServer(opts = {}) {
  const dataDir = opts.dataDir || path.join(os.homedir(), "myduino-teacher");
  const stateFile = path.join(dataDir, "state.json");
  const appToken = opts.appToken || "";        // the app's own window uses it; no password is needed
  const db = { key: "", classes: {}, pending_delete: [] };
  const jetsons = {};                          // id -> what the agent last reported (not saved)
  const sessions = new Set();
  let open = false;                            // the lab is open only after START LAB
  let dirty = false;

  fs.mkdirSync(dataDir, { recursive: true });
  try { Object.assign(db, JSON.parse(fs.readFileSync(stateFile, "utf8"))); } catch { /* first run */ }
  delete db.password;
  if (!db.key) { db.key = crypto.randomBytes(4).toString("hex"); dirty = true; }

  function save() {
    const tmp = stateFile + ".tmp";
    fs.writeFileSync(tmp, JSON.stringify(db, null, 1));
    fs.renameSync(tmp, stateFile);
    dirty = false;
  }
  const saver = setInterval(() => { if (dirty) save(); }, 3000);
  saver.unref();
  if (dirty) save();

  const online = j => now() - (j.seen || 0) < ONLINE;
  const students = () => Object.entries(db.classes).flatMap(([c, cl]) => Object.entries(cl.students).map(([n, s]) => [c, n, s]));

  function freePort(jetson, student) {
    const taken = new Set(students().filter(([, , s]) => s.jetson === jetson && s !== student).map(([, , s]) => s.port));
    const old = (student.ports || {})[jetson];
    if (old && !taken.has(old)) return old;
    let port = FIRST_PORT;
    while (taken.has(port)) port++;
    return port;
  }

  function assign(cls, name, jetson, camera) {
    const s = db.classes[cls].students[name];
    if (!jetson) { s.jetson = ""; s.camera = null; return "Saved."; }
    if (!jetsons[jetson]) return "That Jetson has not reported in.";
    camera = (camera === "" || camera == null) ? null : parseInt(camera, 10);
    if (camera !== null) {
      for (const [c2, n2, o] of students())
        if (o !== s && o.jetson === jetson && o.camera === camera) return `Camera ${camera} of ${jetson} is used by ${c2}/${n2}.`;
    }
    s.jetson = jetson; s.camera = camera;
    s.port = freePort(jetson, s);
    (s.ports = s.ports || {})[jetson] = s.port;
    (s.homes = s.homes || []);
    if (!s.homes.includes(jetson)) s.homes.push(jetson);
    return "Saved.";
  }

  const newStudent = () => ({ pin: pin6(), jetson: "", camera: null, port: 0, ports: {}, homes: [] });

  function removeStudent(cls, name) {
    const s = db.classes[cls].students[name];
    delete db.classes[cls].students[name];
    for (const home of s.homes || []) db.pending_delete.push({ jetson: home, class: cls, student: name });
  }

  function view() {
    const classes = Object.keys(db.classes).sort().map(cn => ({
      name: cn,
      students: Object.keys(db.classes[cn].students).sort().map(sn => {
        const s = db.classes[cn].students[sn];
        const j = jetsons[s.jetson] || {};
        const key = `${cn}__${sn}`;
        const running = (j.running || []).some(r => r.key === key);
        const preparing = (j.preparing || []).includes(key);
        let state = "";
        if (s.jetson) {
          if (!open) state = running ? "closing" : "closed";
          else state = running ? "running" : preparing ? "preparing" : online(j) ? "starting" : "offline";
        }
        return { name: sn, jetson: s.jetson || "", camera: s.camera, pin: s.pin, port: s.port || "",
                 address: s.jetson && j.ip ? `${j.ip}:${s.port}` : "", state, homes: s.homes || [] };
      }),
    }));
    const out = Object.keys(jetsons).sort().map(id => {
      const j = jetsons[id];
      const users = {};
      for (const [c, n, s] of students()) if (s.jetson === id && s.camera != null) users[s.camera] = `${c}/${n}`;
      return { id, ip: j.ip || "", online: online(j), ago: Math.floor(now() - (j.seen || 0)), ready: j.ready !== false, note: j.note || "",
               cameras: (j.cameras || []).map(c => ({ ...c, user: users[c.number] || "" })),
               students: students().filter(([, , s]) => s.jetson === id).length };
    });
    return { ip: myIp(), port: PORT, key: db.key, host: os.hostname(), open, classes, jetsons: out, pending: db.pending_delete.length };
  }

  function agentHello(body) {
    const id = clean(body.id);
    if (!id) return { error: "no id" };
    const j = (jetsons[id] = jetsons[id] || {});
    Object.assign(j, { ip: String(body.ip || ""), seen: now(), cameras: (body.cameras || []).slice(0, 6), running: (body.running || []).slice(0, 40),
                       ready: body.ready !== false, note: String(body.note || "").slice(0, 200), preparing: (body.preparing || []).slice(0, 40) });
    for (const gone of body.deleted || [])
      db.pending_delete = db.pending_delete.filter(d => !(d.jetson === id && `${d.class}__${d.student}` === gone));
    dirty = true;
    const plan = !open ? [] : students().filter(([, , s]) => s.jetson === id)
      .map(([c, n, s]) => ({ class: c, student: n, port: s.port, pin: s.pin, camera: s.camera }));
    return { plan, open, delete: db.pending_delete.filter(d => d.jetson === id) };
  }

  function api(p, b) {
    if (p === "/api/session") {
      open = !!b.open;
      return "Saved.";
    }
    const cls = clean(b.class), stu = clean(b.student);
    if (p === "/api/class") {
      const name = clean(b.name);
      if (!NAME.test(name)) return "Use letters or numbers for the class name.";
      db.classes[name] = db.classes[name] || { students: {} };
      return "Saved.";
    }
    if (!db.classes[cls]) return "There is no such class.";
    const st = db.classes[cls].students;
    if (p === "/api/students") {
      let added = 0;
      for (const raw of String(b.names || "").split(/[,\n;]/)) {
        const n = clean(raw);
        if (NAME.test(n) && !/^\d+$/.test(n) && !st[n]) { st[n] = newStudent(); added++; }
      }
      return added ? "Saved." : "No new valid names (use letters or numbers).";
    }
    if (p === "/api/remove_class") {
      for (const n of Object.keys(st)) removeStudent(cls, n);
      delete db.classes[cls];
      return "Saved.";
    }
    if (!st[stu]) return "There is no such student.";
    if (p === "/api/assign") return assign(cls, stu, String(b.jetson || ""), b.camera);
    if (p === "/api/pin") { st[stu].pin = pin6(); return "Saved."; }
    if (p === "/api/remove") { removeStudent(cls, stu); return "Saved."; }
    return "Unknown action.";
  }

  // ---- HTTP. The teacher page and its API answer only on this PC (the app's own window); the Jetsons use /agent/hello with the class key.
  const local = req => ["127.0.0.1", "::1", "::ffff:127.0.0.1"].includes(req.socket.remoteAddress);
  const cookie = req => Object.fromEntries((req.headers.cookie || "").split(";").map(x => x.trim().split("=")).filter(x => x[0]));
  const authed = req => local(req) && sessions.has(cookie(req).lab_teacher);
  const page = () => fs.readFileSync(path.join(__dirname, "portal.html"));

  function send(res, code, body, type = "application/json", headers = {}) {
    res.writeHead(code, { "Content-Type": type, "Cache-Control": "no-store", ...headers });
    res.end(body);
  }
  function readJson(req) {
    return new Promise(resolve => {
      let data = "";
      req.on("data", c => { data += c; if (data.length > 1e6) req.destroy(); });
      req.on("end", () => { try { resolve(JSON.parse(data || "{}")); } catch { resolve({}); } });
    });
  }

  const server = http.createServer(async (req, res) => {
    const url = new URL(req.url, "http://x");
    try {
      if (req.method === "POST" && url.pathname === "/agent/hello") {
        const key = String(req.headers["x-key"] || "");
        const ok = key.length === db.key.length && crypto.timingSafeEqual(Buffer.from(key), Buffer.from(db.key));
        if (!ok) return send(res, 403, '{"error":"wrong class key"}');
        return send(res, 200, JSON.stringify(agentHello(await readJson(req))));
      }
      if (!local(req)) return send(res, 403, '{"error":"The teacher page opens only on the teacher PC."}');
      if (req.method === "GET" && (url.pathname === "/" || url.pathname === "/index.html")) {
        const t = url.searchParams.get("t");
        const headers = {};
        if (appToken && t === appToken) {
          const c = crypto.randomBytes(24).toString("base64url");
          sessions.add(c);
          headers["Set-Cookie"] = `lab_teacher=${c}; HttpOnly; SameSite=Strict; Path=/`;
        }
        return send(res, 200, page(), "text/html; charset=utf-8", headers);
      }
      if (!authed(req)) return send(res, 401, '{"error":"login"}');
      if (req.method === "GET" && url.pathname === "/api/state") return send(res, 200, JSON.stringify(view()));
      if (req.method === "POST" && url.pathname.startsWith("/api/")) {
        const message = api(url.pathname, await readJson(req));
        save();
        return send(res, 200, JSON.stringify({ message }));
      }
      send(res, 404, '{"error":"not found"}');
    } catch (e) {
      send(res, 500, JSON.stringify({ error: String(e) }));
    }
  });

  return {
    server, db, jetsons, view, myIp,
    get open() { return open; },
    setOpen(v) { open = !!v; },
    key: () => db.key,
    listen: (port = PORT) => new Promise((ok, fail) => { server.once("error", fail); server.listen(port, "0.0.0.0", ok); }),
    close: () => new Promise(done => { clearInterval(saver); if (dirty) save(); server.closeAllConnections?.(); server.close(done); }),
  };
}

module.exports = { createServer, PORT, myIp };

if (require.main === module) {
  const token = crypto.randomBytes(12).toString("hex");
  const t = createServer({ appToken: token, dataDir: process.env.TEACHER_DATA });
  t.listen().then(() => {
    console.log(`Teacher page (this PC only): http://localhost:${PORT}/?t=${token}`);
    console.log(`Class key: ${t.key()}`);
    t.setOpen(process.argv.includes("--open"));
  });
}
