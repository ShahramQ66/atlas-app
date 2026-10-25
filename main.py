# -*- coding: utf-8 -*-
import os
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.utils import platform


class AtlasApp(App):
    def build(self):
        self.title = "Atlas Analyzer"
        if platform == 'android':
            self._show_webview()
            return BoxLayout()
        return Label(text="فقط اندروید")

    def _show_webview(self):
        from android import mActivity
        from android.runnable import run_on_ui_thread
        from jnius import autoclass
        from android.permissions import request_permissions, Permission

        request_permissions([Permission.INTERNET])

        WebView = autoclass('android.webkit.WebView')
        WebViewClient = autoclass('android.webkit.WebViewClient')
        activity = mActivity

        html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'index.html')

        @run_on_ui_thread
        def setup():
            webview = WebView(activity)
            s = webview.getSettings()
            s.setJavaScriptEnabled(True)
            s.setDomStorageEnabled(True)
            s.setAllowFileAccess(True)
            s.setAllowContentAccess(True)
            try:
                s.setAllowUniversalAccessFromFileURLs(True)
                s.setAllowFileAccessFromFileURLs(True)
            except Exception:
                pass
            webview.setWebViewClient(WebViewClient())
            try:
                with open(html_path, 'r', encoding='utf-8') as f:
                    html = f.read()
                webview.loadDataWithBaseURL("https://atlas.local/", html,
                                            "text/html", "UTF-8", None)
            except Exception as e:
                webview.loadData(f"<h1>خطا</h1><p>{e}</p>", "text/html", "UTF-8")
            activity.setContentView(webview)

        setup()


if __name__ == '__main__':
    AtlasApp().run()
