package com.snapgo.operator;

import android.app.Activity;
import android.app.AlertDialog;
import android.app.DownloadManager;
import android.content.BroadcastReceiver;
import android.content.ClipData;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Build;
import android.os.Environment;
import android.provider.Settings;
import android.widget.Toast;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.security.MessageDigest;
import java.util.Arrays;
import org.json.JSONArray;
import org.json.JSONObject;

/** Manual public-release update checker. No token or signing secret is shipped in the APK. */
final class AppUpdater {
    private static final class SigningMismatch extends Exception { }
    private static final String API = "https://api.github.com/repos/Denberg28/snap_go/releases/latest";
    private static final String RELEASES = "https://github.com/Denberg28/snap_go/releases";
    private final Activity activity;
    private final DownloadManager downloads;
    private final File apk;
    private long downloadId = -1;
    private String expectedHash;
    private Uri pendingInstall;
    private boolean registered;

    AppUpdater(Activity activity) {
        this.activity = activity;
        downloads = (DownloadManager) activity.getSystemService(Context.DOWNLOAD_SERVICE);
        apk = new File(activity.getExternalFilesDir(Environment.DIRECTORY_DOWNLOADS), "snap-go-update.apk");
    }

    private void report(String text) {
        if (!activity.isFinishing() && !activity.isDestroyed())
            activity.runOnUiThread(() -> Toast.makeText(activity, text, Toast.LENGTH_LONG).show());
    }

    void check() {
        report("Checking public Snap Go releases…");
        new Thread(() -> {
            HttpURLConnection connection = null;
            try {
                connection = (HttpURLConnection) new URL(API).openConnection();
                connection.setConnectTimeout(8000);
                connection.setReadTimeout(8000);
                connection.setRequestProperty("Accept", "application/vnd.github+json");
                connection.setRequestProperty("User-Agent", "SnapGo-Android");
                int status = connection.getResponseCode();
                if (status == 404) { report("No public signed update yet."); return; }
                if (status != 200) throw new IllegalStateException("HTTP " + status);
                ByteArrayOutputStream bytes = new ByteArrayOutputStream();
                try (InputStream in = connection.getInputStream()) {
                    byte[] block = new byte[8192]; int n;
                    while ((n = in.read(block)) != -1) {
                        if (bytes.size() + n > 512_000) throw new IllegalStateException("Release metadata too large");
                        bytes.write(block, 0, n);
                    }
                }
                JSONObject release = new JSONObject(bytes.toString("UTF-8"));
                String tag = release.getString("tag_name").replaceFirst("^v", "");
                if (compare(tag, BuildConfig.VERSION_NAME) <= 0) {
                    report("Snap Go " + BuildConfig.VERSION_NAME + " is up to date."); return;
                }
                JSONArray assets = release.getJSONArray("assets");
                String download = null, hash = null;
                for (int i = 0; i < assets.length(); i++) {
                    JSONObject asset = assets.getJSONObject(i);
                    String name = asset.optString("name");
                    String digest = asset.optString("digest");
                    if (name.equals("SnapGo-Operator-v" + tag + ".apk") &&
                            digest.matches("sha256:[0-9a-fA-F]{64}")) {
                        download = asset.getString("browser_download_url");
                        hash = digest.substring(7).toLowerCase(java.util.Locale.ROOT);
                        break;
                    }
                }
                if (download == null) { report("Latest release has no verified Android APK."); return; }
                String url = download, expected = hash;
                activity.runOnUiThread(() -> {
                    if (activity.isFinishing() || activity.isDestroyed()) return;
                    new AlertDialog.Builder(activity).setTitle("Snap Go " + tag + " available")
                        .setMessage("Download the verified APK? Android will ask before installation. Live control will stop during the update.")
                        .setNegativeButton("Later", null)
                        .setPositiveButton("Download", (d, w) -> {
                            ((MainActivity) activity).stopForUpdate();
                            download(url, expected);
                        })
                        .show();
                });
            } catch (Exception ex) { report("Update check failed. Check your Internet connection."); }
            finally { if (connection != null) connection.disconnect(); }
        }, "snap-go-update-check").start();
    }

    private static int compare(String candidate, String installed) {
        if (!candidate.matches("[0-9]+(\\.[0-9]+){1,3}") ||
                !installed.matches("[0-9]+(\\.[0-9]+){1,3}")) return -1;
        String[] a = candidate.split("\\."), b = installed.split("\\.");
        try {
            for (int i = 0; i < Math.max(a.length, b.length); i++) {
                int x = i < a.length ? Integer.parseInt(a[i]) : 0;
                int y = i < b.length ? Integer.parseInt(b[i]) : 0;
                if (x != y) return Integer.compare(x, y);
            }
        } catch (NumberFormatException ex) { return -1; }
        return 0;
    }

