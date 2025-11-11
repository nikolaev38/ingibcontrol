import uvicorn, pathlib

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html

from core.config import settings
from app.api_site_v1 import router as router_site_v1



app = FastAPI(
    title='IngibControl Auth API',
    description='IngibControl Auth API service.',
    version='1.1.1',
)
# app = FastAPI(docs_url=None, redoc_url=None)

# Подключаем статические файлы
app.mount('/static', StaticFiles(directory='static'), name='static')

@app.get('/docs/', include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + ' - Swagger UI',
        swagger_css_url='/static/swagger-custom-ui.css',
    )

origins = settings.cors.frontend_urls

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['GET', 'POST', 'PATCH', 'PUT', 'DELETE', 'OPTIONS'],
    allow_headers=[
        'Access-Control-Allow-Headers',
        'Access-Control-Allow-Origin',
        'Authorization',
        'Content-Type',
        'Set-Cookie',
    ],
)

app.include_router(router=router_site_v1, prefix=settings.api_site_v1_prefix)



if __name__ == '__main__':
    cwd = pathlib.Path(__file__).parent.resolve()
    uvicorn.run('main:app', host='0.0.0.0', port=5000, reload=False, log_config=f'{cwd}/configs/log_config.ini')

    # http://localhost:5000/docs/
