







"""
NCP Projects API - Configuration
"""

'''# =========================
# NCP BASE CONFIG
# =========================
NCP_FRONTEND_URL = "https://10.4.5.10"
NCP_LOGIN_URL = f"{NCP_FRONTEND_URL}/api/user/login"

NCP_BASE_URL = "https://10.4.5.10:9001"

NCP_USERNAME = "superadmin"
NCP_PASSWORD = "Admin@123"

VERIFY_SSL = False

# =========================
# PROJECT API ENDPOINTS
# =========================
CREATE_PROJECT_URL = f"{NCP_BASE_URL}/api/v1/projects"
GET_PROJECTS_URL = f"{NCP_BASE_URL}/api/v1/projects"
GET_PROJECT_URL = f"{NCP_BASE_URL}/api/v1/projects/{{project_id}}"
UPDATE_PROJECT_URL = f"{NCP_BASE_URL}/api/v1/projects/{{project_id}}"
DELETE_PROJECT_URL = f"{NCP_BASE_URL}/api/v1/projects/{{project_id}}"
ARCHIVE_PROJECT_URL = f"{NCP_BASE_URL}/api/v1/projects/{{project_id}}/archive"
UNARCHIVE_PROJECT_URL = f"{NCP_BASE_URL}/api/v1/projects/{{project_id}}/unarchive"
DOWNLOAD_PROJECT_URL = f"{NCP_BASE_URL}/api/v1/projects/{{project_id}}/download"

# =========================
# PROJECT MEMBER API ENDPOINTS
# =========================
LIST_MEMBERS_URL     = f"{NCP_BASE_URL}/api/v1/project_members/projects/{{project_id}}/members"
ADD_MEMBER_URL       = f"{NCP_BASE_URL}/api/v1/project_members/projects/{{project_id}}/members"
GET_MEMBER_URL       = f"{NCP_BASE_URL}/api/v1/project_members/projects/{{project_id}}/members/{{username}}"
DELETE_MEMBER_URL    = f"{NCP_BASE_URL}/api/v1/project_members/projects/{{project_id}}/members/{{username}}"
ADD_ADMIN_MEMBER_URL = f"{NCP_BASE_URL}/api/v1/project_members/projects/{{project_id}}/members/{{username}}/admin"

TEST_MEMBER_USERNAME = "admin"

# =========================
# PINNED PROJECTS API ENDPOINTS
# =========================
GET_PINNED_PROJECTS_URL = f"{NCP_BASE_URL}/api/v1/user/pinned/projects"
PIN_PROJECT_URL         = f"{NCP_BASE_URL}/api/v1/user/pinned/projects/{{project_id}}"
UNPIN_PROJECT_URL       = f"{NCP_BASE_URL}/api/v1/user/pinned/projects/{{project_id}}"

# =========================
# USER PREFERENCES API ENDPOINTS
# =========================
GET_USER_PREFERENCES_URL    = f"{NCP_BASE_URL}/api/v1/user_preferences"
CREATE_USER_PREFERENCES_URL = f"{NCP_BASE_URL}/api/v1/user_preferences"
UPDATE_USER_PREFERENCES_URL = f"{NCP_BASE_URL}/api/v1/user_preferences/{{user_id}}"

# user_id for superadmin preferences (from Swagger: user_id="3")
TEST_USER_PREF_USER_ID = "3"

# =========================
# PINNED CHATS API ENDPOINTS
# =========================
GET_PINNED_CHATS_URL = f"{NCP_BASE_URL}/api/v1/user/pinned/chats/{{username}}"
PIN_CHAT_URL         = f"{NCP_BASE_URL}/api/v1/user/pinned/chats/{{chat_id}}"
UNPIN_CHAT_URL       = f"{NCP_BASE_URL}/api/v1/user/pinned/chats/{{chat_id}}"

# Fixed test chat_id — conversation_id=5 from response
TEST_CHAT_ID = 5

# =========================
# CONVERSATION API ENDPOINTS
# =========================
EXPORT_ALL_CONVERSATIONS_URL  = f"{NCP_BASE_URL}/api/v1/conversations/all/export"
USER_FEEDBACK_URL             = f"{NCP_BASE_URL}/api/v1/conversations/{{qa_id}}/user_feedback"
ARCHIVE_CONVERSATION_URL      = f"{NCP_BASE_URL}/api/v1/conversations/{{conversation_id}}/archive"
GET_ARCHIVED_CONVERSATIONS_URL= f"{NCP_BASE_URL}/api/v1/conversations/archived_conversations"
UNARCHIVE_CONVERSATION_URL    = f"{NCP_BASE_URL}/api/v1/conversations/{{conversation_id}}/unarchive"
EXPORT_CONVERSATION_URL       = f"{NCP_BASE_URL}/api/v1/conversations/{{conversation_id}}/export"
GET_CONVERSATIONS_BY_PROJECT_URL = f"{NCP_BASE_URL}/api/v1/conversations/all/{{project_id}}"

# Fixed test IDs — conversations cannot be created via API
TEST_CONVERSATION_ID = 8
TEST_QA_ID           = 19
# Project that actually contains TEST_CONVERSATION_ID (from archived response: project_id=2)
TEST_CONVERSATION_PROJECT_ID = 2

# =========================
# DATA CONNECTORS API ENDPOINTS
# =========================
CREATE_DATA_CONNECTOR_URL = f"{NCP_BASE_URL}/api/v1/data_connectors"
GET_ALL_DATA_CONNECTORS_URL = f"{NCP_BASE_URL}/api/v1/data_connectors"
GET_DATA_CONNECTOR_URL    = f"{NCP_BASE_URL}/api/v1/data_connectors/{{connector_id}}"
UPDATE_DATA_CONNECTOR_URL = f"{NCP_BASE_URL}/api/v1/data_connectors/{{connector_id}}"
DELETE_DATA_CONNECTOR_URL = f"{NCP_BASE_URL}/api/v1/data_connectors/{{connector_id}}"
DEACTIVATE_DATA_CONNECTOR_URL = f"{NCP_BASE_URL}/api/v1/data_connectors/{{connector_id}}/deactivate"
ACTIVATE_DATA_CONNECTOR_URL   = f"{NCP_BASE_URL}/api/v1/data_connectors/{{connector_id}}/activate"
VALIDATE_DATA_CONNECTOR_URL   = f"{NCP_BASE_URL}/api/v1/data_connectors/validate"

# =========================
# PROJECT DATA CONNECTORS ENDPOINTS
# =========================
GET_PROJECT_DATA_CONNECTORS_URL = f"{NCP_BASE_URL}/api/v1/projects/{{project_id}}/data_connectors"
LINK_PROJECT_DATA_CONNECTOR_URL = f"{NCP_BASE_URL}/api/v1/projects/{{project_id}}/data_connectors/{{data_connector_id}}"
UNLINK_PROJECT_DATA_CONNECTOR_URL = f"{NCP_BASE_URL}/api/v1/projects/{{project_id}}/data_connectors/{{data_connector_id}}"
GET_PROJECT_DATA_CONNECTOR_TAGS_URL = f"{NCP_BASE_URL}/api/v1/projects/{{project_id}}/data_connector_tags"
GET_DATA_CONNECTOR_PROJECTS_URL = f"{NCP_BASE_URL}/api/v1/data_connectors/{{data_connector_id}}/projects"

# =========================
# LLM CONFIGURATIONS API ENDPOINTS
# =========================
CREATE_LLM_CONFIG_URL   = f"{NCP_BASE_URL}/api/v1/llm-configs"
GET_ALL_LLM_CONFIGS_URL = f"{NCP_BASE_URL}/api/v1/llm-configs"
GET_LLM_CONFIG_URL      = f"{NCP_BASE_URL}/api/v1/llm-configs/{{config_id}}"
UPDATE_LLM_CONFIG_URL   = f"{NCP_BASE_URL}/api/v1/llm-configs/{{config_id}}"
DELETE_LLM_CONFIG_URL   = f"{NCP_BASE_URL}/api/v1/llm-configs/{{config_id}}"

# =========================
# ROLES AND PERMISSIONS API ENDPOINTS
# =========================
GET_ALL_ROLES_URL             = f"{NCP_BASE_URL}/api/v1/roles_and_permissions"
CREATE_ROLE_URL               = f"{NCP_BASE_URL}/api/v1/roles_and_permissions"
GET_ROLE_URL                  = f"{NCP_BASE_URL}/api/v1/roles_and_permissions/{{role_id}}"
UPDATE_ROLE_URL               = f"{NCP_BASE_URL}/api/v1/roles_and_permissions/{{role_id}}"
DELETE_ROLE_URL               = f"{NCP_BASE_URL}/api/v1/roles_and_permissions/{{role_id}}"
GET_CUSTOM_AGENTS_URL         = f"{NCP_BASE_URL}/api/v1/roles_and_permissions/custom_agents"
REASSIGN_USERS_URL            = f"{NCP_BASE_URL}/api/v1/roles_and_permissions/reassign_users/"
GET_ROLE_BY_USERNAME_URL      = f"{NCP_BASE_URL}/api/v1/roles_and_permissions/get_role_by_username/{{username}}"
GET_USERS_BY_ROLE_URL         = f"{NCP_BASE_URL}/api/v1/roles_and_permissions/get_users_by_role/{{role_id}}"

# Stable test values for read-only role endpoints
TEST_ROLE_ID       = 1        # existing role used for get_users_by_role
TEST_ROLE_USERNAME = "superadmin"   # used for get_role_by_username
TEST_REASSIGN_TO_ROLE_ID = 2  # to_role_id query param for reassign_users

# =========================
# COMMON HEADERS
# =========================
DEFAULT_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
}

# =========================
# TEST DATA - Update with valid project_id from your NCP
# =========================
TEST_PROJECT_ID = "3"

# =========================
# LOGGING
# =========================
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"'''


