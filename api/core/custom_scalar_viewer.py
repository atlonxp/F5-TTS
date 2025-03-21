from django.conf import settings
from django.http import HttpResponse
from ninja.types import DictStrAny
from scalar_django_ninja import ScalarViewer
from typing_extensions import Annotated, Doc

scalar_theme = """
/* basic theme */
.light-mode {
  --scalar-color-1: #2a2f45;
  --scalar-color-2: #757575;
  --scalar-color-3: #8e8e8e;
  --scalar-color-accent: #009485;

  --scalar-background-1: #fff;
  --scalar-background-2: #fcfcfc;
  --scalar-background-3: #f8f8f8;
  --scalar-background-accent: #ecf8f6;

  --scalar-border-color: rgba(0, 0, 0, 0.1);
}
.dark-mode {
  --scalar-color-1: rgba(255, 255, 255, 0.9);
  --scalar-color-2: rgba(255, 255, 255, 0.62);
  --scalar-color-3: rgba(255, 255, 255, 0.44);
  --scalar-color-accent: #00ccb8;

  --scalar-background-1: #1f2129;
  --scalar-background-2: #282a35;
  --scalar-background-3: #30323d;
  --scalar-background-accent: #223136;

  --scalar-border-color: rgba(255, 255, 255, 0.1);
}
/* Document Sidebar */
.light-mode .t-doc__sidebar {
  --sidebar-background-1: var(--scalar-background-1);
  --sidebar-item-hover-color: currentColor;
  --sidebar-item-hover-background: var(--scalar-background-2);
  --sidebar-item-active-background: var(--scalar-background-accent);
  --sidebar-border-color: var(--scalar-border-color);
  --sidebar-color-1: var(--scalar-color-1);
  --sidebar-color-2: var(--scalar-color-2);
  --sidebar-color-active: var(--scalar-color-accent);
  --sidebar-search-background: transparent;
  --sidebar-search-border-color: var(--scalar-border-color);
  --sidebar-search--color: var(--scalar-color-3);
}

.dark-mode .sidebar {
  --sidebar-background-1: var(--scalar-background-1);
  --sidebar-item-hover-color: currentColor;
  --sidebar-item-hover-background: var(--scalar-background-2);
  --sidebar-item-active-background: var(--scalar-background-accent);
  --sidebar-border-color: var(--scalar-border-color);
  --sidebar-color-1: var(--scalar-color-1);
  --sidebar-color-2: var(--scalar-color-2);
  --sidebar-color-active: var(--scalar-color-accent);
  --sidebar-search-background: transparent;
  --sidebar-search-border-color: var(--scalar-border-color);
  --sidebar-search--color: var(--scalar-color-3);
}

/* advanced */
.light-mode {
  --scalar-button-1: rgb(49 53 56);
  --scalar-button-1-color: #fff;
  --scalar-button-1-hover: rgb(28 31 33);

  --scalar-color-green: #009485;
  --scalar-color-red: #d52b2a;
  --scalar-color-yellow: #ffaa01;
  --scalar-color-blue: #0a52af;
  --scalar-color-orange: #953800;
  --scalar-color-purple: #8251df;

  --scalar-scrollbar-color: rgba(0, 0, 0, 0.18);
  --scalar-scrollbar-color-active: rgba(0, 0, 0, 0.36);
}
.dark-mode {
  --scalar-button-1: #f6f6f6;
  --scalar-button-1-color: #000;
  --scalar-button-1-hover: #e7e7e7;

  --scalar-color-green: #00ccb8;
  --scalar-color-red: #e5695b;
  --scalar-color-yellow: #ffaa01;
  --scalar-color-blue: #78bffd;
  --scalar-color-orange: #ffa656;
  --scalar-color-purple: #d2a8ff;

  --scalar-scrollbar-color: rgba(255, 255, 255, 0.24);
  --scalar-scrollbar-color-active: rgba(255, 255, 255, 0.48);
}
:root {
  --scalar-radius: 3px;
  --scalar-radius-lg: 6px;
  --scalar-radius-xl: 8px;
}
.scalar-card:nth-of-type(3) {
  display: none;
}"""


