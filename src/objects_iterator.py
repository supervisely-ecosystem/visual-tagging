import supervisely_lib as sly
import globals as ag
import cache


def get_first_id(ann: sly.Annotation):
    for idx, label in enumerate(ann.labels):
        if label.obj_class.name == ag.target_class_name:
            return label.geometry.sly_id
    return None


def get_prev_id(ann: sly.Annotation, active_figure_id):
    prev_idx = None
    for idx, label in enumerate(ann.labels):
        if label.geometry.sly_id == active_figure_id:
            if prev_idx is None:
                return None
            return ann.labels[prev_idx].geometry.sly_id
        if label.obj_class.name == ag.target_class_name:
            prev_idx = idx


def get_next_id(ann: sly.Annotation, active_figure_id):
    need_search = False
    for idx, label in enumerate(ann.labels):
        if label.geometry.sly_id == active_figure_id:
            need_search = True
            continue
        if need_search:
            if label.obj_class.name == ag.target_class_name:
                return label.geometry.sly_id
    return None


def select_object(api: sly.Api, task_id, context, find_func, show_msg=False):
    user_id = context["userId"]
    image_id = context["imageId"]
    project_id = context["projectId"]
    ann_tool_session = context["sessionId"]

    ann = cache.get_annotation(image_id)

    active_figure_id = context["figureId"]
    if active_figure_id is None:
        active_figure_id = get_first_id(ann)
    else:
        active_figure_id = find_func(ann, active_figure_id)
        # if show_msg is True and active_figure_id is None:
        #     api.app.set_field(task_id, "state.dialogVisible", True)

    if active_figure_id is not None:
        api.img_ann_tool.set_figure(ann_tool_session, active_figure_id)
        api.img_ann_tool.zoom_to_figure(ann_tool_session, active_figure_id, 2)

    return active_figure_id


@ag.app.callback("select_prev_object")
@sly.timeit
def prev_object(api: sly.Api, task_id, context, state, app_logger):
    active_figure_id = select_object(api, task_id, context, get_prev_id)
    context["figureId"] = active_figure_id
    # _refresh_upc(api, task_id, context, state, app_logger)


@ag.app.callback("select_next_object")
@sly.timeit
def next_object(api: sly.Api, task_id, context, state, app_logger):
    active_figure_id = select_object(api, task_id, context, get_next_id, show_msg=True)
    context["figureId"] = active_figure_id
    # _refresh_upc(api, task_id, context, state, app_logger)