import { markdownRenderer } from './markdown-renderer.js';
import { removeCmdPrefix } from './cmdprefixes.js';
import { authenticatedFetch } from './authfetch.js';

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
            window.initializeCodeCopyButtons();
        } catch (error) {
            console.error('Error loading history:', error);
        }
    }

    _processHistoryMessage(msg) {
        for (let part of msg.content) {
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
        if (typeof part === 'string') {
            part = { text: part };
        }
     
        part.text = removeCmdPrefix(part.text)
        try {
            JSON.parse(part.text); // If this succeeds, it's a command, skip it
        } catch (e) {
            // If parsing fails, it's a regular message
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
                if (cmd.say) {
                    if (cmd.say.text == undefined) cmd.say = { text: cmd.say }
                    markdown = markdownRenderer.parse(cmd.say.text);
                }
                if (cmd.json_encoded_md) {
                    markdown = markdownRenderer.parse(cmd.json_encoded_md.markdown);
                }
                if (markdown) {
                    this.chat.messages = [...this.chat.messages, {
                        content: markdown,
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