"""
NCP Projects API - Configuration
"""

# =========================
# NCP BASE CONFIG
# =========================
NCP_FRONTEND_URL = "https://10.4.5.10"
NCP_LOGIN_URL = f"{NCP_FRONTEND_URL}/api/user/login"

NCP_BASE_URL = "https://10.4.5.10:9001"

NCP_USERNAME = "superadmin"
NCP_PASSWORD = "Admin@123"

VERIFY_SSL = False

# =========================
# PROJECT API ENDPOINTS
# =========================
CREATE_PROJECT_URL = f"{NCP_BASE_URL}/api/v1/projects"
GET_PROJECTS_URL = f"{NCP_BASE_URL}/api/v1/projects"
GET_PROJECT_URL = f"{NCP_BASE_URL}/api/v1/projects/{{project_id}}"
UPDATE_PROJECT_URL = f"{NCP_BASE_URL}/api/v1/projects/{{project_id}}"
DELETE_PROJECT_URL = f"{NCP_BASE_URL}/api/v1/projects/{{project_id}}"
ARCHIVE_PROJECT_URL = f"{NCP_BASE_URL}/api/v1/projects/{{project_id}}/archive"
UNARCHIVE_PROJECT_URL = f"{NCP_BASE_URL}/api/v1/projects/{{project_id}}/unarchive"
DOWNLOAD_PROJECT_URL = f"{NCP_BASE_URL}/api/v1/projects/{{project_id}}/download"

