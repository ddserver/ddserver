// SPDX-License-Identifier: AGPL-3.0-or-later
"use strict";

// This is only a hint while typing, the rules are enforced by `passwords.py`.

const MIN_DIFFERENT_CHARACTERS = 5;

const SEQUENCES = [
  "abcdefghijklmnopqrstuvwxyz",
  "0123456789",
  "qwertzuiop",
  "qwertyuiop",
  "asdfghjkl",
  "yxcvbnm",
  "zxcvbnm",
];

const LEVELS = [
  { label: "Too weak", width: 25, colour: "text-bg-danger" },
  { label: "Weak", width: 50, colour: "text-bg-warning" },
  { label: "Good", width: 75, colour: "text-bg-info" },
  { label: "Strong", width: 100, colour: "text-bg-success" },
];

function isSequence(password) {
  const lowered = password.toLowerCase();

  return SEQUENCES.some((row) => {
    const reversed = [...row].reverse().join("");

    return row.repeat(3).includes(lowered) || reversed.repeat(3).includes(lowered);
  });
}

function passwordLevel(password, minLength) {
  const different = new Set(password.toLowerCase()).size;

  if (
    password.length < minLength ||
    different < MIN_DIFFERENT_CHARACTERS ||
    isSequence(password)
  ) {
    return LEVELS[0];
  }

  const kinds = [/[a-z]/, /[A-Z]/, /[0-9]/, /[^a-zA-Z0-9]/].filter((kind) =>
    kind.test(password),
  ).length;

  if (password.length >= 16 || (password.length >= 12 && kinds >= 3)) {
    return LEVELS[3];
  }

  return password.length >= 12 || kinds >= 3 ? LEVELS[2] : LEVELS[1];
}

function addMeter(field) {
  const meter = document.createElement("div");
  meter.className = "progress password-meter";
  meter.hidden = true;

  const bar = document.createElement("div");
  bar.className = "progress-bar";
  meter.append(bar);

  (field.closest(".input-group") ?? field).after(meter);

  field.addEventListener("input", () => {
    const level = passwordLevel(field.value, field.minLength);

    meter.hidden = !field.value;
    bar.className = `progress-bar ${level.colour}`;
    bar.style.width = `${level.width}%`;
    bar.textContent = level.label;
  });
}

document.querySelectorAll("[data-password-meter]").forEach(addMeter);
