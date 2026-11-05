const { contextBridge, ipcRenderer } = require("electron");
contextBridge.exposeInMainWorld("lab", {
  state: () => ipcRenderer.invoke("state"),
  start: () => ipcRenderer.invoke("start"),
  end: () => ipcRenderer.invoke("end"),
  portal: () => ipcRenderer.invoke("portal"),
});
