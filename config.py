# =========================
# NCP BASE CONFIG
# =========================
NCP_FRONTEND_URL = "https://10.4.5.10"
NCP_LOGIN_URL = f"{NCP_FRONTEND_URL}/api/user/login"

NCP_BASE_URL = "https://10.4.5.10"

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
GET_SYSTEM_METRICS_URL    = f"{NCP_BASE_URL}/api/v1/dashboard/metrics/system"
GET_GPU_METRICS_URL       = f"{NCP_BASE_URL}/api/v1/dashboard/metrics/gpu"
GET_DOCKER_STATS_URL      = f"{NCP_BASE_URL}/api/v1/dashboard/metrics/docker"
GENERATE_LOGS_URL         = f"{NCP_BASE_URL}/api/v1/dashboard/logs/generate"
DOWNLOAD_LOGS_URL         = f"{NCP_BASE_URL}/api/v1/dashboard/logs/download/{{log_id}}"
LIST_LOGS_URL             = f"{NCP_BASE_URL}/api/v1/dashboard/logs/list"

# Dashboard test data
TEST_GPU_LLM_NAME     = "gpt-oss-120b"   # llm_name filter for GPU metrics (DB03)
TEST_DOCKER_STATS_LIMIT = 100            # row limit for docker stats (DB04)
TEST_LOG_ID             = 1              # existing log_id to download (DB06)

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

TEST_PROJECT_FILES_PROJECT_ID = 12
TEST_PROJECT_FILE_ID          = 3

# =========================
# ADMIN FILES API ENDPOINTS
# =========================
LIST_ADMIN_FILES_URL    = f"{NCP_BASE_URL}/api/v1/admin/files"
GET_ADMIN_FILE_URL      = f"{NCP_BASE_URL}/api/v1/admin/files/{{file_id}}"
UPDATE_ADMIN_FILE_URL   = f"{NCP_BASE_URL}/api/v1/admin/files/{{file_id}}"
DOWNLOAD_ADMIN_FILE_URL = f"{NCP_BASE_URL}/api/v1/admin/files/{{file_id}}/download"

# role_id filter returns only files explicitly scoped to a role; an
# "everyone"-access file is listed only when no role_id filter is applied, so
# leave role_id None to list all admin files.
TEST_ADMIN_FILE_ID       = 7
TEST_ADMIN_FILES_ROLE_ID = None

# =========================
# EXPORTS API ENDPOINTS
# =========================
LIST_EXPORTS_URL = f"{NCP_BASE_URL}/api/v1/projects/{{project_id}}/exports"
GET_EXPORT_URL   = f"{NCP_BASE_URL}/api/v1/projects/{{project_id}}/exports/{{export_id}}"
DOWNLOAD_EXPORT_URL = f"{NCP_BASE_URL}/api/v1/projects/{{project_id}}/exports/{{export_id}}/download"
PREVIEW_EXPORT_URL  = f"{NCP_BASE_URL}/api/v1/projects/{{project_id}}/exports/{{export_id}}/preview"
LIST_CONVERSATION_EXPORTS_URL = f"{NCP_BASE_URL}/api/v1/conversations/{{conversation_id}}/exports"
DOWNLOAD_USER_EXPORT_URL = f"{NCP_BASE_URL}/api/v1/exports/{{export_id}}/download"
PREVIEW_USER_EXPORT_URL  = f"{NCP_BASE_URL}/api/v1/exports/{{export_id}}/preview"
DELETE_EXPORT_URL   = f"{NCP_BASE_URL}/api/v1/projects/{{project_id}}/exports/{{export_id}}"

# Test data — from List Exports sample response (project_id=2)
TEST_EXPORTS_PROJECT_ID     = 2
TEST_EXPORTS_USERNAME       = "superadmin"
TEST_EXPORT_FORMAT          = "csv"
TEST_EXPORT_STATUS          = "completed"
TEST_EXPORT_CONVERSATION_ID = 31
TEST_EXPORT_ID              = 6
# DELETE is destructive (removes file + DB record) and there is no create-export
# endpoint to recreate one — so point it at a DISPOSABLE export, separate from
# TEST_EXPORT_ID which the read/download/preview steps rely on. Update this to a
# fresh, throwaway export_id before each run.
TEST_EXPORT_DELETE_ID       = 5

