// SPDX-License-Identifier: AGPL-3.0-or-later
"use strict";

const PASSWORD_LENGTH = 14;

// No special characters, as they can cause trouble in URLs and config files
const PASSWORD_CHARACTERS =
  "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";

function randomPassword() {
  const characters = PASSWORD_CHARACTERS;
  // Higher values are skipped, as `%` would otherwise prefer the first characters.
  const limit = 256 - (256 % characters.length);
  let password = "";

  while (password.length < PASSWORD_LENGTH) {
    const [value] = crypto.getRandomValues(new Uint8Array(1));

    if (value < limit) {
      password += characters[value % characters.length];
    }
  }

  return password;
}

/* Fill in a random password */
document.getElementById("generate-password").addEventListener("click", () => {
  const password = randomPassword();

  // Shown as plain text, as it has to be copied into the client.
  for (const id of ["password", "password_repeat"]) {
    const field = document.getElementById(id);
    field.type = "text";
    field.value = password;
    field.dispatchEvent(new Event("input"));
  }
});

/* Fill in the clients current IPv4 address */
for (const button of document.querySelectorAll("[data-use-address]")) {
  button.addEventListener("click", () => {
    document.getElementById(button.dataset.useAddress).value = button.dataset.address;
  });
}
