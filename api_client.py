import os
import requests
import urllib3
import logging

from config import (
    NCP_LOGIN_URL,
    NCP_USERNAME,
    NCP_PASSWORD,
    CREATE_PROJECT_URL,
    GET_PROJECTS_URL,
    GET_PROJECT_URL,
    UPDATE_PROJECT_URL,
    DELETE_PROJECT_URL,
    ARCHIVE_PROJECT_URL,
    UNARCHIVE_PROJECT_URL,
    DOWNLOAD_PROJECT_URL,
    LIST_MEMBERS_URL,
    ADD_MEMBER_URL,
    GET_MEMBER_URL,
    DELETE_MEMBER_URL,
    ADD_ADMIN_MEMBER_URL,
    GET_PINNED_PROJECTS_URL,
    PIN_PROJECT_URL,
    UNPIN_PROJECT_URL,
    GET_USER_PREFERENCES_URL,
    CREATE_USER_PREFERENCES_URL,
    UPDATE_USER_PREFERENCES_URL,
    GET_PINNED_CHATS_URL,
    PIN_CHAT_URL,
    UNPIN_CHAT_URL,
    EXPORT_ALL_CONVERSATIONS_URL,
    USER_FEEDBACK_URL,
    ARCHIVE_CONVERSATION_URL,
    GET_ARCHIVED_CONVERSATIONS_URL,
    UNARCHIVE_CONVERSATION_URL,
    EXPORT_CONVERSATION_URL,
    GET_CONVERSATIONS_BY_PROJECT_URL,
    CREATE_DATA_CONNECTOR_URL,
    GET_ALL_DATA_CONNECTORS_URL,
    GET_DATA_CONNECTOR_URL,
    UPDATE_DATA_CONNECTOR_URL,
    DELETE_DATA_CONNECTOR_URL,
    DEACTIVATE_DATA_CONNECTOR_URL,
    ACTIVATE_DATA_CONNECTOR_URL,
    VALIDATE_DATA_CONNECTOR_URL,
    GET_PROJECT_DATA_CONNECTORS_URL,
    LINK_PROJECT_DATA_CONNECTOR_URL,
    UNLINK_PROJECT_DATA_CONNECTOR_URL,
    GET_PROJECT_DATA_CONNECTOR_TAGS_URL,
    GET_DATA_CONNECTOR_PROJECTS_URL,
    DEFAULT_HEADERS,
    VERIFY_SSL,
    CREATE_LLM_CONFIG_URL, GET_ALL_LLM_CONFIGS_URL,
    GET_LLM_CONFIG_URL, UPDATE_LLM_CONFIG_URL, DELETE_LLM_CONFIG_URL,
    GET_ALL_ROLES_URL, CREATE_ROLE_URL, GET_ROLE_URL,
    UPDATE_ROLE_URL, DELETE_ROLE_URL, GET_CUSTOM_AGENTS_URL,
    REASSIGN_USERS_URL, GET_ROLE_BY_USERNAME_URL, GET_USERS_BY_ROLE_URL,
    GET_LLMS_BY_ROLE_URL, GET_DATA_CONNECTORS_BY_ROLE_URL,
    GET_FILES_BY_ROLE_URL, GET_DEVICES_BY_ROLE_URL, GET_CUSTOM_AGENTS_BY_ROLE_URL,
    GET_ALL_LDAP_CONFIGS_URL, CREATE_LDAP_CONFIG_URL,
    GET_LDAP_CONFIG_URL, UPDATE_LDAP_CONFIG_URL, DELETE_LDAP_CONFIG_URL,
    UPLOAD_KB_FILE_URL, GET_KB_FILES_URL,
    UPDATE_KB_FILE_URL, DELETE_KB_FILE_URL,
    GET_ALL_ROCKETCHAT_CONFIGS_URL, CREATE_ROCKETCHAT_CONFIG_URL,
    GET_ROCKETCHAT_CONFIG_URL, DELETE_ROCKETCHAT_CONFIG_URL,
    GET_DASHBOARD_METRICS_URL, GET_SYSTEM_METRICS_URL, GET_GPU_METRICS_URL,
    GET_DOCKER_STATS_URL, GENERATE_LOGS_URL, DOWNLOAD_LOGS_URL, LIST_LOGS_URL,
    LIST_PROJECT_FILES_URL, GET_PROJECT_FILE_URL,
    UPDATE_PROJECT_FILE_URL, DOWNLOAD_PROJECT_FILE_URL,
    LIST_ADMIN_FILES_URL, GET_ADMIN_FILE_URL,
    UPDATE_ADMIN_FILE_URL, DOWNLOAD_ADMIN_FILE_URL,
    LIST_EXPORTS_URL, GET_EXPORT_URL, DOWNLOAD_EXPORT_URL,
    PREVIEW_EXPORT_URL, LIST_CONVERSATION_EXPORTS_URL,
    DOWNLOAD_USER_EXPORT_URL, PREVIEW_USER_EXPORT_URL,
    DELETE_EXPORT_URL,
    LIST_PLATFORM_AGENTS_URL, EXECUTE_PLATFORM_AGENT_URL,
    PREVIEW_CRON_URL, CAN_CREATE_BG_JOB_URL, CREATE_BG_JOB_URL,
    LIST_BG_JOBS_URL, ADMIN_ALL_BG_JOBS_URL, UPDATE_BG_JOB_URL,
    GET_BG_JOB_URL, RUN_BG_JOB_NOW_URL, PAUSE_BG_JOB_URL, RESUME_BG_JOB_URL,
    LIST_BG_JOB_RUNS_URL, GET_BG_JOB_RUN_URL, DELETE_BG_JOB_URL,
    ONBOARD_CUSTOM_AGENT_URL, LIST_CUSTOM_AGENTS_URL, BG_ELIGIBLE_AGENTS_URL,
    GET_CUSTOM_AGENT_URL, DISABLE_CUSTOM_AGENT_URL, ENABLE_CUSTOM_AGENT_URL,
    ENABLE_BG_CUSTOM_AGENT_URL, DISABLE_BG_CUSTOM_AGENT_URL,
    ADMIN_LIST_CUSTOM_AGENTS_URL, MY_CUSTOM_AGENTS_URL, SUBMIT_CUSTOM_AGENT_URL,
    UPDATE_CUSTOM_AGENT_VERSION_URL, APPROVE_CUSTOM_AGENT_URL,
    DECLINE_CUSTOM_AGENT_URL, FEEDBACK_CUSTOM_AGENT_URL,
    DOWNLOAD_CUSTOM_AGENT_URL, CAN_SUBMIT_AGENT_URL, DELETE_CUSTOM_AGENT_URL,
    DELETE_USER_CUSTOM_AGENT_URL,
    LIST_ORGANIZATIONS_URL, CREATE_ORGANIZATION_URL, UPDATE_ORGANIZATION_URL,
    ASSIGN_ORG_USERS_URL, GET_ORG_USERS_URL, DEACTIVATE_ORGANIZATION_URL,
    DELETE_ORGANIZATION_URL,
)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# JWT Token Management
# ─────────────────────────────────────────────

_jwt_token = None


def get_ncp_token():
    """Authenticate with NCP and return a JWT token."""
    global _jwt_token

    payload = {"username": NCP_USERNAME, "password": NCP_PASSWORD}

    response = requests.post(
        NCP_LOGIN_URL,
        json=payload,
        headers=DEFAULT_HEADERS,
        verify=VERIFY_SSL,
    )

    response.raise_for_status()

    data = response.json()

    # Try multiple possible token locations in the response
    token = (
        data.get("token")
        or data.get("access_token")
        or data.get("data", {}).get("token")
        or data.get("data", {}).get("access_token")
    )

    if not token:
        logger.error("Token not found in response: %s", data)
        return None

    _jwt_token = token
    logger.info("NCP JWT authentication successful")

    return _jwt_token