# =========================
# PLATFORM AGENTS API ENDPOINTS
# =========================
LIST_PLATFORM_AGENTS_URL    = f"{NCP_BASE_URL}/api/v1/platform-agents"
EXECUTE_PLATFORM_AGENT_URL  = f"{NCP_BASE_URL}/api/v1/platform-agents/{{agent_name}}/execute"

# A known platform agent expected in the catalog (used for list verification)
TEST_PLATFORM_AGENT_NAME = "metrics_agent"

# Execute-agent test data. Defaults to a lightweight, deterministic query so the
# functional test is reliable. To exercise the live-SSH audit example from the
# spec instead, set:
#   TEST_EXECUTE_AGENT_NAME  = "audit_report_agent"
#   TEST_EXECUTE_AGENT_QUERY = "fetch live audit data for the device 10.4.6.11"
TEST_EXECUTE_AGENT_NAME       = "metrics_agent"
TEST_EXECUTE_AGENT_QUERY      = "How many devices are in the inventory?"
TEST_EXECUTE_AGENT_PROJECT_ID = 2

# =========================
# BACKGROUND JOBS API ENDPOINTS  (13 endpoints total)
# =========================
PREVIEW_CRON_URL       = f"{NCP_BASE_URL}/api/v1/background_jobs/cron/preview"
CAN_CREATE_BG_JOB_URL  = f"{NCP_BASE_URL}/api/v1/background_jobs/user/can-create"
CREATE_BG_JOB_URL      = f"{NCP_BASE_URL}/api/v1/background_jobs"
LIST_BG_JOBS_URL       = f"{NCP_BASE_URL}/api/v1/background_jobs"
ADMIN_ALL_BG_JOBS_URL  = f"{NCP_BASE_URL}/api/v1/background_jobs/admin/all"
UPDATE_BG_JOB_URL      = f"{NCP_BASE_URL}/api/v1/background_jobs/{{job_id}}"
GET_BG_JOB_URL         = f"{NCP_BASE_URL}/api/v1/background_jobs/{{job_id}}"
RUN_BG_JOB_NOW_URL     = f"{NCP_BASE_URL}/api/v1/background_jobs/{{job_id}}/run-now"
PAUSE_BG_JOB_URL       = f"{NCP_BASE_URL}/api/v1/background_jobs/{{job_id}}/pause"
RESUME_BG_JOB_URL      = f"{NCP_BASE_URL}/api/v1/background_jobs/{{job_id}}/resume"
LIST_BG_JOB_RUNS_URL   = f"{NCP_BASE_URL}/api/v1/background_jobs/{{job_id}}/runs"
GET_BG_JOB_RUN_URL     = f"{NCP_BASE_URL}/api/v1/background_jobs/{{job_id}}/runs/{{message_id}}"
DELETE_BG_JOB_URL      = f"{NCP_BASE_URL}/api/v1/background_jobs/{{job_id}}"

# Preview Cron test data — a valid CRON expression the wizard would validate.
TEST_CRON_EXPRESSION = "*/5 * * * *"
TEST_CRON_TIMEZONE   = "UTC"

# Can-create test data. superadmin is an admin, so the gate is expected to
# return true. Set to False when running the suite as a restricted role.
TEST_CAN_CREATE_BG_JOB_EXPECTED = True

# Create Background Job test data. agent_name / project_id / slack channel are
# environment-specific — update to values that exist in the target NCP instance.
# The created job's job_id is captured at runtime and reused by later steps.
TEST_BG_JOB_PROJECT_ID            = 1
TEST_BG_JOB_AGENT_NAME            = "verizon-bigquery-agent"
TEST_BG_JOB_PROMPT                = "List all the devices"
TEST_BG_JOB_CRON                  = "*/6 * * * *"
TEST_BG_JOB_TIMEZONE              = "UTC"
TEST_BG_JOB_NAME                  = "List all the devices"
TEST_BG_JOB_NOTIFICATION_CHANNELS = ["in_app", "slack"]
TEST_BG_JOB_SLACK_CHANNEL_IDS     = ["C0B6M3KD9EZ"]

