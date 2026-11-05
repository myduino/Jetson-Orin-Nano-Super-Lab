// The Myduino Jetson Lab teacher app. Two buttons: START LAB opens the portal and lets the Jetsons start the student sessions,
// END LAB closes the portal and tells every Jetson to stop them. The server (server.js) runs inside this app.
"use strict";
const { app, BrowserWindow, ipcMain, dialog } = require("electron");
const path = require("path");
const crypto = require("crypto");
const { createServer, PORT } = require("./server.js");

const token = crypto.randomBytes(16).toString("hex");
let teacher, launcher, portal;

function running() {
  const v = teacher.view();
  return { open: teacher.open, key: v.key, ip: v.ip, port: v.port, online: v.jetsons.filter(j => j.online).length,
           running: Object.values(teacher.jetsons).reduce((n, j) => n + (j.running || []).length, 0) };
}

function openPortal() {
  if (portal && !portal.isDestroyed()) { portal.focus(); return; }
  portal = new BrowserWindow({ width: 1240, height: 820, title: "Myduino Jetson Lab: teacher portal", autoHideMenuBar: true });
  portal.loadURL(`http://localhost:${PORT}/?t=${token}`);
  portal.on("closed", () => { portal = null; });
}

async function endLab() {
  const n = running().running;
  const r = await dialog.showMessageBox(launcher, {
    type: "warning", buttons: ["End lab", "Cancel"], defaultId: 1, cancelId: 1, title: "End lab",
    message: "End the lab now?",
    detail: `All student Jupyter sessions will stop${n ? ` (${n} running now)` : ""}. Unsaved notebook changes are lost. Ask the students to save first. Their files stay on the Jetsons.`,
  });
  if (r.response !== 0) return { cancelled: true };
  teacher.setOpen(false);
  if (portal && !portal.isDestroyed()) portal.close();
  for (let i = 0; i < 20 && running().running > 0; i++) await new Promise(ok => setTimeout(ok, 1000));   // wait until the Jetsons confirm
  return {};
}

app.whenReady().then(async () => {
  teacher = createServer({ appToken: token });
  try {
    await teacher.listen();
  } catch (e) {
    dialog.showErrorBox("Myduino Jetson Lab", `Port ${PORT} is already in use. Close the other Myduino Jetson Lab window first.`);
    return app.quit();
  }
  ipcMain.handle("state", () => running());
  ipcMain.handle("start", () => { teacher.setOpen(true); openPortal(); return {}; });
  ipcMain.handle("end", () => endLab());
  ipcMain.handle("portal", () => openPortal());
  launcher = new BrowserWindow({ width: 460, height: 340, resizable: false, maximizable: false, title: "Myduino Jetson Lab", autoHideMenuBar: true,
                                 webPreferences: { preload: path.join(__dirname, "preload.js") } });
  launcher.loadFile(path.join(__dirname, "launcher.html"));
  launcher.on("close", async e => {
    if (!teacher.open) return;
    e.preventDefault();
    const r = await endLab();
    if (!r.cancelled) { teacher.setOpen(false); launcher.destroy(); }
  });
  launcher.on("closed", async () => { await teacher.close(); app.quit(); });
});
app.on("window-all-closed", () => app.quit());