# =========================
# PROJECT MEMBER API ENDPOINTS
# =========================
LIST_MEMBERS_URL     = f"{NCP_BASE_URL}/api/v1/project_members/projects/{{project_id}}/members"
ADD_MEMBER_URL       = f"{NCP_BASE_URL}/api/v1/project_members/projects/{{project_id}}/members"
GET_MEMBER_URL       = f"{NCP_BASE_URL}/api/v1/project_members/projects/{{project_id}}/members/{{username}}"
DELETE_MEMBER_URL    = f"{NCP_BASE_URL}/api/v1/project_members/projects/{{project_id}}/members/{{username}}"
ADD_ADMIN_MEMBER_URL = f"{NCP_BASE_URL}/api/v1/project_members/projects/{{project_id}}/members/{{username}}/admin"

TEST_MEMBER_USERNAME = "admin"

# =========================
# PINNED PROJECTS API ENDPOINTS
# =========================
GET_PINNED_PROJECTS_URL = f"{NCP_BASE_URL}/api/v1/user/pinned/projects"
PIN_PROJECT_URL         = f"{NCP_BASE_URL}/api/v1/user/pinned/projects/{{project_id}}"
UNPIN_PROJECT_URL       = f"{NCP_BASE_URL}/api/v1/user/pinned/projects/{{project_id}}"

