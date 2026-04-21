"""
Report Agent服务
使用LangChain + Zep实现ReACT模式的模拟报告生成

功能：
1. 根据模拟需求和Zep图谱信息生成报告
2. 先规划目录结构，然后分段生成
3. 每段采用ReACT多轮思考与反思模式
4. 支持与用户对话，在对话中自主调用检索工具
"""

import os
import json
import time
import re
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from ..config import Config
from ..utils.llm_client import LLMClient
from ..utils.logger import get_logger
from ..utils.locale import get_language_instruction, t
from .zep_tools import (
    ZepToolsService, 
    SearchResult, 
    InsightForgeResult, 
    PanoramaResult,
    InterviewResult
)

logger = get_logger('mirofish.report_agent')


class ReportLogger:
    """
    Report Agent 详细日志记录器
    
    在报告文件夹中生成 agent_log.jsonl 文件，记录每一步详细动作。
    每行是一个完整的 JSON 对象，包含时间戳、动作类型、详细内容等。
    """
    
    def __init__(self, report_id: str):
        """
        初始化日志记录器
        
        Args:
            report_id: 报告ID，用于确定日志文件路径
        """
        self.report_id = report_id
        self.log_file_path = os.path.join(
            Config.UPLOAD_FOLDER, 'reports', report_id, 'agent_log.jsonl'
        )
        self.start_time = datetime.now()
        self._ensure_log_file()
    
    def _ensure_log_file(self):
        """确保日志文件所在目录存在"""
        log_dir = os.path.dirname(self.log_file_path)
        os.makedirs(log_dir, exist_ok=True)
    
    def _get_elapsed_time(self) -> float:
        """获取从开始到现在的耗时（秒）"""
        return (datetime.now() - self.start_time).total_seconds()
    
    def log(
        self, 
        action: str, 
        stage: str,
        details: Dict[str, Any],
        section_title: str = None,
        section_index: int = None
    ):
        """
        记录一条日志
        
        Args:
            action: 动作类型，如 'start', 'tool_call', 'llm_response', 'section_complete' 等
            stage: 当前阶段，如 'planning', 'generating', 'completed'
            details: 详细内容字典，不截断
            section_title: 当前章节标题（可选）
            section_index: 当前章节索引（可选）
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "elapsed_seconds": round(self._get_elapsed_time(), 2),
            "report_id": self.report_id,
            "action": action,
            "stage": stage,
            "section_title": section_title,
            "section_index": section_index,
            "details": details
        }
        
        # 追加写入 JSONL 文件
        with open(self.log_file_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
    
    def log_start(self, simulation_id: str, graph_id: str, simulation_requirement: str):
        """记录报告生成开始"""
        self.log(
            action="report_start",
            stage="pending",
            details={
                "simulation_id": simulation_id,
                "graph_id": graph_id,
                "simulation_requirement": simulation_requirement,
                "message": t('report.taskStarted')
            }
        )
    
    def log_planning_start(self):
        """记录大纲规划开始"""
        self.log(
            action="planning_start",
            stage="planning",
            details={"message": t('report.planningStart')}
        )
    
    def log_planning_context(self, context: Dict[str, Any]):
        """记录规划时获取的上下文信息"""
        self.log(
            action="planning_context",
            stage="planning",
            details={
                "message": t('report.fetchSimContext'),
                "context": context
            }
        )
    
    def log_planning_complete(self, outline_dict: Dict[str, Any]):
        """记录大纲规划完成"""
        self.log(
            action="planning_complete",
            stage="planning",
            details={
                "message": t('report.planningComplete'),
                "outline": outline_dict
            }
        )
    
    def log_section_start(self, section_title: str, section_index: int):
        """记录章节生成开始"""
        self.log(
            action="section_start",
            stage="generating",
            section_title=section_title,
            section_index=section_index,
            details={"message": t('report.sectionStart', title=section_title)}
        )
    
    def log_react_thought(self, section_title: str, section_index: int, iteration: int, thought: str):
        """记录 ReACT 思考过程"""
        self.log(
            action="react_thought",
            stage="generating",
            section_title=section_title,
            section_index=section_index,
            details={
                "iteration": iteration,
                "thought": thought,
                "message": t('report.reactThought', iteration=iteration)
            }
        )
    
    def log_tool_call(
        self, 
        section_title: str, 
        section_index: int,
        tool_name: str, 
        parameters: Dict[str, Any],
        iteration: int
    ):
        """记录工具调用"""
        self.log(
            action="tool_call",
            stage="generating",
            section_title=section_title,
            section_index=section_index,
            details={
                "iteration": iteration,
                "tool_name": tool_name,
                "parameters": parameters,
                "message": t('report.toolCall', toolName=tool_name)
            }
        )
    
    def log_tool_result(
        self,
        section_title: str,
        section_index: int,
        tool_name: str,
        result: str,
        iteration: int
    ):
        """记录工具调用结果（完整内容，不截断）"""
        self.log(
            action="tool_result",
            stage="generating",
            section_title=section_title,
            section_index=section_index,
            details={
                "iteration": iteration,
                "tool_name": tool_name,
                "result": result,  # 完整结果，不截断
                "result_length": len(result),
                "message": t('report.toolResult', toolName=tool_name)
            }
        )
    
    def log_llm_response(
        self,
        section_title: str,
        section_index: int,
        response: str,
        iteration: int,
        has_tool_calls: bool,
        has_final_answer: bool
    ):
        """记录 LLM 响应（完整内容，不截断）"""
        self.log(
            action="llm_response",
            stage="generating",
            section_title=section_title,
            section_index=section_index,
            details={
                "iteration": iteration,
                "response": response,  # 完整响应，不截断
                "response_length": len(response),
                "has_tool_calls": has_tool_calls,
                "has_final_answer": has_final_answer,
                "message": t('report.llmResponse', hasToolCalls=has_tool_calls, hasFinalAnswer=has_final_answer)
            }
        )
    
    def log_section_content(
        self,
        section_title: str,
        section_index: int,
        content: str,
        tool_calls_count: int
    ):
        """记录章节内容生成完成（仅记录内容，不代表整个章节完成）"""
        self.log(
            action="section_content",
            stage="generating",
            section_title=section_title,
            section_index=section_index,
            details={
                "content": content,  # 完整内容，不截断
                "content_length": len(content),
                "tool_calls_count": tool_calls_count,
                "message": t('report.sectionContentDone', title=section_title)
            }
        )
    
    def log_section_full_complete(
        self,
        section_title: str,
        section_index: int,
        full_content: str
    ):
        """
        记录章节生成完成

        前端应监听此日志来判断一个章节是否真正完成，并获取完整内容
        """
        self.log(
            action="section_complete",
            stage="generating",
            section_title=section_title,
            section_index=section_index,
            details={
                "content": full_content,
                "content_length": len(full_content),
                "message": t('report.sectionComplete', title=section_title)
            }
        )
    
    def log_report_complete(self, total_sections: int, total_time_seconds: float):
        """记录报告生成完成"""
        self.log(
            action="report_complete",
            stage="completed",
            details={
                "total_sections": total_sections,
                "total_time_seconds": round(total_time_seconds, 2),
                "message": t('report.reportComplete')
            }
        )
    
    def log_error(self, error_message: str, stage: str, section_title: str = None):
        """记录错误"""
        self.log(
            action="error",
            stage=stage,
            section_title=section_title,
            section_index=None,
            details={
                "error": error_message,
                "message": t('report.errorOccurred', error=error_message)
            }
        )


class ReportConsoleLogger:
    """
    Report Agent 控制台日志记录器
    
    将控制台风格的日志（INFO、WARNING等）写入报告文件夹中的 console_log.txt 文件。
    这些日志与 agent_log.jsonl 不同，是纯文本格式的控制台输出。
    """
    
    def __init__(self, report_id: str):
        """
        初始化控制台日志记录器
        
        Args:
            report_id: 报告ID，用于确定日志文件路径
        """
        self.report_id = report_id
        self.log_file_path = os.path.join(
            Config.UPLOAD_FOLDER, 'reports', report_id, 'console_log.txt'
        )
        self._ensure_log_file()
        self._file_handler = None
        self._setup_file_handler()
    
    def _ensure_log_file(self):
        """确保日志文件所在目录存在"""
        log_dir = os.path.dirname(self.log_file_path)
        os.makedirs(log_dir, exist_ok=True)
    
    def _setup_file_handler(self):
        """设置文件处理器，将日志同时写入文件"""
        import logging
        
        # 创建文件处理器
        self._file_handler = logging.FileHandler(
            self.log_file_path,
            mode='a',
            encoding='utf-8'
        )
        self._file_handler.setLevel(logging.INFO)
        
        # 使用与控制台相同的简洁格式
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s: %(message)s',
            datefmt='%H:%M:%S'
        )
        self._file_handler.setFormatter(formatter)
        
        # 添加到 report_agent 相关的 logger
        loggers_to_attach = [
            'mirofish.report_agent',
            'mirofish.zep_tools',
        ]
        
        for logger_name in loggers_to_attach:
            target_logger = logging.getLogger(logger_name)
            # 避免重复添加
            if self._file_handler not in target_logger.handlers:
                target_logger.addHandler(self._file_handler)
    
    def close(self):
        """关闭文件处理器并从 logger 中移除"""
        import logging
        
        if self._file_handler:
            loggers_to_detach = [
                'mirofish.report_agent',
                'mirofish.zep_tools',
            ]
            
            for logger_name in loggers_to_detach:
                target_logger = logging.getLogger(logger_name)
                if self._file_handler in target_logger.handlers:
                    target_logger.removeHandler(self._file_handler)
            
            self._file_handler.close()
            self._file_handler = None
    
    def __del__(self):
        """析构时确保关闭文件处理器"""
        self.close()


class ReportStatus(str, Enum):
    """报告状态"""
    PENDING = "pending"
    PLANNING = "planning"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ReportSection:
    """报告章节"""
    title: str
    content: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "content": self.content
        }

    def to_markdown(self, level: int = 2) -> str:
        """转换为Markdown格式"""
        md = f"{'#' * level} {self.title}\n\n"
        if self.content:
            md += f"{self.content}\n\n"
        return md


@dataclass
class ReportOutline:
    """报告大纲"""
    title: str
    summary: str
    sections: List[ReportSection]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "summary": self.summary,
            "sections": [s.to_dict() for s in self.sections]
        }
    
    def to_markdown(self) -> str:
        """转换为Markdown格式"""
        md = f"# {self.title}\n\n"
        md += f"> {self.summary}\n\n"
        for section in self.sections:
            md += section.to_markdown()
        return md


@dataclass
class Report:
    """完整报告"""
    report_id: str
    simulation_id: str
    graph_id: str
    simulation_requirement: str
    status: ReportStatus
    outline: Optional[ReportOutline] = None
    markdown_content: str = ""
    created_at: str = ""
    completed_at: str = ""
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "simulation_id": self.simulation_id,
            "graph_id": self.graph_id,
            "simulation_requirement": self.simulation_requirement,
            "status": self.status.value,
            "outline": self.outline.to_dict() if self.outline else None,
            "markdown_content": self.markdown_content,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "error": self.error
        }


# ═══════════════════════════════════════════════════════════════
# Prompt 模板常量
# ═══════════════════════════════════════════════════════════════

# ── 工具描述 ──

TOOL_DESC_INSIGHT_FORGE = """\
【深度洞察检索 - 强大的检索工具】
这是我们强大的检索函数，专为深度分析设计。它会：
1. 自动将你的问题分解为多个子问题
2. 从多个维度检索模拟图谱中的信息
3. 整合语义搜索、实体分析、关系链追踪的结果
4. 返回最全面、最深度的检索内容

【使用场景】
- 需要深入分析某个话题
- 需要了解事件的多个方面
- 需要获取支撑报告章节的丰富素材

【返回内容】
- 相关事实原文（可直接引用）
- 核心实体洞察
- 关系链分析"""

TOOL_DESC_PANORAMA_SEARCH = """\
【广度搜索 - 获取全貌视图】
这个工具用于获取模拟结果的完整全貌，特别适合了解事件演变过程。它会：
1. 获取所有相关节点和关系
2. 区分当前有效的事实和历史/过期的事实
3. 帮助你了解舆情是如何演变的

