# Snap Go Android updates

The app's **Check for update** button reads the latest public release from `Denberg28/snap_go`. It needs Internet only while checking/downloading; camera control stays on the local Pi network. No GitHub personal access token is used or embedded in the APK. The update checker accepts only a newer numeric tag and `SnapGo-Operator-vTAG.apk` asset from this repository with a SHA-256 release digest; it verifies the downloaded bytes, package name, version code and signing certificate before opening Android's system installer. Android asks permission to install the update.

## One-time signing secret setup

Android requires the same signing certificate for in-place updates. GitHub Actions debug builds use disposable keys. The first stable signed APK requires uninstalling any debug APK. Future signed releases can update in place if the signing key, package ID and increasing version code are retained.

On a trusted computer create and securely back up one keystore **outside Git**:

```bash
keytool -genkeypair -keystore snapgo-release.jks -alias snapgo -keyalg RSA -keysize 3072 -validity 10000
```

On Windows, run that command in PowerShell from a private folder outside the repository. After creating the keystore, use this PowerShell command to copy its single-line base64 value (it is a **secret**; paste it only into the GitHub secret field):

```powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes((Resolve-Path .\snapgo-release.jks))) | Set-Clipboard
```

Then clear the clipboard after entering the GitHub secret. If `keytool` is not on PATH, run it from the JDK `bin` folder.

The keystore and key passwords may differ. Back both up with the `.jks` file. In the repository Settings → Secrets and variables → Actions, add these **repository secrets**:

| Name | Value |
| --- | --- |
| `SNAP_GO_SIGNING_KEYSTORE_BASE64` | Single-line base64 of the `.jks` file (`base64 -w0 snapgo-release.jks` on Linux) |
| `SNAP_GO_SIGNING_PASSWORD` | Keystore password |
| `SNAP_GO_KEY_PASSWORD` | Password for the signing key |

Add these **repository variables** (plain text, not secrets):

| Name | Value |
| --- | --- |
| `SNAP_GO_KEY_ALIAS` | Alias in the keystore, e.g. `snapgo` |
| `SNAP_GO_SIGNING_CERT_SHA256` | SHA-256 fingerprint of the signing certificate (64 hex digits, with or without colons) |

Get the certificate fingerprint locally, without uploading the private key anywhere except GitHub Actions secrets:

```bash
keytool -list -v -keystore snapgo-release.jks -alias snapgo
```

Copy the `SHA256:` value from its `Certificate fingerprints` section into the variable. The release workflow checks the signed APK against this fingerprint before publishing; a missing or mismatched value fails the release. **Do not reuse TeleRC's keystore** unless you intentionally want the two apps to share one private signing identity. The alias and fingerprint are public metadata, while the keystore and both passwords must remain secret.

Store a backup of the `.jks` and password where you can recover them. Never commit the keystore, paste it into an issue or embed credentials in Android source. The repository's built-in `GITHUB_TOKEN` publishes the signed APK; no personal access token is needed. After merging the reviewed source to `main`, manually run **Signed Android release** in Actions. It builds, verifies, hashes and publishes the APK as a public GitHub release. The update button remains honest about missing releases until that first signed release is published.

Release requires `VERSION` and Android `versionName` to match, and each successive Android `versionCode` to increase. The package ID must remain `com.snapgo.operator`. A private release cannot be fetched by a public APK without an authenticated delivery service; do not put a repository secret into the APK.