def get_custom_scalar_api_reference(
        *,
        openapi_url: Annotated[
            str,
            Doc(
                """
                The OpenAPI URL that Scalar should load and use.
                This is normally done automatically by Ninja using the default URL
                `/openapi.json`.
                """
            ),
        ],
        title: Annotated[
            str,
            Doc(
                """
                The HTML `<title>` content, normally shown in the browser tab.
                """
            ),
        ],
        scalar_js_url: Annotated[
            str,
            Doc(
                """
                The URL to use to load the Scalar JavaScript.
                It is normally set to a CDN URL.
                """
            ),
        ],
        scalar_proxy_url: Annotated[
            str,
            Doc(
                """
                The URL to use to set the Scalar Proxy.
                It is normally set to a Scalar API URL (https://api.scalar.com/request-proxy), but default is empty # noqa: E501
                """
            ),
        ],
        scalar_favicon_url: Annotated[
            str,
            Doc(
                """
                The URL of the favicon to use. It is normally shown in the browser tab. # noqa: E501
                """
            ),
        ],
        scalar_theme: Annotated[
            str,
            Doc(
                """
                Custom CSS theme for Scalar.
                """
            ),
        ],
        configuration: Annotated[
            DictStrAny,
            Doc(
                """
                Configuration settings for Scalar.
                """
            ),
        ],
) -> HttpResponse:
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <title>{title}</title>
    <!-- needed for adaptive design -->
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="shortcut icon" href="{scalar_favicon_url}">
    <style>
      body {{
        margin: 0;
        padding: 0;
      }}
      .footer {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 14px;
        padding: 12px 20px;
        background: var(--scalar-background-3, #f8f9fa);
        color: var(--scalar-color-2, #2a2f45);
        border-top: 1px solid var(--scalar-border-color, #ddd);
        position: fixed;
        bottom: 0;
        width: 100%;
        box-shadow: 0px -2px 4px rgba(0, 0, 0, 0.1);
        font-family: "Inter", sans-serif;
      }}
      .footer div {{
        display: flex;
        gap: 12px;
      }}
      .footer a {{
        color: var(--scalar-color-accent, #009485);
        text-decoration: none;
        margin-left: 15px;
        font-weight: 400;
      }}
      .footer a:hover {{
        text-decoration: underline;
      }}
    </style>
    <style>
    {scalar_theme}
    </style>
    </head>
    <body>
    <noscript>
        Scalar requires Javascript to function. Please enable it to browse the documentation. # noqa: E501
    </noscript>
    <script
    id="api-reference"
    data-url="{openapi_url}"
    data-proxy-url="{scalar_proxy_url}"
    data-configuration='{configuration}'>
    </script>
    <script src="{scalar_js_url}"></script>
    <div class="footer">
      <span>&copy; 2025 <a style="margin-left: 0;"href="mailto:watthanasak.jea@nectec.or.th">Watthanasak Jeamwatthanachai</a>. All rights reserved.</span>
      <div style="margin-right: 50px;">
        <a href="https://a100.ap.ngrok.io/f5/playground/" target="_blank">Playground</a>
        <a href="https://a100.ap.ngrok.io/f5/admin" target="_blank">Dashboard</a>
        <a href="https://a100.ap.ngrok.io/jupyter/lab/" target="_blank">Jupyter</a>
      </div>
    </div>
    </body>
    </html>
    """
    return HttpResponse(html)


class CustomScalarViewer(ScalarViewer):
    def __init__(
            self,
            title: str = "API Reference | F5-TTS by Watthanasak J.",
            openapi_url: str = "/f5/api/openapi.json" if settings.ON_NGINX else "/api/openapi.json",
            scalar_js_url: str = "https://cdn.jsdelivr.net/npm/@scalar/api-reference",  # noqa: E501
            scalar_proxy_url: str = "",
            scalar_favicon_url: str = "",
            scalar_theme: str = scalar_theme,
    ):
        self.title = title
        self.openapi_url = openapi_url
        self.scalar_js_url = scalar_js_url
        self.scalar_proxy_url = scalar_proxy_url
        self.scalar_favicon_url = scalar_favicon_url
        self.scalar_theme = scalar_theme
        self.configuration = """ {"theme": "kepler", "hideModels": "true", "operationsSorter": "method"} """

    def render_page(self, request, api):
        return get_custom_scalar_api_reference(
            openapi_url=self.openapi_url,
            title=self.title,
            scalar_js_url=self.scalar_js_url,
            scalar_proxy_url=self.scalar_proxy_url,
            scalar_favicon_url=self.scalar_favicon_url,
            scalar_theme=self.scalar_theme,
            configuration=self.configuration,
        )