# List Background Jobs test data.
TEST_BG_JOBS_PROJECT_ID      = 1
TEST_BG_JOBS_MINE_ONLY       = True
TEST_BG_JOBS_INCLUDE_REMOVED = False

# Admin List All Background Jobs test data.
TEST_BG_JOBS_ADMIN_INCLUDE_REMOVED = False

# Fallback job_id for the single-job steps (get / update / run / delete) when
# BJ03 (create) has not populated a runtime job_id — e.g. running a step in
# isolation. Point this at a real job_id in the target instance.
TEST_BG_JOB_ID = "job-9cdd2631"

# Fallback message_id (a single run) for the run-detail step when BJ11 (list
# runs) has not captured one — e.g. running BJ12 in isolation. Point this at a
# real run message_id belonging to TEST_BG_JOB_ID.
TEST_BG_JOB_RUN_MESSAGE_ID = 809

# Update Background Job (PATCH) test data — only these fields are modified.
TEST_BG_JOB_UPDATE_NAME                  = "3 sigma anomalies"
TEST_BG_JOB_UPDATE_PROMPT                = "List 3 sigma anomalies"
TEST_BG_JOB_UPDATE_AGENT_NAME            = "verizon-bigquery-agent"
TEST_BG_JOB_UPDATE_TRIGGER_TYPE          = "scheduled"
TEST_BG_JOB_UPDATE_CRON                  = "*/6 * * * *"
TEST_BG_JOB_UPDATE_TIMEZONE              = "UTC"
TEST_BG_JOB_UPDATE_NOTIFICATION_CHANNELS = ["in_app"]

# =========================
# CUSTOM AGENTS API ENDPOINTS  (19 endpoints total)
# =========================
ONBOARD_CUSTOM_AGENT_URL = f"{NCP_BASE_URL}/api/v1/custom_agents/onboard"
LIST_CUSTOM_AGENTS_URL   = f"{NCP_BASE_URL}/api/v1/custom_agents/list"
BG_ELIGIBLE_AGENTS_URL   = f"{NCP_BASE_URL}/api/v1/custom_agents/background-eligible"
GET_CUSTOM_AGENT_URL     = f"{NCP_BASE_URL}/api/v1/custom_agents/{{agent_name}}"
DISABLE_CUSTOM_AGENT_URL = f"{NCP_BASE_URL}/api/v1/custom_agents/{{agent_name}}/disable"
ENABLE_CUSTOM_AGENT_URL  = f"{NCP_BASE_URL}/api/v1/custom_agents/{{agent_name}}/enable"
ENABLE_BG_CUSTOM_AGENT_URL = f"{NCP_BASE_URL}/api/v1/custom_agents/{{agent_name}}/enable-background"
DISABLE_BG_CUSTOM_AGENT_URL = f"{NCP_BASE_URL}/api/v1/custom_agents/{{agent_name}}/disable-background"
ADMIN_LIST_CUSTOM_AGENTS_URL = f"{NCP_BASE_URL}/api/v1/custom_agents/admin/list"
MY_CUSTOM_AGENTS_URL     = f"{NCP_BASE_URL}/api/v1/custom_agents/user/my-agent"
SUBMIT_CUSTOM_AGENT_URL  = f"{NCP_BASE_URL}/api/v1/custom_agents/user/submit"
UPDATE_CUSTOM_AGENT_VERSION_URL = f"{NCP_BASE_URL}/api/v1/custom_agents/{{agent_id}}/version"
APPROVE_CUSTOM_AGENT_URL = f"{NCP_BASE_URL}/api/v1/custom_agents/{{agent_id}}/approve"
DECLINE_CUSTOM_AGENT_URL = f"{NCP_BASE_URL}/api/v1/custom_agents/{{agent_id}}/decline"
FEEDBACK_CUSTOM_AGENT_URL = f"{NCP_BASE_URL}/api/v1/custom_agents/{{agent_id}}/feedback"
DOWNLOAD_CUSTOM_AGENT_URL = f"{NCP_BASE_URL}/api/v1/custom_agents/{{agent_id}}/download"
CAN_SUBMIT_AGENT_URL     = f"{NCP_BASE_URL}/api/v1/custom_agents/user/can-submit-agent"
DELETE_CUSTOM_AGENT_URL  = f"{NCP_BASE_URL}/api/v1/custom_agents/{{agent_name}}"
DELETE_USER_CUSTOM_AGENT_URL = f"{NCP_BASE_URL}/api/v1/custom_agents/user/{{agent_name}}"