# =========================
# USER PREFERENCES API ENDPOINTS
# =========================
GET_USER_PREFERENCES_URL    = f"{NCP_BASE_URL}/api/v1/user_preferences"
CREATE_USER_PREFERENCES_URL = f"{NCP_BASE_URL}/api/v1/user_preferences"
UPDATE_USER_PREFERENCES_URL = f"{NCP_BASE_URL}/api/v1/user_preferences/{{user_id}}"

# user_id for superadmin preferences (from Swagger: user_id="3")
TEST_USER_PREF_USER_ID = "3"

# =========================
# PINNED CHATS API ENDPOINTS
# =========================
GET_PINNED_CHATS_URL = f"{NCP_BASE_URL}/api/v1/user/pinned/chats/{{username}}"
PIN_CHAT_URL         = f"{NCP_BASE_URL}/api/v1/user/pinned/chats/{{chat_id}}"
UNPIN_CHAT_URL       = f"{NCP_BASE_URL}/api/v1/user/pinned/chats/{{chat_id}}"

# Fixed test chat_id — conversation_id=5 from response
TEST_CHAT_ID = 5

# =========================
# CONVERSATION API ENDPOINTS
# =========================
EXPORT_ALL_CONVERSATIONS_URL  = f"{NCP_BASE_URL}/api/v1/conversations/all/export"
USER_FEEDBACK_URL             = f"{NCP_BASE_URL}/api/v1/conversations/{{qa_id}}/user_feedback"
ARCHIVE_CONVERSATION_URL      = f"{NCP_BASE_URL}/api/v1/conversations/{{conversation_id}}/archive"
GET_ARCHIVED_CONVERSATIONS_URL= f"{NCP_BASE_URL}/api/v1/conversations/archived_conversations"
UNARCHIVE_CONVERSATION_URL    = f"{NCP_BASE_URL}/api/v1/conversations/{{conversation_id}}/unarchive"
EXPORT_CONVERSATION_URL       = f"{NCP_BASE_URL}/api/v1/conversations/{{conversation_id}}/export"
GET_CONVERSATIONS_BY_PROJECT_URL = f"{NCP_BASE_URL}/api/v1/conversations/all/{{project_id}}"

# Fixed test IDs — conversations cannot be created via API
TEST_CONVERSATION_ID = 8
TEST_QA_ID           = 19
# Project that actually contains TEST_CONVERSATION_ID (from archived response: project_id=2)
TEST_CONVERSATION_PROJECT_ID = 2

# =========================
# DATA CONNECTORS API ENDPOINTS
# =========================
CREATE_DATA_CONNECTOR_URL = f"{NCP_BASE_URL}/api/v1/data_connectors"
GET_ALL_DATA_CONNECTORS_URL = f"{NCP_BASE_URL}/api/v1/data_connectors"
GET_DATA_CONNECTOR_URL    = f"{NCP_BASE_URL}/api/v1/data_connectors/{{connector_id}}"
UPDATE_DATA_CONNECTOR_URL = f"{NCP_BASE_URL}/api/v1/data_connectors/{{connector_id}}"
DELETE_DATA_CONNECTOR_URL = f"{NCP_BASE_URL}/api/v1/data_connectors/{{connector_id}}"
DEACTIVATE_DATA_CONNECTOR_URL = f"{NCP_BASE_URL}/api/v1/data_connectors/{{connector_id}}/deactivate"
ACTIVATE_DATA_CONNECTOR_URL   = f"{NCP_BASE_URL}/api/v1/data_connectors/{{connector_id}}/activate"
VALIDATE_DATA_CONNECTOR_URL   = f"{NCP_BASE_URL}/api/v1/data_connectors/validate"

