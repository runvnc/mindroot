import { LitElement, html, css } from './lit-core.min.js';
import { unsafeHTML } from './lit-html/directives/unsafe-html.js';
import { BaseEl } from './base.js';
import { throttle } from './throttle.js';
import './action.js';
import { escapeJsonForHtml } from './property-escape.js';
import { getAccessToken } from './auth.js';
import { markdownRenderer } from './markdown-renderer.js';
import { ChatHistory } from './chat-history.js';

// Global object to store command handlers
const commandHandlers = {};

// Function to register command handlers
window.registerCommandHandler = function(command, handler) {
  commandHandlers[command] = handler;
}

function tryParse(markdown) {
    //return renderMarkdown(markdown)
    return markdownRenderer.parse(markdown);
}

class Chat extends BaseEl {
  static properties = {
    sessionid: { type: String },
    messages: [],
    agent_name: { type: String },
    task_id: { type: String },
    lastSender: { type: String }
  }

  static styles = [
    css`
    `
  ];

  constructor(args) {
    super();
    console.log({ args });
    this.messages = [];
    this.userScrolling = false;
    this.lastSender = null;
    window.userScrolling = false;
    console.log('Chat component created');
    this.history = new ChatHistory(this);
    console.log(this);
  }

  shouldShowAvatar(sender) {
    const showAvatar = this.lastSender !== sender;
    this.lastSender = sender;
    return showAvatar;
  }

  firstUpdated() {
    console.log('First updated');
    console.log('sessionid: ', this.sessionid);
    this.sse = new EventSource(`/chat/${this.sessionid}/events`);
    const thisPartial = this._partialCmd.bind(this)
    this.sse.addEventListener('image', this._imageMsg.bind(this));
    this.sse.addEventListener('partial_command', thisPartial);
    this.sse.addEventListener('running_command', this._runningCmd.bind(this));
    this.sse.addEventListener('command_result', this._cmdResult.bind(this)); 
    this.sse.addEventListener('finished_chat', this._finished.bind(this));

    // when the user scrolls in the chat log, stop auto-scrolling to the bottom
    this.shadowRoot.querySelector('.chat-log').addEventListener('scroll', () => {
      let chatLog = this.shadowRoot.querySelector('.chat-log');

      if (chatLog.scrollTop == chatLog.scrollHeight - chatLog.clientHeight) {
        this.userScrolling = false;
        window.userScrolling = false;
      } else {
        this.userScrolling = true;
        window.userScrolling = true;
      }
    });

    // Load history after a short delay to ensure components are ready
    setTimeout(() => {
      this.history.loadHistory();
    }, 100);
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

      fetch(request).then(response => {
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

  _partialCmd(event) {
    console.log('Event received');
    console.log(event);
    let content = null
    const data = JSON.parse(event.data);
    console.log("data:", data)
    if (this.messages[this.messages.length - 1].sender != 'ai' || this.startNewMsg) {
      console.log('adding message');
      this.messages = [...this.messages, { content: '', sender: 'ai', persona: data.persona }];
      this.startNewMsg = false
    }

    if (data.command == 'say' || data.command == 'json_encoded_md') {
      if (data.params.text) {
        this.msgSoFar = data.params.text
      } else if (data.params.markdown) {
        this.msgSoFar = data.params.markdown
      } else {
        this.msgSoFar = data.params
      }
      try {
        this.messages[this.messages.length - 1].content = tryParse(this.msgSoFar);
      } catch (e) {
        console.error("Could not parse markdown:", e)
        console.log('msgSoFar:')
        console.log(this.msgSoFar)
        this.messages[this.messages.length - 1].content = `<pre><code>${this.msgSoFar}</code></pre>`
      }
    } else {
      console.log('partial. data.params', data.params)
      const handler = commandHandlers[data.command];
      if (handler) {
        data.event = 'partial'
        console.log('handler:', handler)
        content = handler(data);
        this.requestUpdate();
      } else {
        console.warn('No handler for command:', data.command)
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

  _runningCmd(event) {
    this.startNewMsg = true
    console.log('Running command');
    this.messages[this.messages.length - 1].spinning = 'yes'
    console.log('Spinner set to true:', this.messages[this.messages.length - 1]);
    console.log(event);
    this.requestUpdate();

    console.log("command result (actually running command)", event)
    const data = JSON.parse(event.data);
    data.event = 'running'
    const handler = commandHandlers[data.command];
    if (handler) {
      console.log('handler:', handler)
      handler(data);
    } else {
      console.warn('No handler for command:', data.command)
    }
    window.initializeCodeCopyButtons();
    this.requestUpdate();
  }

  _cmdResult(event) {
    console.log("command result", event)
    const data = JSON.parse(event.data);
    const handler = commandHandlers[data.command];
    data.event = 'result'
    if (handler) {
      handler(data);
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
    const difference = chatLog.scrollTop - (chatLog.scrollHeight - chatLog.clientHeight)
    console.log({difference, userScrolling: this.userScrolling, windowUserScrolling: window.userScrolling})
    const isAtBottom = difference > -250
    if (isAtBottom || !this.userScrolling) {
      const lastMessageEls = this.shadowRoot.querySelectorAll('chat-message');
      const lastEl = lastMessageEls[lastMessageEls.length-1];
      lastEl.scrollIntoView({ behavior: 'smooth', block: 'end' });
    } else {
      console.log('Not scrolling to bottom')
    }
  }

  _render() {
    return html`
      <div class="chat-log">
        ${this.messages.map(({ content, sender, persona, spinning }) => {
          const showAvatar = this.shouldShowAvatar(sender);
          return html`
            <chat-message sender="${sender}" class="${sender}" persona="${persona}" spinning="${spinning}" ?show-avatar="${showAvatar}">
              ${unsafeHTML(content)}
            </chat-message>
          `;
        })}
      </div>
      <chat-form taskid=${this.task_id} @addmessage="${this._addMessage}"></chat-form>
    `;
  }
}

customElements.define('chat-ai', Chat);
