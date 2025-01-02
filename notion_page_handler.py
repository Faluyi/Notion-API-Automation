import os
import re
from notion_client import Client
from dotenv import load_dotenv
from datetime import datetime, timezone
load_dotenv()


class NotionPageHandler:
    def __init__(self, page_id, token: str):
        self.page_id = page_id
        self.notion_client = Client(auth=token)
        self.page_data: dict = self.__get_page_data()

    def __get_page_data(self):
        page_data = self.notion_client.pages.retrieve(page_id=self.page_id)
        return page_data

    def update_page_name(self, new_name: str):
        try:
            properties = {
                "title": {
                    "title": [
                        {
                            "text": {
                                "content": new_name
                            },
                            "annotations": {
                                "bold": False,
                                "italic": False,
                                "strikethrough": False,
                                "underline": False,
                                "code": False,
                                "color": "default"
                            },
                            "plain_text": new_name
                        }
                    ]
                },
                "title checked": {
                    "checkbox": True  # Set the checkbox to True
                }
            }

            self.notion_client.pages.update(self.page_id, properties=properties)
        except Exception as err:
            print("UPDATING PAGE NAME ERR ==> ", err)

    def add_comment(self, comment: str = 'Invalid Name detected'):
        try:
            parent = {"page_id": self.page_id}
            rich_text = [{"text": {"content": comment}}]

            self.notion_client.comments.create(
                parent=parent,
                rich_text=rich_text
            )
        except Exception as err:
            print("ADDING COMMENTS ERR ==> ", err)

    def mention_and_comment(self, user_id: str, comment: str):
        try:
            parent = {"page_id": self.page_id}
            mention = {
                "mention": {
                    "type": "user",
                    "user": {
                        "object": "user",
                        "id": user_id
                    }
                }
            }
            rich_text = [mention, {"text": {"content": comment}}]

            self.notion_client.comments.create(
                parent=parent,
                rich_text=rich_text
            )
        except Exception as err:
            print("ADDING COMMENTS ERR ==> ", err)
    def mark_page_as_checked(self):
        try:
            properties = {
                "title checked": {
                    "checkbox": True  # Set the checkbox to True
                }
            }
            self.notion_client.pages.update(self.page_id, properties=properties)
        except Exception as err:
            print("COULDN'T MARK PAGE AS CHECKED ==> ", err)

    def get_page_last_editor_id(self):
        """Retrieves the last editor of a specified Notion page and assigns it to the page."""
        try:
            last_editor_id = self.page_data.get("last_edited_by", {}).get("id")
            if not last_editor_id:
                return "Last editor information not available for this page."
            print("Last editor ID:", last_editor_id)
            return last_editor_id
        except Exception as e:
            print("Error fetching or updating page details:", e)

    def assign_user_to_page(self, user_id):
        try:
            user_id = user_id.replace('-', '')
            # Update the page to assign it to the last editor
            update_data = {
                "properties": {
                    "Assignee": {
                        "people": [{"object": "user", "id": user_id}]
                    }
                }
            }
            self.notion_client.pages.update(page_id=self.page_id, **update_data)
            print("Page assigned successfully to the last editor")
        except Exception as err:
            print("ASSIGN USER TO PAGE ERR: ", err)

    def get_page_status(self) -> str:
        status_id = self.page_data.get('properties', {}).get('Status', {}).get('status', {}).get('id')
        return status_id

    def get_page_assignees(self) -> list:
        """
        :return: [{"object": "user", "id": user_id}, ...]
        """
        assignee_data = self.page_data.get('Assignee', {}).get('people', [])
        return assignee_data

    def get_page_owner(self):
        page_owner = self.page_data.get('created_by', {})

        return page_owner

    def get_days_since_last_edit(self) -> int:
        last_edited_dt = datetime.fromisoformat(self.page_data["last_edited_time"].replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        day_difference = (now - last_edited_dt).days

        return day_difference

    def check_if_task_is_due(self) -> bool:
        end_date_str = self.page_data.get('properties', {}).get('Created Date', {}).get('date', {}).get('end')
        if not end_date_str:
            return False

        end_date = datetime.fromisoformat(end_date_str).replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        return now > end_date

    def nudge_page_assignee(self, comment: str):
        page_assignees = self.get_page_assignees()

        try:
            for assignee in page_assignees:
                self.mention_and_comment(assignee["id"], comment)

        except Exception as err:
            print("ERROR NUDGING ASSIGNEE: ", err)

    def nudge_page_owner(self, comment: str):
        page_owner = self.get_page_owner()

        try:
            self.mention_and_comment(page_owner["id"], comment)

        except Exception as err:
            print("ERROR NUDGING PROJECT OWNER: ", err)

    def check_for_checklist_or_kpi(self):
        kpi_relations = self.page_data.get('properties', {}).get('KPI', {}).get('relation', [])
        checklist_relations = self.page_data.get('properties', {}).get('Checklist', {}).get('relation', [])

        return len(kpi_relations) > 0 or len(checklist_relations) > 0

    def get_page_assigned_to(self) -> list:
        """
        :return: [{"object": "user", "id": user_id}, ...]
        """
        assignee_data = self.page_data.get('properties', {}).get('Assigned To', {}).get('people', [])
        return assignee_data

    def get_page_blocks(self) -> list:
        all_blocks = []
        next_cursor = None

        while True:
            response = self.notion_client.blocks.children.list(
                block_id=self.page_id,
                page_size=100,
                start_cursor=next_cursor
            )
            blocks = response.get("results", [])
            all_blocks.extend(blocks)

            next_cursor = response.get("next_cursor")
            if not next_cursor:
                break

        return all_blocks

    def update_block_text(self, block_id, block_type, updated_text):
        """
        Update the text content of a Notion block.

        :param block_id: The ID of the block to be updated.
        :param block_type: The type of the block (e.g., paragraph, heading_1).
        :param updated_text: The new text content for the block.
        :return: None
        """
        try:
            self.notion_client.blocks.update(
                block_id=block_id,
                **{
                    block_type: {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": updated_text}
                            }
                        ]
                    }
                }
            )
        except Exception as e:
            print(f"Error updating block {block_id} text: {e}")

    def add_new_text_block(self, content):
        """Add a new text block to the page."""
        page_id = self.page_id
        self.notion_client.blocks.children.append(
            block_id=page_id,
            children=[
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": content}}]
                    }
                }
            ]
        )






