import functions_framework
from notion_project_handler import NotionProjectHandler
from notion_page_handler import NotionPageHandler
from get_workspaces_api_keys import get_workspaces_api_keys


@functions_framework.http
def hello_http(request):
    """Entry point for Google Cloud Function"""
    try:
        # List of Notion workspaces with their tokens and root page IDs
        workspaces = get_workspaces_api_keys()
        notion_workspaces = workspaces['notion'].get('workspaces')
        if not notion_workspaces:
            return 'No notion workspace available'

        for workspace in notion_workspaces:
            notion_project_handler = NotionProjectHandler(workspace)
            notion_project_handler.check_projects_for_proper_naming()
        return 'Project names checked successfully'
    except Exception as err:
        return "An error occurred"


@functions_framework.http
def check_and_update_assignees(request):
    """Entry point for Google Cloud Function"""
    try:
        workspaces = get_workspaces_api_keys()
        notion_workspaces = workspaces['notion'].get('workspaces')
        if not notion_workspaces:
            return 'No notion workspace available'

        for workspace in notion_workspaces:
            notion_project_handler = NotionProjectHandler(workspace)
            pages = notion_project_handler.get_all_pages_in_database()
            for page in pages:
                page['id'] = page['id'].replace('-', '')
                notion_page_handler = NotionPageHandler(page['id'], workspace['token'])
                status = notion_page_handler.get_page_status()
                if status and (status != 'in-progress'):
                    continue
                assignee_data = notion_page_handler.get_page_assignees()
                if len(assignee_data) > 0:
                    continue
                print("SETTING ASSIGNEE")
                last_editor_id = notion_page_handler.get_page_last_editor_id()
                notion_page_handler.assign_user_to_page(last_editor_id)
    except Exception as err:
        return "An error occurred"

@functions_framework.http
def check_and_nudge_assignees_or_project_owner(request):
    """Entry point for Google Cloud Function"""
    try:
        workspaces = get_workspaces_api_keys()
        notion_workspaces = workspaces['notion'].get('workspaces')
        if not notion_workspaces:
            return 'No notion workspace available'

        for workspace in notion_workspaces:
            notion_project_handler = NotionProjectHandler(workspace)
            pages = notion_project_handler.get_all_pages_in_database()
            for page in pages:
                page['id'] = page['id'].replace('-', '')
                notion_page_handler = NotionPageHandler(page['id'], workspace['token'])
                status = notion_page_handler.get_page_status()
                if status and (status != 'Not started'):
                    continue
                stale_period = notion_page_handler.get_days_since_last_edit()
                is_due = notion_page_handler.check_if_task_is_due()

                if stale_period > 14 or is_due:
                    assignee_data = notion_page_handler.get_page_assignees()
                    if len(assignee_data) > 0:
                        print("NUDGING ASSIGNEE")
                        comment = """
                                    This project is overdue / is stale. 
                                    You should consider removing yourself from it, prioritizing it, or delegating it.
                                """
                        notion_page_handler.nudge_page_assignee(comment)
                    else:
                        print("NUDGING PROJECT OWNER")
                        comment = """
                                    This project is overdue / stale. 
                                    You should consider doing, deleting, or delegating it. 
                                """
                        notion_page_handler.nudge_page_owner(comment)
                else:
                    continue

    except Exception as err:
        return "An error occurred"

@functions_framework.http
def check_for_kpi_or_checklist_item(request):
    try:
        workspaces = get_workspaces_api_keys()
        notion_workspaces = workspaces['notion'].get('workspaces')
        if not notion_workspaces:
            return 'No notion workspace available'

        for workspace in notion_workspaces:
            notion_project_handler = NotionProjectHandler(workspace)
            pages = notion_project_handler.get_all_pages_in_database()
            for page in pages:
                if 'Accountability' in page['properties']:
                    notion_page_handler = NotionPageHandler(page['id'], workspace['token'])
                    checklist_or_kpi_attached = notion_page_handler.check_for_checklist_or_kpi()

                    if checklist_or_kpi_attached:
                        continue

                    role_relations = notion_page_handler.page_data.get('properties', {}).get('Roles', {}).get('relation', [])
                    if not role_relations:
                        continue

                    for relation in role_relations:
                        relation_id = relation['id']
                        relation_page_handler = NotionPageHandler(relation_id, workspace['token'])
                        assigned_to = relation_page_handler.get_page_assigned_to()
                        if assigned_to:
                            for assignee in assigned_to:
                                print('TAGGING THE ASSIGNEE AND COMMENTING...')
                                comment = ' No KPI or Checklist attached to this accountability. Kindly attach one or more.'
                                notion_page_handler.mention_and_comment(assignee['id'], comment)

    except Exception as err:
        return "An error occurred"

@functions_framework.http
def update_page_content_with_a_full_stop(page_id):
    try:
        workspaces = get_workspaces_api_keys()
        notion_workspaces = workspaces['notion'].get('workspaces')
        if not notion_workspaces:
            return 'No notion workspace available'

        for workspace in notion_workspaces:
            notion_project_handler = NotionProjectHandler(workspace)
            pages = notion_project_handler.get_all_pages_in_database()
            for page in pages:
                page['id'] = page['id'].replace('-', '')
                notion_page_handler = NotionPageHandler(page['id'], workspace['token'])
                blocks = notion_page_handler.get_page_blocks()

                if not blocks:
                    continue

                last_block = blocks[-1]
                block_id = last_block.get("id")
                block_type = last_block.get("type")

                if block_type in ["paragraph", "heading_1", "heading_2", "heading_3", "bulleted_list_item",
                                  "numbered_list_item"]:
                    text_content = last_block[block_type].get("rich_text", [])

                    if not text_content:
                        updated_text = "."
                        notion_page_handler.update_block_text(block_id, block_type, updated_text)

                    if text_content:
                        last_text = text_content[-1]["text"]["content"]
                        updated_text = f"{last_text}."
                        notion_page_handler.update_block_text(block_id, block_type, updated_text)

                else:
                    notion_page_handler.add_new_text_block(".")
                    print(f"Added a new text block below the last block ID: {block_id}")

    except Exception as err:
        return "An error occurred"




