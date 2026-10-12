"""Built-in tool registration."""

from guyline.tools.agent_tool import AgentTool
from guyline.tools.ask_user_question_tool import AskUserQuestionTool
from guyline.tools.base import BaseTool, ToolExecutionContext, ToolRegistry, ToolResult
from guyline.tools.bash_tool import BashTool
from guyline.tools.brief_tool import BriefTool
from guyline.tools.config_tool import ConfigTool
from guyline.tools.cron_create_tool import CronCreateTool
from guyline.tools.cron_delete_tool import CronDeleteTool
from guyline.tools.cron_list_tool import CronListTool
from guyline.tools.cron_toggle_tool import CronToggleTool
from guyline.tools.enter_plan_mode_tool import EnterPlanModeTool
from guyline.tools.enter_worktree_tool import EnterWorktreeTool
from guyline.tools.exit_plan_mode_tool import ExitPlanModeTool
from guyline.tools.exit_worktree_tool import ExitWorktreeTool
from guyline.tools.file_edit_tool import FileEditTool
from guyline.tools.file_read_tool import FileReadTool
from guyline.tools.file_write_tool import FileWriteTool
from guyline.tools.glob_tool import GlobTool
from guyline.tools.grep_tool import GrepTool
from guyline.tools.image_generation_tool import ImageGenerationTool
from guyline.tools.image_to_text_tool import ImageToTextTool
from guyline.tools.list_mcp_resources_tool import ListMcpResourcesTool
from guyline.tools.lsp_tool import LspTool
from guyline.tools.mcp_auth_tool import McpAuthTool
from guyline.tools.mcp_tool import McpToolAdapter
from guyline.tools.notebook_edit_tool import NotebookEditTool
from guyline.tools.read_mcp_resource_tool import ReadMcpResourceTool
from guyline.tools.remote_trigger_tool import RemoteTriggerTool
from guyline.tools.send_message_tool import SendMessageTool
from guyline.tools.skill_tool import SkillTool
from guyline.tools.sleep_tool import SleepTool
from guyline.tools.task_create_tool import TaskCreateTool
from guyline.tools.task_get_tool import TaskGetTool
from guyline.tools.task_list_tool import TaskListTool
from guyline.tools.task_output_tool import TaskOutputTool
from guyline.tools.task_stop_tool import TaskStopTool
from guyline.tools.task_update_tool import TaskUpdateTool
from guyline.tools.team_create_tool import TeamCreateTool
from guyline.tools.team_delete_tool import TeamDeleteTool
from guyline.tools.todo_write_tool import TodoWriteTool
from guyline.tools.tool_search_tool import ToolSearchTool
from guyline.tools.web_fetch_tool import WebFetchTool
from guyline.tools.web_search_tool import WebSearchTool


def create_default_tool_registry(mcp_manager=None) -> ToolRegistry:
    """Return the default built-in tool registry."""
    registry = ToolRegistry()
    for tool in (
        BashTool(),
        AskUserQuestionTool(),
        FileReadTool(),
        FileWriteTool(),
        FileEditTool(),
        NotebookEditTool(),
        LspTool(),
        McpAuthTool(),
        GlobTool(),
        GrepTool(),
        ImageToTextTool(),
        ImageGenerationTool(),
        SkillTool(),
        ToolSearchTool(),
        WebFetchTool(),
        WebSearchTool(),
        ConfigTool(),
        BriefTool(),
        SleepTool(),
        EnterWorktreeTool(),
        ExitWorktreeTool(),
        TodoWriteTool(),
        EnterPlanModeTool(),
        ExitPlanModeTool(),
        CronCreateTool(),
        CronListTool(),
        CronDeleteTool(),
        CronToggleTool(),
        RemoteTriggerTool(),
        TaskCreateTool(),
        TaskGetTool(),
        TaskListTool(),
        TaskStopTool(),
        TaskOutputTool(),
        TaskUpdateTool(),
        AgentTool(),
        SendMessageTool(),
        TeamCreateTool(),
        TeamDeleteTool(),
    ):
        registry.register(tool)
    if mcp_manager is not None:
        registry.register(ListMcpResourcesTool(mcp_manager))
        registry.register(ReadMcpResourceTool(mcp_manager))
        for tool_info in mcp_manager.list_tools():
            registry.register(McpToolAdapter(mcp_manager, tool_info))
    return registry


__all__ = [
    "BaseTool",
    "ToolExecutionContext",
    "ToolRegistry",
    "ToolResult",
    "create_default_tool_registry",
]
