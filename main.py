from typing import Optional, Dict, Any, List

from fastapi import FastAPI, HTTPException, Request
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


def custom_openapi(app: FastAPI, title: str, version: str):
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=title,
        version=version,
        description="This is a very custom OpenAPI schema",
        routes=app.routes,
    )

    openapi_schema["info"]["x-logo"] = {
        "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema


# ================================
# OPENAPI 보여주기 위한 앱
# ================================
dashboard_openapi_schema = custom_openapi(
    dashboard_app, title="dashboard openapi spec", version="1.0.0"
)
api_openapi_schema = custom_openapi(api_app, title="api openapi spec", version="1.0.0")


OPENAPI_SCHEMA_MAP = {
    "dashboard": dashboard_openapi_schema,
    "api": api_openapi_schema,
}

APP_NAMES = list(OPENAPI_SCHEMA_MAP.keys())

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
    selected_app_name: str
    available_app_names: List[str]

    class Config:
        arbitrary_types_allowed = True


@openapi_app.get("/docs", include_in_schema=True, response_class=HTMLResponse)
async def custom_swagger_ui_html(request: Request, name: Optional[str] = None):
    if len(APP_NAMES) == 0:
        raise HTTPException(404)

    if name is None:
        name = APP_NAMES[0]

    if name not in OPENAPI_SCHEMA_MAP:
        raise HTTPException(404)

    openapi_app.openapi_schema = OPENAPI_SCHEMA_MAP[name]
    available_apps = list(OPENAPI_SCHEMA_MAP.keys())

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
            available_app_names=available_apps,
        ).dict(),
    )
