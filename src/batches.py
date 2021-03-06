import os
import supervisely_lib as sly
import globals as ag

user2batches = None
batches = None
figureId2Key = {}

empty_gallery = {
    "content": {
        "projectMeta": {},
        "annotations": {},
        "layout": []
    },
    "previewOptions": ag.image_preview_options,
    "options": ag.image_grid_options,
}

user_grid = {}
user_selected = {}
CNT_GRID_COLUMNS = 2


def init(data, state):
    global user2batches, batches, user_grid, figureId2Key

    local_path = os.path.join(ag.app.data_dir, ag.user2batches_path.lstrip("/"))
    ag.api.file.download(ag.team_id, ag.user2batches_path, local_path)
    user2batches = sly.json.load_json_file(local_path)

    local_batches_path = os.path.join(ag.app.data_dir, user2batches["batches_path"].lstrip("/"))
    ag.api.file.download(ag.team_id, user2batches["batches_path"], local_batches_path)
    batches = sly.json.load_json_file(local_batches_path)
    batches = {batch["batch_index"]: batch for batch in batches}

    for userLogin, bindices in user2batches["users"].items():
        user_info = ag.api.user.get_member_info_by_login(ag.team_id, userLogin)
        if user_info is None:
            sly.logger.warn(f"User {userLogin} not found in team_id={ag.team_id}")
            continue
        user_id = user_info.id
        user_selected[user_id] = None
        user_grid_items = []
        for bindex in bindices:
            if bindex not in batches:
                raise KeyError(f"Batch with index {bindex} is assigned to user {userLogin}. "
                               f"But batch with index {bindex} doesn't exist in {user2batches['batches_path']}")
            batch = batches[bindex]
            for reference_key, ref_examples in batch["references"].items():
                for reference_info in ref_examples:
                    image_url = reference_info["image_url"]
                    [top, left, bottom, right] = reference_info["bbox"]
                    label = sly.Label(sly.Rectangle(top, left, bottom, right), ag.gallery_meta.get_obj_class("product"))
                    catalog_info = batch["references_catalog_info"][reference_key]
                    figure_id = reference_info["geometry"]["id"]

                    figureId2Key[str(figure_id)] = reference_key
                    user_grid_items.append({
                        "batchIndex": bindex,  # store for simplicity
                        "labelId": figure_id,  # duplicate for simplicity
                        "url": image_url,
                        "figures": [label.to_json()],
                        "zoomToFigure": {
                            "figureId": figure_id,
                            "factor": 1.2
                        },
                        "catalogInfo": catalog_info
                    })

        user_grid[user_id] = {
            "content": {
                "projectMeta": ag.gallery_meta.to_json(),
                "annotations": {},
                "layout": [[] for i in range(CNT_GRID_COLUMNS)]
            },
            "previewOptions": ag.image_preview_options,
            "options": ag.image_grid_options,
        }

        for idx, item in enumerate(user_grid_items):
            user_grid[user_id]["content"]["annotations"][item["labelId"]] = item
            user_grid[user_id]["content"]["layout"][idx % CNT_GRID_COLUMNS].append(item["labelId"])

    data["userGrid"] = user_grid
    data["allowedUsers"] = list(user_grid.keys())
    data["allowedUsers"].append(ag.owner_id)
    state["selected"] = {}
