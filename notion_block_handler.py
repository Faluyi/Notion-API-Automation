import os
import re
from notion_client import Client
from dotenv import load_dotenv
from datetime import datetime, timezone
load_dotenv()


class NotionBlockHandler:
    def __init__(self, page_id, token: str):
        self.block_id = page_id
        self.notion_client = Client(auth=token)
        self.page_data: dict = self.__get_page_data()

    def __get_page_data(self):
        blocks = self.notion_client.pages.retrieve(page_id=self.page_id)
        return page_data

    def fetch_page_blocks(page_id):
        """
        Fetch all blocks of a Notion page, handling pagination.

        :param page_id: The ID of the Notion page.
        :return: List of all blocks on the page.
        """
        all_blocks = []
        next_cursor = None

        while True:
            response = notion.blocks.children.list(
                block_id=page_id,
                page_size=100,
                start_cursor=next_cursor
            )
            blocks = response.get("results", [])
            all_blocks.extend(blocks)

            next_cursor = response.get("next_cursor")
            if not next_cursor:
                break

        return all_blocks