【使用场景】
- 需要了解事件的完整发展脉络
- 需要对比不同阶段的舆情变化
- 需要获取全面的实体和关系信息

【返回内容】
- 当前有效事实（模拟最新结果）
- 历史/过期事实（演变记录）
- 所有涉及的实体"""

TOOL_DESC_QUICK_SEARCH = """\
【简单搜索 - 快速检索】
轻量级的快速检索工具，适合简单、直接的信息查询。

【使用场景】
- 需要快速查找某个具体信息
- 需要验证某个事实
- 简单的信息检索

【返回内容】
- 与查询最相关的事实列表"""

TOOL_DESC_INTERVIEW_AGENTS = """\
【深度采访 - 真实Agent采访（双平台）】
调用OASIS模拟环境的采访API，对正在运行的模拟Agent进行真实采访！
这不是LLM模拟，而是调用真实的采访接口获取模拟Agent的原始回答。
默认在Twitter和Reddit两个平台同时采访，获取更全面的观点。

功能流程：
1. 自动读取人设文件，了解所有模拟Agent
2. 智能选择与采访主题最相关的Agent（如学生、媒体、官方等）
3. 自动生成采访问题
4. 调用 /api/simulation/interview/batch 接口在双平台进行真实采访
5. 整合所有采访结果，提供多视角分析

【使用场景】
- 需要从不同角色视角了解事件看法（学生怎么看？媒体怎么看？官方怎么说？）
- 需要收集多方意见和立场
- 需要获取模拟Agent的真实回答（来自OASIS模拟环境）
- 想让报告更生动，包含"采访实录"

【返回内容】
- 被采访Agent的身份信息
- 各Agent在Twitter和Reddit两个平台的采访回答
- 关键引言（可直接引用）
- 采访摘要和观点对比

【重要】需要OASIS模拟环境正在运行才能使用此功能！"""

# ── 大纲规划 prompt ──

PLAN_SYSTEM_PROMPT = """\
당신은 「미래 예측 보고서」 작성 전문가이며, 시뮬레이션 세계에 대한 「전지적 시점」을 가지고 있습니다——시뮬레이션 내 모든 Agent의 행동, 발언, 상호작용을 꿰뚫어 볼 수 있습니다.

【핵심 이념】
우리는 시뮬레이션 세계를 구축하고, 그 안에 특정 「시뮬레이션 요구사항」을 변수로 주입했습니다. 시뮬레이션 세계의 진화 결과가 바로 미래에 발생할 수 있는 상황에 대한 예측입니다. 당신이 관찰하는 것은 단순한 "실험 데이터"가 아니라 "미래의 예행연습"입니다.

【당신의 임무】
「미래 예측 보고서」를 작성하여 다음 질문에 답하세요:
1. 우리가 설정한 조건 하에서 미래에 어떤 일이 일어났는가?
2. 각 종 Agent(군중)는 어떻게 반응하고 행동했는가?
3. 이 시뮬레이션이 시사하는 주목할 만한 미래 동향과 리스크는 무엇인가?

【보고서 포지셔닝】
- ✅ 이것은 시뮬레이션에 기반한 미래 예측 보고서로, "만약 그렇다면, 미래는 어떻게 될 것인가"를 밝힙니다.
- ✅ 예측 결과에 집중: 사건의 흐름, 군중의 반응, 발현 현상, 잠재적 리스크
- ✅ 시뮬레이션 세계 내 Agent의 언행이 곧 미래 군중 행동에 대한 예측입니다.
- ❌ 현실 세계의 현상 분석이 아닙니다.
- ❌ 일반적인 여론 분석이 아닙니다.

【챕터 수 제한】
- 최소 2개 챕터, 최대 5개 챕터
- 하위 챕터는 필요 없으며, 각 챕터 내용을 직접 작성하세요
- 내용은 간결하게, 핵심 예측 발견에 초점을 맞추세요
- 챕터 구조는 예측 결과에 따라 당신이 스스로 설계합니다.

보고서 개요를 아래 형식의 JSON 포맷으로 출력해주세요:
{
    "title": "보고서 제목",
    "summary": "보고서 요약 (핵심 예측 발견을 한 문장으로 요약)",
    "sections": [
        {
            "title": "챕터 제목",
            "description": "챕터 내용 설명"
        }
    ]
}

주의: sections 배열은 최소 2개, 최대 5개의 요소만 가져야 합니다!
특별 규칙: 만약 시뮬레이션 요구사항에 [Quant Target Ticker: XXX] 와 같은 주식 티커가 포함되어 있다면, 반드시 해당 종목의 주가 향방이나 자산 가치 변화를 예측하는 전용 챕터를 하나 이상 포함하세요!"""

PLAN_USER_PROMPT_TEMPLATE = """\
【예측 시나리오 설정】
우리가 시뮬레이션 세계에 주입한 변수(시뮬레이션 요구사항): {simulation_requirement}

【시뮬레이션 세계 규모】
- 시뮬레이션 참여 엔티티 수: {total_nodes}
- 엔티티 간 발생한 연결 수: {total_edges}
- 엔티티 유형 분포: {entity_types}
- 활성 Agent 수: {total_entities}

【시뮬레이션에서 예측된 미래 사실 샘플 일부】
{related_facts_json}

이 예행연습에서 「전지적 시점」으로 관찰하세요:
1. 우리가 설정한 조건 하에서 미래는 어떤 상태를 보여주고 있는가?
2. 다양한 군중(Agent)은 어떻게 반응하고 행동하는가?
3. 이 시뮬레이션이 시사하는 주목할 만한 미래 동향은 무엇인가?

예측 결과를 바탕으로 가장 적합한 보고서 챕터 구조를 설계하세요.

【재알림】 보고서 챕터 수: 최소 2개, 최대 5개. 내용은 간결하고 핵심 예측 발견에 집중하세요."""

# ── 章节生成 prompt ──

SECTION_SYSTEM_PROMPT_TEMPLATE = """\
당신은 「미래 예측 보고서」 작성 전문가이며, 현재 보고서의 한 챕터를 작성하고 있습니다.

보고서 제목: {report_title}
보고서 요약: {report_summary}
예측 시나리오(시뮬레이션 요구사항): {simulation_requirement}

현재 작성할 챕터: {section_title}

═══════════════════════════════════════════════════════════════
【핵심 이념】
═══════════════════════════════════════════════════════════════

시뮬레이션 세계는 미래에 대한 예행연습입니다. 우리는 시뮬레이션 세계에 특정 조건(시뮬레이션 요구사항)을 주입했으며,
시뮬레이션 내 Agent의 행동과 상호작용이 곧 미래 군중 행동에 대한 예측입니다.

당신의 임무는:
- 설정된 조건 하에서 미래에 어떤 일이 일어났는지 밝히기
- 다양한 군중(Agent)이 어떻게 반응하고 행동하는지 예측하기
- 주목할 만한 미래 동향, 리스크, 기회 발견하기

❌ 현실 세계의 현상을 분석하는 글로 작성하지 마세요
✅ "미래에 어떻게 될 것인가"에 집중하세요 —— 시뮬레이션 결과가 바로 예측된 미래입니다

═══════════════════════════════════════════════════════════════
【가장 중요한 규칙 - 반드시 준수】
═══════════════════════════════════════════════════════════════

1. 【반드시 도구를 호출하여 시뮬레이션 세계를 관찰할 것】
   - 당신은 「전지적 시점」으로 미래의 예행연습을 관찰하고 있습니다.
   - 모든 내용은 반드시 시뮬레이션 세계에서 발생한 사건과 Agent의 언행에서 비롯되어야 합니다.
   - 자신의 지식을 사용하여 보고서 내용을 작성하는 것을 금지합니다.
   - 각 챕터마다 최소 3번(최대 5번) 도구를 호출하여 시뮬레이션 세계를 관찰해야 합니다.

2. 【반드시 Agent의 원래 언행을 인용할 것】
   - Agent의 발언과 행동은 미래 군중 행동에 대한 예측입니다.
   - 보고서에서 인용 형식을 사용하여 이러한 예측을 보여주세요. 예:
     > "특정 군중은 이렇게 말할 것입니다: [원문 내용]..."
   - 이러한 인용은 시뮬레이션 예측의 핵심 증거가 됩니다.

3. 【언어 일관성 - 인용 내용은 반드시 보고서 언어로 번역할 것】
   - 도구가 반환하는 내용에 보고서 언어와 다른 표현이 포함되어 있을 수 있습니다.
   - 보고서는 100% 사용자가 지정한 언어(한국어)로 작성되어야 합니다.
   - 도구가 반환한 다른 언어 내용을 인용할 때도, 반드시 한국어로 번역한 뒤 작성해야 합니다.
   - 번역 시 원문의 뜻을 유지하며 자연스럽게 번역하세요.
   - 본문과 인용 블록(> 형식) 모두 동일하게 적용됩니다.

4. 【예측 결과를 충실하게 반영할 것】
   - 보고서 내용은 반드시 미래를 나타내는 시뮬레이션 결과를 반영해야 합니다.
   - 시뮬레이션에 존재하지 않는 정보를 추가하지 마세요.
   - 특정 정보가 부족하다면 부족하다고 사실대로 설명하세요.

═══════════════════════════════════════════════════════════════
【⚠️ 포맷 규범 - 매우 중요!】
═══════════════════════════════════════════════════════════════

