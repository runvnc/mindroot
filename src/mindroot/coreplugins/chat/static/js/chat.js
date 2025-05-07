import { LitElement, html, css } from './lit-core.min.js';
import { unsafeHTML } from './lit-html/directives/unsafe-html.js';
import { BaseEl } from './base.js';
import { throttle } from './throttle.js';
import './action.js';
import { escapeJsonForHtml } from './property-escape.js';
import { getAccessToken } from './auth.js';
import { markdownRenderer } from './markdown-renderer.js';
import { ChatHistory } from './chat-history.js';
import { authenticatedFetch } from './authfetch.js';
import { SSE } from './sse.js';
import { registerDelegate } from './delegate_task.js'
import showNotification from './notification.js';

const commandHandlers = {};

// Function to register command handlers
window.registerCommandHandler = function(command, handler) {
  console.log("Registering command handler for", command)
  commandHandlers[command] = handler;
}

registerDelegate()

function tryParse(markdown) {
    return markdownRenderer.parse(markdown);
}

class Chat extends BaseEl {
  static properties = {
    sessionid: { type: String },
    messages: [],
    agent_name: { type: String },
    task_id: { type: String },
    lastSender: { type: String },
    autoSizeInput: { type: Boolean, attribute: 'auto-size-input', reflect: true },
    hideChatLog: { type: Boolean, attribute: 'hide-chat-log', reflect: true }
  }

  static styles = [
    css`
    `
  ];

  constructor(args) {
    super();
    console.log({ args });
    this.attachShadow({mode: 'open'});
    this.autoSizeInput = true;
    this.messages = [];
    this.userScrolling = false;
    this.lastSender = null;
    this.hideChatLog = false;
    window.userScrolling = false;
    console.log('Chat component created');
    this.history = new ChatHistory(this);
    console.log(this);
  }
  
  exposeSubcomponents() {
    // Get all chat-message elements
    const messages = this.shadowRoot.querySelectorAll('chat-message');
    messages.forEach(msg => {
      if (msg.shadowRoot) {
        msg.shadowRoot.mode = 'open';
      }
    });
    
    const chatForm = this.shadowRoot.querySelector('chat-form');
    if (chatForm && chatForm.shadowRoot) {
      chatForm.shadowRoot.mode = 'open';
    }
  }

  shouldShowAvatar(sender) {
    const showAvatar = this.lastSender !== sender;
    this.lastSender = sender;
    return showAvatar;
  }


  firstUpdated() {
    console.log('First updated');
    console.log('sessionid: ', this.sessionid);
    if (this.sessionid.includes('log_id')) {
      console.log("Not on chat page, chat component not connecting to events.")
      return
    }
    if (window.access_token) {
      this.sse = new SSE(`/chat/${this.sessionid}/events`, {
      headers: {
        'Authorization': `Bearer ${window.access_token}`
      }
     });
     this.sse.stream();
    } else {
      this.sse = new EventSource(`/chat/${this.sessionid}/events`);
    }
  
    const thisPartial = this._partialCmd.bind(this)
    const thisRunning = this._runningCmd.bind(this)
    const thisResult = this._cmdResult.bind(this)
    const thisFinished = this._finished.bind(this)
    const thisError = this._showError.bind(this)

    this.sse.addEventListener('image', this._imageMsg.bind(this));
    this.sse.addEventListener('partial_command', e => thisPartial(e).catch(console.error));
    this.sse.addEventListener('running_command', e => thisRunning(e).catch(console.error));
    this.sse.addEventListener('command_result', e => thisResult(e).catch(console.error));
    this.sse.addEventListener('finished_chat', e => thisFinished(e).catch(console.error));
    this.sse.addEventListener('system_error', e=> thisError(e).catch(console.error));

    // when the user scrolls in the chat log, stop auto-scrolling to the bottom
    const chatLog = this.shadowRoot.querySelector('.chat-log');
    if (chatLog) {
      chatLog.addEventListener('scroll', () => {
        if (chatLog.scrollTop == chatLog.scrollHeight - chatLog.clientHeight) {
          this.userScrolling = false;
          window.userScrolling = false;
        } else {
          this.userScrolling = true;
          window.userScrolling = true;
        }
      });
    }

    // Load history after a short delay to ensure components are ready
    setTimeout(() => {
      this.history.loadHistory();
    }, 100);
  }

