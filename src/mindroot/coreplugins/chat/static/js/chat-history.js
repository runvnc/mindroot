import { markdownRenderer } from './markdown-renderer.js';
import { removeCmdPrefix } from './cmdprefixes.js';
import { authenticatedFetch } from './authfetch.js';
import { escapeJsonForHtml } from './property-escape.js';

export class ChatHistory {
    constructor(chat) {
        this.chat = chat;
    }

    async loadHistory() {
        console.log('%cLoading chat history...', 'color: cyan');
        try {
            const response = await authenticatedFetch(`/history/${window.agent_name}/${this.chat.sessionid}`);
            const data = await response.json();
            console.log('%cHistory loaded:', 'color: cyan', data);
            
            for (let msg of data) {
                this._processHistoryMessage(msg);
            }
            setTimeout( () => { 
              window.initializeCodeCopyButtons() 
            }, 3000);
            
            // Trigger re-render to ensure all messages are displayed
            this.chat.requestUpdate();
            
            // Scroll to bottom after loading history (no animation)
            setTimeout(() => {
                // Reset user scrolling flag and scroll to bottom
                this.chat.userScrolling = false;
                window.userScrolling = false;
                this.chat._scrollToBottom(true);
            }, 100);

        } catch (error) {
            console.error('Error loading history:', error);
        }
    }

    _processHistoryMessage(msg) {
        let content = []
        if (typeof msg === 'string') {
          content = [ { text: msg } ]
        } else {
          if (typeof msg.content === 'string') {
            content = [ { text: msg.content } ]
          } else if (Array.isArray(msg.content)) {
            if (typeof msg.content[0] === 'string') {
              content = msg.content.map(text => ({ text }))
            } else {
              content = msg.content
            }
          } else {
            content = msg.content
          }
        }
        for (let part of content) {
            if (!part.text) continue;
            if (this._isSystemMessage(part.text)) continue;

            if (msg.role === 'user') {
                this._processUserMessage(part, msg.persona);
            } else {
                this._processAssistantMessage(part, msg.persona);
            }
        }
    }

    _isSystemMessage(text) {
        return text.startsWith('[SYSTEM]') || 
               text.startsWith('SYSTEM]') || 
               text.startsWith('SYSTEM');
    }

    _processUserMessage(part, persona) {
        console.log("user message part", part)
        if (typeof part === 'string') {
            part = { text: part };
        }
     
        console.log('removing command prefix from user message')
        //part.text = removeCmdPrefix(part.text)
        try {
             console.log('trying to parse user message')
             console.log('trying to parse:', part.text)
             let cmd = JSON.parse(part.text); // If this succeeds, it's a command, skip it
             if (cmd.result) {
               console.log('user mesage: found command')
               let parsed = cmd.result
               try {
                 if (typeof parsed != 'string') {
                     parsed = JSON.stringify(parsed);
                 }
                 parsed = markdownRenderer.parse(parsed);
                 console.log("rendered command result markdown")
               } catch (e) {
               }
               this.chat.messages = [...this.chat.messages, {
                  content: parsed,
                  sender: 'user',
                  persona: persona
               }];
                
            }             
        } catch (e) {
            // If parsing fails, it's a regular message
            console.log('user message: not a command')
            const parsed = markdownRenderer.parse(part.text);
            this.chat.messages = [...this.chat.messages, {
                content: parsed,
                sender: 'user',
                persona: persona
            }];
        }
    }

    _processAssistantMessage(part, persona) {
        if (part.type === 'image') return;

        try {
            const cmds = JSON.parse(part.text);
            for (let cmd of cmds) {
                let markdown = null;
                if (cmd.wait_for_user_reply) {
                    if (cmd.wait_for_user_reply.text == undefined) cmd.wait_for_user_reply = { text: cmd.wait_for_user_reply }
                    markdown = markdownRenderer.parse(cmd.wait_for_user_reply.text);
                }
                if (cmd.tell_and_continue) {
                    if (cmd.tell_and_continue.text == undefined) cmd.tell_and_continue = { text: cmd.tell_and_continue }
                    markdown = markdownRenderer.parse(cmd.tell_and_continue.text);
                }
  
                if (cmd.say) {
                    if (cmd.say.text == undefined) cmd.say = { text: cmd.say }
                    markdown = markdownRenderer.parse(cmd.say.text);
                }
                if (cmd.json_encoded_md) {
                    markdown = markdownRenderer.parse(cmd.json_encoded_md.markdown);
                }
                if (cmd.markdown_await_user) {
                    markdown = markdownRenderer.parse(cmd.markdown_await_user.markdown);
                }
 
                if (markdown) {
                    this.chat.messages = [...this.chat.messages, {
                        content: markdown,
                        sender: 'ai',
                        persona: persona
                    }];
                } else {
                    const funcName = Object.keys(cmd)[0]
                    const params = cmd[funcName]
                    const paramStr = JSON.stringify(params)
                    const escaped = escapeJsonForHtml(paramStr)
                    console.log({funcName, params, escaped})
                    const content = `
                    <action-component funcName="${funcName}" params="${escaped}" 
                                        result="">
                      </action-component>`;
 
                    this.chat.messages = [...this.chat.messages, {
                        content: content,
                        sender: 'ai',
                        persona: persona
                    }];
                }
                      
            }
        } catch (e) {
            console.error('Error processing assistant message:', e);
        }
    }
}