    private final BroadcastReceiver receiver = new BroadcastReceiver() {
        @Override public void onReceive(Context context, Intent intent) {
            if (!DownloadManager.ACTION_DOWNLOAD_COMPLETE.equals(intent.getAction()) ||
                    intent.getLongExtra(DownloadManager.EXTRA_DOWNLOAD_ID, -1) != downloadId) return;
            Uri uri = downloads.getUriForDownloadedFile(downloadId);
            if (uri == null) { report("Update download failed."); return; }
            new Thread(() -> {
                try {
                    if (!verify()) { report("Update verification failed; APK discarded."); apk.delete(); return; }
                    pendingInstall = uri;
                    activity.runOnUiThread(() -> { if (!activity.isFinishing()) offerInstall(); });
                } catch (SigningMismatch ex) { apk.delete(); }
                catch (Exception ex) { report("Could not verify the update."); apk.delete(); }
            }, "snap-go-update-verify").start();
        }
    };

    private void download(String address, String hash) {
        Uri url = Uri.parse(address);
        if (!"https".equals(url.getScheme()) || !"github.com".equals(url.getHost()) ||
                !url.getPath().matches("/Denberg28/snap_go/releases/download/v[0-9]+(\\.[0-9]+){1,3}/SnapGo-Operator-v[0-9]+(\\.[0-9]+){1,3}\\.apk")) {
            report("Untrusted release URL rejected."); return;
        }
        try {
            if (downloadId != -1) downloads.remove(downloadId);
            apk.delete(); expectedHash = hash;
            DownloadManager.Request request = new DownloadManager.Request(url)
                .setTitle("Snap Go update")
                .setDescription("Verified public release APK")
                .setMimeType("application/vnd.android.package-archive")
                .setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED)
                .setDestinationInExternalFilesDir(activity, Environment.DIRECTORY_DOWNLOADS, apk.getName());
            downloadId = downloads.enqueue(request);
            if (!registered) {
                IntentFilter filter = new IntentFilter(DownloadManager.ACTION_DOWNLOAD_COMPLETE);
                if (Build.VERSION.SDK_INT >= 33) activity.registerReceiver(receiver, filter, Context.RECEIVER_EXPORTED);
                else activity.registerReceiver(receiver, filter);
                registered = true;
            }
            report("Downloading Snap Go update…");
        } catch (Exception ex) { report("Could not download update."); }
    }

    private boolean verify() throws Exception {
        if (expectedHash == null || !apk.isFile() || apk.length() < 10_000 || apk.length() > 50_000_000) return false;
        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        try (InputStream in = new java.io.FileInputStream(apk)) {
            byte[] block = new byte[8192]; int n;
            while ((n = in.read(block)) != -1) digest.update(block, 0, n);
        }
        StringBuilder hex = new StringBuilder();
        for (byte b : digest.digest()) hex.append(String.format(java.util.Locale.ROOT, "%02x", b & 0xff));
        if (!expectedHash.equals(hex.toString())) return false;
        PackageManager pm = activity.getPackageManager();
        int flag = Build.VERSION.SDK_INT >= 28 ? PackageManager.GET_SIGNING_CERTIFICATES : PackageManager.GET_SIGNATURES;
        PackageInfo candidate = pm.getPackageArchiveInfo(apk.getAbsolutePath(), flag);
        PackageInfo current = pm.getPackageInfo(activity.getPackageName(), flag);
        if (candidate == null || !activity.getPackageName().equals(candidate.packageName)) return false;
        long newCode = Build.VERSION.SDK_INT >= 28 ? candidate.getLongVersionCode() : candidate.versionCode;
        long oldCode = Build.VERSION.SDK_INT >= 28 ? current.getLongVersionCode() : current.versionCode;
        if (newCode <= oldCode) return false;
        android.content.pm.Signature[] newSign = Build.VERSION.SDK_INT >= 28 ?
            candidate.signingInfo.getApkContentsSigners() : candidate.signatures;
        android.content.pm.Signature[] oldSign = Build.VERSION.SDK_INT >= 28 ?
            current.signingInfo.getApkContentsSigners() : current.signatures;
        if (newSign == null || oldSign == null || !Arrays.equals(newSign, oldSign)) {
            activity.runOnUiThread(() -> new AlertDialog.Builder(activity)
                .setTitle("Different signing key")
                .setMessage("This debug APK cannot update to the first stable signed release. Uninstall the debug app, then install from the public release page. Future signed updates will install in place.")
                .setNegativeButton("Later", null)
                .setPositiveButton("Release page", (d, w) -> activity.startActivity(
                    new Intent(Intent.ACTION_VIEW, Uri.parse(RELEASES)))).show());
            throw new SigningMismatch();
        }
        return true;
    }

    void resumePendingInstall() {
        if (pendingInstall != null && activity.getPackageManager().canRequestPackageInstalls()) offerInstall();
    }

    private void offerInstall() {
        Uri uri = pendingInstall;
        if (uri == null || activity.isFinishing()) return;
        if (!activity.getPackageManager().canRequestPackageInstalls()) {
            report("Allow Snap Go to install updates, then return here.");
            activity.startActivity(new Intent(Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES,
                    Uri.parse("package:" + activity.getPackageName())));
            return;
        }
        pendingInstall = null;
        try {
            Intent intent = new Intent(Intent.ACTION_VIEW)
                .setDataAndType(uri, "application/vnd.android.package-archive")
                .setClipData(ClipData.newUri(activity.getContentResolver(), "Snap Go update", uri))
                .addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
            activity.startActivity(intent);
        } catch (Exception ex) { report("Android could not open the installer."); }
    }

    void close() {
        if (registered) { activity.unregisterReceiver(receiver); registered = false; }
    }
}
