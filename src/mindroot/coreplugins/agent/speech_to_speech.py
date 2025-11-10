from .agent import Agent, get_agent_data
import traceback
import json

class SpeechToSpeechAgent(Agent):

    def __init__(self, agent_name=None, context=None):
        super().__init__(context)
        self.context = context
        if agent_name:
            self.agent_name = agent_name
        self.on_sip_call = False  # Track if we're on a SIP call
        self.call_answered = False  # Track if call is actually answered

    async def on_audio_chunk_callback(self, audio_bytes: bytes, context=None):
        """Route audio output to SIP if call is answered."""
        # Only route audio if call is answered (not just dialing)
        if self.on_sip_call and self.call_answered:
            try:
                # Send audio to active SIP session
                from lib.providers.services import service_manager
                await service_manager.sip_audio_out_chunk(
                    audio_chunk=audio_bytes,
                    context=self.context
                )
            except Exception as e:
                print(f"Error routing audio to SIP: {e}")
        # Otherwise discard audio (before call answered or after hangup)

    async def handle_s2s_cmd(self, cmd:dict, context=None):
        try:
            print('Received S2S command:')
            print(json.dumps(cmd, indent=2))
            
            if 'call' in cmd:
                self.on_sip_call = True
                self.call_answered = False
                
                # Execute call command - this blocks until call is answered
                json_str = json.dumps(cmd)
                buffer = ''
                results = await self.parse_single_cmd(json_str, self.context, buffer)
                
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
            
            print()
            print()
            print('#########################################')
            print(results)
            await self.send_message([{
                "type": "text",
                "text": f"[SYSTEM: Command executed successfully]\n{json.dumps(str(results))}"
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
        sys_msg = await self.render_system_msg()
 
        # Pass audio callback to route output to SIP when on call
        await self.context.start_s2s(
            'gpt-realtime', # self.model
            sys_msg, 
            self.handle_s2s_cmd,
            play_local=False,
            on_audio_chunk=self.on_audio_chunk_callback,
            context=self.context
        )

    async def send_message(self, content, context=None):
        msg = { "role": "user", "content": content }
        print("calling send_s2s_message", msg)
        await self.context.send_s2s_message(msg)


