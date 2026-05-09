# Core Module

Core configuration, security, and helper functions.

## Purpose

- Application configuration
- Security utilities (JWT, authentication)
- Common middleware
- Error handlers
- Constants





## Password Security

- Passwords are hashed with **Argon2** (preferred) for new users; legacy **bcrypt** hashes are still accepted for existing users.
- Passwords must meet strong policy:
  - At least 12 characters
  - At least one uppercase letter
  - At least one lowercase letter
  - At least one digit
  - At least one special character
  - Maximum 256 characters
- If a password does not meet these requirements, the API returns a clear error message.
- **Argon2** is a modern, memory-hard password hashing algorithm recommended for production systems. No password truncation is performed.
- **bcrypt** is an older, battle-tested password hash (used by default in many frameworks), but it truncates passwords at 72 bytes and is less resistant to GPU attacks than Argon2.

### Argon2 vs bcrypt (short)

- **bcrypt**:
  - Widely used, secure for most use cases, but truncates passwords at 72 bytes (anything longer is ignored).
  - Slower to hash, but less memory-hard (easier for attackers with GPUs/ASICs).
  - Still safe for legacy users, but not recommended for new systems.

- **Argon2**:
  - Winner of the Password Hashing Competition (PHC), modern and highly secure.
  - Memory-hard: much more resistant to GPU/ASIC attacks (costly to brute-force).
  - No password truncation; supports long passphrases.
  - Recommended for all new applications and for upgrading legacy hashes.

**If you are migrating from bcrypt:**
- Existing users can still log in with their old password (bcrypt hashes are still verified).
- To upgrade, re-hash their password with Argon2 on next login or password change.


