package com.snapgo.operator;

import android.app.Activity;
import android.os.Bundle;
import android.graphics.Color;
import android.net.Uri;
import android.os.Handler;
import android.os.Looper;
import android.view.ViewGroup;
import android.webkit.CookieManager;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.TextView;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;

public final class MainActivity extends Activity {
    private WebView browser;
    private LinearLayout root;
    private boolean livePage = true;
    private boolean switching = false;
    private final Handler handler = new Handler(Looper.getMainLooper());

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        showConnect(null);
    }

    private static boolean privateHost(String host) {
        if (host == null) return false;
        if (host.equals("raspberrypi.local") || host.matches("[a-zA-Z0-9-]+\\.local")) return true;
        if (!host.matches("[0-9.]+")) return false;
        String[] octets = host.split("\\.", -1);
        if (octets.length != 4) return false;
        int[] n = new int[4];
        try {
            for (int i = 0; i < 4; i++) {
                n[i] = Integer.parseInt(octets[i]);
                if (n[i] < 0 || n[i] > 255) return false;
            }
        } catch (NumberFormatException ex) { return false; }
        return n[0] == 10 || (n[0] == 172 && n[1] >= 16 && n[1] <= 31)
                || (n[0] == 192 && n[1] == 168);
    }

    private static String checkedOrigin(String entry) {
        Uri uri = Uri.parse(entry.trim());
        String scheme = uri.getScheme();
        if (!("http".equals(scheme) || "https".equals(scheme)) ||
                uri.getUserInfo() != null || uri.getQuery() != null || uri.getFragment() != null ||
                !privateHost(uri.getHost()) || (uri.getPort() != -1 && (uri.getPort() < 1 || uri.getPort() > 65535)))
            throw new IllegalArgumentException("Use a private Pi address, e.g. http://192.168.1.50:8080");
        int port = uri.getPort();
        return scheme + "://" + uri.getHost() + (port == -1 ? "" : ":" + port);
    }

    private void stopControl() {
        if (browser != null && livePage) browser.evaluateJavascript(
                "if (typeof releaseAll === 'function') releaseAll(); if (typeof state !== 'undefined' && state?.enabled) queued({action:'stop'});", null);
    }

    private void disposeBrowser() {
        if (browser == null) return;
        ViewGroup parent = (ViewGroup) browser.getParent();
        if (parent != null) parent.removeView(browser);
        browser.destroy();
        browser = null;
    }

    private void selectTest() {
        if (switching) return;
        if (browser != null && livePage) {
            switching = true;
            stopControl();
            // Give the explicit STOP time to reach the Pi before removing WebView.
            handler.postDelayed(() -> { switching = false; disposeBrowser(); showTest(); }, 500);
        } else { disposeBrowser(); showTest(); }
    }

    private void shell(boolean live) {
        livePage = live;
        root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(Color.rgb(12, 20, 27));
        LinearLayout tabs = new LinearLayout(this);
        tabs.setPadding(10, 8, 10, 8);
        Button liveButton = new Button(this);
        liveButton.setText("LIVE");
        liveButton.setEnabled(!live);
        Button testButton = new Button(this);
        testButton.setText("TEST");
        testButton.setEnabled(live);
        tabs.addView(liveButton, new LinearLayout.LayoutParams(0, -2, 1));
        tabs.addView(testButton, new LinearLayout.LayoutParams(0, -2, 1));
        root.addView(tabs);
        liveButton.setOnClickListener(v -> { disposeBrowser(); showConnect(null); });
        testButton.setOnClickListener(v -> selectTest());
        setContentView(root);
    }

    private void showConnect(String error) {
        shell(true);
        LinearLayout form = new LinearLayout(this);
        form.setOrientation(LinearLayout.VERTICAL);
        form.setPadding(24, 18, 24, 24);
        TextView title = new TextView(this);
        title.setText("Snap Go · Pi connection"); title.setTextSize(22); title.setTextColor(Color.WHITE);
        form.addView(title);
        TextView hint = new TextView(this);
        hint.setText("Connect phone and Pi to the same trusted Wi-Fi. Start Snap Go on the Pi with --host 0.0.0.0. Test works offline without a Pi.");
        hint.setTextColor(Color.LTGRAY); form.addView(hint);
        EditText address = new EditText(this);
        address.setSingleLine(true); address.setTextColor(Color.WHITE);
        address.setHintTextColor(Color.GRAY);
        address.setHint("http://192.168.1.50:8080");
        address.setText(getPreferences(MODE_PRIVATE).getString("pi_address", ""));
        form.addView(address);
        TextView feedback = new TextView(this);
        feedback.setTextColor(Color.RED);
        if (error != null) feedback.setText(error);
        form.addView(feedback);
        Button connect = new Button(this);
        connect.setText("Connect to Pi"); form.addView(connect);
        connect.setOnClickListener(v -> {
            try {
                String selected = checkedOrigin(address.getText().toString());
                getPreferences(MODE_PRIVATE).edit().putString("pi_address", selected).apply();
                showDashboard(selected);
            } catch (IllegalArgumentException ex) { feedback.setText(ex.getMessage()); }
        });
        root.addView(form);
    }

    private WebView newBrowser(boolean network) {
        WebView view = new WebView(this);
        view.setBackgroundColor(Color.rgb(12, 20, 27));
        view.getSettings().setJavaScriptEnabled(true);
        view.getSettings().setAllowFileAccess(false);
        view.getSettings().setAllowContentAccess(false);
        view.getSettings().setDomStorageEnabled(false);
        view.getSettings().setCacheMode(android.webkit.WebSettings.LOAD_NO_CACHE);
        view.getSettings().setBlockNetworkLoads(!network);
        view.getSettings().setMixedContentMode(android.webkit.WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        CookieManager.getInstance().setAcceptCookie(false);
        return view;
    }

    private void showDashboard(String selected) {
        shell(true);
        Button changePi = new Button(this);
        changePi.setText("⚙ Pi connection");
        root.addView(changePi);
        browser = newBrowser(true);
        browser.setWebViewClient(new WebViewClient() {
            @Override public boolean shouldOverrideUrlLoading(WebView view, android.webkit.WebResourceRequest request) {
                return !request.getUrl().toString().equals(selected + "/");
            }
        });
        root.addView(browser, new LinearLayout.LayoutParams(-1, 0, 1));
        changePi.setOnClickListener(v -> selectConnection());
        browser.loadUrl(selected + "/");
    }

    private void selectConnection() {
        if (switching) return;
        switching = true;
        stopControl();
        handler.postDelayed(() -> { switching = false; disposeBrowser(); showConnect(null); }, 500);
    }

    private void showTest() {
        shell(false);
        browser = newBrowser(false);
        browser.setWebViewClient(new WebViewClient() {
            @Override public boolean shouldOverrideUrlLoading(WebView view, android.webkit.WebResourceRequest request) {
                return true;
            }
        });
        root.addView(browser, new LinearLayout.LayoutParams(-1, 0, 1));
        try (InputStream stream = getAssets().open("test.html")) {
            ByteArrayOutputStream output = new ByteArrayOutputStream();
            byte[] chunk = new byte[4096]; int length;
            while ((length = stream.read(chunk)) != -1) output.write(chunk, 0, length);
            browser.loadDataWithBaseURL("https://appassets.androidplatform.net/",
                    output.toString(StandardCharsets.UTF_8.name()), "text/html", "UTF-8", null);
        } catch (Exception ex) {
            browser.loadData("<p>Could not load test scene.</p>", "text/html", "UTF-8");
        }
    }

    @Override protected void onPause() {
        stopControl();
        super.onPause();
    }

    @Override protected void onDestroy() {
        handler.removeCallbacksAndMessages(null);
        stopControl();
        disposeBrowser();
        super.onDestroy();
    }
}