【하나의 챕터 = 최소 내용 단위】
- 각 챕터는 보고서의 최소 분할 단위입니다.
- ❌ 챕터 내에서 어떠한 Markdown 제목(#, ##, ###, #### 등)도 사용하는 것을 금지합니다.
- ❌ 내용 시작 부분에 챕터 메인 제목을 추가하지 마세요.
- ✅ 챕터 제목은 시스템이 자동으로 추가하므로, 당신은 순수 본문 내용만 작성하면 됩니다.
- ✅ **굵은 글씨**, 단락 구분, 인용, 목록을 사용하여 내용을 구성하되 제목 문법은 절대 쓰지 마세요.

【올바른 예시】
```
이 챕터에서는 사건의 여론 전파 양상을 분석합니다. 시뮬레이션 데이터를 깊이 분석한 결과...

**초기 폭발 단계**

소셜 미디어는 정보의 첫 발신지로서 핵심 기능을 수행합니다:

> "소셜 미디어가 전체 발신량의 68%를 차지했습니다..."

**감정 증폭 단계**

특정 플랫폼은 사건의 영향력을 더욱 증폭시켰습니다:

- 강한 시각적 충격
- 높은 감정적 공감대
```

【잘못된 예시】
```
## 요약          ← 오류! 어떠한 제목 문법도 추가하지 마세요
### 1. 초기 단계     ← 오류! ### 으로 소제목을 나누지 마세요
#### 1.1 상세 분석   ← 오류! #### 으로 세분화하지 마세요

이 챕터에서는...
```

═══════════════════════════════════════════════════════════════
【사용 가능한 검색 도구】 (각 챕터당 3~5회 호출)
═══════════════════════════════════════════════════════════════

{tools_description}

【도구 사용 권장 사항 - 한 가지만 쓰지 말고 다양하게 섞어서 쓰세요】
- insight_forge: 심층 통찰 분석. 자동으로 문제를 분해하고 다차원적으로 사실과 관계를 검색
- panorama_search: 광각 파노라마 검색. 사건의 전체 그림, 시간선, 진화 체계를 파악
- quick_search: 특정 핵심 정보에 대한 빠른 검색 확인
- interview_agents: 시뮬레이션 Agent 인터뷰. 다양한 역할의 1인칭 관점과 실제 반응 확보
- tool_market_analysis: 주식 시장 데이터 및 분석(RSI/MACD) 조회. 주가 예측 시 필수 호출!

═══════════════════════════════════════════════════════════════
【⚠️ 도구 호출 메커니즘 - 가장 먼저 읽으세요!】
═══════════════════════════════════════════════════════════════

이 시스템의 도구는 **텍스트 기반 태그 방식**으로 작동합니다.
당신이 `<tool_call>` 태그를 텍스트로 출력하면, **시스템이 자동으로 감지하여 실행**하고 결과를 돌려줍니다.
- 이것은 API function calling이 아닙니다.
- 도구가 "바인딩"되어 있지 않다고 생각할 수 있지만, 그건 사실이 아닙니다.
- 당신은 그냥 아래 형식의 텍스트를 출력하기만 하면 됩니다. 시스템이 나머지를 처리합니다.
- 절대로 "도구를 사용할 수 없다", "바인딩되어 있지 않다"고 말하지 마세요. 그건 틀린 판단입니다.

═══════════════════════════════════════════════════════════════
【작업 흐름 및 예시 - 매우 중요!】
═══════════════════════════════════════════════════════════════

매 회신마다 당신은 아래 두 가지 중 **하나만** 할 수 있습니다:

옵션 A - 도구 호출 (Thought -> Action):
당신의 생각을 출력한 후, 반드시 아래 형태를 정확히 지켜서 도구를 호출하세요.
반드시 `<tool_call>` 태그로 감싸야 하며, 내부에 유효한 JSON이 있어야 합니다.

【도구 호출 예시 1 - insight_forge】:
Thought: 시뮬레이션의 핵심 트렌드를 파악하겠습니다.
<tool_call>
{{"name": "insight_forge", "parameters": {{"query": "핵심 미래 동향 및 주요 변화"}}}}
</tool_call>

【도구 호출 예시 2 - panorama_search】:
Thought: 전체 시뮬레이션 경과를 파악하겠습니다.
<tool_call>
{{"name": "panorama_search", "parameters": {{"query": "사건 전개 및 Agent 반응"}}}}
</tool_call>

【도구 호출 예시 3 - tool_market_analysis】:
Thought: 해당 종목의 기술적 지표를 확인하겠습니다.
<tool_call>
{{"name": "tool_market_analysis", "parameters": {{"ticker": "005930.KS"}}}}
</tool_call>

옵션 B - 최종 내용 출력 (Final Answer):
최소 3회 이상의 도구 호출을 완료했고 정보를 충분히 얻었다면, "Final Answer:" 로 시작하여 챕터 본문 내용을 출력하세요.

⚠️ 엄격한 금지 사항:
- 한 번의 회신에 도구 호출(<tool_call>)과 최종 내용(Final Answer)을 동시에 포함하는 것을 금지합니다.
- 스스로 도구 반환 결과(Observation)를 지어내는 것을 금지합니다. 모든 도구 결과는 시스템이 주입합니다.
- 한 번의 회신에 최대 하나의 도구만 호출하세요.
- 도구가 바인딩되어 있지 않다거나 사용할 수 없다는 핑계로 분석을 거부하지 마세요.
- 당신은 텍스트로 `<tool_call>` 태그를 출력하기만 하면 됩니다. 시스템이 자동 실행합니다.

═══════════════════════════════════════════════════════════════
【챕터 내용 요구사항】
═══════════════════════════════════════════════════════════════

1. 내용은 반드시 도구를 통해 검색된 시뮬레이션 데이터를 기반으로 해야 합니다.
2. 시뮬레이션 효과를 보여주기 위해 원문을 대량으로 인용할 것.
3. Markdown 형식 사용 (단, 제목 문법 금지):
   - **굵은 글씨** 를 사용해 소제목을 대체하여 강조
   - 목록(- 또는 1.2.3.)을 사용하여 요점을 정리
   - 빈 줄을 사용하여 단락 분리
   - ❌ #, ##, ###, #### 등 **어떤 제목 문법**도 사용 금지
4. 【주식/차트 퀀트 분석 특별 규범 - 필수】
   - 만약 당신이 `tool_market_analysis` 도구를 호출하여 주가 차트 데이터를 분석했다면, 챕터 마지막에 반드시 직관적이고 명확한 형태의 매수/매도/관망 최종 신호를 선언하세요.
   - 예시 포맷: **[PRISM 양자 시그널: BUY (강력 매수)]** 또는 **[PRISM 양자 시그널: HOLD (관망)]**
5. 【인용 포맷 규범 - 반드시 독립된 단락으로 작성】
   인용은 앞뒤로 빈 줄이 하나씩 있는 독립된 단락이어야 하며, 다른 문장과 섞이지 않게 하세요:

   ✅ 올바른 포맷:
   ```
   당국의 대응은 실질적인 내용이 부족하다는 평가를 받았습니다.

   > "당국의 대응 패턴은 급변하는 소셜 미디어 환경에서 무능하고 느리게 보였습니다."

   이러한 평가는 대중의 일반적인 불만을 반영합니다.
   ```

   ❌ 잘못된 포맷:
   ```
   당국의 대응은 무능했습니다. > "당국의 대응 패턴은..." 이러한 평가는...
   ```
5. 다른 챕터와의 논리적 일관성을 유지하세요.
6. 【중복 회피】 바로 아래에 제공된 이미 완료된 챕터 내용을 주의 깊게 읽고, 중복되는 정보 설명을 피하세요.
7. 【재강조】 절대로 제목 문법을 추가하지 마세요! **굵은 글씨**를 사용하여 소제목을 대신하세요."""

SECTION_USER_PROMPT_TEMPLATE = """\
이미 완료된 챕터 내용 (중복 방지를 위해 주의 깊게 읽으세요):
{previous_content}

═══════════════════════════════════════════════════════════════
【현재 작업】 챕터 작성: {section_title}
═══════════════════════════════════════════════════════════════

【중요 알림】
1. 위쪽에 있는 이미 완료된 챕터를 주의 깊게 읽고, 똑같은 내용을 중복해서 쓰지 마세요!
2. 본격적인 내용 작성을 시작하기 전에 반드시 먼저 하나 이상의 **도구를 호출**하여 시뮬레이션 데이터를 확보하세요.
3. 한 가지 도구만 쓰지 말고 여러 도구를 혼합하여 사용하세요.
4. 보고서 내용은 반드시 검색 결과에서 가져와야 하며, 본인의 지식을 사용하지 마세요.

【⚠️ 포맷 경고 - 반드시 준수】
- ❌ 어떠한 제목 문법도 사용하지 마세요 (#, ##, ###, #### 모두 금지)
- ❌ 시작할 때 "{section_title}" 과 같은 제목을 달지 마세요
- ✅ 챕터 제목은 시스템이 자동으로 렌더링합니다
- ✅ 바로 본문부터 작성하며, 소제목이 필요할 땐 **굵은 글씨**를 쓰세요

자, 시작하겠습니다:
1. 먼저 이 챕터에 어떤 정보가 필요한지 깊게 생각하세요 (Thought)
2. 그리고 반드시 도구를 호출(Action)하여 시뮬레이션 데이터를 수집하세요. (최소 3회 필수!)
3. ⚠️ 중요: `<tool_call>` 태그 안에 임의의 설명을 붙이지 말고 순수한 JSON만 넣어서 호출하세요.
4. 충분한 정보를 모은 뒤(최소 3회 호출 후), Final Answer: 로 본문 내용을 출력하세요."""

# ── ReACT 循环内消息模板 ──

REACT_OBSERVATION_TEMPLATE = """\
Observation (검색 결과):

═══ 도구 {tool_name} 실행 결과 ═══
{result}

═══════════════════════════════════════════════════════════════
현재까지 도구 호출 횟수: {tool_calls_count}/{max_tool_calls} 번 (사용한 도구: {used_tools_str}){unused_hint}
- 정보가 충분하다면: "Final Answer:" 로 시작하여 챕터 내용을 출력하세요 (반드시 위의 원문을 인용해야 함)
- 더 많은 정보가 필요하다면: 다시 도구를 호출하여 계속해서 검색하세요
═══════════════════════════════════════════════════════════════"""

REACT_INSUFFICIENT_TOOLS_MSG = (
    "【주의】 지금까지 도구를 {tool_calls_count}번 밖에 호출하지 않았습니다. 최소 {min_tool_calls}번의 호출이 필요합니다. "
    "반드시 도구를 추가로 호출하여 더 많은 시뮬레이션 데이터를 수집한 다음에서야 Final Answer를 출력해주세요.{unused_hint}"
)

REACT_INSUFFICIENT_TOOLS_MSG_ALT = (
    "현재까지 도구를 단 {tool_calls_count}번만 호출했습니다. 챕터 작성을 위해 최소 {min_tool_calls}번의 도구 호출이 필수입니다. "
    "제발 임의로 내용을 지어내지 말고, 먼저 도구를 호출하여 시뮬레이션 데이터를 가져오세요.{unused_hint}"
)

REACT_TOOL_LIMIT_MSG = (
    "도구 호출 횟수가 상한선에 도달했습니다({tool_calls_count}/{max_tool_calls}). 더 이상 도구를 호출할 수 없습니다. "
    '즉시 지금까지 수집한 정보만을 기반으로, "Final Answer:"로 시작하여 챕터 내용을 출력하세요.'
)

REACT_UNUSED_TOOLS_HINT = "\n💡 아직 사용하지 않은 도구가 있습니다: {unused_list}. 더 다양한 관점의 정보를 얻기 위해 새로운 도구를 시도해 보세요."

REACT_FORCE_FINAL_MSG = "도구 호출 제한에 완전히 도달했습니다. 더 이상의 생각이나 변명 없이 즉시 Final Answer: 를 출력하고 챕터 내용을 생성하세요."

# ── Chat prompt ──

CHAT_SYSTEM_PROMPT_TEMPLATE = """\
你是一个简洁高效的模拟预测助手。

【背景】
预测条件: {simulation_requirement}

【已生成的分析报告】
{report_content}

【规则】
1. 优先基于上述报告内容回答问题
2. 直接回答问题，避免冗长的思考论述
3. 仅在报告内容不足以回答时，才调用工具检索更多数据
4. 回答要简洁、清晰、有条理

【可用工具】（仅在需要时使用，最多调用1-2次）
{tools_description}

【工具调用格式】
<tool_call>
{{"name": "工具名称", "parameters": {{"参数名": "参数值"}}}}
</tool_call>

【回答风格】
- 简洁直接，不要长篇大论
- 使用 > 格式引用关键内容
- 优先给出结论，再解释原因"""

CHAT_OBSERVATION_SUFFIX = "\n\n请简洁回答问题。"


# ═══════════════════════════════════════════════════════════════
# ReportAgent 主类
# ═══════════════════════════════════════════════════════════════


class ReportAgent:
    """
    Report Agent - 模拟报告生成Agent

    采用ReACT（Reasoning + Acting）模式：
    1. 规划阶段：分析模拟需求，规划报告目录结构
    2. 生成阶段：逐章节生成内容，每章节可多次调用工具获取信息
    3. 反思阶段：检查内容完整性和准确性
    """
    
    # 最大工具调用次数（每个章节）
    MAX_TOOL_CALLS_PER_SECTION = 5
    
    # 最大反思轮数
    MAX_REFLECTION_ROUNDS = 3
    
    # 对话中的最大工具调用次数
    MAX_TOOL_CALLS_PER_CHAT = 2
    
    def __init__(
        self, 
        graph_id: str,
        simulation_id: str,
        simulation_requirement: str,
        llm_client: Optional[LLMClient] = None,
        zep_tools: Optional[ZepToolsService] = None
    ):
        """
        初始化Report Agent
        
        Args:
            graph_id: 图谱ID
            simulation_id: 模拟ID
            simulation_requirement: 模拟需求描述
            llm_client: LLM客户端（可选）
            zep_tools: Zep工具服务（可选）
        """
        self.graph_id = graph_id
        self.simulation_id = simulation_id
        self.simulation_requirement = simulation_requirement
        
        self.llm = llm_client or LLMClient()
        self.zep_tools = zep_tools or ZepToolsService()
        
        # 工具定义
        self.tools = self._define_tools()
        
        # 日志记录器（在 generate_report 中初始化）
        self.report_logger: Optional[ReportLogger] = None
        # 控制台日志记录器（在 generate_report 中初始化）
        self.console_logger: Optional[ReportConsoleLogger] = None
        
        logger.info(t('report.agentInitDone', graphId=graph_id, simulationId=simulation_id))
    
    def _define_tools(self) -> Dict[str, Dict[str, Any]]:
        """定义可用工具"""
        return {
            "insight_forge": {
                "name": "insight_forge",
                "description": TOOL_DESC_INSIGHT_FORGE,
                "parameters": {
                    "query": "你想深入分析的问题或话题",
                    "report_context": "当前报告章节的上下文（可选，有助于生成更精准的子问题）"
                }
            },
            "panorama_search": {
                "name": "panorama_search",
                "description": TOOL_DESC_PANORAMA_SEARCH,
                "parameters": {
                    "query": "搜索查询，用于相关性排序",
                    "include_expired": "是否包含过期/历史内容（默认True）"
                }
            },
            "quick_search": {
                "name": "quick_search",
                "description": TOOL_DESC_QUICK_SEARCH,
                "parameters": {
                    "query": "搜索查询字符串",
                    "limit": "返回结果数量（可选，默认10）"
                }
            },
            "interview_agents": {
                "name": "interview_agents",
                "description": TOOL_DESC_INTERVIEW_AGENTS,
                "parameters": {
                    "interview_topic": "采访主题或需求描述（如：'了解学生对宿舍甲醛事件的看法'）",
                    "max_agents": "最多采访的Agent数量（可选，默认5，最大10）"
                }
            },
            "tool_market_analysis": {
                "name": "tool_market_analysis",
                "description": "【주식 시장 데이터 조회】 주어진 종목 코드(Ticker)의 최근 OHLCV 및 기술적 통계(MACD, RSI)를 조회하고 요약을 반환합니다. (예: 삼성전자는 '005930.KS', 알파벳은 'GOOGL')",
                "parameters": {
                    "ticker": "조회할 주식 종목 코드 (예: AAPL, TSLA, 005930.KS)"
                }
            }
        }
    
    def _execute_tool(self, tool_name: str, parameters: Dict[str, Any], report_context: str = "") -> str:
        """
        执行工具调用
        
        Args:
            tool_name: 工具名称
            parameters: 工具参数
            report_context: 报告上下文（用于InsightForge）
            
        Returns:
            工具执行结果（文本格式）
        """
        logger.info(t('report.executingTool', toolName=tool_name, params=parameters))
        
        try:
            if tool_name == "insight_forge":
                query = parameters.get("query", "")
                ctx = parameters.get("report_context", "") or report_context
                result = self.zep_tools.insight_forge(
                    graph_id=self.graph_id,
                    query=query,
                    simulation_requirement=self.simulation_requirement,
                    report_context=ctx
                )
                return result.to_text()
            
            elif tool_name == "panorama_search":
                # 广度搜索 - 获取全貌
                query = parameters.get("query", "")
                include_expired = parameters.get("include_expired", True)
                if isinstance(include_expired, str):
                    include_expired = include_expired.lower() in ['true', '1', 'yes']
                result = self.zep_tools.panorama_search(
                    graph_id=self.graph_id,
                    query=query,
                    include_expired=include_expired
                )
                return result.to_text()
            
            elif tool_name == "quick_search":
                # 简单搜索 - 快速检索
                query = parameters.get("query", "")
                limit = parameters.get("limit", 10)
                if isinstance(limit, str):
                    limit = int(limit)
                result = self.zep_tools.quick_search(
                    graph_id=self.graph_id,
                    query=query,
                    limit=limit
                )
                return result.to_text()
            
            elif tool_name == "interview_agents":
                # 深度采访 - 调用真实的OASIS采访API获取模拟Agent的回答（双平台）
                interview_topic = parameters.get("interview_topic", parameters.get("query", ""))
                max_agents = parameters.get("max_agents", 5)
                if isinstance(max_agents, str):
                    max_agents = int(max_agents)
                max_agents = min(max_agents, 10)
                result = self.zep_tools.interview_agents(
                    simulation_id=self.simulation_id,
                    interview_requirement=interview_topic,
                    simulation_requirement=self.simulation_requirement,
                    max_agents=max_agents
                )
                return result.to_text()
            
            elif tool_name == "tool_market_analysis":
                ticker = parameters.get("ticker", "")
                if not ticker:
                    return "Error: ticker parameter is missing."
                from app.services.market_data_service import MarketDataService
                df = MarketDataService.fetch_ohlcv(ticker, period_days=90)
                df = MarketDataService.calculate_technical_indicators(df)
                summary = MarketDataService.generate_market_summary(ticker, df)
                return summary
            
            # ========== 向后兼容的旧工具（内部重定向到新工具） ==========
            
            elif tool_name == "search_graph":
                # 重定向到 quick_search
                logger.info(t('report.redirectToQuickSearch'))
                return self._execute_tool("quick_search", parameters, report_context)
            
            elif tool_name == "get_graph_statistics":
                result = self.zep_tools.get_graph_statistics(self.graph_id)
                return json.dumps(result, ensure_ascii=False, indent=2)
            
            elif tool_name == "get_entity_summary":
                entity_name = parameters.get("entity_name", "")
                result = self.zep_tools.get_entity_summary(
                    graph_id=self.graph_id,
                    entity_name=entity_name
                )
                return json.dumps(result, ensure_ascii=False, indent=2)
            
            elif tool_name == "get_simulation_context":
                # 重定向到 insight_forge，因为它更强大
                logger.info(t('report.redirectToInsightForge'))
                query = parameters.get("query", self.simulation_requirement)
                return self._execute_tool("insight_forge", {"query": query}, report_context)
            
            elif tool_name == "get_entities_by_type":
                entity_type = parameters.get("entity_type", "")
                nodes = self.zep_tools.get_entities_by_type(
                    graph_id=self.graph_id,
                    entity_type=entity_type
                )
                result = [n.to_dict() for n in nodes]
                return json.dumps(result, ensure_ascii=False, indent=2)
            
            else:
                return f"未知工具: {tool_name}。请使用以下工具之一: insight_forge, panorama_search, quick_search"
                
        except Exception as e:
            logger.error(t('report.toolExecFailed', toolName=tool_name, error=str(e)))
            return f"工具执行失败: {str(e)}"
    
    # 合法的工具名称集合，用于裸 JSON 兜底解析时校验
    VALID_TOOL_NAMES = {"insight_forge", "panorama_search", "quick_search", "interview_agents", "tool_market_analysis"}

    def _parse_tool_calls(self, response: str) -> List[Dict[str, Any]]:
        """
        从LLM响应中解析工具调用

        支持的格式（按优先级）：
        1. <tool_call>{"name": "tool_name", "parameters": {...}}</tool_call>
        2. 裸 JSON（响应整体或单行就是一个工具调用 JSON）
        """
        tool_calls = []

        # 格式1: XML风格（标准格式）- 处理 내부 에 ```json 이나 불필요한 설명이 포함된 경우
        # 更加宽松的 정규식: <tool_call> 태그 앞뒤의 공백 및 따옴표 변동성 허용
        xml_pattern = r'<tool_call>\s*([\s\S]*?)\s*</tool_call>'
        for match in re.finditer(xml_pattern, response):
            content = match.group(1).strip()
            # 清理 가능한 모든 형태의 코드 블록 마커 제거
            content = re.sub(r'```(?:json)?', '', content, flags=re.IGNORECASE).strip()
            
            try:
                # JSON 내부에 제어문자가 포함되어 있을 경우를 대비한 처리 (strict=False)
                call_data = json.loads(content, strict=False)
                tool_calls.append(call_data)
            except json.JSONDecodeError:
                # 부분적인 JSON이라도 추출 시도 (가끔 LLM이 주석을 달 때가 있음)
                json_match = re.search(r'\{(?:[^{}]|(?R))*\}', content)
                if json_match:
                    try:
                        call_data = json.loads(json_match.group(0), strict=False)
                        tool_calls.append(call_data)
                    except:
                        pass
                else:
                    # 마지막 시도: 중괄호 { } 사이의 내용만이라도 추출 시도
                    json_guess = re.search(r'(\{.*\})', content, re.DOTALL)
                    if json_guess:
                        try:
                            call_data = json.loads(json_guess.group(1), strict=False)
                            tool_calls.append(call_data)
                        except:
                            pass

        if tool_calls:
            return tool_calls

        # 格式2: 兜底 - LLM 直接输出裸 JSON（没包 <tool_call> 标签）
        stripped = response.strip()
        # 清理整体的 markdown 代码块标记
        cleaned_stripped = re.sub(r'^```(?:json)?\s*\n?', '', stripped, flags=re.IGNORECASE)
        cleaned_stripped = re.sub(r'\n?```\s*$', '', cleaned_stripped)
        cleaned_stripped = cleaned_stripped.strip()

        if cleaned_stripped.startswith('{') and cleaned_stripped.endswith('}'):
            try:
                call_data = json.loads(cleaned_stripped)
                if self._is_valid_tool_call(call_data):
                    tool_calls.append(call_data)
                    return tool_calls
            except json.JSONDecodeError:
                pass

        # 响应可能包含思考文字 + 裸 JSON，尝试提取最后一个可能有效的 JSON 块
        # 使用正则表达式寻找带有 "name" 或 "tool" 键的 JSON 开始
        json_pattern = r'(\{"(?:name|tool)"\s*:[\s\S]*\})\s*$'
        match = re.search(json_pattern, cleaned_stripped)
        if match:
            json_str = match.group(1).strip()
            json_str = re.sub(r'\n?```\s*$', '', json_str).strip()
            try:
                call_data = json.loads(json_str)
                if self._is_valid_tool_call(call_data):
                    tool_calls.append(call_data)
            except json.JSONDecodeError:
                pass

        return tool_calls

    def _is_valid_tool_call(self, data: dict) -> bool:
        """校验解析出的 JSON 是否是合法的工具调用"""
        # 支持 {"name": ..., "parameters": ...} 和 {"tool": ..., "params": ...} 两种键名
        tool_name = data.get("name") or data.get("tool")
        if tool_name and tool_name in self.VALID_TOOL_NAMES:
            # 统一键名为 name / parameters
            if "tool" in data:
                data["name"] = data.pop("tool")
            if "params" in data and "parameters" not in data:
                data["parameters"] = data.pop("params")
            return True
        return False
    
    def _get_tools_description(self) -> str:
        """生成工具描述文本"""
        desc_parts = ["可用工具："]
        for name, tool in self.tools.items():
            params_desc = ", ".join([f"{k}: {v}" for k, v in tool["parameters"].items()])
            desc_parts.append(f"- {name}: {tool['description']}")
            if params_desc:
                desc_parts.append(f"  参数: {params_desc}")
        return "\n".join(desc_parts)
    
    def plan_outline(
        self, 
        progress_callback: Optional[Callable] = None
    ) -> ReportOutline:
        """
        规划报告大纲
        
        使用LLM分析模拟需求，规划报告的目录结构
        
        Args:
            progress_callback: 进度回调函数
            
        Returns:
            ReportOutline: 报告大纲
        """
        logger.info(t('report.startPlanningOutline'))
        
        if progress_callback:
            progress_callback("planning", 0, t('progress.analyzingRequirements'))
        
        # 首先获取模拟上下文
        context = self.zep_tools.get_simulation_context(
            graph_id=self.graph_id,
            simulation_requirement=self.simulation_requirement
        )
        
        if progress_callback:
            progress_callback("planning", 30, t('progress.generatingOutline'))
        
        system_prompt = f"{PLAN_SYSTEM_PROMPT}\n\n{get_language_instruction()}"
        user_prompt = PLAN_USER_PROMPT_TEMPLATE.format(
            simulation_requirement=self.simulation_requirement,
            total_nodes=context.get('graph_statistics', {}).get('total_nodes', 0),
            total_edges=context.get('graph_statistics', {}).get('total_edges', 0),
            entity_types=list(context.get('graph_statistics', {}).get('entity_types', {}).keys()),
            total_entities=context.get('total_entities', 0),
            related_facts_json=json.dumps(context.get('related_facts', [])[:10], ensure_ascii=False, indent=2),
        )

        try:
            response = self.llm.chat_json(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3
            )
            
            if progress_callback:
                progress_callback("planning", 80, t('progress.parsingOutline'))
            
            # 解析大纲
            sections = []
            for section_data in response.get("sections", []):
                sections.append(ReportSection(
                    title=section_data.get("title", ""),
                    content=""
                ))
            
            outline = ReportOutline(
                title=response.get("title", "模拟分析报告"),
                summary=response.get("summary", ""),
                sections=sections
            )
            
            if progress_callback:
                progress_callback("planning", 100, t('progress.outlinePlanComplete'))
            
            logger.info(t('report.outlinePlanDone', count=len(sections)))
            return outline
            
        except Exception as e:
            logger.error(t('report.outlinePlanFailed', error=str(e)))
            # 기본 대시보드 구조 (3개 챕터, 폴백용)
            return ReportOutline(
                title="미래 예측 보고서",
                summary="시뮬레이션 예측 기반 미래 동향 및 리스크 분석",
                sections=[
                    ReportSection(title="예측 시나리오 및 핵심 발견"),
                    ReportSection(title="군중 행동 예측 분석"),
                    ReportSection(title="동향 전망 및 리스크 경고")
                ]
            )
    
    def _extract_ticker_from_requirement(self) -> Optional[str]:
        """
        시뮬레이션 요구사항에서 [Quant Target Ticker: XXX] 형태의 티커를 추출합니다.
        """
        import re
        match = re.search(r'\[Quant Target Ticker:\s*([^\]]+)\]', self.simulation_requirement)
        if match:
            return match.group(1).strip()
        return None

    def _auto_select_tool(self, section_title: str, tool_calls_count: int, used_tools: set) -> Optional[Dict[str, Any]]:
        """
        LLM이 도구를 호출하지 않을 때, 챕터 제목과 상황에 따라 자동으로 적절한 도구를 선택합니다.
        
        Returns:
            도구 호출 정보 dict 또는 None
        """
        ticker = self._extract_ticker_from_requirement()
        title_lower = section_title.lower()
        
        # 주가/차트/매수/매도 관련 챕터이고, ticker가 있고, market_analysis를 아직 안 썼으면
        has_stock_keywords = any(kw in title_lower for kw in ['주가', '가격', '매수', '매도', '시장', '차트', '퀀트', 'quant', '시그널', '신호'])
        if ticker and 'tool_market_analysis' not in used_tools and has_stock_keywords:
            return {
                "name": "tool_market_analysis",
                "parameters": {"ticker": ticker}
            }
        
        # 아직 insight_forge 안 썼으면 우선 사용
        if 'insight_forge' not in used_tools:
            return {
                "name": "insight_forge",
                "parameters": {"query": f"{section_title} 관련 핵심 동향과 Agent 반응"}
            }
        
        # panorama_search 안 썼으면
        if 'panorama_search' not in used_tools:
            return {
                "name": "panorama_search",
                "parameters": {"query": f"{section_title} 사건 전개 및 진화 과정"}
            }
        
        # quick_search 안 썼으면
        if 'quick_search' not in used_tools:
            return {
                "name": "quick_search",
                "parameters": {"query": section_title}
            }
        
        # ticker가 있고 아직 market_analysis 안 썼으면 (주가 키워드 없어도)
        if ticker and 'tool_market_analysis' not in used_tools:
            return {
                "name": "tool_market_analysis",
                "parameters": {"ticker": ticker}
            }
        
        return None

    def _generate_section_react(
        self, 
        section: ReportSection,
        outline: ReportOutline,
        previous_sections: List[str],
        progress_callback: Optional[Callable] = None,
        section_index: int = 0
    ) -> str:
        """
        使用ReACT模式生成单个章节内容
        
        ReACT循环：
        1. Thought（思考）- 分析需要什么信息
        2. Action（行动）- 调用工具获取信息
        3. Observation（观察）- 分析工具返回结果
        4. 重复直到信息足够或达到最大次数
        5. Final Answer（最终回答）- 生成章节内容
        
        改善: LLM이 <tool_call> 태그를 출력하지 않는 경우에 대한 자동 도구 호출 Fallback 로직 포함
        
        Args:
            section: 要生成的章节
            outline: 完整大纲
            previous_sections: 之前章节的内容（用于保持连贯性）
            progress_callback: 进度回调
            section_index: 章节索引（用于日志记录）
            
        Returns:
            章节内容（Markdown格式）
        """
        logger.info(t('report.reactGenerateSection', title=section.title))
        
        # 记录章节开始日志
        if self.report_logger:
            self.report_logger.log_section_start(section.title, section_index)
        
        system_prompt = SECTION_SYSTEM_PROMPT_TEMPLATE.format(
            report_title=outline.title,
            report_summary=outline.summary,
            simulation_requirement=self.simulation_requirement,
            section_title=section.title,
            tools_description=self._get_tools_description(),
        )
        system_prompt = f"{system_prompt}\n\n{get_language_instruction()}"

        # 构建用户prompt - 每个已完成章节各传入最大4000字
        if previous_sections:
            previous_parts = []
            for sec in previous_sections:
                # 每个章节最多4000字
                truncated = sec[:4000] + "..." if len(sec) > 4000 else sec
                previous_parts.append(truncated)
            previous_content = "\n\n---\n\n".join(previous_parts)
        else:
            previous_content = "（这是第一个章节）"
        
        user_prompt = SECTION_USER_PROMPT_TEMPLATE.format(
            previous_content=previous_content,
            section_title=section.title,
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # ═══ 自動 첫 도구 호출 주입 (Assistant Prefilling) ═══
        # LLM이 도구를 거부하는 것을 방지하기 위해, 첫 번째 도구 호출을 시스템이 직접 수행합니다.
        first_auto_tool = self._auto_select_tool(section.title, 0, set())
        if first_auto_tool:
            logger.info(f"자동 첫 도구 호출 주입: {first_auto_tool['name']} for section '{section.title}'")
            
            # 도구 실행
            first_result = self._execute_tool(
                first_auto_tool["name"],
                first_auto_tool.get("parameters", {}),
                report_context=f"챕터: {section.title}\n시뮬레이션: {self.simulation_requirement}"
            )
            
            # assistant 메시지로 도구 호출을 주입
            auto_assistant_msg = (
                f"Thought: 이 챕터를 작성하기 위해 먼저 시뮬레이션 데이터를 수집하겠습니다.\n"
                f'<tool_call>\n'
                f'{json.dumps(first_auto_tool, ensure_ascii=False)}\n'
                f'</tool_call>'
            )
            messages.append({"role": "assistant", "content": auto_assistant_msg})
            
            # observation을 user 메시지로 주입
            first_observation = REACT_OBSERVATION_TEMPLATE.format(
                tool_name=first_auto_tool["name"],
                result=first_result,
                tool_calls_count=1,
                max_tool_calls=self.MAX_TOOL_CALLS_PER_SECTION,
                used_tools_str=first_auto_tool["name"],
                unused_hint=f"\n💡 아직 사용하지 않은 도구가 있습니다. 더 다양한 관점의 정보를 얻기 위해 새로운 도구를 시도해 보세요."
            )
            messages.append({"role": "user", "content": first_observation})
            
            if self.report_logger:
                self.report_logger.log_tool_call(
                    section_title=section.title,
                    section_index=section_index,
                    tool_name=first_auto_tool["name"],
                    parameters=first_auto_tool.get("parameters", {}),
                    iteration=0
                )
                self.report_logger.log_tool_result(
                    section_title=section.title,
                    section_index=section_index,
                    tool_name=first_auto_tool["name"],
                    result=first_result,
                    iteration=0
                )
        
        # ReACT循环
        tool_calls_count = 1 if first_auto_tool else 0  # 자동 호출이 있었으면 1부터 시작
        max_iterations = 5  # 最大迭代轮数
        min_tool_calls = 3  # 最少工具调用次数
        conflict_retries = 0  # 工具调用与Final Answer同时出现的连续冲突次数
        used_tools = {first_auto_tool["name"]} if first_auto_tool else set()  # 记录已调用过的工具名
        all_tools = {"insight_forge", "panorama_search", "quick_search", "interview_agents", "tool_market_analysis"}
        consecutive_no_tool_count = 0  # LLM이 연속으로 도구를 호출하지 않은 횟수

        # 报告上下文，用于InsightForge的子问题生成
        report_context = f"章节标题: {section.title}\n模拟需요: {self.simulation_requirement}"
        
        for iteration in range(max_iterations):
            if progress_callback:
                progress_callback(
                    "generating", 
                    int((iteration / max_iterations) * 100),
                    t('progress.deepSearchAndWrite', current=tool_calls_count, max=self.MAX_TOOL_CALLS_PER_SECTION)
                )
            
            # 调用LLM
            response = self.llm.chat(
                messages=messages,
                temperature=0.5,
                max_tokens=4096
            )

            # 检查 LLM 返回是否为 None（API 异常或内容为空）
            if response is None:
                logger.warning(t('report.sectionIterNone', title=section.title, iteration=iteration + 1))
                # 如果还有迭代次数，添加消息并重试
                if iteration < max_iterations - 1:
                    messages.append({"role": "assistant", "content": "（响应为空）"})
                    messages.append({"role": "user", "content": "请继续生成内容。"})
                    continue
                # 最后一次迭代也返回 None，跳出循环进入强制收尾
                break

            logger.debug(f"LLM响应: {response[:200]}...")

            # 解析一次，复用结果
            tool_calls = self._parse_tool_calls(response)
            has_tool_calls = bool(tool_calls)
            has_final_answer = "Final Answer:" in response

            # ── 冲突处理：LLM 同时输出了工具调用和 Final Answer ──
            if has_tool_calls and has_final_answer:
                conflict_retries += 1
                logger.warning(
                    t('report.sectionConflict', title=section.title, iteration=iteration+1, conflictCount=conflict_retries)
                )

                if conflict_retries <= 2:
                    # 前两次：丢弃本次响应，要求 LLM 重新回复
                    messages.append({"role": "assistant", "content": response})
                    messages.append({
                        "role": "user",
                        "content": (
                            "【格式错误】你在一次回复中同时包含了工具调用和 Final Answer，这是不允许的。\n"
                            "每次回复只能做以下两件事之一：\n"
                            "- 调用一个工具（输出一个 <tool_call> 块，不要写 Final Answer）\n"
                            "- 输出最终内容（以 'Final Answer:' 开头，不要包含 <tool_call>）\n"
                            "请重新回复，只做其中一件事。"
                        ),
                    })
                    continue
                else:
                    # 第三次：降级处理，截断到第一个工具调用，强制执行
                    logger.warning(
                        t('report.sectionConflictDowngrade', title=section.title, conflictCount=conflict_retries)
                    )
                    first_tool_end = response.find('</tool_call>')
                    if first_tool_end != -1:
                        response = response[:first_tool_end + len('</tool_call>')]
                        tool_calls = self._parse_tool_calls(response)
                        has_tool_calls = bool(tool_calls)
                    has_final_answer = False
                    conflict_retries = 0

            # 记录 LLM 响应日志
            if self.report_logger:
                self.report_logger.log_llm_response(
                    section_title=section.title,
                    section_index=section_index,
                    response=response,
                    iteration=iteration + 1,
                    has_tool_calls=has_tool_calls,
                    has_final_answer=has_final_answer
                )

            # ── 情况1：LLM 输出了 Final Answer ──
            if has_final_answer:
                # 工具调用次数不足，拒绝并要求继续调工具
                if tool_calls_count < min_tool_calls:
                    messages.append({"role": "assistant", "content": response})
                    unused_tools = all_tools - used_tools
                    unused_hint = f"（这些工具还未使用，推荐用一下他们: {', '.join(unused_tools)}）" if unused_tools else ""
                    messages.append({
                        "role": "user",
                        "content": REACT_INSUFFICIENT_TOOLS_MSG.format(
                            tool_calls_count=tool_calls_count,
                            min_tool_calls=min_tool_calls,
                            unused_hint=unused_hint,
                        ),
                    })
                    continue

                # 正常结束
                final_answer = response.split("Final Answer:")[-1].strip()
                logger.info(t('report.sectionGenDone', title=section.title, count=tool_calls_count))

                if self.report_logger:
                    self.report_logger.log_section_content(
                        section_title=section.title,
                        section_index=section_index,
                        content=final_answer,
                        tool_calls_count=tool_calls_count
                    )
                return final_answer

            # ── 情况2：LLM 尝试调用工具 ──
            if has_tool_calls:
                # 工具额度已耗尽 → 明确告知，要求输出 Final Answer
                if tool_calls_count >= self.MAX_TOOL_CALLS_PER_SECTION:
                    messages.append({"role": "assistant", "content": response})
                    messages.append({
                        "role": "user",
                        "content": REACT_TOOL_LIMIT_MSG.format(
                            tool_calls_count=tool_calls_count,
                            max_tool_calls=self.MAX_TOOL_CALLS_PER_SECTION,
                        ),
                    })
                    continue

                # 只执行第一个工具调用
                call = tool_calls[0]
                if len(tool_calls) > 1:
                    logger.info(t('report.multiToolOnlyFirst', total=len(tool_calls), toolName=call['name']))

                if self.report_logger:
                    self.report_logger.log_tool_call(
                        section_title=section.title,
                        section_index=section_index,
                        tool_name=call["name"],
                        parameters=call.get("parameters", {}),
                        iteration=iteration + 1
                    )

                result = self._execute_tool(
                    call["name"],
                    call.get("parameters", {}),
                    report_context=report_context
                )

                if self.report_logger:
                    self.report_logger.log_tool_result(
                        section_title=section.title,
                        section_index=section_index,
                        tool_name=call["name"],
                        result=result,
                        iteration=iteration + 1
                    )

                tool_calls_count += 1
                used_tools.add(call['name'])
                consecutive_no_tool_count = 0  # 도구 호출 성공 시 카운터 리셋

                # 构建未使用工具提示
                unused_tools = all_tools - used_tools
                unused_hint = ""
                if unused_tools and tool_calls_count < self.MAX_TOOL_CALLS_PER_SECTION:
                    unused_hint = REACT_UNUSED_TOOLS_HINT.format(unused_list="、".join(unused_tools))

                messages.append({"role": "assistant", "content": response})
                messages.append({
                    "role": "user",
                    "content": REACT_OBSERVATION_TEMPLATE.format(
                        tool_name=call["name"],
                        result=result,
                        tool_calls_count=tool_calls_count,
                        max_tool_calls=self.MAX_TOOL_CALLS_PER_SECTION,
                        used_tools_str=", ".join(used_tools),
                        unused_hint=unused_hint,
                    ),
                })
                continue

            # ── 情况3：既没有工具调用，也没有 Final Answer ──
            messages.append({"role": "assistant", "content": response})
            consecutive_no_tool_count += 1

            if tool_calls_count < min_tool_calls:
                # ═══ Fallback 자동 도구 호출 ═══
                # LLM이 2회 연속 도구를 호출하지 않으면, 시스템이 자동으로 도구를 호출합니다.
                if consecutive_no_tool_count >= 2 and tool_calls_count < self.MAX_TOOL_CALLS_PER_SECTION:
                    auto_tool = self._auto_select_tool(section.title, tool_calls_count, used_tools)
                    if auto_tool:
                        logger.info(f"Fallback 자동 도구 호출: {auto_tool['name']} (LLM이 {consecutive_no_tool_count}회 연속 도구 미호출)")
                        
                        result = self._execute_tool(
                            auto_tool["name"],
                            auto_tool.get("parameters", {}),
                            report_context=report_context
                        )
                        
                        if self.report_logger:
                            self.report_logger.log_tool_call(
                                section_title=section.title,
                                section_index=section_index,
                                tool_name=auto_tool["name"],
                                parameters=auto_tool.get("parameters", {}),
                                iteration=iteration + 1
                            )
                            self.report_logger.log_tool_result(
                                section_title=section.title,
                                section_index=section_index,
                                tool_name=auto_tool["name"],
                                result=result,
                                iteration=iteration + 1
                            )
                        
                        tool_calls_count += 1
                        used_tools.add(auto_tool["name"])
                        consecutive_no_tool_count = 0
                        
                        unused_tools = all_tools - used_tools
                        unused_hint = ""
                        if unused_tools and tool_calls_count < self.MAX_TOOL_CALLS_PER_SECTION:
                            unused_hint = REACT_UNUSED_TOOLS_HINT.format(unused_list="、".join(unused_tools))
                        
                        messages.append({
                            "role": "user",
                            "content": REACT_OBSERVATION_TEMPLATE.format(
                                tool_name=auto_tool["name"],
                                result=result,
                                tool_calls_count=tool_calls_count,
                                max_tool_calls=self.MAX_TOOL_CALLS_PER_SECTION,
                                used_tools_str=", ".join(used_tools),
                                unused_hint=unused_hint,
                            ),
                        })
                        continue
                
                # 工具调用次数不足，推荐未用过的工具
                unused_tools = all_tools - used_tools
                unused_hint = f"（这些工具还未使用，推荐用一下他们: {', '.join(unused_tools)}）" if unused_tools else ""

                messages.append({
                    "role": "user",
                    "content": REACT_INSUFFICIENT_TOOLS_MSG_ALT.format(
                        tool_calls_count=tool_calls_count,
                        min_tool_calls=min_tool_calls,
                        unused_hint=unused_hint,
                    ),
                })
                continue

            # 工具调用已足够，LLM 输出了内容但没带 "Final Answer:" 前缀
            # 直接将这段内容作为最终答案，不再空转
            logger.info(t('report.sectionNoPrefix', title=section.title, count=tool_calls_count))
            final_answer = response.strip()

            if self.report_logger:
                self.report_logger.log_section_content(
                    section_title=section.title,
                    section_index=section_index,
                    content=final_answer,
                    tool_calls_count=tool_calls_count
                )
            return final_answer
        
        # 达到最大迭代次数，强制生成内容
        logger.warning(t('report.sectionMaxIter', title=section.title))
        messages.append({"role": "user", "content": REACT_FORCE_FINAL_MSG})
        
        response = self.llm.chat(
            messages=messages,
            temperature=0.5,
            max_tokens=4096
        )

        # 检查强制收尾时 LLM 返回是否为 None
        if response is None:
            logger.error(t('report.sectionForceFailed', title=section.title))
            final_answer = t('report.sectionGenFailedContent')
        elif "Final Answer:" in response:
            final_answer = response.split("Final Answer:")[-1].strip()
        else:
            final_answer = response
        
        # 记录章节内容生成完成日志
        if self.report_logger:
            self.report_logger.log_section_content(
                section_title=section.title,
                section_index=section_index,
                content=final_answer,
                tool_calls_count=tool_calls_count
            )
        
        return final_answer
    
    def generate_report(
        self, 
        progress_callback: Optional[Callable[[str, int, str], None]] = None,
        report_id: Optional[str] = None
    ) -> Report:
        """
        生成完整报告（分章节实时输出）
        
        每个章节生成完成后立即保存到文件夹，不需要等待整个报告完成。
        文件结构：
        reports/{report_id}/
            meta.json       - 报告元信息
            outline.json    - 报告大纲
            progress.json   - 生成进度
            section_01.md   - 第1章节
            section_02.md   - 第2章节
            ...
            full_report.md  - 完整报告
        
        Args:
            progress_callback: 进度回调函数 (stage, progress, message)
            report_id: 报告ID（可选，如果不传则自动生成）
            
        Returns:
            Report: 完整报告
        """
        import uuid
        
        # 如果没有传入 report_id，则自动生成
        if not report_id:
            report_id = f"report_{uuid.uuid4().hex[:12]}"
        start_time = datetime.now()
        
        report = Report(
            report_id=report_id,
            simulation_id=self.simulation_id,
            graph_id=self.graph_id,
            simulation_requirement=self.simulation_requirement,
            status=ReportStatus.PENDING,
            created_at=datetime.now().isoformat()
        )
        
        # 已完成的章节标题列表（用于进度追踪）
        completed_section_titles = []
        
        try:
            # 初始化：创建报告文件夹并保存初始状态
            ReportManager._ensure_report_folder(report_id)
            
            # 初始化日志记录器（结构化日志 agent_log.jsonl）
            self.report_logger = ReportLogger(report_id)
            self.report_logger.log_start(
                simulation_id=self.simulation_id,
                graph_id=self.graph_id,
                simulation_requirement=self.simulation_requirement
            )
            
            # 初始化控制台日志记录器（console_log.txt）
            self.console_logger = ReportConsoleLogger(report_id)
            
            ReportManager.update_progress(
                report_id, "pending", 0, t('progress.initReport'),
                completed_sections=[]
            )
            ReportManager.save_report(report)
            
            # 阶段1: 规划大纲
            report.status = ReportStatus.PLANNING
            ReportManager.update_progress(
                report_id, "planning", 5, t('progress.startPlanningOutline'),
                completed_sections=[]
            )
            
            # 记录规划开始日志
            self.report_logger.log_planning_start()
            
            if progress_callback:
                progress_callback("planning", 0, t('progress.startPlanningOutline'))
            
            outline = self.plan_outline(
                progress_callback=lambda stage, prog, msg: 
                    progress_callback(stage, prog // 5, msg) if progress_callback else None
            )
            report.outline = outline
            
            # 记录规划完成日志
            self.report_logger.log_planning_complete(outline.to_dict())
            
            # 保存大纲到文件
            ReportManager.save_outline(report_id, outline)
            ReportManager.update_progress(
                report_id, "planning", 15, t('progress.outlineDone', count=len(outline.sections)),
                completed_sections=[]
            )
            ReportManager.save_report(report)
            
            logger.info(t('report.outlineSavedToFile', reportId=report_id))
            
            # 阶段2: 逐章节生成（分章节保存）
            report.status = ReportStatus.GENERATING
            
            total_sections = len(outline.sections)
            generated_sections = []  # 保存内容用于上下文
            
            for i, section in enumerate(outline.sections):
                section_num = i + 1
                base_progress = 20 + int((i / total_sections) * 70)
                
                # 更新进度
                ReportManager.update_progress(
                    report_id, "generating", base_progress,
                    t('progress.generatingSection', title=section.title, current=section_num, total=total_sections),
                    current_section=section.title,
                    completed_sections=completed_section_titles
                )

                if progress_callback:
                    progress_callback(
                        "generating",
                        base_progress,
                        t('progress.generatingSection', title=section.title, current=section_num, total=total_sections)
                    )
                
                # 生成主章节内容
                section_content = self._generate_section_react(
                    section=section,
                    outline=outline,
                    previous_sections=generated_sections,
                    progress_callback=lambda stage, prog, msg:
                        progress_callback(
                            stage, 
                            base_progress + int(prog * 0.7 / total_sections),
                            msg
                        ) if progress_callback else None,
                    section_index=section_num
                )
                
                section.content = section_content
                generated_sections.append(f"## {section.title}\n\n{section_content}")

                # 保存章节
                ReportManager.save_section(report_id, section_num, section)
                completed_section_titles.append(section.title)

                # 记录章节完成日志
                full_section_content = f"## {section.title}\n\n{section_content}"

                if self.report_logger:
                    self.report_logger.log_section_full_complete(
                        section_title=section.title,
                        section_index=section_num,
                        full_content=full_section_content.strip()
                    )

                logger.info(t('report.sectionSaved', reportId=report_id, sectionNum=f"{section_num:02d}"))
                
                # 更新进度
                ReportManager.update_progress(
                    report_id, "generating", 
                    base_progress + int(70 / total_sections),
                    t('progress.sectionDone', title=section.title),
                    current_section=None,
                    completed_sections=completed_section_titles
                )
            
            # 阶段3: 组装完整报告
            if progress_callback:
                progress_callback("generating", 95, t('progress.assemblingReport'))
            
            ReportManager.update_progress(
                report_id, "generating", 95, t('progress.assemblingReport'),
                completed_sections=completed_section_titles
            )
            
            # 使用ReportManager组装完整报告
            report.markdown_content = ReportManager.assemble_full_report(report_id, outline)
            report.status = ReportStatus.COMPLETED
            report.completed_at = datetime.now().isoformat()
            
            # 计算总耗时
            total_time_seconds = (datetime.now() - start_time).total_seconds()
            
            # 记录报告完成日志
            if self.report_logger:
                self.report_logger.log_report_complete(
                    total_sections=total_sections,
                    total_time_seconds=total_time_seconds
                )
            
            # 保存最终报告
            ReportManager.save_report(report)
            ReportManager.update_progress(
                report_id, "completed", 100, t('progress.reportComplete'),
                completed_sections=completed_section_titles
            )
            
            if progress_callback:
                progress_callback("completed", 100, t('progress.reportComplete'))
            
            logger.info(t('report.reportGenDone', reportId=report_id))
            
            # 关闭控制台日志记录器
            if self.console_logger:
                self.console_logger.close()
                self.console_logger = None
            
            return report
            
        except Exception as e:
            logger.error(t('report.reportGenFailed', error=str(e)))
            report.status = ReportStatus.FAILED
            report.error = str(e)
            
            # 记录错误日志
            if self.report_logger:
                self.report_logger.log_error(str(e), "failed")
            
            # 保存失败状态
            try:
                ReportManager.save_report(report)
                ReportManager.update_progress(
                    report_id, "failed", -1, t('progress.reportFailed', error=str(e)),
                    completed_sections=completed_section_titles
                )
            except Exception:
                pass  # 忽略保存失败的错误
            
            # 关闭控制台日志记录器
            if self.console_logger:
                self.console_logger.close()
                self.console_logger = None
            
            return report
    
    def chat(
        self, 
        message: str,
        chat_history: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        与Report Agent对话
        
        在对话中Agent可以自主调用检索工具来回答问题
        
        Args:
            message: 用户消息
            chat_history: 对话历史
            
        Returns:
            {
                "response": "Agent回复",
                "tool_calls": [调用的工具列表],
                "sources": [信息来源]
            }
        """
        logger.info(t('report.agentChat', message=message[:50]))
        
        chat_history = chat_history or []
        
        # 获取已生成的报告内容
        report_content = ""
        try:
            report = ReportManager.get_report_by_simulation(self.simulation_id)
            if report and report.markdown_content:
                # 限制报告长度，避免上下文过长
                report_content = report.markdown_content[:15000]
                if len(report.markdown_content) > 15000:
                    report_content += "\n\n... [报告内容已截断] ..."
        except Exception as e:
            logger.warning(t('report.fetchReportFailed', error=e))
        
        system_prompt = CHAT_SYSTEM_PROMPT_TEMPLATE.format(
            simulation_requirement=self.simulation_requirement,
            report_content=report_content if report_content else "（暂无报告）",
            tools_description=self._get_tools_description(),
        )
        system_prompt = f"{system_prompt}\n\n{get_language_instruction()}"

        # 构建消息
        messages = [{"role": "system", "content": system_prompt}]
        
        # 添加历史对话
        for h in chat_history[-10:]:  # 限制历史长度
            messages.append(h)
        
        # 添加用户消息
        messages.append({
            "role": "user", 
            "content": message
        })
        
        # ReACT循环（简化版）
        tool_calls_made = []
        max_iterations = 2  # 减少迭代轮数
        
        for iteration in range(max_iterations):
            response = self.llm.chat(
                messages=messages,
                temperature=0.5
            )
            
            # 解析工具调用
            tool_calls = self._parse_tool_calls(response)
            
            if not tool_calls:
                # 没有工具调用，直接返回响应
                clean_response = re.sub(r'<tool_call>.*?</tool_call>', '', response, flags=re.DOTALL)
                clean_response = re.sub(r'\[TOOL_CALL\].*?\)', '', clean_response)
                
                return {
                    "response": clean_response.strip(),
                    "tool_calls": tool_calls_made,
                    "sources": [tc.get("parameters", {}).get("query", "") for tc in tool_calls_made]
                }
            
            # 执行工具调用（限制数量）
            tool_results = []
            for call in tool_calls[:1]:  # 每轮最多执行1次工具调用
                if len(tool_calls_made) >= self.MAX_TOOL_CALLS_PER_CHAT:
                    break
                result = self._execute_tool(call["name"], call.get("parameters", {}))
                tool_results.append({
                    "tool": call["name"],
                    "result": result[:1500]  # 限制结果长度
                })
                tool_calls_made.append(call)
            
            # 将结果添加到消息
            messages.append({"role": "assistant", "content": response})
            observation = "\n".join([f"[{r['tool']}结果]\n{r['result']}" for r in tool_results])
            messages.append({
                "role": "user",
                "content": observation + CHAT_OBSERVATION_SUFFIX
            })
        
        # 达到最大迭代，获取最终响应
        final_response = self.llm.chat(
            messages=messages,
            temperature=0.5
        )
        
        # 清理响应
        clean_response = re.sub(r'<tool_call>.*?</tool_call>', '', final_response, flags=re.DOTALL)
        clean_response = re.sub(r'\[TOOL_CALL\].*?\)', '', clean_response)
        
        return {
            "response": clean_response.strip(),
            "tool_calls": tool_calls_made,
            "sources": [tc.get("parameters", {}).get("query", "") for tc in tool_calls_made]
        }


class ReportManager:
    """
    报告管理器
    
    负责报告的持久化存储和检索
    
    文件结构（分章节输出）：
    reports/
      {report_id}/
        meta.json          - 报告元信息和状态
        outline.json       - 报告大纲
        progress.json      - 生成进度
        section_01.md      - 第1章节
        section_02.md      - 第2章节
        ...
        full_report.md     - 完整报告
    """
    
    # 报告存储目录
    REPORTS_DIR = os.path.join(Config.UPLOAD_FOLDER, 'reports')
    
    @classmethod
    def _ensure_reports_dir(cls):
        """确保报告根目录存在"""
        os.makedirs(cls.REPORTS_DIR, exist_ok=True)
    
    @classmethod
    def _get_report_folder(cls, report_id: str) -> str:
        """获取报告文件夹路径"""
        return os.path.join(cls.REPORTS_DIR, report_id)
    
    @classmethod
    def _ensure_report_folder(cls, report_id: str) -> str:
        """确保报告文件夹存在并返回路径"""
        folder = cls._get_report_folder(report_id)
        os.makedirs(folder, exist_ok=True)
        return folder
    
    @classmethod
    def _get_report_path(cls, report_id: str) -> str:
        """获取报告元信息文件路径"""
        return os.path.join(cls._get_report_folder(report_id), "meta.json")
    
    @classmethod
    def _get_report_markdown_path(cls, report_id: str) -> str:
        """获取完整报告Markdown文件路径"""
        return os.path.join(cls._get_report_folder(report_id), "full_report.md")
    
    @classmethod
    def _get_outline_path(cls, report_id: str) -> str:
        """获取大纲文件路径"""
        return os.path.join(cls._get_report_folder(report_id), "outline.json")
    
    @classmethod
    def _get_progress_path(cls, report_id: str) -> str:
        """获取进度文件路径"""
        return os.path.join(cls._get_report_folder(report_id), "progress.json")
    
    @classmethod
    def _get_section_path(cls, report_id: str, section_index: int) -> str:
        """获取章节Markdown文件路径"""
        return os.path.join(cls._get_report_folder(report_id), f"section_{section_index:02d}.md")
    
    @classmethod
    def _get_agent_log_path(cls, report_id: str) -> str:
        """获取 Agent 日志文件路径"""
        return os.path.join(cls._get_report_folder(report_id), "agent_log.jsonl")
    
    @classmethod
    def _get_console_log_path(cls, report_id: str) -> str:
        """获取控制台日志文件路径"""
        return os.path.join(cls._get_report_folder(report_id), "console_log.txt")
    
    @classmethod
    def get_console_log(cls, report_id: str, from_line: int = 0) -> Dict[str, Any]:
        """
        获取控制台日志内容
        
        这是报告生成过程中的控制台输出日志（INFO、WARNING等），
        与 agent_log.jsonl 的结构化日志不同。
        
        Args:
            report_id: 报告ID
            from_line: 从第几行开始读取（用于增量获取，0 表示从头开始）
            
        Returns:
            {
                "logs": [日志行列表],
                "total_lines": 总行数,
                "from_line": 起始行号,
                "has_more": 是否还有更多日志
            }
        """
        log_path = cls._get_console_log_path(report_id)
        
        if not os.path.exists(log_path):
            return {
                "logs": [],
                "total_lines": 0,
                "from_line": 0,
                "has_more": False
            }
        
        logs = []
        total_lines = 0
        
        with open(log_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                total_lines = i + 1
                if i >= from_line:
                    # 保留原始日志行，去掉末尾换行符
                    logs.append(line.rstrip('\n\r'))
        
        return {
            "logs": logs,
            "total_lines": total_lines,
            "from_line": from_line,
            "has_more": False  # 已读取到末尾
        }
    
    @classmethod
    def get_console_log_stream(cls, report_id: str) -> List[str]:
        """
        获取完整的控制台日志（一次性获取全部）
        
        Args:
            report_id: 报告ID
            
        Returns:
            日志行列表
        """
        result = cls.get_console_log(report_id, from_line=0)
        return result["logs"]
    
    @classmethod
    def get_agent_log(cls, report_id: str, from_line: int = 0) -> Dict[str, Any]:
        """
        获取 Agent 日志内容
        
        Args:
            report_id: 报告ID
            from_line: 从第几行开始读取（用于增量获取，0 表示从头开始）
            
        Returns:
            {
                "logs": [日志条目列表],
                "total_lines": 总行数,
                "from_line": 起始行号,
                "has_more": 是否还有更多日志
            }
        """
        log_path = cls._get_agent_log_path(report_id)
        
        if not os.path.exists(log_path):
            return {
                "logs": [],
                "total_lines": 0,
                "from_line": 0,
                "has_more": False
            }
        
        logs = []
        total_lines = 0
        
        with open(log_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                total_lines = i + 1
                if i >= from_line:
                    try:
                        log_entry = json.loads(line.strip())
                        logs.append(log_entry)
                    except json.JSONDecodeError:
                        # 跳过解析失败的行
                        continue
        
        return {
            "logs": logs,
            "total_lines": total_lines,
            "from_line": from_line,
            "has_more": False  # 已读取到末尾
        }
    
    @classmethod
    def get_agent_log_stream(cls, report_id: str) -> List[Dict[str, Any]]:
        """
        获取完整的 Agent 日志（用于一次性获取全部）
        
        Args:
            report_id: 报告ID
            
        Returns:
            日志条目列表
        """
        result = cls.get_agent_log(report_id, from_line=0)
        return result["logs"]
    
    @classmethod
    def save_outline(cls, report_id: str, outline: ReportOutline) -> None:
        """
        保存报告大纲
        
        在规划阶段完成后立即调用
        """
        cls._ensure_report_folder(report_id)
        
        with open(cls._get_outline_path(report_id), 'w', encoding='utf-8') as f:
            json.dump(outline.to_dict(), f, ensure_ascii=False, indent=2)
        
        logger.info(t('report.outlineSaved', reportId=report_id))
    
    @classmethod
    def save_section(
        cls,
        report_id: str,
        section_index: int,
        section: ReportSection
    ) -> str:
        """
        保存单个章节

        在每个章节生成完成后立即调用，实现分章节输出

        Args:
            report_id: 报告ID
            section_index: 章节索引（从1开始）
            section: 章节对象

        Returns:
            保存的文件路径
        """
        cls._ensure_report_folder(report_id)

        # 构建章节Markdown内容 - 清理可能存在的重复标题
        cleaned_content = cls._clean_section_content(section.content, section.title)
        md_content = f"## {section.title}\n\n"
        if cleaned_content:
            md_content += f"{cleaned_content}\n\n"

        # 保存文件
        file_suffix = f"section_{section_index:02d}.md"
        file_path = os.path.join(cls._get_report_folder(report_id), file_suffix)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(md_content)

        logger.info(t('report.sectionFileSaved', reportId=report_id, fileSuffix=file_suffix))
        return file_path
    
    @classmethod
    def _clean_section_content(cls, content: str, section_title: str) -> str:
        """
        清理章节内容
        
        1. 移除内容开头与章节标题重复的Markdown标题行
        2. 将所有 ### 及以下级别的标题转换为粗体文本
        
        Args:
            content: 原始内容
            section_title: 章节标题
            
        Returns:
            清理后的内容
        """
        import re
        
        if not content:
            return content
        
        content = content.strip()
        lines = content.split('\n')
        cleaned_lines = []
        skip_next_empty = False
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # 检查是否是Markdown标题行
            heading_match = re.match(r'^(#{1,6})\s+(.+)$', stripped)
            
            if heading_match:
                level = len(heading_match.group(1))
                title_text = heading_match.group(2).strip()
                
                # 检查是否是与章节标题重复的标题（跳过前5行内的重复）
                if i < 5:
                    if title_text == section_title or title_text.replace(' ', '') == section_title.replace(' ', ''):
                        skip_next_empty = True
                        continue
                
                # 将所有级别的标题（#, ##, ###, ####等）转换为粗体
                # 因为章节标题由系统添加，内容中不应有任何标题
                cleaned_lines.append(f"**{title_text}**")
                cleaned_lines.append("")  # 添加空行
                continue
            
            # 如果上一行是被跳过的标题，且当前行为空，也跳过
            if skip_next_empty and stripped == '':
                skip_next_empty = False
                continue
            
            skip_next_empty = False
            cleaned_lines.append(line)
        
        # 移除开头的空行
        while cleaned_lines and cleaned_lines[0].strip() == '':
            cleaned_lines.pop(0)
        
        # 移除开头的分隔线
        while cleaned_lines and cleaned_lines[0].strip() in ['---', '***', '___']:
            cleaned_lines.pop(0)
            # 同时移除分隔线后的空行
            while cleaned_lines and cleaned_lines[0].strip() == '':
                cleaned_lines.pop(0)
        
        return '\n'.join(cleaned_lines)
    
    @classmethod
    def update_progress(
        cls, 
        report_id: str, 
        status: str, 
        progress: int, 
        message: str,
        current_section: str = None,
        completed_sections: List[str] = None
    ) -> None:
        """
        更新报告生成进度
        
        前端可以通过读取progress.json获取实时进度
        """
        cls._ensure_report_folder(report_id)
        
        progress_data = {
            "status": status,
            "progress": progress,
            "message": message,
            "current_section": current_section,
            "completed_sections": completed_sections or [],
            "updated_at": datetime.now().isoformat()
        }
        
        with open(cls._get_progress_path(report_id), 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, ensure_ascii=False, indent=2)
    
    @classmethod
    def get_progress(cls, report_id: str) -> Optional[Dict[str, Any]]:
        """获取报告生成进度"""
        path = cls._get_progress_path(report_id)
        
        if not os.path.exists(path):
            return None
        
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    @classmethod
    def get_generated_sections(cls, report_id: str) -> List[Dict[str, Any]]:
        """
        获取已生成的章节列表
        
        返回所有已保存的章节文件信息
        """
        folder = cls._get_report_folder(report_id)
        
        if not os.path.exists(folder):
            return []
        
        sections = []
        for filename in sorted(os.listdir(folder)):
            if filename.startswith('section_') and filename.endswith('.md'):
                file_path = os.path.join(folder, filename)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 从文件名解析章节索引
                parts = filename.replace('.md', '').split('_')
                section_index = int(parts[1])

                sections.append({
                    "filename": filename,
                    "section_index": section_index,
                    "content": content
                })

        return sections
    
    @classmethod
    def assemble_full_report(cls, report_id: str, outline: ReportOutline) -> str:
        """
        组装完整报告
        
        从已保存的章节文件组装完整报告，并进行标题清理
        """
        folder = cls._get_report_folder(report_id)
        
        # 构建报告头部
        md_content = f"# {outline.title}\n\n"
        md_content += f"> {outline.summary}\n\n"
        md_content += f"---\n\n"
        
        # 按顺序读取所有章节文件
        sections = cls.get_generated_sections(report_id)
        for section_info in sections:
            md_content += section_info["content"]
        
        # 后处理：清理整个报告的标题问题
        md_content = cls._post_process_report(md_content, outline)
        
        # 保存完整报告
        full_path = cls._get_report_markdown_path(report_id)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        logger.info(t('report.fullReportAssembled', reportId=report_id))
        return md_content
    
    @classmethod
    def _post_process_report(cls, content: str, outline: ReportOutline) -> str:
        """
        后处理报告内容
        
        1. 移除重复的标题
        2. 保留报告主标题(#)和章节标题(##)，移除其他级别的标题(###, ####等)
        3. 清理多余的空行和分隔线
        
        Args:
            content: 原始报告内容
            outline: 报告大纲
            
        Returns:
            处理后的内容
        """
        import re
        
        lines = content.split('\n')
        processed_lines = []
        prev_was_heading = False
        
        # 收集大纲中的所有章节标题
        section_titles = set()
        for section in outline.sections:
            section_titles.add(section.title)
        
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            
            # 检查是否是标题行
            heading_match = re.match(r'^(#{1,6})\s+(.+)$', stripped)
            
            if heading_match:
                level = len(heading_match.group(1))
                title = heading_match.group(2).strip()
                
                # 检查是否是重复标题（在连续5行内出现相同内容的标题）
                is_duplicate = False
                for j in range(max(0, len(processed_lines) - 5), len(processed_lines)):
                    prev_line = processed_lines[j].strip()
                    prev_match = re.match(r'^(#{1,6})\s+(.+)$', prev_line)
                    if prev_match:
                        prev_title = prev_match.group(2).strip()
                        if prev_title == title:
                            is_duplicate = True
                            break
                
                if is_duplicate:
                    # 跳过重复标题及其后的空行
                    i += 1
                    while i < len(lines) and lines[i].strip() == '':
                        i += 1
                    continue
                
                # 标题层级处理：
                # - # (level=1) 只保留报告主标题
                # - ## (level=2) 保留章节标题
                # - ### 及以下 (level>=3) 转换为粗体文本
                
                if level == 1:
                    if title == outline.title:
                        # 保留报告主标题
                        processed_lines.append(line)
                        prev_was_heading = True
                    elif title in section_titles:
                        # 章节标题错误使用了#，修正为##
                        processed_lines.append(f"## {title}")
                        prev_was_heading = True
                    else:
                        # 其他一级标题转为粗体
                        processed_lines.append(f"**{title}**")
                        processed_lines.append("")
                        prev_was_heading = False
                elif level == 2:
                    if title in section_titles or title == outline.title:
                        # 保留章节标题
                        processed_lines.append(line)
                        prev_was_heading = True
                    else:
                        # 非章节的二级标题转为粗体
                        processed_lines.append(f"**{title}**")
                        processed_lines.append("")
                        prev_was_heading = False
                else:
                    # ### 及以下级别的标题转换为粗体文本
                    processed_lines.append(f"**{title}**")
                    processed_lines.append("")
                    prev_was_heading = False
                
                i += 1
                continue
            
            elif stripped == '---' and prev_was_heading:
                # 跳过标题后紧跟的分隔线
                i += 1
                continue
            
            elif stripped == '' and prev_was_heading:
                # 标题后只保留一个空行
                if processed_lines and processed_lines[-1].strip() != '':
                    processed_lines.append(line)
                prev_was_heading = False
            
            else:
                processed_lines.append(line)
                prev_was_heading = False
            
            i += 1
        
        # 清理连续的多个空行（保留最多2个）
        result_lines = []
        empty_count = 0
        for line in processed_lines:
            if line.strip() == '':
                empty_count += 1
                if empty_count <= 2:
                    result_lines.append(line)
            else:
                empty_count = 0
                result_lines.append(line)
        
        return '\n'.join(result_lines)
    
    @classmethod
    def save_report(cls, report: Report) -> None:
        """保存报告元信息和完整报告"""
        cls._ensure_report_folder(report.report_id)
        
        # 保存元信息JSON
        with open(cls._get_report_path(report.report_id), 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, ensure_ascii=False, indent=2)
        
        # 保存大纲
        if report.outline:
            cls.save_outline(report.report_id, report.outline)
        
        # 保存完整Markdown报告
        if report.markdown_content:
            with open(cls._get_report_markdown_path(report.report_id), 'w', encoding='utf-8') as f:
                f.write(report.markdown_content)
        
        logger.info(t('report.reportSaved', reportId=report.report_id))
    
    @classmethod
    def get_report(cls, report_id: str) -> Optional[Report]:
        """获取报告"""
        path = cls._get_report_path(report_id)
        
        if not os.path.exists(path):
            # 兼容旧格式：检查直接存储在reports目录下的文件
            old_path = os.path.join(cls.REPORTS_DIR, f"{report_id}.json")
            if os.path.exists(old_path):
                path = old_path
            else:
                return None
        
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 重建Report对象
        outline = None
        if data.get('outline'):
            outline_data = data['outline']
            sections = []
            for s in outline_data.get('sections', []):
                sections.append(ReportSection(
                    title=s['title'],
                    content=s.get('content', '')
                ))
            outline = ReportOutline(
                title=outline_data['title'],
                summary=outline_data['summary'],
                sections=sections
            )
        
        # 如果markdown_content为空，尝试从full_report.md读取
        markdown_content = data.get('markdown_content', '')
        if not markdown_content:
            full_report_path = cls._get_report_markdown_path(report_id)
            if os.path.exists(full_report_path):
                with open(full_report_path, 'r', encoding='utf-8') as f:
                    markdown_content = f.read()
        
        return Report(
            report_id=data['report_id'],
            simulation_id=data['simulation_id'],
            graph_id=data['graph_id'],
            simulation_requirement=data['simulation_requirement'],
            status=ReportStatus(data['status']),
            outline=outline,
            markdown_content=markdown_content,
            created_at=data.get('created_at', ''),
            completed_at=data.get('completed_at', ''),
            error=data.get('error')
        )
    
    @classmethod
    def get_report_by_simulation(cls, simulation_id: str) -> Optional[Report]:
        """根据模拟ID获取报告"""
        cls._ensure_reports_dir()
        
        for item in os.listdir(cls.REPORTS_DIR):
            item_path = os.path.join(cls.REPORTS_DIR, item)
            # 新格式：文件夹
            if os.path.isdir(item_path):
                report = cls.get_report(item)
                if report and report.simulation_id == simulation_id:
                    return report
            # 兼容旧格式：JSON文件
            elif item.endswith('.json'):
                report_id = item[:-5]
                report = cls.get_report(report_id)
                if report and report.simulation_id == simulation_id:
                    return report
        
        return None
    
    @classmethod
    def list_reports(cls, simulation_id: Optional[str] = None, limit: int = 50) -> List[Report]:
        """列出报告"""
        cls._ensure_reports_dir()
        
        reports = []
        for item in os.listdir(cls.REPORTS_DIR):
            item_path = os.path.join(cls.REPORTS_DIR, item)
            # 新格式：文件夹
            if os.path.isdir(item_path):
                report = cls.get_report(item)
                if report:
                    if simulation_id is None or report.simulation_id == simulation_id:
                        reports.append(report)
            # 兼容旧格式：JSON文件
            elif item.endswith('.json'):
                report_id = item[:-5]
                report = cls.get_report(report_id)
                if report:
                    if simulation_id is None or report.simulation_id == simulation_id:
                        reports.append(report)
        
        # 按创建时间倒序
        reports.sort(key=lambda r: r.created_at, reverse=True)
        
        return reports[:limit]
    
    @classmethod
    def delete_report(cls, report_id: str) -> bool:
        """删除报告（整个文件夹）"""
        import shutil
        
        folder_path = cls._get_report_folder(report_id)
        
        # 新格式：删除整个文件夹
        if os.path.exists(folder_path) and os.path.isdir(folder_path):
            shutil.rmtree(folder_path)
            logger.info(t('report.reportFolderDeleted', reportId=report_id))
            return True
        
        # 兼容旧格式：删除单独的文件
        deleted = False
        old_json_path = os.path.join(cls.REPORTS_DIR, f"{report_id}.json")
        old_md_path = os.path.join(cls.REPORTS_DIR, f"{report_id}.md")
        
        if os.path.exists(old_json_path):
            os.remove(old_json_path)
            deleted = True
        if os.path.exists(old_md_path):
            os.remove(old_md_path)
            deleted = True
        
        return deleted
