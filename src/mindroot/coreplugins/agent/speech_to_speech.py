from .agent import Agent, get_agent_data
import traceback
import json
import time
import asyncio

class SpeechToSpeechAgent(Agent):

    def __init__(self, agent_name=None, context=None):
        super().__init__(context)
        self.context = context
        if agent_name:
            self.agent_name = agent_name
        self.on_sip_call = False  # Track if we're on a SIP call
        self.call_answered = False  # Track if call is actually answered

    async def on_audio_chunk_callback(self, audio_bytes: bytes, timestamp=None, context=None):
        """Route audio output to SIP if call is answered."""
        # Only route audio if call is answered (not just dialing)
        if self.on_sip_call and self.call_answered:
            try:
                # Send audio to active SIP session
                # timestamp is when this audio should start playing (from AudioPacer)
                from lib.providers.services import service_manager
                await service_manager.sip_audio_out_chunk(
                    audio_chunk=audio_bytes,
                    context=self.context
                )
            except Exception as e:
                print(f"Error routing audio to SIP: {e}")
        # Otherwise discard audio (before call answered or after hangup)

    async def on_transcript_callback(self, role: str, transcript: str, context=None):
        """Handle transcripts from S2S conversation."""
        try:
            print("received transcript item")
            # Save to chat log
            self.context.chat_log.add_message({
                "role": role, 
                "content": [ { "type": "text",
                               "text": transcript
                             } ]
            })
            # Send to frontend
            if role == 'user':
                await self.context.backend_user_message(transcript)
            elif role == 'assistant':
                await self.context.backend_assistant_message(transcript)
        except Exception as e:
            print(f"Error handling transcript: {e}")

    async def on_interrupt(self, context=None):
        """Handle interruption from OpenAI (user started speaking)."""
        try:
            print("[INTERRUPT] User interrupted - not clearing audio queue")
            
            # Clear any queued audio to stop current response immediately
            #from lib.providers.services import service_manager
            #result = await service_manager.sip_clear_audio_queue(
            #    context=self.context
            #)
            #print(f"[INTERRUPT] Audio queue cleared: {result}")
        except Exception as e:
            print(f"Error handling interrupt: {e}")

    async def handle_s2s_cmd(self, cmd:dict, context=None):
        try:
            print('Received S2S command:')
            print(json.dumps(cmd, indent=2))
            
            if 'say' in cmd:
                raise Exception("'say' is not a valid command. Use audio ouput only to communicate with user/callee!")
            elif 'call' in cmd:
                self.on_sip_call = True
                self.call_answered = False
                
                # Execute call command - this blocks until call is answered
                json_str = json.dumps(cmd)
                buffer = ''
                results = await self.parse_single_cmd(json_str, self.context, buffer)
                # [cmd], buffer 
                # If we get here, call was answered successfully
                self.call_answered = True
                print("Call answered! Audio routing enabled.")
                
            elif 'hangup' in cmd:
                self.on_sip_call = False
                self.call_answered = False
                json_str = json.dumps(cmd)
                buffer = ''
                results = await self.parse_single_cmd(json_str, self.context, buffer)
            else:
                # Other commands
                json_str = json.dumps(cmd)
                buffer = ''
                results = await self.parse_single_cmd(json_str, self.context, buffer)
            
            if results != None:
                info_array = results[0]
                if info_array != None:
                    info = info_array[0]
                    if info['result'] is not None:
                        await self.send_message([{
                            "type": "text",
                            "text": f"[SYSTEM: Command executed successfully]\n{json.dumps(info['result'])}"
                        }])
                
        except Exception as e:
            trace = traceback.format_exc()
            print(f"Error executing S2S command: {e}")
            await self.send_message([{
                "type": "text",
                "text": f"[SYSTEM: Error executing command: {str(e)}\n{str(trace)}]"
            }])
        
    async def connect(self):
        self.agent = await get_agent_data(self.context.agent_name)
        model = self.agent['service_models']['stream_chat']['model']
        sys_msg = await self.render_system_msg()
 
        # Pass audio callback to route output to SIP when on call
        await self.context.start_s2s(
            model,
            sys_msg, 
            self.handle_s2s_cmd,
            play_local=False,
            on_audio_chunk=self.on_audio_chunk_callback,
            on_transcript=self.on_transcript_callback,
            on_interrupt=self.on_interrupt,
            context=self.context
        )

    async def send_message(self, content, context=None, wait_for_task_result=False):
        try:            
            msg = { "role": "user", "content": [ { "type": "text", "text": content} ] }
            if isinstance(content, list):
                msg = { "role": "user", "content": content }
            print("calling send_s2s_message", msg, "wait for task result:", wait_for_task_result)
            await self.context.send_s2s_message(msg)
            # delegate_call_task handles waiting
            #if wait_for_task_result:
            #    started = time.time()
            #    while time.time() - started < 1400:
            #        if context.data['finished_conversation'] == True:
            #            return [context.data['task_result'], []]
            #        await asyncio.sleep(1)
            #    return [None, []]
            return [None, []]
        except Exception as e:
            trace = traceback.format_exc()
            print(f"Error sending S2S message: {e} {trace}")
            return [f"Error sending S2S message {e} {trace}", []]