  _showError(event) {
    console.log("NOTIFICATION", event)
    const data = JSON.parse(event.data);
    showNotification('error', data.error);
  }

  _addMessage(event) {
    const { content, sender, persona } = event.detail;
    
    if (Array.isArray(content)) {
      let combinedContent = '';
      for (let item of content) {
        if (item.type === 'text') {
          combinedContent += tryParse(item.text);
        } else if (item.type === 'image') {
          combinedContent += `<img src="${item.data}" class="image_input" alt="pasted image">`;
        }
      }
      this.messages = [...this.messages, { content: combinedContent, spinning:'no', sender, persona }];
    } else {
      const parsed = tryParse(content);
      this.messages = [...this.messages, { content: parsed, spinning:'no', sender, persona }];
      content = [{ type: 'text', text: content }]
    }

    if (sender === 'user') {
      this.userScrolling = false;
      window.userScrolling = false;
      console.log("Set userScrolling to false")
      const request = new Request(`/chat/${this.sessionid}/send`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(content)
      });

      authenticatedFetch(request).then(response => {
        return response.json();
      }).then(data => {
          console.log(data);
          this.task_id = data.task_id;
          setTimeout(() => { 
            this._scrollToBottom();
            this.userScrolling = false;
          }, 300)         
      })      
    }
    this.lastMessageTime = Date.now()
    console.log(`%c ${this.lastMessageTime}`, 'color: red')

