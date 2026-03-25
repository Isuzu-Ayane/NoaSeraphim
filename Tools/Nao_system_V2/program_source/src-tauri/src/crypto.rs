use aes_gcm::{
    aead::{Aead, KeyInit},
    Aes256Gcm, Nonce,
};
use base64::{engine::general_purpose, Engine as _};

// ※本来は環境変数等で管理すべきだけど、ローカル用なので固定キー
const SECRET_KEY: &[u8; 32] = b"nao_seraphim_holy_shield_2026_03"; 
const FIXED_NONCE: &[u8; 12] = b"nao_nonce_12"; 

pub fn encrypt(data: &str) -> String {
    let cipher = Aes256Gcm::new_from_slice(SECRET_KEY).unwrap();
    let nonce = Nonce::from_slice(FIXED_NONCE);
    let ciphertext = cipher.encrypt(nonce, data.as_bytes()).expect("Encryption failed");
    general_purpose::STANDARD.encode(ciphertext)
}

pub fn decrypt(encrypted_data: &str) -> String {
    let cipher = Aes256Gcm::new_from_slice(SECRET_KEY).unwrap();
    let nonce = Nonce::from_slice(FIXED_NONCE);
    let encrypted_bytes = general_purpose::STANDARD.decode(encrypted_data).unwrap_or_default();
    let decrypted_bytes = cipher.decrypt(nonce, encrypted_bytes.as_ref()).unwrap_or_default();
    String::from_utf8(decrypted_bytes).unwrap_or_default()
}