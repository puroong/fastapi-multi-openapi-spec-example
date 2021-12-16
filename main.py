from typing import Optional, Dict, Any, List

from fastapi import FastAPI, HTTPException, Request
from fastapi.openapi.models import Server
from fastapi.openapi.utils import get_openapi
from fastapi.templating import Jinja2Templates

# ================================
# openapi 문서 뽑아낼 앱들
# ================================
from pydantic import BaseModel
from starlette.responses import HTMLResponse

api_app = FastAPI()
dashboard_app = FastAPI()


@api_app.get("/api", tags=["api"])
def hello_api():
    return {"hello": "api"}


@dashboard_app.get("/", tags=["dashboard"])
def hello_dashboard():
    return {"Hello": "dashboard"}


# ================================
# OPENAPI 보여주기 위한 앱
# ================================
class OpenApiApp:
    def __init__(
        self, app: FastAPI, feature_version: Optional[str], title: str, version: str
    ):
        self._app = app
        self._feature_version = feature_version
        self._title = title
        self._version = version

    def get_schema(self):
        openapi_schema = get_openapi(
            title=self._title,
            version=self._version,
            description="This is a very custom OpenAPI schema",
            routes=self._app.routes,
            servers=self._get_servers(),
        )

        openapi_schema["info"]["x-logo"] = {
            "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
        }
        self._app.openapi_schema = openapi_schema
        return self._app.openapi_schema

    def _get_servers(self):
        pass


class ApiOpenApiApp(OpenApiApp):
    def _get_servers(self):
        servers = []
        if self._feature_version:
            servers.append(
                Server(
                    url=f"https://feature-{self._feature_version}.api.com",
                    description="feature",
                ).dict()
            )
        servers.append(
            Server(url=f"https://production.api.com", description="production").dict()
        )
        servers.append(
            Server(
                url=f"https://developement.api.com", description="developement"
            ).dict()
        )

        return servers


class DashboardOpenApiApp(OpenApiApp):
    def _get_servers(self):
        servers = []
        if self._feature_version:
            servers.append(
                Server(
                    url=f"https://feature-{self._feature_version}.dashboard.com",
                    description="feature",
                ).dict()
            )
        servers.append(
            Server(
                url=f"https://production.dashboard.com", description="production"
            ).dict()
        )
        servers.append(
            Server(
                url=f"https://developement.dashboard.com", description="developement"
            ).dict()
        )

        return servers


openapi_app = FastAPI(docs_url=None)
templates = Jinja2Templates(directory="templates")


class SwaggerUiContext(BaseModel):
    request: Request

    # for swagger ui
    openapi_url: str
    title: str
    swagger_js_url: Optional[str]
    swagger_css_url: Optional[str]
    swagger_favicon_url: Optional[str]
    oauth2_redirect_url: Optional[str]
    init_oauth: Optional[Dict[str, Any]]

    # additional data
    feature_version: Optional[str]
    selected_app_name: str
    available_app_names: List[str]

    class Config:
        arbitrary_types_allowed = True


@openapi_app.get("/docs", include_in_schema=True, response_class=HTMLResponse)
async def custom_swagger_ui_html(
    request: Request, name: Optional[str] = None, feature_version: Optional[str] = None
):
    OPENAPI_APP_MAP = {
        "dashboard": DashboardOpenApiApp(
            app=dashboard_app,
            feature_version=feature_version,
            title="dashboard openapi spec",
            version="1.0.0",
        ),
        "api": ApiOpenApiApp(
            app=api_app,
            feature_version=feature_version,
            title="api openapi spec",
            version="1.0.0",
        ),
    }

    APP_NAMES = list(OPENAPI_APP_MAP.keys())

    name = name or APP_NAMES[0]
    if name not in OPENAPI_APP_MAP:
        raise HTTPException(404)

    openapi_app.openapi_schema = OPENAPI_APP_MAP[name].get_schema()

    available_apps = APP_NAMES

    return templates.TemplateResponse(
        "swagger-ui.html",
        SwaggerUiContext(
            request=request,
            openapi_url=openapi_app.openapi_url,
            title="openapi",
            swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@3/swagger-ui-bundle.js",
            swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@3/swagger-ui.css",
            swagger_favicon_url="https://fastapi.tiangolo.com/img/favicon.png",
            selected_app_name=name,
            feature_version=feature_version,
            available_app_names=available_apps,
        ).dict(),
    )
