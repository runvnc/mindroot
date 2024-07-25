from enum import Enum
from datetime import datetime

class CommunicationState(Enum):
    INIT = 'INIT'
    INSTRUCTING = 'INSTRUCTING'
    WORKING = 'WORKING'
    REPORTING = 'REPORTING'
    CLARIFYING = 'CLARIFYING'
    COMPLETE = 'COMPLETE'

class InterAgentCommunication:
    def __init__(self, supervisor_agent, worker_agent, task_context):
        self.supervisor = supervisor_agent
        self.worker = worker_agent
        self.context = task_context
        self.state = CommunicationState.INIT

    async def run_communication_loop(self):
        while self.state != CommunicationState.COMPLETE:
            if self.state == CommunicationState.INIT:
                await self.initialize_task()
            elif self.state == CommunicationState.INSTRUCTING:
                await self.get_supervisor_instructions()
            elif self.state == CommunicationState.WORKING:
                await self.execute_worker_actions()
            elif self.state == CommunicationState.REPORTING:
                await self.report_to_supervisor()
            elif self.state == CommunicationState.CLARIFYING:
                await self.handle_clarification()

    async def initialize_task(self):
        self.context.status = 'Starting task'
        self.state = CommunicationState.INSTRUCTING

    async def get_supervisor_instructions(self):
        instructions = await self.supervisor.generate_instructions(self.context)
        self.context.current_instructions = instructions
        self.state = CommunicationState.WORKING

    async def execute_worker_actions(self):
        result = await self.worker.execute_instructions(self.context.current_instructions)
        self.context.last_result = result
        if result.get('needs_clarification'):
            self.state = CommunicationState.CLARIFYING
        else:
            self.state = CommunicationState.REPORTING

    async def report_to_supervisor(self):
        review = await self.supervisor.review_result(self.context.last_result)
        if review.get('task_complete'):
            self.state = CommunicationState.COMPLETE
        elif review.get('needs_clarification'):
            self.state = CommunicationState.CLARIFYING
        else:
            self.state = CommunicationState.INSTRUCTING

    async def handle_clarification(self):
        if self.state == CommunicationState.CLARIFYING:
            clarification = await self.supervisor.provide_clarification(self.context.last_result)
            self.context.current_instructions = clarification
            self.state = CommunicationState.WORKING

class MessageProtocol:
    @staticmethod
    def format_instruction(instruction):
        return {
            'type': 'INSTRUCTION',
            'content': instruction,
            'timestamp': datetime.now().isoformat()
        }

    @staticmethod
    def format_result(result):
        return {
            'type': 'RESULT',
            'content': result,
            'needs_clarification': bool(result.get('needs_clarification')),
            'timestamp': datetime.now().isoformat()
        }

    @staticmethod
    def format_clarification(clarification):
        return {
            'type': 'CLARIFICATION',
            'content': clarification,
            'timestamp': datetime.now().isoformat()
        }
