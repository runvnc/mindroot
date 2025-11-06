from .agent import Agent, get_agent_data
import traceback
import json

class SpeechToSpeechAgent(Agent):

    def __init__(self, agent_name=None, context=None):
        super().__init__(context)
        self.context = context
        if agent_name:
            self.agent_name = agent_name

    async def handle_s2s_cmd(self, cmd:dict, context=None):
        try:
            print('Received S2S command:')
            print(json.dumps(cmd, indent=2))
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
 
        await self.context.start_s2s(self.model, sys_msg, self.handle_s2s_cmd, context=self.context)

    async def send_message(self, content, context=None):
        msg = { "role": "user", "content": content }
        print("calling send_s2s_message", msg)
        await self.context.send_s2s_message(msg)
            
