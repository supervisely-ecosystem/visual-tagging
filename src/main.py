import os
from collections import defaultdict
import supervisely_lib as sly


app: sly.AppService = sly.AppService()
api = app.public_api


owner_id = int(os.environ['context.userId'])
team_id = int(os.environ['context.teamId'])
workspace_id = int(os.environ['context.workspaceId'])
project_id = int(os.environ['modal.state.slyProjectId'])
project = None
meta: sly.ProjectMeta = None

CNT_GRID_COLUMNS = 3
gallery = {
    "content": {
        "projectMeta": sly.ProjectMeta().to_json(),
        "annotations": {},
        "layout": [[] for i in range(CNT_GRID_COLUMNS)]
    },
    "previewOptions": {
        "enableZoom": True,
        "resizeOnZoom": True
    },
    "options": {
        "enableZoom": False,
        "syncViews": False,
        "showPreview": True,
        "selectable": True
    }
}
gallery2tag = {}


@app.callback("init")
@sly.timeit
def init(api: sly.Api, task_id, context, state, app_logger):
    global project_info, meta

    project_info = api.project.get_info_by_id(project_id)
    meta = sly.ProjectMeta.from_json(api.project.get_meta(project_id))

    same_tags = defaultdict(list)

    progress = sly.Progress("Initializing image examples", project_info.items_count, need_info_log=True)
    for dataset in api.dataset.get_list(project_id):
        images_infos = api.image.get_list(dataset.id)
        for batch in sly.batched(images_infos):
            img_ids = [info.id for info in batch]
            ann_infos = api.annotation.download_batch(dataset.id, img_ids)
            anns = [sly.Annotation.from_json(ann_info.annotation, meta) for ann_info in ann_infos]
            for img_info, ann in zip(batch, anns):
                for tag in ann.img_tags:
                    tag: sly.Tag
                    same_tags[tag.get_compact_str()].append( {
                        "url": img_info.full_storage_url,
                        "figures": [],
                        "tag": {
                            **tag.to_json(),
                            "color": sly.color.rgb2hex(meta.get_tag_meta(tag.name).color)
                        },
                        "_tag": tag
                    })
            progress.iters_done_report(len(batch))

    index = 0
    for key, cards in same_tags.items():
        for card in cards:
            tag = card.pop('_tag', None)
            gallery["content"]["annotations"][str(index)] = card
            gallery["content"]["layout"][index % CNT_GRID_COLUMNS].append(str(index))
            gallery2tag[str(index)] = tag
            index += 1

    api.task.set_field(task_id, "data.gallery", gallery)
    if len(gallery2tag) > 0:
        api.task.set_field(task_id, "state.selectedItem", '0')

    sly.logger.info("Initialization finished")


@app.callback("assign_tag")
@sly.timeit
def assign_tag(api: sly.Api, task_id, context, state, app_logger):
    index = state.get("selectedItem")
    if index is None:
        sly.logger.warn("Tag is not selected")
        return
    if index not in gallery2tag:
        sly.logger.warn(f"Selected index {index} is not in {list(gallery2tag.keys())}")
    tag = gallery2tag[index]

    cur_image_id = context.get("imageId")
    if cur_image_id is None:  # double check, never happens
        sly.logger.warn("Image is not defined in context, contact support")
        return

    cur_project_id = context.get("projectId")
    if cur_project_id is None:  # double check, never happens
        sly.logger.warn("Project is not defined in context, contact support")
        return

    cur_meta = sly.ProjectMeta.from_json(api.project.get_meta(cur_project_id))

    cur_tag_meta: sly.TagMeta = cur_meta.get_tag_meta(tag.name)
    tag_meta: sly.TagMeta = meta.get_tag_meta(tag.name)
    if cur_tag_meta is None:
        if tag_meta is None: # impossible
            raise RuntimeError(f"Tag '{tag.name}' not found in original project")
        cur_meta = cur_meta.add_tag_meta(tag_meta)
        api.project.update_meta(cur_project_id, cur_meta.to_json())
        cur_meta = sly.ProjectMeta.from_json(api.project.get_meta(cur_project_id))
        cur_tag_meta = cur_meta.get_tag_meta(tag.name)
        api.project.update_meta(cur_project_id, cur_meta.to_json())
    elif cur_tag_meta != tag_meta:
        sly.logger.error(f"Conflict: different tag with same name {tag.name} already exists in destination project")
        return

    api.image.add_tag(cur_image_id, cur_tag_meta.sly_id, tag.value)


def main():
    data = {}
    data["ownerId"] = owner_id
    data["gallery"] = gallery

    state = {}
    state["selectedItem"] = None
    state["tabName"] = "examples"

    app.run(data=data, state=state, initial_events=[{"command": "init"}])


#@TODO: cnt columns in grid gallery
if __name__ == "__main__":
    sly.main_wrapper("main", main)
