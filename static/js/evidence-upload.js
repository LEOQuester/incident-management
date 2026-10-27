// Native submission remains available when JavaScript is disabled.
document.querySelectorAll('form[enctype="multipart/form-data"]').forEach(function (form) {
  var input = form.querySelector('input[name="evidence"]');
  if (!input) return;
  var output = document.createElement('p');
  output.setAttribute('aria-live', 'polite');
  input.after(output);
  input.addEventListener('change', function () {
    output.textContent = Array.from(input.files).map(function (file) {
      return file.name + ' (' + (file.size / 1048576).toFixed(1) + ' MiB)';
    }).join(', ');
  });
  form.addEventListener('submit', function () {
    var progress = document.createElement('progress');
    progress.setAttribute('aria-label', 'Submitting case and uploading evidence');
    output.textContent = 'Uploading and validating evidence. Please wait…';
    output.appendChild(progress);
    form.querySelectorAll('button[type="submit"], button:not([type])').forEach(function (button) {
      button.disabled = true;
    });
  });
});
