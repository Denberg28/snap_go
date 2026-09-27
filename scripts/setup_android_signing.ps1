# Run on the owner's Windows computer. No signing key or password is committed to Git.
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$repository = 'Denberg28/snap_go'
$keyAlias = 'snapgo'
$signingDirectory = Join-Path $env:USERPROFILE 'SnapGoSigning'
$keystore = Join-Path $signingDirectory 'snapgo-release.jks'

foreach ($command in @('gh', 'keytool')) {
    if (-not (Get-Command $command -ErrorAction SilentlyContinue)) {
        throw "$command is required. Install the official GitHub CLI and a JDK, then rerun this script."
    }
}

& gh auth status *> $null
if ($LASTEXITCODE -ne 0) {
    & gh auth login --hostname github.com --git-protocol https --web
    if ($LASTEXITCODE -ne 0) { throw 'GitHub login was not completed.' }
}

$actualRepository = & gh repo view $repository --json nameWithOwner --jq '.nameWithOwner'
if ($LASTEXITCODE -ne 0 -or $actualRepository.Trim() -cne $repository) {
    throw "Cannot verify access to $repository. No signing key was created."
}

New-Item -ItemType Directory -Path $signingDirectory -Force | Out-Null
if (Test-Path -LiteralPath $keystore) {
    if ((Read-Host "Signing key exists at $keystore. Type REUSE to keep using this key") -cne 'REUSE') {
        throw 'Stopped without replacing the existing signing key.'
    }
} else {
    Write-Host "Creating the Snap Go signing key at $keystore"
    Write-Host 'Choose a strong keystore password. At the key-password prompt, press Enter to use that same password.'
    & keytool -genkeypair -keystore $keystore -storetype JKS -alias $keyAlias -keyalg RSA -keysize 3072 -validity 10000 -dname 'CN=Snap Go Operator, OU=Engineering, O=Snap Go, C=PH'
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $keystore)) {
        throw 'Keystore creation failed; no GitHub signing entries were changed.'
    }
}

Write-Host 'Enter the keystore password again to read the public certificate fingerprint.'
$certificateDetails = & keytool -list -v -keystore $keystore -alias $keyAlias 2>&1
if ($LASTEXITCODE -ne 0) { throw 'Could not read the certificate. Keep the keystore and check its password.' }
$fingerprintMatch = [regex]::Match(($certificateDetails -join "`n"), '(?mi)^\s*SHA256:\s*((?:[0-9A-F]{2}:){31}[0-9A-F]{2})\s*$')
if (-not $fingerprintMatch.Success) { throw 'Could not identify the certificate SHA-256 fingerprint.' }
$fingerprint = $fingerprintMatch.Groups[1].Value

$securePassword = Read-Host 'Re-enter the keystore password for GitHub Actions' -AsSecureString
$passwordPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePassword)
try {
    $password = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($passwordPointer)
    if ([string]::IsNullOrWhiteSpace($password)) { throw 'An empty password is not allowed.' }
    $encodedKeystore = [Convert]::ToBase64String([IO.File]::ReadAllBytes($keystore))
    $encodedKeystore | & gh secret set SNAP_GO_SIGNING_KEYSTORE_BASE64 --repo $repository --app actions
    if ($LASTEXITCODE -ne 0) { throw 'Could not upload keystore secret.' }
    $password | & gh secret set SNAP_GO_SIGNING_PASSWORD --repo $repository --app actions
    if ($LASTEXITCODE -ne 0) { throw 'Could not upload keystore password secret.' }
    $password | & gh secret set SNAP_GO_KEY_PASSWORD --repo $repository --app actions
    if ($LASTEXITCODE -ne 0) { throw 'Could not upload key password secret.' }
} finally {
    $password = $null
    $encodedKeystore = $null
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($passwordPointer)
}

& gh variable set SNAP_GO_KEY_ALIAS --repo $repository --body $keyAlias
if ($LASTEXITCODE -ne 0) { throw 'Could not set signing alias variable.' }
& gh variable set SNAP_GO_SIGNING_CERT_SHA256 --repo $repository --body $fingerprint
if ($LASTEXITCODE -ne 0) { throw 'Could not set certificate fingerprint variable.' }

Write-Host 'Signing entries created. Keep the keystore and its password backed up separately and securely.'
Write-Host "Keystore: $keystore"
Write-Host "Public certificate SHA-256: $fingerprint"
Write-Host 'GitHub Actions secrets and variables are now ready; the release workflow still requires a reviewed main-branch build.'
