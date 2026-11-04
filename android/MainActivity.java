package com.kontra.game;

import android.app.Activity;
import android.content.Context;
import android.net.ConnectivityManager;
import android.net.NetworkInfo;
import android.os.Bundle;
import android.view.WindowManager;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import java.io.InputStream;

public class MainActivity extends Activity {
    private static final String SITE = "https://rjynhf.onrender.com";
    private static final String GAME_URL = SITE + "/play";
    private WebView web;

    private boolean online() {
        try {
            ConnectivityManager cm = (ConnectivityManager) getSystemService(Context.CONNECTIVITY_SERVICE);
            NetworkInfo n = cm == null ? null : cm.getActiveNetworkInfo();
            return n != null && n.isConnected();
        } catch (Exception e) { return true; }
    }

    // Без интернета отдаём встроенную копию игры с тем же адресом, чтобы сохранения были общими.
    private WebResourceResponse offlineAsset(String url) {
        if (online() || !url.startsWith(SITE)) return null;
        String path = url.substring(SITE.length());
        int q = path.indexOf('?');
        if (q >= 0) path = path.substring(0, q);
        String file = null, mime = null;
        if (path.equals("") || path.equals("/") || path.equals("/play") || path.equals("/play.html")) { file = "play.html"; mime = "text/html"; }
        else if (path.equals("/vendor/three.min.js")) { file = "vendor/three.min.js"; mime = "application/javascript"; }
        else if (path.equals("/icon-192.png")) { file = "icon-192.png"; mime = "image/png"; }
        if (file == null) return null;
        try {
            InputStream in = getAssets().open(file);
            return new WebResourceResponse(mime, "utf-8", in);
        } catch (Exception e) { return null; }
    }

    @Override
    public void onCreate(Bundle state) {
        super.onCreate(state);
        getWindow().setFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN, WindowManager.LayoutParams.FLAG_FULLSCREEN);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        web = new WebView(this);
        web.setBackgroundColor(0xFF000000);
        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setDatabaseEnabled(true);
        s.setUserAgentString(s.getUserAgentString() + " KontraApp/1.3");
        web.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView v, String url) { return false; }
            @Override
            public WebResourceResponse shouldInterceptRequest(WebView v, String url) { return offlineAsset(url); }
            @Override
            public void onReceivedError(WebView v, int code, String desc, String url) {
                if (url != null && url.startsWith(SITE) && !url.endsWith("#offline")) v.loadUrl(GAME_URL + "#offline");
            }
        });
        web.setWebChromeClient(new WebChromeClient());
        setContentView(web);
        hideBars();
        if (state != null) web.restoreState(state); else web.loadUrl(GAME_URL);
    }

    private void hideBars() {
        web.setSystemUiVisibility(0x0002 | 0x0004 | 0x0100 | 0x0200 | 0x0400 | 0x1000);
    }

    @Override
    public void onWindowFocusChanged(boolean hasFocus) {
        super.onWindowFocusChanged(hasFocus);
        if (hasFocus) hideBars();
    }

    @Override
    protected void onSaveInstanceState(Bundle out) { super.onSaveInstanceState(out); web.saveState(out); }

    @Override
    protected void onPause() { super.onPause(); web.onPause(); }

    @Override
    protected void onResume() { super.onResume(); web.onResume(); }

    @Override
    public void onBackPressed() { if (web.canGoBack()) web.goBack(); else super.onBackPressed(); }
}
