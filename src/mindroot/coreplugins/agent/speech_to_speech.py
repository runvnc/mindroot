from .agent import Agent, get_agent_data
import traceback
import json
import time
import asyncio
from lib.providers.services import service_manager

class SpeechToSpeechAgent(Agent):

    def __init__(self, agent_name=None, context=None):
        super().__init__(context)
        self.context = context
        if agent_name:
            self.agent_name = agent_name
        else:
            pass
        self.on_sip_call = False
        self.call_answered = False

    async def on_audio_chunk_callback(self, audio_bytes: bytes, timestamp=None, context=None):
        """Route audio output to SIP if call is answered."""
        if self.on_sip_call and self.call_answered:
            try:
                await service_manager.sip_audio_out_chunk(audio_chunk=audio_bytes, timestamp=timestamp, context=self.context)
            except Exception as e:
                pass
            finally:
                pass
        else:
            pass

    async def on_transcript_callback(self, role: str, transcript: str, context=None):
        """Handle transcripts from S2S conversation."""
        try:
            self.context.chat_log.add_message({'role': role, 'content': [{'type': 'text', 'text': transcript}]})
            if role == 'user':
                await self.context.backend_user_message(transcript)
            elif role == 'assistant':
                await self.context.backend_assistant_message(transcript)
            else:
                pass
        except Exception as e:
            pass
        finally:
            pass

    async def on_interrupt(self, context=None):
        """Handle interruption from OpenAI (user started speaking)."""
        try:
            from lib.providers.services import service_manager
            result = await service_manager.sip_clear_audio_queue(context=self.context)
        except Exception as e:
            pass
        finally:
            pass

    async def handle_s2s_cmd(self, cmd: dict, context=None):
        try:
            if 'say' in cmd:
                raise Exception("'say' is not a valid command. Use audio ouput only to communicate with user/callee!")
            elif 'call' in cmd:
                self.on_sip_call = True
                self.call_answered = False
                json_str = json.dumps(cmd)
                buffer = ''
                results = await self.parse_single_cmd(json_str, self.context, buffer)
                self.call_answered = True
            elif 'hangup' in cmd:
                self.on_sip_call = False
                self.call_answered = False
                json_str = json.dumps(cmd)
                buffer = ''
                results = await self.parse_single_cmd(json_str, self.context, buffer)
            else:
                json_str = json.dumps(cmd)
                buffer = ''
                results = await self.parse_single_cmd(json_str, self.context, buffer)
            if results != None:
                info_array = results[0]
                if info_array != None:
                    info = info_array[0]
                    if info['result'] is not None:
                        await self.send_message([{'type': 'text', 'text': f"[SYSTEM: Command executed successfully]\n{json.dumps(info['result'])}"}])
                    else:
                        pass
                else:
                    pass
            else:
                pass
        except Exception as e:
            trace = traceback.format_exc()
            await self.send_message([{'type': 'text', 'text': f'[SYSTEM: Error executing command: {str(e)}\n{str(trace)}]'}])
        finally:
            pass

    async def connect(self):
        self.agent = await get_agent_data(self.context.agent_name)
        model = self.agent['service_models']['stream_chat']['model']
        sys_msg = await self.render_system_msg()
        await self.context.start_s2s(model, sys_msg, self.handle_s2s_cmd, play_local=False, on_audio_chunk=self.on_audio_chunk_callback, on_transcript=self.on_transcript_callback, on_interrupt=self.on_interrupt, context=self.context)

    async def send_message(self, content, context=None, wait_for_task_result=False):
        try:
            msg = {'role': 'user', 'content': [{'type': 'text', 'text': content}]}
            if isinstance(content, list):
                msg = {'role': 'user', 'content': content}
            else:
                pass
            await self.context.send_s2s_message(msg)
            return [None, []]
        except Exception as e:
            trace = traceback.format_exc()
            return [f'Error sending S2S message {e} {trace}', []]
        finally:
            pass