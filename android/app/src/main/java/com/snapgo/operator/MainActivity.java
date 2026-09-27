package com.snapgo.operator;

import android.app.Activity;
import android.os.Bundle;
import android.graphics.Color;
import android.net.Uri;
import android.view.View;
import android.webkit.CookieManager;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.TextView;

public final class MainActivity extends Activity {
    private WebView browser;
    private LinearLayout root;
    private String origin;

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

    private void showConnect(String error) {
        origin = null;
        root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(32, 48, 32, 24);
        root.setBackgroundColor(Color.WHITE);
        TextView title = new TextView(this);
        title.setText("Snap Go · Pi connection"); title.setTextSize(22);
        root.addView(title);
        TextView hint = new TextView(this);
        hint.setText("Connect your phone and Pi to the same trusted Wi-Fi. Start Snap Go on the Pi with --host 0.0.0.0, then enter its address. The access token is entered on the next screen and is not saved by this app.");
        root.addView(hint);
        EditText address = new EditText(this);
        address.setSingleLine(true);
        address.setHint("http://192.168.1.50:8080");
        address.setText(getPreferences(MODE_PRIVATE).getString("pi_address", ""));
        root.addView(address);
        TextView feedback = new TextView(this);
        if (error != null) feedback.setText(error);
        root.addView(feedback);
        Button connect = new Button(this);
        connect.setText("Connect"); root.addView(connect);
        connect.setOnClickListener(v -> {
            try {
                String selected = checkedOrigin(address.getText().toString());
                getPreferences(MODE_PRIVATE).edit().putString("pi_address", selected).apply();
                showDashboard(selected);
            } catch (IllegalArgumentException ex) { feedback.setText(ex.getMessage()); }
        });
        setContentView(root);
    }

    private void showDashboard(String selected) {
        origin = selected;
        root.removeAllViews();
        Button disconnect = new Button(this);
        disconnect.setText("Stop and change Pi");
        root.addView(disconnect);
        browser = new WebView(this);
        browser.setBackgroundColor(Color.WHITE);
        browser.getSettings().setJavaScriptEnabled(true);
        browser.getSettings().setAllowFileAccess(false);
        browser.getSettings().setAllowContentAccess(false);
        browser.getSettings().setDomStorageEnabled(false);
        browser.getSettings().setCacheMode(android.webkit.WebSettings.LOAD_NO_CACHE);
        CookieManager.getInstance().setAcceptCookie(false);
        browser.setWebViewClient(new WebViewClient() {
            @Override public boolean shouldOverrideUrlLoading(WebView view, android.webkit.WebResourceRequest request) {
                return !request.getUrl().toString().equals(selected + "/");
            }
        });
        root.addView(browser, new LinearLayout.LayoutParams(-1, 0, 1));
        disconnect.setOnClickListener(v -> {
            stopControl();
            browser.destroy(); browser = null;
            showConnect(null);
        });
        browser.loadUrl(selected + "/");
    }

    private void stopControl() {
        if (browser != null) browser.evaluateJavascript(
                "if (typeof state !== 'undefined' && state?.enabled) action({action:'stop'});", null);
    }

    @Override protected void onPause() {
        stopControl();
        super.onPause();
    }

    @Override protected void onDestroy() {
        if (browser != null) { browser.destroy(); browser = null; }
        super.onDestroy();
    }
}