# Onboard test data. The .ncp package must be placed alongside the test files
# (same folder). agent_name is the name embedded in that package.
TEST_CA_PACKAGE_FILENAME = "calculator-agent.ncp"
TEST_CA_AGENT_NAME       = "calculator-agent"

# Fallback agent_id for the id-based steps (version upload, etc.) when CA01 /
# CA02 have not captured one at runtime — e.g. running a step in isolation.
# Point this at a real custom-agent id in the target instance.
TEST_CA_AGENT_ID         = 3

# CA12 (version bump) needs a SECOND package: the SAME filename
# (TEST_CA_PACKAGE_FILENAME — the platform keys on the agent name inside the
# package, so the file must NOT be renamed) but a HIGHER version baked into its
# toml. Two files can't share a name in one folder, so the bumped package lives
# in this subfolder (relative to the test files). CA01/CA11 use the base file in
# the test dir; CA12 uses <test_dir>/<subdir>/calculator-agent.ncp.
TEST_CA_VERSION_SUBDIR   = "agent_version_package"

# Decline (CA14) request body — admin feedback explaining the rejection.
TEST_CA_DECLINE_FEEDBACK = "not as expected"

# Feedback (CA15) request body.
TEST_CA_FEEDBACK_MESSAGE = "good"
TEST_CA_FEEDBACK_TYPE    = "general"

# Can-submit-agent (CA17) expected gate value. superadmin can submit → true.
# Set to False when running the suite as a restricted role.
TEST_CA_CAN_SUBMIT_EXPECTED = True

# User-scoped remove (CA19) query flag — force-delete even if the agent is
# referenced elsewhere (e.g. by background jobs).
TEST_CA_ALLOW_FORCE_DELETE = True

# =========================
# ORGANIZATION API ENDPOINTS  (7 endpoints total)
# =========================
LIST_ORGANIZATIONS_URL   = f"{NCP_BASE_URL}/api/v1/organizations"
CREATE_ORGANIZATION_URL  = f"{NCP_BASE_URL}/api/v1/organizations"
UPDATE_ORGANIZATION_URL  = f"{NCP_BASE_URL}/api/v1/organizations/{{org_id}}"
ASSIGN_ORG_USERS_URL     = f"{NCP_BASE_URL}/api/v1/organizations/{{org_id}}/users"
GET_ORG_USERS_URL        = f"{NCP_BASE_URL}/api/v1/organizations/{{org_id}}/users"
DEACTIVATE_ORGANIZATION_URL = f"{NCP_BASE_URL}/api/v1/organizations/{{org_id}}/deactivate"
DELETE_ORGANIZATION_URL  = f"{NCP_BASE_URL}/api/v1/organizations/{{org_id}}"

# The seeded default organization id — where OR07 reassigns a deleted org's
# users before hard-deleting it (delete fails while users are attached).
DEFAULT_ORG_ID = 1

# A known organization expected in the list (the seeded default org).
TEST_ORG_NAME = "default"
# Fallback org id for the id-based steps (get / update / delete) when OR01 has
# not captured one at runtime — e.g. running a step in isolation.
TEST_ORG_ID   = 1

# Create Organization (OR02) request body. usernames are optional members to
# attach; leave empty to avoid a dependency on a specific user existing.
TEST_ORG_CREATE_NAME        = "Microsoft"
TEST_ORG_CREATE_DESCRIPTION = "Test"
TEST_ORG_CREATE_USERNAMES   = []

# Update Organization (OR03) request body.
TEST_ORG_UPDATE_NAME        = "XBOX"
TEST_ORG_UPDATE_DESCRIPTION = "test-123"
TEST_ORG_UPDATE_IS_ACTIVE   = True

# Assign Users To Organization (OR04) — usernames to attach to the (disposable,
# OR02-created) org. NOTE: this REPLACES each user's current org assignment, so
# pick user(s) you don't mind moving off their current org. Must be real users.
TEST_ORG_ASSIGN_USERNAMES   = ["john"]