def _auth_headers(token=None):
    """Build headers with JWT Authorization bearer token."""
    t = token or _jwt_token
    headers = DEFAULT_HEADERS.copy()
    if t:
        headers["Authorization"] = f"Bearer {t}"
    return headers


def safe_json(response):
    """Safely parse JSON from a response."""
    try:
        return response.json()
    except Exception:
        logger.warning("Non-JSON response: %s", response.text[:200])
        return {}


# ─────────────────────────────────────────────
# 1. Create Project
#    POST /api/v1/projects
# ─────────────────────────────────────────────

def create_project(project_payload, token=None):
    """Create a new project."""
    response = requests.post(
        CREATE_PROJECT_URL,
        json=project_payload,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Create project → %s", response.status_code)
    return response


# ─────────────────────────────────────────────
# 2. Get All Projects
#    GET /api/v1/projects
# ─────────────────────────────────────────────

def get_projects(token=None):
    """Fetch all projects."""
    response = requests.get(
        GET_PROJECTS_URL,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Get projects → %s", response.status_code)
    return response


# ─────────────────────────────────────────────
# 3. Get Project by ID
#    GET /api/v1/projects/{project_id}
# ─────────────────────────────────────────────

def get_project(project_id, token=None):
    """Fetch a single project by ID."""
    url = GET_PROJECT_URL.format(project_id=project_id)
    response = requests.get(
        url,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Get project %s → %s", project_id, response.status_code)
    return response


# ─────────────────────────────────────────────
# 4. Update Project
#    PUT /api/v1/projects/{project_id}
# ─────────────────────────────────────────────

def update_project(project_id, update_payload, token=None):
    """Update an existing project."""
    url = UPDATE_PROJECT_URL.format(project_id=project_id)
    response = requests.put(
        url,
        json=update_payload,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Update project %s → %s", project_id, response.status_code)
    return response


# ─────────────────────────────────────────────
# 5. Delete Project
#    DELETE /api/v1/projects/{project_id}
# ─────────────────────────────────────────────

def delete_project(project_id, token=None):
    """Delete a project by ID."""
    url = DELETE_PROJECT_URL.format(project_id=project_id)
    response = requests.delete(
        url,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Delete project %s → %s", project_id, response.status_code)
    return response


# ─────────────────────────────────────────────
# 6. Archive Project
#    POST /api/v1/projects/{project_id}/archive
# ─────────────────────────────────────────────

def archive_project(project_id, token=None):
    """Archive a project by ID."""
    url = ARCHIVE_PROJECT_URL.format(project_id=project_id)
    response = requests.post(
        url,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Archive project %s → %s", project_id, response.status_code)
    return response


# ─────────────────────────────────────────────
# 7. Unarchive Project
#    POST /api/v1/projects/{project_id}/unarchive
# ─────────────────────────────────────────────

def unarchive_project(project_id, token=None):
    """Unarchive a project by ID."""
    url = UNARCHIVE_PROJECT_URL.format(project_id=project_id)
    response = requests.post(
        url,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Unarchive project %s → %s", project_id, response.status_code)
    return response


# ─────────────────────────────────────────────
# 8. Download Project Export
#    GET /api/v1/projects/{project_id}/download
# ─────────────────────────────────────────────

def download_project(project_id, token=None):
    """Download project export."""
    url = DOWNLOAD_PROJECT_URL.format(project_id=project_id)
    response = requests.get(
        url,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Download project %s → %s", project_id, response.status_code)
    return response


# ─────────────────────────────────────────────
# 9. List Project Members
#    GET /api/v1/project_members/projects/{project_id}/members
# ─────────────────────────────────────────────

def list_members(project_id, token=None):
    """List all members of a project."""
    url = LIST_MEMBERS_URL.format(project_id=project_id)
    response = requests.get(
        url,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("List members project=%s → %s", project_id, response.status_code)
    return response


# ─────────────────────────────────────────────
# 10. Add Project Member
#     POST /api/v1/project_members/projects/{project_id}/members
# ─────────────────────────────────────────────

def add_member(project_id, username, token=None):
    """Add a member to a project."""
    url = ADD_MEMBER_URL.format(project_id=project_id)
    response = requests.post(
        url,
        json={"username": username},
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Add member '%s' project=%s → %s", username, project_id, response.status_code)
    return response


# ─────────────────────────────────────────────
# 11. Get Project Member
#     GET /api/v1/project_members/projects/{project_id}/members/{username}
# ─────────────────────────────────────────────

def get_member(project_id, username, token=None):
    """Get a specific member of a project."""
    url = GET_MEMBER_URL.format(project_id=project_id, username=username)
    response = requests.get(
        url,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Get member '%s' project=%s → %s", username, project_id, response.status_code)
    return response


# ─────────────────────────────────────────────
# 12. Delete Project Member
#     DELETE /api/v1/project_members/projects/{project_id}/members/{username}
# ─────────────────────────────────────────────

def delete_member(project_id, username, token=None):
    """Remove a member from a project."""
    url = DELETE_MEMBER_URL.format(project_id=project_id, username=username)
    response = requests.delete(
        url,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Delete member '%s' project=%s → %s", username, project_id, response.status_code)
    return response


# ─────────────────────────────────────────────
# 13. Add Project Member As Admin
#     POST /api/v1/project_members/projects/{project_id}/members/{username}/admin
# ─────────────────────────────────────────────

def add_member_as_admin(project_id, username, token=None):
    """Promote a project member to admin."""
    url = ADD_ADMIN_MEMBER_URL.format(project_id=project_id, username=username)
    response = requests.post(
        url,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Add admin '%s' project=%s → %s", username, project_id, response.status_code)
    return response


# ─────────────────────────────────────────────
# 14. Get Pinned Projects
#     GET /api/v1/user/pinned/projects
# ─────────────────────────────────────────────

def get_pinned_projects(token=None):
    """Get all pinned projects for the current user."""
    response = requests.get(
        GET_PINNED_PROJECTS_URL,
        params={"username": NCP_USERNAME},
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Get pinned projects → %s", response.status_code)
    return response


# ─────────────────────────────────────────────
# 15. Pin Project
#     PUT /api/v1/user/pinned/projects/{project_id}
# ─────────────────────────────────────────────

def pin_project(project_id, token=None):
    """Pin a project for the current user."""
    url = PIN_PROJECT_URL.format(project_id=project_id)
    response = requests.put(
        url,
        params={"username": NCP_USERNAME},
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Pin project %s → %s", project_id, response.status_code)
    return response


# ─────────────────────────────────────────────
# 16. Unpin Project
#     DELETE /api/v1/user/pinned/projects/{project_id}
# ─────────────────────────────────────────────

def unpin_project(project_id, token=None):
    """Unpin a project for the current user."""
    url = UNPIN_PROJECT_URL.format(project_id=project_id)
    response = requests.delete(
        url,
        params={"username": NCP_USERNAME},
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Unpin project %s → %s", project_id, response.status_code)
    return response


# ─────────────────────────────────────────────
# 17. Export All Conversations
#     GET /api/v1/conversations/all/export
# ─────────────────────────────────────────────

def export_all_conversations(token=None):
    """Export all conversations."""
    response = requests.get(
        EXPORT_ALL_CONVERSATIONS_URL,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Export all conversations → %s", response.status_code)
    return response


# ─────────────────────────────────────────────
# 18. User Feedback By Qa Id
#     POST /api/v1/conversations/{qa_id}/user_feedback
# ─────────────────────────────────────────────

def post_user_feedback(qa_id, message, token=None):
    """Submit user feedback for a QA pair."""
    url = USER_FEEDBACK_URL.format(qa_id=qa_id)
    response = requests.post(
        url,
        json={"message": message},
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Post user feedback qa_id=%s → %s", qa_id, response.status_code)
    return response


# ─────────────────────────────────────────────
# 19. Archive Conversation
#     POST /api/v1/conversations/{conversation_id}/archive
# ─────────────────────────────────────────────

def archive_conversation(conversation_id, token=None):
    """Archive a conversation."""
    url = ARCHIVE_CONVERSATION_URL.format(conversation_id=conversation_id)
    response = requests.post(
        url,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Archive conversation %s → %s", conversation_id, response.status_code)
    return response


# ─────────────────────────────────────────────
# 20. Get Archived Conversations
#     GET /api/v1/conversations/archived_conversations
# ─────────────────────────────────────────────

def get_archived_conversations(token=None):
    """Get all archived conversations."""
    response = requests.get(
        GET_ARCHIVED_CONVERSATIONS_URL,
        params={"username": NCP_USERNAME},
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Get archived conversations → %s", response.status_code)
    return response


# ─────────────────────────────────────────────
# 21. Unarchive Conversation
#     POST /api/v1/conversations/{conversation_id}/unarchive
# ─────────────────────────────────────────────

def unarchive_conversation(conversation_id, token=None):
    """Unarchive a conversation."""
    url = UNARCHIVE_CONVERSATION_URL.format(conversation_id=conversation_id)
    response = requests.post(
        url,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Unarchive conversation %s → %s", conversation_id, response.status_code)
    return response


# ─────────────────────────────────────────────
# 22. Export Conversation By Id
#     GET /api/v1/conversations/{conversation_id}/export
# ─────────────────────────────────────────────

def export_conversation(conversation_id, file_format="txt", token=None):
    """Export a specific conversation."""
    url = EXPORT_CONVERSATION_URL.format(conversation_id=conversation_id)
    response = requests.get(
        url,
        params={"file_format": file_format},
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Export conversation %s → %s", conversation_id, response.status_code)
    return response


# ─────────────────────────────────────────────
# 23. Get All Conversations By Project Id
#     GET /api/v1/conversations/all/{project_id}
# ─────────────────────────────────────────────

def get_conversations_by_project(project_id, token=None):
    """Get all conversations for a project."""
    url = GET_CONVERSATIONS_BY_PROJECT_URL.format(project_id=project_id)
    response = requests.get(
        url,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Get conversations project=%s → %s", project_id, response.status_code)
    return response


# ─────────────────────────────────────────────
# 24. Get Pinned Chats
#     GET /api/v1/user/pinned/chats/{username}
# ─────────────────────────────────────────────

def get_pinned_chats(token=None):
    """Get all pinned chats for the current user."""
    url = GET_PINNED_CHATS_URL.format(username=NCP_USERNAME)
    response = requests.get(
        url,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Get pinned chats → %s", response.status_code)
    return response


# ─────────────────────────────────────────────
# 25. Pin Chat
#     PUT /api/v1/user/pinned/chats/{chat_id}
# ─────────────────────────────────────────────

def pin_chat(chat_id, token=None):
    """Pin a chat for the current user."""
    url = PIN_CHAT_URL.format(chat_id=chat_id)
    response = requests.put(
        url,
        params={"username": NCP_USERNAME},
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Pin chat %s → %s", chat_id, response.status_code)
    return response


# ─────────────────────────────────────────────
# 26. Unpin Chat
#     DELETE /api/v1/user/pinned/chats/{chat_id}
# ─────────────────────────────────────────────

def unpin_chat(chat_id, token=None):
    """Unpin a chat for the current user."""
    url = UNPIN_CHAT_URL.format(chat_id=chat_id)
    response = requests.delete(
        url,
        params={"username": NCP_USERNAME},
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Unpin chat %s → %s", chat_id, response.status_code)
    return response


# ─────────────────────────────────────────────
# 27. Get User Preferences
#     GET /api/v1/user_preferences?user_id={user_id}
# ─────────────────────────────────────────────

def get_user_preferences(user_id, token=None):
    """Get user preferences by user_id."""
    response = requests.get(
        GET_USER_PREFERENCES_URL,
        params={"user_id": user_id},
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Get user preferences user_id=%s → %s", user_id, response.status_code)
    return response


# ─────────────────────────────────────────────
# 28. Create User Preferences
#     POST /api/v1/user_preferences
# ─────────────────────────────────────────────

def create_user_preferences(user_id, notifications, token=None):
    """Create user preferences."""
    payload = {"user_id": user_id, "notifications": notifications}
    response = requests.post(
        CREATE_USER_PREFERENCES_URL,
        json=payload,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Create user preferences user_id=%s → %s", user_id, response.status_code)
    return response


# ─────────────────────────────────────────────
# 29. Update User Preferences
#     PUT /api/v1/user_preferences/{user_id}
# ─────────────────────────────────────────────

def update_user_preferences(user_id, notifications, token=None):
    """Update user preferences by user_id."""
    url = UPDATE_USER_PREFERENCES_URL.format(user_id=user_id)
    payload = {"notifications": notifications}
    response = requests.put(
        url,
        json=payload,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Update user preferences user_id=%s → %s", user_id, response.status_code)
    return response


# ─────────────────────────────────────────────
# DATA CONNECTORS APIs
# ─────────────────────────────────────────────

def validate_data_connector(payload, token=None):
    """Validate a data connector payload."""
    response = requests.post(
        VALIDATE_DATA_CONNECTOR_URL,
        json=payload,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Validate data connector → %s", response.status_code)
    return response

def create_data_connector(payload, token=None):
    """Create a new data connector."""
    response = requests.post(
        CREATE_DATA_CONNECTOR_URL,
        json=payload,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Create data connector → %s", response.status_code)
    return response

def get_all_data_connectors(token=None):
    """Get all data connectors."""
    response = requests.get(
        GET_ALL_DATA_CONNECTORS_URL,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Get all data connectors → %s", response.status_code)
    return response

def get_data_connector(connector_id, token=None):
    """Get a specific data connector."""
    url = GET_DATA_CONNECTOR_URL.format(connector_id=connector_id)
    response = requests.get(
        url,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Get data connector %s → %s", connector_id, response.status_code)
    return response

def update_data_connector(connector_id, payload, token=None):
    """Update a data connector."""
    url = UPDATE_DATA_CONNECTOR_URL.format(connector_id=connector_id)
    response = requests.put(
        url,
        json=payload,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Update data connector %s → %s", connector_id, response.status_code)
    return response

def deactivate_data_connector(connector_id, token=None):
    """Deactivate a data connector."""
    url = DEACTIVATE_DATA_CONNECTOR_URL.format(connector_id=connector_id)
    response = requests.post(
        url,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Deactivate data connector %s → %s", connector_id, response.status_code)
    return response

def activate_data_connector(connector_id, token=None):
    """Activate a data connector."""
    url = ACTIVATE_DATA_CONNECTOR_URL.format(connector_id=connector_id)
    response = requests.post(
        url,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Activate data connector %s → %s", connector_id, response.status_code)
    return response

def delete_data_connector(connector_id, token=None):
    """Delete a data connector."""
    url = DELETE_DATA_CONNECTOR_URL.format(connector_id=connector_id)
    response = requests.delete(
        url,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Delete data connector %s → %s", connector_id, response.status_code)
    return response

# ================================
# PROJECT DATA CONNECTORS APIS
# ================================

def get_project_data_connectors(project_id, token=None):
    url = GET_PROJECT_DATA_CONNECTORS_URL.format(project_id=project_id)
    response = requests.get(url, headers=_auth_headers(token), verify=VERIFY_SSL)
    logger.info("Get project data connectors %s → %s", project_id, response.status_code)
    return response

def link_project_data_connector(project_id, data_connector_id, payload=None, token=None):
    url = LINK_PROJECT_DATA_CONNECTOR_URL.format(project_id=project_id, data_connector_id=data_connector_id)
    if payload is None:
        payload = {"enabled": True}
    response = requests.put(url, json=payload, headers=_auth_headers(token), verify=VERIFY_SSL)
    logger.info("Link project dataconnector %s<->%s → %s", project_id, data_connector_id, response.status_code)
    return response

def unlink_project_data_connector(project_id, data_connector_id, token=None):
    url = UNLINK_PROJECT_DATA_CONNECTOR_URL.format(project_id=project_id, data_connector_id=data_connector_id)
    response = requests.delete(url, headers=_auth_headers(token), verify=VERIFY_SSL)
    logger.info("Unlink project dataconnector %s<->%s → %s", project_id, data_connector_id, response.status_code)
    return response

def get_project_data_connector_tags(project_id, token=None):
    url = GET_PROJECT_DATA_CONNECTOR_TAGS_URL.format(project_id=project_id)
    response = requests.get(url, headers=_auth_headers(token), verify=VERIFY_SSL)
    logger.info("Get project %s data connector tags → %s", project_id, response.status_code)
    return response

def get_data_connector_projects(data_connector_id, token=None):
    url = GET_DATA_CONNECTOR_PROJECTS_URL.format(data_connector_id=data_connector_id)
    response = requests.get(url, headers=_auth_headers(token), verify=VERIFY_SSL)
    logger.info("Get dataconnector %s projects → %s", data_connector_id, response.status_code)
    return response




def create_llm_config(payload, token=None):
    """Create a new LLM configuration."""
    response = requests.post(
        CREATE_LLM_CONFIG_URL,
        json=payload,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Create LLM config → %s", response.status_code)
    return response
 
 
def get_all_llm_configs(token=None):
    """List all LLM configurations."""
    response = requests.get(
        GET_ALL_LLM_CONFIGS_URL,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Get all LLM configs → %s", response.status_code)
    return response
 
 
def get_llm_config(config_id, token=None):
    """Read a single LLM configuration by ID."""
    url = GET_LLM_CONFIG_URL.format(config_id=config_id)
    response = requests.get(
        url,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Get LLM config %s → %s", config_id, response.status_code)
    return response
 
 
def update_llm_config(config_id, payload, token=None):
    """Update an existing LLM configuration."""
    url = UPDATE_LLM_CONFIG_URL.format(config_id=config_id)
    response = requests.put(
        url,
        json=payload,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Update LLM config %s → %s", config_id, response.status_code)
    return response
 
 
def delete_llm_config(config_id, token=None):
    """Delete an LLM configuration by ID."""
    url = DELETE_LLM_CONFIG_URL.format(config_id=config_id)
    response = requests.delete(
        url,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Delete LLM config %s → %s", config_id, response.status_code)
    return response

# ─────────────────────────────────────────────
# ROLES AND PERMISSIONS APIs
# ─────────────────────────────────────────────

def get_all_roles(token=None):
    """Get all roles."""
    response = requests.get(
        GET_ALL_ROLES_URL,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Get all roles → %s", response.status_code)
    return response


def create_role(payload, token=None):
    """Create a new role."""
    response = requests.post(
        CREATE_ROLE_URL,
        json=payload,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Create role → %s", response.status_code)
    return response


def get_role(role_id, token=None):
    """Get a single role by ID."""
    url = GET_ROLE_URL.format(role_id=role_id)
    response = requests.get(
        url,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Get role %s → %s", role_id, response.status_code)
    return response


def update_role(role_id, payload, token=None):
    """Update a role by ID."""
    url = UPDATE_ROLE_URL.format(role_id=role_id)
    response = requests.put(
        url,
        json=payload,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Update role %s → %s", role_id, response.status_code)
    return response


def delete_role(role_id, token=None):
    """Delete a role by ID."""
    url = DELETE_ROLE_URL.format(role_id=role_id)
    response = requests.delete(
        url,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Delete role %s → %s", role_id, response.status_code)
    return response


def get_custom_agents(token=None):
    """Get all custom agents."""
    response = requests.get(
        GET_CUSTOM_AGENTS_URL,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Get custom agents → %s", response.status_code)
    return response


def reassign_users(to_role_id, body_payload, token=None):
    """Reassign users to a different role.
    
    Args:
        to_role_id: integer query param — target role ID
        body_payload: list of {entity_name, entity_type, entity_id}
    """
    response = requests.post(
        REASSIGN_USERS_URL,
        params={"to_role_id": to_role_id},
        json=body_payload,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Reassign users to_role_id=%s → %s", to_role_id, response.status_code)
    return response


def get_role_by_username(username, token=None):
    """Get role assigned to a specific username."""
    url = GET_ROLE_BY_USERNAME_URL.format(username=username)
    response = requests.get(
        url,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Get role by username=%s → %s", username, response.status_code)
    return response


def get_users_by_role(role_id, token=None):
    """Get all users assigned to a specific role."""
    url = GET_USERS_BY_ROLE_URL.format(role_id=role_id)
    response = requests.get(
        url,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Get users by role_id=%s → %s", role_id, response.status_code)
    return response


def get_llms_by_role(role_id, token=None):
    """Get all LLMs assigned to a specific role."""
    url = GET_LLMS_BY_ROLE_URL.format(role_id=role_id)
    response = requests.get(
        url,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Get LLMs by role_id=%s → %s", role_id, response.status_code)
    return response


def get_data_connectors_by_role(role_id, token=None):
    """Get all data connectors assigned to a specific role."""
    url = GET_DATA_CONNECTORS_BY_ROLE_URL.format(role_id=role_id)
    response = requests.get(
        url,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Get data connectors by role_id=%s → %s", role_id, response.status_code)
    return response


def get_files_by_role(role_id, token=None):
    """Get all files assigned to a specific role."""
    url = GET_FILES_BY_ROLE_URL.format(role_id=role_id)
    response = requests.get(
        url,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Get files by role_id=%s → %s", role_id, response.status_code)
    return response


def get_devices_by_role(role_id, token=None):
    """Get all devices assigned to a specific role."""
    url = GET_DEVICES_BY_ROLE_URL.format(role_id=role_id)
    response = requests.get(
        url,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Get devices by role_id=%s → %s", role_id, response.status_code)
    return response


def get_custom_agents_by_role(role_id, token=None):
    """Get all custom agents assigned to a specific role."""
    url = GET_CUSTOM_AGENTS_BY_ROLE_URL.format(role_id=role_id)
    response = requests.get(
        url,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Get custom agents by role_id=%s → %s", role_id, response.status_code)
    return response


# ─────────────────────────────────────────────
# LDAP CONFIGURATIONS APIs
# ─────────────────────────────────────────────

def get_all_ldap_configs(token=None):
    """Get all LDAP configurations."""
    response = requests.get(
        GET_ALL_LDAP_CONFIGS_URL,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Get all LDAP configs → %s", response.status_code)
    return response


def create_ldap_config(payload, token=None):
    """Create a new LDAP configuration."""
    response = requests.post(
        CREATE_LDAP_CONFIG_URL,
        json=payload,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Create LDAP config → %s", response.status_code)
    return response


def get_ldap_config(config_id, token=None):
    """Get a single LDAP configuration by ID."""
    url = GET_LDAP_CONFIG_URL.format(config_id=config_id)
    response = requests.get(
        url,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Get LDAP config %s → %s", config_id, response.status_code)
    return response


def update_ldap_config(config_id, payload, token=None):
    """Update an existing LDAP configuration."""
    url = UPDATE_LDAP_CONFIG_URL.format(config_id=config_id)
    response = requests.put(
        url,
        json=payload,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Update LDAP config %s → %s", config_id, response.status_code)
    return response


def delete_ldap_config(config_id, token=None):
    """Delete an LDAP configuration by ID."""
    url = DELETE_LDAP_CONFIG_URL.format(config_id=config_id)
    response = requests.delete(
        url,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Delete LDAP config %s → %s", config_id, response.status_code)
    return response




import os
import requests
import mimetypes
from config import (
    UPLOAD_KB_FILE_URL,
    NCP_USERNAME,
    VERIFY_SSL
)

def upload_knowledge_base_file(file_path, token=None):
    """
    Upload a file to the knowledge base.
    Uses multipart/form-data.
    """

    mime_type, _ = mimetypes.guess_type(file_path)
    if not mime_type:
        mime_type = "application/octet-stream"

    # Remove Content-Type so requests sets multipart boundary
    auth_headers = _auth_headers(token)
    headers = {
        k: v for k, v in auth_headers.items()
        if k.lower() != "content-type"
    }
    headers["Accept"] = "application/json"

    with open(file_path, "rb") as f:
        files = {
            "file": (os.path.basename(file_path), f, mime_type)
        }
        params = {
            "username": NCP_USERNAME
        }

        response = requests.post(
            UPLOAD_KB_FILE_URL,
            headers=headers,
            files=files,
            params=params,
            verify=VERIFY_SSL,
        )

    logger.info(
        "Upload KB file '%s' → %s",
        os.path.basename(file_path),
        response.status_code
    )

    return response
 
 
def get_knowledge_base_files(username, token=None):
    """Get all knowledge base files for a given username."""
    url = GET_KB_FILES_URL.format(username=username)
    response = requests.get(
        url,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Get KB files for username='%s' → %s", username, response.status_code)
    return response
 
 
def update_knowledge_base_file(username, file_id, payload, token=None):
    """Update the description of a knowledge base file."""
    url = UPDATE_KB_FILE_URL.format(username=username, id=file_id)
    response = requests.put(
        url,
        json=payload,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info(
        "Update KB file id=%s for username='%s' → %s",
        file_id, username, response.status_code,
    )
    return response
 
 
def delete_knowledge_base_file(username, file_id, token=None):
    """Delete a knowledge base file by username and file id."""
    url = DELETE_KB_FILE_URL.format(username=username, id=file_id)
    response = requests.delete(
        url,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info(
        "Delete KB file id=%s for username='%s' → %s",
        file_id, username, response.status_code,
    )
    return response


# ─────────────────────────────────────────────
# DASHBOARD APIs
# ─────────────────────────────────────────────

def get_dashboard_metrics(range_type=None, from_ts=None, to_ts=None,
                          granularity=None, token=None):
    """Get dashboard metrics with optional time range and granularity filters."""
    params = {}
    if range_type:
        params["range_type"] = range_type
    if from_ts:
        params["from_ts"] = from_ts
    if to_ts:
        params["to_ts"] = to_ts
    if granularity:
        params["granularity"] = granularity

    response = requests.get(
        GET_DASHBOARD_METRICS_URL,
        params=params,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Get dashboard metrics → %s", response.status_code)
    return response


def get_system_metrics(start_time=None, end_time=None, token=None):
    """Get system metrics (CPU/memory/disk time-series) with optional time range."""
    params = {}
    if start_time:
        params["start_time"] = start_time
    if end_time:
        params["end_time"] = end_time

    response = requests.get(
        GET_SYSTEM_METRICS_URL,
        params=params,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Get system metrics → %s", response.status_code)
    return response


def get_gpu_metrics(llm_name, start_time=None, end_time=None, token=None):
    """Get GPU metrics for a given LLM model, with optional time range."""
    params = {"llm_name": llm_name}
    if start_time:
        params["start_time"] = start_time
    if end_time:
        params["end_time"] = end_time

    response = requests.get(
        GET_GPU_METRICS_URL,
        params=params,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Get GPU metrics (llm_name=%s) → %s", llm_name, response.status_code)
    return response


def get_docker_stats(limit=None, token=None):
    """Get the latest docker stats for tabular display, with an optional row limit."""
    params = {}
    if limit is not None:
        params["limit"] = limit

    response = requests.get(
        GET_DOCKER_STATS_URL,
        params=params,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Get docker stats (limit=%s) → %s", limit, response.status_code)
    return response


def generate_logs(token=None):
    """Trigger asynchronous log generation (reads from the local docker daemon)."""
    response = requests.post(
        GENERATE_LOGS_URL,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Generate logs → %s", response.status_code)
    return response


def download_logs(log_id, token=None):
    """Download the zipped docker logs for a given log_id (returns raw bytes response)."""
    url = DOWNLOAD_LOGS_URL.format(log_id=log_id)
    headers = _auth_headers(token)
    headers.pop("Accept", None)
    response = requests.get(
        url,
        headers=headers,
        verify=VERIFY_SSL,
        stream=True,
    )
    logger.info("Download logs log_id=%s → %s", log_id, response.status_code)
    return response


def list_logs(token=None):
    """List all log archives."""
    response = requests.get(
        LIST_LOGS_URL,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("List logs → %s", response.status_code)
    return response


# ─────────────────────────────────────────────
# ROCKETCHAT CONFIGURATION APIs
# ─────────────────────────────────────────────

def get_all_rocketchat_configs(token=None):
    """Get all Rocketchat configurations."""
    response = requests.get(
        GET_ALL_ROCKETCHAT_CONFIGS_URL,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Get all Rocketchat configs → %s", response.status_code)
    return response


def create_rocketchat_config(payload, token=None):
    """Create a new Rocketchat configuration."""
    response = requests.post(
        CREATE_ROCKETCHAT_CONFIG_URL,
        json=payload,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Create Rocketchat config → %s", response.status_code)
    return response


def get_rocketchat_config(config_id, token=None):
    """Get a single Rocketchat configuration by ID."""
    url = GET_ROCKETCHAT_CONFIG_URL.format(config_id=config_id)
    response = requests.get(
        url,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Get Rocketchat config %s → %s", config_id, response.status_code)
    return response


def delete_rocketchat_config(config_id, token=None):
    """Delete a Rocketchat configuration by ID."""
    url = DELETE_ROCKETCHAT_CONFIG_URL.format(config_id=config_id)
    response = requests.delete(
        url,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Delete Rocketchat config %s → %s", config_id, response.status_code)
    return response


# ─────────────────────────────────────────────
# PROJECT FILES APIs
# ─────────────────────────────────────────────

def list_project_files(project_id, token=None):
    """List all files in a project."""
    url = LIST_PROJECT_FILES_URL.format(project_id=project_id)
    response = requests.get(
        url,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("List project files project_id=%s → %s", project_id, response.status_code)
    return response


def get_project_file(project_id, file_id, token=None):
    """Get metadata for a single project file."""
    url = GET_PROJECT_FILE_URL.format(project_id=project_id, file_id=file_id)
    response = requests.get(
        url,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Get project file project_id=%s file_id=%s → %s",
                project_id, file_id, response.status_code)
    return response


def update_project_file(project_id, file_id, payload, token=None):
    """Update metadata for a project file."""
    url = UPDATE_PROJECT_FILE_URL.format(project_id=project_id, file_id=file_id)
    response = requests.put(
        url,
        json=payload,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Update project file project_id=%s file_id=%s → %s",
                project_id, file_id, response.status_code)
    return response


def download_project_file(project_id, file_id, token=None):
    """Download a project file (returns raw bytes response)."""
    url = DOWNLOAD_PROJECT_FILE_URL.format(project_id=project_id, file_id=file_id)
    headers = _auth_headers(token)
    headers.pop("Accept", None)
    response = requests.get(
        url,
        headers=headers,
        verify=VERIFY_SSL,
        stream=True,
    )
    logger.info("Download project file project_id=%s file_id=%s → %s",
                project_id, file_id, response.status_code)
    return response


# ─────────────────────────────────────────────
# ADMIN FILES APIs
# ─────────────────────────────────────────────

def list_admin_files(role_id=None, token=None):
    """List all admin files, optionally filtered by role_id."""
    params = {}
    if role_id is not None:
        params["role_id"] = role_id
    response = requests.get(
        LIST_ADMIN_FILES_URL,
        params=params,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("List admin files role_id=%s → %s", role_id, response.status_code)
    return response


def get_admin_file(file_id, token=None):
    """Get metadata for a single admin file."""
    url = GET_ADMIN_FILE_URL.format(file_id=file_id)
    response = requests.get(
        url,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Get admin file file_id=%s → %s", file_id, response.status_code)
    return response


def update_admin_file(file_id, payload, token=None):
    """Update an admin file using PATCH."""
    url = UPDATE_ADMIN_FILE_URL.format(file_id=file_id)
    response = requests.patch(
        url,
        json=payload,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Update admin file file_id=%s → %s", file_id, response.status_code)
    return response


def download_admin_file(file_id, token=None):
    """Download an admin file (returns raw bytes response)."""
    url = DOWNLOAD_ADMIN_FILE_URL.format(file_id=file_id)
    headers = _auth_headers(token)
    headers.pop("Accept", None)
    response = requests.get(
        url,
        headers=headers,
        verify=VERIFY_SSL,
        stream=True,
    )
    logger.info("Download admin file file_id=%s → %s", file_id, response.status_code)
    return response


# ─────────────────────────────────────────────
# EXPORTS APIs
# ─────────────────────────────────────────────

def list_exports(project_id, username=None, export_format=None, status=None,
                 conversation_id=None, token=None):
    """List all exports for a project, with optional filters."""
    url = LIST_EXPORTS_URL.format(project_id=project_id)
    params = {}
    if username is not None:
        params["username"] = username
    if export_format is not None:
        params["export_format"] = export_format
    if status is not None:
        params["status"] = status
    if conversation_id is not None:
        params["conversation_id"] = conversation_id

    response = requests.get(
        url,
        params=params,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("List exports project_id=%s → %s", project_id, response.status_code)
    return response


def get_export(project_id, export_id, token=None):
    """Get metadata for a specific export."""
    url = GET_EXPORT_URL.format(project_id=project_id, export_id=export_id)
    response = requests.get(
        url,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Get export project_id=%s export_id=%s → %s",
                project_id, export_id, response.status_code)
    return response


def download_export(project_id, export_id, token=None):
    """Download an exported file (returns raw bytes response)."""
    url = DOWNLOAD_EXPORT_URL.format(project_id=project_id, export_id=export_id)
    headers = _auth_headers(token)
    headers.pop("Accept", None)
    response = requests.get(
        url,
        headers=headers,
        verify=VERIFY_SSL,
        stream=True,
    )
    logger.info("Download export project_id=%s export_id=%s → %s",
                project_id, export_id, response.status_code)
    return response


def preview_export(project_id, export_id, token=None):
    """Get a preview of the first few rows of an exported file."""
    url = PREVIEW_EXPORT_URL.format(project_id=project_id, export_id=export_id)
    response = requests.get(
        url,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Preview export project_id=%s export_id=%s → %s",
                project_id, export_id, response.status_code)
    return response


def list_conversation_exports(conversation_id, token=None):
    """List all exports generated within a specific conversation."""
    url = LIST_CONVERSATION_EXPORTS_URL.format(conversation_id=conversation_id)
    response = requests.get(
        url,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("List conversation exports conversation_id=%s → %s",
                conversation_id, response.status_code)
    return response


def download_user_export(export_id, token=None):
    """Download an exported file by export_id (exports without a project scope)."""
    url = DOWNLOAD_USER_EXPORT_URL.format(export_id=export_id)
    headers = _auth_headers(token)
    headers.pop("Accept", None)
    response = requests.get(
        url,
        headers=headers,
        verify=VERIFY_SSL,
        stream=True,
    )
    logger.info("Download user export export_id=%s → %s", export_id, response.status_code)
    return response


def preview_user_export(export_id, token=None):
    """Get a preview of an exported file by export_id (no project scope)."""
    url = PREVIEW_USER_EXPORT_URL.format(export_id=export_id)
    response = requests.get(
        url,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Preview user export export_id=%s → %s", export_id, response.status_code)
    return response


def delete_export(project_id, export_id, token=None):
    """Delete an exported file (file + DB record)."""
    url = DELETE_EXPORT_URL.format(project_id=project_id, export_id=export_id)
    response = requests.delete(
        url,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Delete export project_id=%s export_id=%s → %s",
                project_id, export_id, response.status_code)
    return response


# ─────────────────────────────────────────────
# PLATFORM AGENTS APIs
# ─────────────────────────────────────────────

def get_platform_agents(token=None):
    """List all platform agents with their tool schemas (agent catalog)."""
    response = requests.get(
        LIST_PLATFORM_AGENTS_URL,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("List platform agents → %s", response.status_code)
    return response


def execute_platform_agent(agent_name, query, project_id=None, token=None, timeout=300):
    """Execute a platform agent with a query and return the result.

    Agent execution can be long-running (e.g. live device collection), so a
    generous request timeout is applied by default.
    """
    url = EXECUTE_PLATFORM_AGENT_URL.format(agent_name=agent_name)
    payload = {"query": query}
    if project_id is not None:
        payload["project_id"] = project_id

    response = requests.post(
        url,
        json=payload,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
        timeout=timeout,
    )
    logger.info("Execute platform agent '%s' → %s", agent_name, response.status_code)
    return response


# ─────────────────────────────────────────────
# BACKGROUND JOBS
# ─────────────────────────────────────────────

def preview_cron(cron_expression, timezone="UTC", token=None):
    """Validate a CRON expression and return the next 5 fire times.

    Used by the Job Creation wizard's "Schedule" step so the user can sanity
    check the schedule before submitting.
    """
    payload = {"cron_expression": cron_expression, "timezone": timezone}

    response = requests.post(
        PREVIEW_CRON_URL,
        json=payload,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info(
        "Preview cron '%s' (%s) → %s",
        cron_expression, timezone, response.status_code,
    )
    return response


def can_create_background_job(token=None):
    """Whether the caller's role can create / trigger background jobs.

    Used by the FE to gate the "Schedule a job" entry points. Returns true for
    admins, "Power user", and any custom role with can_create_background_job=true.
    """
    response = requests.get(
        CAN_CREATE_BG_JOB_URL,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Can create background job → %s", response.status_code)
    return response


def create_background_job(project_id, agent_name, prompt, cron_expression,
                          name, timezone="UTC", notification_channels=None,
                          slack_channel_ids=None, token=None):
    """Create a recurring background job.

    Validates the agent + CRON + project membership, persists the row, then
    registers the schedule in redbeat. Same code path the LLM tool uses.
    """
    payload = {
        "project_id":      project_id,
        "agent_name":      agent_name,
        "prompt":          prompt,
        "cron_expression": cron_expression,
        "timezone":        timezone,
        "name":            name,
    }
    if notification_channels is not None:
        payload["notification_channels"] = notification_channels
    if slack_channel_ids is not None:
        payload["slack_channel_ids"] = slack_channel_ids

    response = requests.post(
        CREATE_BG_JOB_URL,
        json=payload,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info(
        "Create background job '%s' (project_id=%s, agent=%s) → %s",
        name, project_id, agent_name, response.status_code,
    )
    return response


def list_background_jobs(project_id, mine_only=True, include_removed=False, token=None):
    """List background jobs in a project.

    By default returns only the caller's jobs. Pass mine_only=False to see all
    jobs in the project (project-admin / Admin Console views).
    """
    params = {
        "project_id":      project_id,
        "mine_only":       mine_only,
        "include_removed": include_removed,
    }
    response = requests.get(
        LIST_BG_JOBS_URL,
        params=params,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info(
        "List background jobs (project_id=%s, mine_only=%s, include_removed=%s) → %s",
        project_id, mine_only, include_removed, response.status_code,
    )
    return response


def admin_list_all_background_jobs(include_removed=False, token=None):
    """List every background job across all projects (with project names).

    Role-aware: admins see every job in the system; non-admins see only the
    jobs they created across every project they belong to.
    """
    params = {"include_removed": include_removed}
    response = requests.get(
        ADMIN_ALL_BG_JOBS_URL,
        params=params,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info(
        "Admin list all background jobs (include_removed=%s) → %s",
        include_removed, response.status_code,
    )
    return response


def update_background_job(job_id, name=None, prompt=None, agent_name=None,
                          trigger_type=None, cron_expression=None, timezone=None,
                          notification_channels=None, slack_channel_ids=None,
                          token=None):
    """Edit an existing background job (partial update).

    Only fields passed here are sent in the body and modified. If trigger_type
    or cron_expression changes, the redbeat schedule is updated automatically.
    """
    payload = {}
    if name is not None:                  payload["name"] = name
    if prompt is not None:                payload["prompt"] = prompt
    if agent_name is not None:            payload["agent_name"] = agent_name
    if trigger_type is not None:          payload["trigger_type"] = trigger_type
    if cron_expression is not None:       payload["cron_expression"] = cron_expression
    if timezone is not None:              payload["timezone"] = timezone
    if notification_channels is not None: payload["notification_channels"] = notification_channels
    if slack_channel_ids is not None:     payload["slack_channel_ids"] = slack_channel_ids

    url = UPDATE_BG_JOB_URL.format(job_id=job_id)
    response = requests.patch(
        url,
        json=payload,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info(
        "Update background job '%s' (fields=%s) → %s",
        job_id, list(payload.keys()), response.status_code,
    )
    return response


def get_background_job(job_id, token=None):
    """Fetch a single background job. Accessible to any member of its project."""
    url = GET_BG_JOB_URL.format(job_id=job_id)
    response = requests.get(
        url,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Get background job '%s' → %s", job_id, response.status_code)
    return response


def run_background_job_now(job_id, token=None):
    """Trigger an immediate one-off run of an existing job.

    Enqueues the same Celery task the CRON schedule fires. Valid for both
    scheduled and manual jobs; a removed job is not runnable.
    """
    url = RUN_BG_JOB_NOW_URL.format(job_id=job_id)
    response = requests.post(
        url,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Run background job now '%s' → %s", job_id, response.status_code)
    return response


def pause_background_job(job_id, token=None):
    """Pause an active job — unregisters the redbeat entry (DB row preserved).

    No-op if the job is already paused.
    """
    url = PAUSE_BG_JOB_URL.format(job_id=job_id)
    response = requests.post(
        url,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Pause background job '%s' → %s", job_id, response.status_code)
    return response


def resume_background_job(job_id, token=None):
    """Resume a paused job — re-registers it in redbeat using its stored cron.

    No-op if the job is already active.
    """
    url = RESUME_BG_JOB_URL.format(job_id=job_id)
    response = requests.post(
        url,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Resume background job '%s' → %s", job_id, response.status_code)
    return response


def list_background_job_runs(job_id, token=None):
    """List a job's runs and basic aggregates (execution history + stat cards)."""
    url = LIST_BG_JOB_RUNS_URL.format(job_id=job_id)
    response = requests.get(
        url,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("List background job runs '%s' → %s", job_id, response.status_code)
    return response


def get_background_job_run(job_id, message_id, token=None):
    """Fetch a single run's metadata and output (Run Detail screen).

    message_id is the id of the assistant message that holds the run's card and
    output — the same handle returned by list_background_job_runs.
    """
    url = GET_BG_JOB_RUN_URL.format(job_id=job_id, message_id=message_id)
    response = requests.get(
        url,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info(
        "Get background job run '%s'/%s → %s",
        job_id, message_id, response.status_code,
    )
    return response


def delete_background_job(job_id, token=None):
    """Permanently remove a job.

    Unregisters the schedule, marks the job row removed (soft delete for audit),
    and hard-deletes the result conversation.
    """
    url = DELETE_BG_JOB_URL.format(job_id=job_id)
    response = requests.delete(
        url,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Delete background job '%s' → %s", job_id, response.status_code)
    return response


# ─────────────────────────────────────────────
# CUSTOM AGENTS
# ─────────────────────────────────────────────

def onboard_custom_agent(file_path, update=None, token=None):
    """Onboard a custom agent from a .ncp package (admin-only).

    Uses multipart/form-data. Pass `update` (an existing agent name) to update
    that agent instead of creating a new one.
    """
    mime_type, _ = mimetypes.guess_type(file_path)
    if not mime_type:
        mime_type = "application/octet-stream"

    # Remove Content-Type so requests sets the multipart boundary.
    auth_headers = _auth_headers(token)
    headers = {
        k: v for k, v in auth_headers.items()
        if k.lower() != "content-type"
    }
    headers["Accept"] = "application/json"

    params = {}
    if update is not None:
        params["update"] = update

    with open(file_path, "rb") as f:
        files = {"file": (os.path.basename(file_path), f, mime_type)}
        response = requests.post(
            ONBOARD_CUSTOM_AGENT_URL,
            headers=headers,
            files=files,
            params=params,
            verify=VERIFY_SSL,
        )

    logger.info(
        "Onboard custom agent '%s' (update=%s) → %s",
        os.path.basename(file_path), update, response.status_code,
    )
    return response


def list_custom_agents(token=None):
    """List all custom agents (admin-only)."""
    response = requests.get(
        LIST_CUSTOM_AGENTS_URL,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("List custom agents → %s", response.status_code)
    return response


def list_background_eligible_agents(token=None):
    """List custom agents eligible for background scheduling (all active agents)."""
    response = requests.get(
        BG_ELIGIBLE_AGENTS_URL,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("List background-eligible custom agents → %s", response.status_code)
    return response


def get_custom_agent(agent_name, token=None):
    """Get details of a custom agent by name (admin-only)."""
    url = GET_CUSTOM_AGENT_URL.format(agent_name=agent_name)
    response = requests.get(
        url,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Get custom agent '%s' → %s", agent_name, response.status_code)
    return response


def disable_custom_agent(agent_name, token=None):
    """Disable a custom agent (admin-only) — not loaded into the orchestrator."""
    url = DISABLE_CUSTOM_AGENT_URL.format(agent_name=agent_name)
    response = requests.post(
        url,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Disable custom agent '%s' → %s", agent_name, response.status_code)
    return response


def enable_custom_agent(agent_name, token=None):
    """Enable a disabled custom agent (admin-only)."""
    url = ENABLE_CUSTOM_AGENT_URL.format(agent_name=agent_name)
    response = requests.post(
        url,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Enable custom agent '%s' → %s", agent_name, response.status_code)
    return response


def enable_custom_agent_background(agent_name, token=None):
    """Allow a custom agent to be scheduled as a background job (admin-only)."""
    url = ENABLE_BG_CUSTOM_AGENT_URL.format(agent_name=agent_name)
    response = requests.post(
        url,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info(
        "Enable custom agent background '%s' → %s", agent_name, response.status_code,
    )
    return response


def disable_custom_agent_background(agent_name, token=None):
    """Revoke a custom agent's background-scheduling eligibility (admin-only).

    Does NOT touch existing scheduled jobs — those fail at their next fire.
    """
    url = DISABLE_BG_CUSTOM_AGENT_URL.format(agent_name=agent_name)
    response = requests.post(
        url,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info(
        "Disable custom agent background '%s' → %s", agent_name, response.status_code,
    )
    return response


def admin_list_custom_agents(token=None):
    """List all custom agents for admin (ACTIVE / PENDING / REJECTED)."""
    response = requests.get(
        ADMIN_LIST_CUSTOM_AGENTS_URL,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Admin list custom agents → %s", response.status_code)
    return response


def get_my_custom_agents(token=None):
    """Get custom agents submitted by the authenticated user."""
    response = requests.get(
        MY_CUSTOM_AGENTS_URL,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Get my custom agents → %s", response.status_code)
    return response


def submit_custom_agent(file_path, token=None):
    """Upload/submit a new custom agent (role-aware).

    Uses multipart/form-data. Admin submissions go straight to ACTIVE; regular
    users' submissions land in PENDING (awaiting admin approval).
    """
    mime_type, _ = mimetypes.guess_type(file_path)
    if not mime_type:
        mime_type = "application/octet-stream"

    # Remove Content-Type so requests sets the multipart boundary.
    auth_headers = _auth_headers(token)
    headers = {
        k: v for k, v in auth_headers.items()
        if k.lower() != "content-type"
    }
    headers["Accept"] = "application/json"

    with open(file_path, "rb") as f:
        files = {"file": (os.path.basename(file_path), f, mime_type)}
        response = requests.post(
            SUBMIT_CUSTOM_AGENT_URL,
            headers=headers,
            files=files,
            verify=VERIFY_SSL,
        )

    logger.info(
        "Submit custom agent '%s' → %s",
        os.path.basename(file_path), response.status_code,
    )
    return response


def update_custom_agent_version(agent_id, file_path, token=None):
    """Upload a new version of an existing custom agent (multipart/form-data)."""
    mime_type, _ = mimetypes.guess_type(file_path)
    if not mime_type:
        mime_type = "application/octet-stream"

    # Remove Content-Type so requests sets the multipart boundary.
    auth_headers = _auth_headers(token)
    headers = {
        k: v for k, v in auth_headers.items()
        if k.lower() != "content-type"
    }
    headers["Accept"] = "application/json"

    url = UPDATE_CUSTOM_AGENT_VERSION_URL.format(agent_id=agent_id)
    with open(file_path, "rb") as f:
        files = {"file": (os.path.basename(file_path), f, mime_type)}
        response = requests.post(
            url,
            headers=headers,
            files=files,
            verify=VERIFY_SSL,
        )

    logger.info(
        "Update custom agent version id=%s ('%s') → %s",
        agent_id, os.path.basename(file_path), response.status_code,
    )
    return response


def approve_custom_agent(agent_id, token=None):
    """Approve a custom agent (admin-only) — extracts it to the runtime dir."""
    url = APPROVE_CUSTOM_AGENT_URL.format(agent_id=agent_id)
    response = requests.post(
        url,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Approve custom agent id=%s → %s", agent_id, response.status_code)
    return response


def decline_custom_agent(agent_id, feedback=None, token=None):
    """Decline a custom agent (admin-only) with optional feedback."""
    url = DECLINE_CUSTOM_AGENT_URL.format(agent_id=agent_id)
    payload = {}
    if feedback is not None:
        payload["feedback"] = feedback

    response = requests.post(
        url,
        json=payload,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Decline custom agent id=%s → %s", agent_id, response.status_code)
    return response


def submit_custom_agent_feedback(agent_id, message, feedback_type=None, token=None):
    """Submit feedback for a custom agent (admin-only)."""
    url = FEEDBACK_CUSTOM_AGENT_URL.format(agent_id=agent_id)
    payload = {"message": message}
    if feedback_type is not None:
        payload["feedback_type"] = feedback_type

    response = requests.post(
        url,
        json=payload,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Feedback custom agent id=%s → %s", agent_id, response.status_code)
    return response


def download_custom_agent(agent_id, token=None):
    """Download a custom agent's .ncp package (admin and owner). Returns bytes."""
    url = DOWNLOAD_CUSTOM_AGENT_URL.format(agent_id=agent_id)
    response = requests.get(
        url,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info(
        "Download custom agent id=%s → %s (%s bytes)",
        agent_id, response.status_code, len(response.content),
    )
    return response


def can_submit_custom_agent(token=None):
    """Check whether the caller can submit a new custom agent."""
    response = requests.get(
        CAN_SUBMIT_AGENT_URL,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Can submit custom agent → %s", response.status_code)
    return response


def remove_custom_agent(agent_name, token=None):
    """Remove a custom agent by name (admin-only)."""
    url = DELETE_CUSTOM_AGENT_URL.format(agent_name=agent_name)
    response = requests.delete(
        url,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Remove custom agent '%s' → %s", agent_name, response.status_code)
    return response


def remove_user_custom_agent(agent_name, allow_force_delete=None, token=None):
    """Remove a custom agent (user-scoped) by name.

    Pass allow_force_delete=True to force removal even when the agent is still
    referenced elsewhere (e.g. by background jobs).
    """
    url = DELETE_USER_CUSTOM_AGENT_URL.format(agent_name=agent_name)
    params = {}
    if allow_force_delete is not None:
        params["allow_force_delete"] = allow_force_delete

    response = requests.delete(
        url,
        params=params,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info(
        "Remove user custom agent '%s' (force=%s) → %s",
        agent_name, allow_force_delete, response.status_code,
    )
    return response


# ─────────────────────────────────────────────
# ORGANIZATIONS
# ─────────────────────────────────────────────

def list_organizations(token=None):
    """List all organizations (returns a JSON array)."""
    response = requests.get(
        LIST_ORGANIZATIONS_URL,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("List organizations → %s", response.status_code)
    return response


def create_organization(name, description=None, usernames=None, token=None):
    """Create a new organization."""
    payload = {"name": name}
    if description is not None:
        payload["description"] = description
    if usernames is not None:
        payload["usernames"] = usernames

    response = requests.post(
        CREATE_ORGANIZATION_URL,
        json=payload,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Create organization '%s' → %s", name, response.status_code)
    return response


def update_organization(org_id, name=None, description=None, is_active=None, token=None):
    """Update an organization (PUT). Only provided fields are sent."""
    payload = {}
    if name is not None:        payload["name"] = name
    if description is not None: payload["description"] = description
    if is_active is not None:   payload["is_active"] = is_active

    url = UPDATE_ORGANIZATION_URL.format(org_id=org_id)
    response = requests.put(
        url,
        json=payload,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Update organization id=%s → %s", org_id, response.status_code)
    return response


def assign_users_to_organization(org_id, usernames, token=None):
    """Assign one or more users to an organization (replaces their current org)."""
    url = ASSIGN_ORG_USERS_URL.format(org_id=org_id)
    response = requests.patch(
        url,
        json={"usernames": usernames},
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info(
        "Assign users %s to organization id=%s → %s",
        usernames, org_id, response.status_code,
    )
    return response


def get_organization_users(org_id, token=None):
    """List all users assigned to an organization (returns a JSON array)."""
    url = GET_ORG_USERS_URL.format(org_id=org_id)
    response = requests.get(
        url,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Get organization users id=%s → %s", org_id, response.status_code)
    return response


def deactivate_organization(org_id, token=None):
    """Soft-delete (deactivate) an organization."""
    url = DEACTIVATE_ORGANIZATION_URL.format(org_id=org_id)
    response = requests.patch(
        url,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Deactivate organization id=%s → %s", org_id, response.status_code)
    return response


def delete_organization(org_id, token=None):
    """Hard-delete (permanently remove) an organization.

    Fails with 400 if any users are still associated — reassign them first.
    """
    url = DELETE_ORGANIZATION_URL.format(org_id=org_id)
    response = requests.delete(
        url,
        headers=_auth_headers(token),
        verify=VERIFY_SSL,
    )
    logger.info("Delete organization id=%s → %s", org_id, response.status_code)
    return response