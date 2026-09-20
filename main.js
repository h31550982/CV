const copyButton = document.querySelector("[data-copy]");
const copyNote = document.querySelector(".footer__copy-note");

function copyToClipboard(text) {
  if (navigator.clipboard && window.isSecureContext) {
    return navigator.clipboard.writeText(text);
  }

  // Fallback for file:// and plain http, where the clipboard API is unavailable.
  return new Promise((resolve, reject) => {
    const field = document.createElement("textarea");
    field.value = text;
    field.setAttribute("readonly", "");
    field.style.position = "fixed";
    field.style.opacity = "0";
    document.body.appendChild(field);
    field.select();

    const copied = document.execCommand("copy");
    document.body.removeChild(field);
    copied ? resolve() : reject();
  });
}

let noteTimer;

function showNote(message) {
  copyNote.textContent = message;
  copyNote.classList.add("is-visible");
  clearTimeout(noteTimer);
  noteTimer = setTimeout(() => {
    copyNote.classList.remove("is-visible");
  }, 2000);
}

if (copyButton && copyNote) {
  copyButton.addEventListener("click", () => {
    copyToClipboard(copyButton.dataset.copy)
      .then(() => showNote("Kopioitu"))
      .catch(() => showNote("Kopiointi ei onnistunut"));
  });
}