# =========================
# PROJECT DATA CONNECTORS ENDPOINTS
# =========================
GET_PROJECT_DATA_CONNECTORS_URL = f"{NCP_BASE_URL}/api/v1/projects/{{project_id}}/data_connectors"
LINK_PROJECT_DATA_CONNECTOR_URL = f"{NCP_BASE_URL}/api/v1/projects/{{project_id}}/data_connectors/{{data_connector_id}}"
UNLINK_PROJECT_DATA_CONNECTOR_URL = f"{NCP_BASE_URL}/api/v1/projects/{{project_id}}/data_connectors/{{data_connector_id}}"
GET_PROJECT_DATA_CONNECTOR_TAGS_URL = f"{NCP_BASE_URL}/api/v1/projects/{{project_id}}/data_connector_tags"
GET_DATA_CONNECTOR_PROJECTS_URL = f"{NCP_BASE_URL}/api/v1/data_connectors/{{data_connector_id}}/projects"

# =========================
# LLM CONFIGURATIONS API ENDPOINTS
# =========================
CREATE_LLM_CONFIG_URL   = f"{NCP_BASE_URL}/api/v1/llm-configs"
GET_ALL_LLM_CONFIGS_URL = f"{NCP_BASE_URL}/api/v1/llm-configs"
GET_LLM_CONFIG_URL      = f"{NCP_BASE_URL}/api/v1/llm-configs/{{config_id}}"
UPDATE_LLM_CONFIG_URL   = f"{NCP_BASE_URL}/api/v1/llm-configs/{{config_id}}"
DELETE_LLM_CONFIG_URL   = f"{NCP_BASE_URL}/api/v1/llm-configs/{{config_id}}"

# =========================
# LDAP CONFIGURATIONS API ENDPOINTS
# =========================
GET_ALL_LDAP_CONFIGS_URL = f"{NCP_BASE_URL}/api/v1/ldap-configs"
CREATE_LDAP_CONFIG_URL   = f"{NCP_BASE_URL}/api/v1/ldap-configs"
GET_LDAP_CONFIG_URL      = f"{NCP_BASE_URL}/api/v1/ldap-configs/{{config_id}}"
UPDATE_LDAP_CONFIG_URL   = f"{NCP_BASE_URL}/api/v1/ldap-configs/{{config_id}}"
DELETE_LDAP_CONFIG_URL   = f"{NCP_BASE_URL}/api/v1/ldap-configs/{{config_id}}"

# =========================
# ROLES AND PERMISSIONS API ENDPOINTS
# =========================
GET_ALL_ROLES_URL             = f"{NCP_BASE_URL}/api/v1/roles_and_permissions"
CREATE_ROLE_URL               = f"{NCP_BASE_URL}/api/v1/roles_and_permissions"
GET_ROLE_URL                  = f"{NCP_BASE_URL}/api/v1/roles_and_permissions/{{role_id}}"
UPDATE_ROLE_URL               = f"{NCP_BASE_URL}/api/v1/roles_and_permissions/{{role_id}}"
DELETE_ROLE_URL               = f"{NCP_BASE_URL}/api/v1/roles_and_permissions/{{role_id}}"
GET_CUSTOM_AGENTS_URL         = f"{NCP_BASE_URL}/api/v1/roles_and_permissions/custom_agents"
REASSIGN_USERS_URL            = f"{NCP_BASE_URL}/api/v1/roles_and_permissions/reassign_users/"
GET_ROLE_BY_USERNAME_URL      = f"{NCP_BASE_URL}/api/v1/roles_and_permissions/get_role_by_username/{{username}}"
GET_USERS_BY_ROLE_URL         = f"{NCP_BASE_URL}/api/v1/roles_and_permissions/get_users_by_role/{{role_id}}"
GET_LLMS_BY_ROLE_URL            = f"{NCP_BASE_URL}/api/v1/roles_and_permissions/llms/{{role_id}}"
GET_DATA_CONNECTORS_BY_ROLE_URL = f"{NCP_BASE_URL}/api/v1/roles_and_permissions/data_connectors/{{role_id}}"
GET_FILES_BY_ROLE_URL           = f"{NCP_BASE_URL}/api/v1/roles_and_permissions/files/{{role_id}}"
GET_DEVICES_BY_ROLE_URL         = f"{NCP_BASE_URL}/api/v1/roles_and_permissions/devices/{{role_id}}"
GET_CUSTOM_AGENTS_BY_ROLE_URL   = f"{NCP_BASE_URL}/api/v1/roles_and_permissions/custom_agents/{{role_id}}"

