/* Let Me Explain! — flipbook decryption (browser side).
   AES-256-GCM, key derived from the password via PBKDF2-SHA256.
   Each encrypted blob is [12-byte IV | ciphertext+tag]. Matches encrypt.mjs.
   The derived key is never stored — it lives only in this page's memory. */
window.FlipCrypto = (function () {
  "use strict";
  var subtle = (window.crypto || {}).subtle;
  var VERIFY_TOKEN = "lme-flipbook-ok";

  function b64ToBytes(b64) {
    var bin = atob(b64), a = new Uint8Array(bin.length);
    for (var i = 0; i < bin.length; i++) a[i] = bin.charCodeAt(i);
    return a;
  }

  async function deriveKey(password, saltBytes, iterations) {
    var base = await subtle.importKey("raw", new TextEncoder().encode(password), "PBKDF2", false, ["deriveKey"]);
    return subtle.deriveKey(
      { name: "PBKDF2", salt: saltBytes, iterations: iterations, hash: "SHA-256" },
      base,
      { name: "AES-GCM", length: 256 },
      false,                 // not extractable
      ["decrypt"]
    );
  }

  // packed = Uint8Array([ iv(12) | ciphertext+tag ]) -> Uint8Array(plaintext)
  async function decrypt(key, packed) {
    var iv = packed.slice(0, 12);
    var ct = packed.slice(12);
    return new Uint8Array(await subtle.decrypt({ name: "AES-GCM", iv: iv }, key, ct));
  }

  // verifier = base64 of an encrypted known token; wrong key -> GCM auth fails -> false
  async function verify(key, verifierB64) {
    try {
      var plain = await decrypt(key, b64ToBytes(verifierB64));
      return new TextDecoder().decode(plain) === VERIFY_TOKEN;
    } catch (e) { return false; }
  }

  return { b64ToBytes: b64ToBytes, deriveKey: deriveKey, decrypt: decrypt, verify: verify };
})();