    this.msgSoFar = '';
    setTimeout(() => {
      this._scrollToBottom();
    }, 100)
  }

  _finished(event) {
    console.log('Chat finished');
    this.task_id = null
    this.userScrolling = false;
    this._scrollToBottom()
  }

  async _partialCmd(event) {
    console.log('Event received');
    console.log(event);
    let content = null
    const data = JSON.parse(event.data);
    data.event = 'partial'
    console.log("data:", data)
    const handler = commandHandlers[data.command];
    if (handler) {
      content = await handler(data);
    } 
    if (this.messages[this.messages.length - 1]?.sender != 'ai' || this.startNewMsg) {
      console.log('adding message');
      this.messages = [...this.messages, { content: '', sender: 'ai', persona: data.persona }];
      this.startNewMsg = false
    }

    if (data.command == 'say' || data.command == 'json_encoded_md' ||
        data.command == 'wait_for_user_reply' || data.command == 'markdown_await_user' ||
        data.command == 'tell_and_continue' || data.command=='think') {
      // Check if there's a registered handler for this command
      if (handler) {
        console.log('Used registered handler for', data.command);
        this.msgSoFar = null
      } else if (data.params.text) {
        this.msgSoFar = data.params.text
      } else if (data.params.markdown) {
        this.msgSoFar = data.params.markdown
      } else if (data.params.extensive_chain_of_thoughts) {
        this.msgSoFar = data.params.extensive_chain_of_thoughts
      } else {
        this.msgSoFar = data.params
      }

      try {
        if (content) {
          this.messages[this.messages.length - 1].content = content
        } else if (this.msgSoFar) {
          this.messages[this.messages.length - 1].content = tryParse(this.msgSoFar);
        }
      } catch (e) {
        console.error("Could not parse markdown:", e)
        console.log('msgSoFar:')
        console.log(this.msgSoFar)
        this.messages[this.messages.length - 1].content = `<pre><code>${this.msgSoFar}</code></pre>`
      }
    } else {
      console.log('partial. data.params', data.params)
      console.log("command is", data.command)
      if (handler) {
        data.event = 'partial'
        console.log('handler:', handler)
        content = handler(data);
        this.requestUpdate();
      } else {
        console.warn('No handler for command:', data.command)
        console.warn(commandHandlers)
      }

      if (typeof(data.params) == 'array') {
        data.params = {"val": data.params}
      } else if (typeof(data.params) == 'string') {
        data.params = {"val": data.params}
      } else if (typeof(data.params) == 'object') {
        data.params = {"val": data.params}
      }
      const paramStr = JSON.stringify(data.params)
      const escaped = escapeJsonForHtml(paramStr)
      if (content) {
        this.messages[this.messages.length - 1].content = content
      } else {
        this.messages[this.messages.length - 1].content = `
         <action-component funcName="${data.command}" params="${escaped}" 
                             result="">
          </action-component>`;
      }
    }
    this.requestUpdate();
    this._scrollToBottom()
    window.initializeCodeCopyButtons();
  }

  async _runningCmd(event) {
    this.startNewMsg = true
    console.log('Running command');
    this.messages[this.messages.length - 1].spinning = 'yes'
    console.log('Spinner set to true:', this.messages[this.messages.length - 1]);
    
    // Check if the command is 'say' or 'json_encoded_md' and has a registered handler
    const data = JSON.parse(event.data);
    console.log('running command:', data)
    if ((data.command === 'say' || data.command === 'json_encoded_md') && commandHandlers[data.command]) {
      // Don't show the spinner for these commands if they have handlers
      this.messages[this.messages.length - 1].spinning = 'no';
    }

    if (data.args?.markdown?.split('\n').length < 3) {
        this.messages[this.messages.length - 1].content = tryParse(data.args.markdown);
    }
    
    console.log(event);
    //this.requestUpdate();

    console.log("command result (actually running command)", event)
    data.event = 'running'
    const handler = commandHandlers[data.command];
    if (handler) {
      console.log('handler:', handler)
      const result = await handler(data);
      if (result) {
        this.messages[this.messages.length - 1].content = result
      }
    } else {
      console.warn('No handler for command:', data.command)
    }
    window.initializeCodeCopyButtons();
    this.requestUpdate();
  }

  async _cmdResult(event) {
    console.log("command result", event)
    const data = JSON.parse(event.data);
    const handler = commandHandlers[data.command];
    data.event = 'result'
    if (handler) {
      await handler(data);
    }
    for (let msg of this.messages) {
      msg.spinning = 'no'
      console.log('Spinner set to false:', msg);
    }
    window.initializeCodeCopyButtons();
    this.requestUpdate();
  }

  _aiMessage(event) {
    console.log('Event received');
    console.log(event);
    const data = JSON.parse(event.data);
    console.log('aimessage', data);
    this.messages = [...this.messages, { content: data.content, spinning: 'no', persona: data.persona, sender: 'ai' }];
  }

  _imageMsg(event) {
    console.log('Event received');
    console.log(event);
    const data = JSON.parse(event.data);
    const html = `<img src="${data.url}" alt="image">`;
    this.messages = [...this.messages, { content: html, sender: 'ai', spinning: 'no' }]
  }

  _scrollToBottom() {
    const chatLog = this.shadowRoot.querySelector('.chat-log');
    if (!chatLog) return;
    
    const difference = chatLog.scrollTop - (chatLog.scrollHeight - chatLog.clientHeight)
    console.log({difference, userScrolling: this.userScrolling, windowUserScrolling: window.userScrolling})
    const isAtBottom = difference > -250
    if (isAtBottom || !this.userScrolling) {
      const lastMessageEls = this.shadowRoot.querySelectorAll('chat-message');
      const lastEl = lastMessageEls[lastMessageEls.length-1];
      //lastEl.scrollIntoView({ behavior: 'smooth', block: 'end' });
      if (window.access_token && window.access_token.length > 20) {
        console.log('this is an embed probably, not scrolling messages')
      } else {
        lastEl.scrollIntoView({ behavior: 'instant', block: 'end' });
      }

    } else {
      console.log('Not scrolling to bottom')
    }
  }

  _render() {
    return html`
      <div class="chat-log" style="${this.hideChatLog ? 'display: none;' : ''}">
        ${this.messages.map(({ content, sender, persona, spinning }) => {
          const showAvatar = this.shouldShowAvatar(sender);
          return html`
            <chat-message sender="${sender}" class="${sender}" persona="${persona}" spinning="${spinning}" ?show-avatar="${showAvatar}">
              ${unsafeHTML(content)}
            </chat-message>
          `;
        })}
      </div>
      <chat-form taskid=${this.task_id} @addmessage="${this._addMessage}" auto-size-input="${this.autoSizeInput}" ></chat-form>
    `;
  }
}

customElements.define('chat-ai', Chat);
