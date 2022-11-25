from collections import defaultdict

import supervisely as sly

import globals as g


@g.app.callback("init")
@sly.timeit
def init(api: sly.Api, task_id, context, state, app_logger):
    project_info = api.project.get_info_by_id(g.PROJECT_ID)
    g.META = sly.ProjectMeta.from_json(api.project.get_meta(g.PROJECT_ID))

    same_tags = defaultdict(list)

    progress = sly.Progress(
        "Initializing image examples", project_info.items_count, need_info_log=True
    )
    for dataset in api.dataset.get_list(g.PROJECT_ID):
        images_infos = api.image.get_list(dataset.id)
        for batch in sly.batched(images_infos):
            img_ids = [info.id for info in batch]
            ann_infos = api.annotation.download_batch(dataset.id, img_ids)
            anns = [
                sly.Annotation.from_json(ann_info.annotation, g.META)
                for ann_info in ann_infos
            ]
            for img_info, ann in zip(batch, anns):
                for tag in ann.img_tags:
                    tag: sly.Tag
                    same_tags[tag.get_compact_str()].append(
                        {
                            "url": img_info.path_original,
                            "figures": [],
                            "tag": {
                                **tag.to_json(),
                                "color": sly.color.rgb2hex(
                                    g.META.get_tag_meta(tag.name).color
                                ),
                            },
                            "_tag": tag,
                        }
                    )
            progress.iters_done_report(len(batch))

    index = 0
    for key, cards in same_tags.items():
        for card in cards:
            tag = card.pop("_tag", None)
            g.GALLERY["content"]["annotations"][str(index)] = card
            g.GALLERY["content"]["layout"][index % g.CNT_GRID_COLUMNS].append(
                str(index)
            )
            g.GALLERY2TAG[str(index)] = tag
            index += 1

    api.task.set_field(task_id, "data.gallery", g.GALLERY)
    if len(g.GALLERY2TAG) > 0:
        api.task.set_field(task_id, "state.selectedItem", "0")

    sly.logger.info("Initialization finished")


@g.app.callback("assign_tag")
@sly.timeit
def assign_tag(api: sly.Api, task_id, context, state, app_logger):
    index = state.get("selectedItem")
    if index is None:
        sly.logger.warn("Tag is not selected")
        return
    if index not in g.GALLERY2TAG:
        sly.logger.warn(
            f"Selected index {index} is not in {list(g.GALLERY2TAG.keys())}"
        )
    tag = g.GALLERY2TAG[index]

    cur_image_id = context.get("imageId")
    if cur_image_id is None:  # double check, never happens
        sly.logger.warn("Image is not defined in context, contact support")
        return

    cur_img_tags = sly.Annotation.from_json(
        data=api.annotation.download_json(image_id=cur_image_id),
        project_meta=g.META,
    ).img_tags
    cur_img_tags_names = [tag.name for tag in cur_img_tags]
    if tag.name in cur_img_tags_names:
        g.app.show_modal_window(
            message=f"Tag: {tag.name} already assigned to this image", level="info"
        )
        return

    cur_project_id = context.get("projectId")
    if cur_project_id is None:  # double check, never happens
        sly.logger.warn("Project is not defined in context, contact support")
        return

    cur_meta = sly.ProjectMeta.from_json(api.project.get_meta(cur_project_id))

    cur_tag_meta: sly.TagMeta = cur_meta.get_tag_meta(tag.name)
    tag_meta: sly.TagMeta = g.META.get_tag_meta(tag.name)
    if cur_tag_meta is None:
        if tag_meta is None:  # impossible
            raise RuntimeError(f"Tag '{tag.name}' not found in original project")
        cur_meta = cur_meta.add_tag_meta(tag_meta)
        api.project.update_meta(cur_project_id, cur_meta.to_json())
        cur_meta = sly.ProjectMeta.from_json(api.project.get_meta(cur_project_id))
        cur_tag_meta = cur_meta.get_tag_meta(tag.name)
        api.project.update_meta(cur_project_id, cur_meta.to_json())
    elif cur_tag_meta != tag_meta:
        sly.logger.error(
            f"Conflict: different tag with same name {tag.name} already exists in destination project"
        )
        return

    api.image.add_tag(cur_image_id, cur_tag_meta.sly_id, tag.value)


def main():
    data = {}
    data["ownerId"] = g.OWNER_ID
    data["gallery"] = g.GALLERY

    state = {}
    state["selectedItem"] = None
    state["tabName"] = "examples"

    g.app.run(data=data, state=state, initial_events=[{"command": "init"}])


# @TODO: cnt columns in grid gallery
if __name__ == "__main__":
    sly.main_wrapper("main", main)
