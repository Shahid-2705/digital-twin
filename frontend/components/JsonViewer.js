export function renderJsonViewer(root, data) {
  root.innerHTML = `<pre>${JSON.stringify(data || {}, null, 2)}</pre>`;
}
