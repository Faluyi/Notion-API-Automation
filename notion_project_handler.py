import os
import re
from notion_client import Client
from typing import List, Dict, Tuple
from dotenv import load_dotenv
from prompts import NAMING_CONVENTION_PROMPT
from anthropic import Anthropic
from get_secret_from_google import get_secret
from notion_page_handler import NotionPageHandler

load_dotenv()


class NotionProjectHandler:
    def __init__(self, workspace: Dict):
        self.notion_client = Client(auth=workspace["token"])
        self.database_id = workspace["database_id"]
        self.workspace = workspace

    def __is_valid_project_name(self, name: str) -> bool:
        """Check if project name follows GTD outcome-focused naming convention"""
        # Look for present perfect ("has been") or present tense ("is") constructions
        patterns = [
            r'.+\s+is\s+.+',  # "drawer is stocked"
            r'.+\s+has\s+been\s+.+',  # "drawer has been stocked"
            r'.+\s+are\s+.+',  # "supplies are organized"
            r'.+\s+have\s+been\s+.+'  # "supplies have been organized"
        ]

        return any(re.match(pattern, name.lower()) for pattern in patterns)

    def __suggest_project_name(self, name: str) -> str:
        """Generate a suggestion for better project name"""
        # Simple transformation to add "is" if not present
        words = name.split()
        # Basic suggestion by adding "is" after first word
        return f"{words[0]} is {' '.join(words[1:])}"

    def analyze_project_name_with_ai(self, name: str) -> Tuple[bool, str]:
        """Use Claude to check project name validity and get suggestions"""
        try:
            anthropic = Anthropic(api_key=get_secret("ANTHROPIC_API_KEY"))

            message = anthropic.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=100,
                messages=[{
                    "role": "user",
                    "content": NAMING_CONVENTION_PROMPT.format(name=name)
                }]
            )

            response = message.content[0].split('\n')
            is_valid = response[0].strip().lower() == "valid"
            suggestion = response[1].strip()

            return is_valid, suggestion

        except Exception as e:
            print(f"Error using Claude API: {str(e)}")

            # Fall back to basic validation if Claude fails
            is_valid_project_name = self.__is_valid_project_name(name)
            project_name_suggestion = name if is_valid_project_name else self.__suggest_project_name(name)

            return is_valid_project_name, project_name_suggestion

    def add_title_checkbox_to_database_schema(self):
        try:
            self.notion_client.databases.update(
                self.database_id,
                properties={
                    "title checked": {
                        "checkbox": {}
                    }
                }
            )
        except Exception as err:
            print("add_title_checkbox_to_database_schema ERR ==> ", err)

    def check_projects_for_proper_naming(self):
        """Check projects in a workspace for proper naming"""
        try:
            self.add_title_checkbox_to_database_schema()
            pages = self.get_all_pages_in_database()
            for page in pages:
                notion_page_handler = NotionPageHandler(page['id'], self.workspace['token'])
                page_properties = page.get('properties')
                if not page_properties or not page_properties.get('Project name'):
                    continue
                if page_properties.get('title checked') and page_properties['title checked'].get('Checkbox'):
                    continue
                project_name = page_properties["Project name"]["title"][0]["text"]["content"]
                is_valid, suggestion = self.analyze_project_name_with_ai(project_name)

                if is_valid:
                    notion_page_handler.mark_page_as_checked()
                    continue

                notion_page_handler.add_comment()
                notion_page_handler.update_page_name(suggestion)  # marks page as checked as well

                print(f"""
                    Workspace: {self.workspace['name']}
                    Invalid project name: {project_name}
                    Suggested name: {suggestion}
                """)

        except Exception as e:
            print(f"Error processing workspace {self.workspace['name']}: {str(e)}")

    def get_all_pages_in_database(self):
        try:
            response = self.notion_client.databases.query(
                database_id=self.database_id
            )
            return response["results"]
        except:
            return []


def main():
    workspace = {"token": os.getenv("NOTION_INTEGRATION_TOKEN"), "database_id": "3b48f522cc674f9d96df582e78a5c5e0", "name": "Tasks"}
    notion_project_handler = NotionProjectHandler(workspace)
    pages = notion_project_handler.get_all_pages_in_database()
    for page in pages:
        page['id'] = page['id'].replace('-', '')
        notion_page_handler = NotionPageHandler(page['id'], workspace['token'])
        status = notion_page_handler.get_page_status()
        if status and status != 'in-progress':
            continue
        assignee_data = notion_page_handler.get_page_assignees()
        if len(assignee_data) > 0:
            continue
        print("SETTING ASSIGNEE")
        last_editor_id = notion_page_handler.get_page_last_editor_id()
        notion_page_handler.assign_user_to_page(last_editor_id)


if __name__ == "__main__":
    main()
