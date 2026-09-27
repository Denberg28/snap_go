# Snap_Go contributor contract

Read README.md, docs/SPEC.md, docs/CONTINUITY.md and docs/VERIFICATION.md first.
- Camera payload only. Do not introduce rover drive commands or weapon/payload actuation.
- Never auto-enable at startup or after a fault. Keep ESP32 safety independent of vision/UI.
- Maintain fixed-width protocol1 interoperability; update Python/C++ tests together.
- Never expand pulse/velocity limits without calibration evidence. ACK is not physical feedback.
- Never add credentials, model binaries, recordings or private images to git.
- Version is0.1.0 in VERSION, pyproject.toml, Python, firmware comment and static UI. Run scripts/check_versions.py.
- Test from repository root: python -m pytest -q; node --check snap_go/static/app.js; python -m platformio run -d firmware.
- Write actual results and untested gates to docs/VERIFICATION.md; do not call simulation hardware validation.
- Keep changes scoped, lightweight and offline after provisioning. Pin dependencies and regenerate uv.lock.
- Public publication currently awaiting owner decision. Do not push to the public remote until authorized.
- Release only with scripts/package.py after builds; include checksums. Keep source/license/rollback docs with artifacts.
