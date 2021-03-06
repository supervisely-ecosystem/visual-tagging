import os
import supervisely_lib as sly


def _empty_string_error(var, name):
    if var == '':
        raise ValueError(f"{name} is undefined")


app: sly.AppService = sly.AppService()
api: sly.Api = None
task_id = None
owner_id = None
team_id = None
workspace_id = None
project_id = None
project = None
meta: sly.ProjectMeta = None
user2batches_path = None
catalog_path = None
field_name = None
target_class_name = None
reference_tag_name = None
multiselect_class_name = None
gallery_meta: sly.ProjectMeta = None


image_grid_options = {
    "opacity": 1, #0.5,
    "fillRectangle": False, #True
    "enableZoom": False,
    "syncViews": False,
    "showPreview": True,
    "selectable": True
}

image_preview_options = {
    "opacity": 1, #0.5,
    "fillRectangle": False,
    "enableZoom": False,
    "resizeOnZoom": True
}


def init():
    sly.logger.info("Initialize input arguments")

    global api
    api = app.public_api

    global task_id
    task_id = app.task_id

    global owner_id
    owner_id = int(os.environ['context.userId'])
    sly.logger.info("owner_id", extra={"owner_id": owner_id})

    global team_id
    team_id = int(os.environ['context.teamId'])
    sly.logger.info("team_id", extra={"team_id": team_id})

    global workspace_id
    workspace_id = int(os.environ['context.workspaceId'])
    sly.logger.info("workspace_id", extra={"workspace_id": workspace_id})

    global project_id
    project_id = int(os.environ['modal.state.slyProjectId'])
    sly.logger.info("project_id", extra={"project_id": project_id})

    global project
    project = api.project.get_info_by_id(project_id)

    global meta
    meta = sly.ProjectMeta.from_json(api.project.get_meta(project_id))
    if len(meta.obj_classes) == 0:
        raise RuntimeError(f"Project {project.name} doesn't have classes")
    if len(meta.tag_metas) == 0:
        raise RuntimeError(f"Project {project.name} doesn't have tags")

    global user2batches_path
    user2batches_path = os.environ["modal.state.user2batchesPath"]
    _empty_string_error(user2batches_path, "user2batchesPath path")
    sly.logger.info("user2batches_path", extra={"user2batches_path": user2batches_path})

    global catalog_path
    catalog_path = os.environ["modal.state.catalogPath"]
    _empty_string_error(catalog_path, "CSV catalog path")
    sly.logger.info("catalog_path", extra={"catalog_path": catalog_path})

    global tag_name
    tag_name = os.environ["modal.state.tagName"]
    _empty_string_error(tag_name, "Target tag name")
    sly.logger.info("tag_name", extra={"tag_name": tag_name})

    _tag: sly.TagMeta = meta.tag_metas.get(tag_name)
    if _tag.value_type != sly.TagValueType.ANY_STRING:
        raise TypeError(f"Tag {tag_name} should have string value type")

    global target_class_name
    target_class_name = os.environ['modal.state.targetClassName']
    _empty_string_error(target_class_name, "Target class name")
    sly.logger.info("target_class_name", extra={"target_class_name": target_class_name})

    global multiselect_class_name
    multiselect_class_name = os.environ['modal.state.multiselectClassName']
    _empty_string_error(multiselect_class_name, "Multiselect class name")
    sly.logger.info("multiselect_class_name", extra={"multiselect_class_name": multiselect_class_name})

    global gallery_meta
    gallery_meta = sly.ProjectMeta(obj_classes=sly.ObjClassCollection([
        sly.ObjClass("product", sly.Rectangle, [0, 255, 0])
    ]))
