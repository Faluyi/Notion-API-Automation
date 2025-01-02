## Notion & Slack Workspace Automation
This project automates running a collections of functions on notion and slack workspaces periodically. 
It was built using python and runs on Google Cloud Platform as serverless functions.

### Setup on Google Cloud
<ul>
<li>Create your own notion internal integrated token</li>
<li>Search Secrets Manager and edit/add a secret called `ANTHROPIC_API_KEY` with your own API KEY.</li>
<li>Download the workspaces_api_keys.json located in the root of this github project.</li>
<li>Edit the workspaces_api_keys.json and add the database id, token and name</li>
<li>Go to google cloud and open the bucket containing this file (ask for the bucket name).</li>
<li>Replace the workspaces_api_keys.json with the edited version.</li>
</ul>
