// Checks the server with a pretend Jetson. Run: node test.js
const assert = require("assert");
const os = require("os"), fs = require("fs"), path = require("path");
const { createServer } = require("./server.js");
(async () => {
  const t = createServer({ appToken: "tok", dataDir: fs.mkdtempSync(path.join(os.tmpdir(), "myd-")) });
  await t.listen(8898);
  const f = (p, o) => fetch("http://localhost:8898" + p, o);
  assert.equal((await f("/api/state")).status, 401);
  const cookie = (await f("/?t=tok")).headers.get("set-cookie").split(";")[0];
  const post = (p, b) => f(p, { method: "POST", headers: { cookie, "content-type": "application/json" }, body: JSON.stringify(b) }).then(r => r.json());
  const hello = (key, b) => f("/agent/hello", { method: "POST", headers: { "x-key": key, "content-type": "application/json" }, body: JSON.stringify(b) });
  assert.equal((await hello("bad", {})).status, 403);
  await post("/api/class", { name: "a" });
  await post("/api/students", { class: "a", names: "amira, ali" });
  await hello(t.key(), { id: "j1", ip: "1.2.3.4", cameras: [{ number: 0, device: "/dev/video0", name: "cam" }] });
  assert.equal((await post("/api/assign", { class: "a", student: "amira", jetson: "j1", camera: 0 })).message, "Saved.");
  assert.match((await post("/api/assign", { class: "a", student: "ali", jetson: "j1", camera: 0 })).message, /is used by/);
  assert.deepEqual((await (await hello(t.key(), { id: "j1" })).json()).plan, [], "closed lab: nothing to run");
  await post("/api/session", { open: true });
  const plan = (await (await hello(t.key(), { id: "j1" })).json()).plan;
  assert.equal(plan.length, 1); assert.equal(plan[0].port, 8881);
  await post("/api/session", { open: false });
  assert.deepEqual((await (await hello(t.key(), { id: "j1" })).json()).plan, []);
  await post("/api/remove", { class: "a", student: "amira" });
  assert.equal((await (await hello(t.key(), { id: "j1" })).json()).delete.length, 1);
  await t.close();
  console.log("all good");
})().catch(e => { console.error(e); process.exit(1); });