# Stable test values for read-only role endpoints
TEST_ROLE_ID       = 19       # existing role used for get_users_by_role and detail endpoints
TEST_ROLE_USERNAME = "koushik"      # used for get_role_by_username
TEST_REASSIGN_TO_ROLE_ID = 2  # to_role_id query param for reassign_users

# =========================
# COMMON HEADERS
# =========================
DEFAULT_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
}

# =========================
# TEST DATA - Update with valid project_id from your NCP
# =========================
TEST_PROJECT_ID = "3"

# =========================
# LOGGING
# =========================
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"


# =========================
# KNOWLEDGE BASE API ENDPOINTS
# =========================
UPLOAD_KB_FILE_URL      = f"{NCP_BASE_URL}/api/v1/knowledge_base/upload"
GET_KB_FILES_URL        = f"{NCP_BASE_URL}/api/v1/knowledge_base/files/{{username}}"
UPDATE_KB_FILE_URL      = f"{NCP_BASE_URL}/api/v1/knowledge_base/files/{{username}}/{{id}}"
DELETE_KB_FILE_URL      = f"{NCP_BASE_URL}/api/v1/knowledge_base/files/{{username}}/{{id}}"

# =========================
# DASHBOARD API ENDPOINTS
# =========================
GET_DASHBOARD_METRICS_URL = f"{NCP_BASE_URL}/api/v1/dashboard/metrics"

# =========================
# ROCKETCHAT CONFIGURATION API ENDPOINTS
# =========================
GET_ALL_ROCKETCHAT_CONFIGS_URL = f"{NCP_BASE_URL}/api/v1/rocketchat-configuration"
CREATE_ROCKETCHAT_CONFIG_URL   = f"{NCP_BASE_URL}/api/v1/rocketchat-configuration"
GET_ROCKETCHAT_CONFIG_URL      = f"{NCP_BASE_URL}/api/v1/rocketchat-configuration/{{config_id}}"
DELETE_ROCKETCHAT_CONFIG_URL   = f"{NCP_BASE_URL}/api/v1/rocketchat-configuration/{{config_id}}"

TEST_ROCKETCHAT_SERVER_URL = "http://10.4.4.33:7777"
TEST_ROCKETCHAT_ROOM_NAME  = "NCP-KOUSHIK"
TEST_ROCKETCHAT_USERNAME   = "sai.koushik"
TEST_ROCKETCHAT_PASSWORD   = "Admin@123"

# =========================
# PROJECT FILES API ENDPOINTS
# =========================
LIST_PROJECT_FILES_URL    = f"{NCP_BASE_URL}/api/v1/projects/{{project_id}}/files"
GET_PROJECT_FILE_URL      = f"{NCP_BASE_URL}/api/v1/projects/{{project_id}}/files/{{file_id}}"
UPDATE_PROJECT_FILE_URL   = f"{NCP_BASE_URL}/api/v1/projects/{{project_id}}/files/{{file_id}}"
DOWNLOAD_PROJECT_FILE_URL = f"{NCP_BASE_URL}/api/v1/projects/{{project_id}}/files/{{file_id}}/download"

TEST_PROJECT_FILES_PROJECT_ID = 229
TEST_PROJECT_FILE_ID          = 6

# =========================
# ADMIN FILES API ENDPOINTS
# =========================
LIST_ADMIN_FILES_URL    = f"{NCP_BASE_URL}/api/v1/admin/files"
GET_ADMIN_FILE_URL      = f"{NCP_BASE_URL}/api/v1/admin/files/{{file_id}}"
UPDATE_ADMIN_FILE_URL   = f"{NCP_BASE_URL}/api/v1/admin/files/{{file_id}}"
DOWNLOAD_ADMIN_FILE_URL = f"{NCP_BASE_URL}/api/v1/admin/files/{{file_id}}/download"

TEST_ADMIN_FILE_ID       = 1
TEST_ADMIN_FILES_ROLE_ID = 19