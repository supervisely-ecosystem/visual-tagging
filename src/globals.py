import os

import supervisely as sly
from dotenv import load_dotenv
from supervisely.app.v1.app_service import AppService

if sly.is_development():
    load_dotenv("local.env")
    load_dotenv(os.path.expanduser("~/supervisely.env"))

app: AppService = AppService()
api = app.public_api

OWNER_ID = int(os.environ["context.userId"])
TEAM_ID = sly.env.team_id()
WORKSPACE_ID = sly.env.workspace_id()
PROJECT_ID = sly.env.project_id()
PROJECT = None
META: sly.ProjectMeta = None

CNT_GRID_COLUMNS = 3
GALLERY = {
    "content": {
        "projectMeta": sly.ProjectMeta().to_json(),
        "annotations": {},
        "layout": [[] for i in range(CNT_GRID_COLUMNS)],
    },
    "previewOptions": {"enableZoom": True, "resizeOnZoom": True},
    "options": {
        "enableZoom": False,
        "syncViews": False,
        "showPreview": True,
        "selectable": True,
    },
}
GALLERY2TAG = {}
