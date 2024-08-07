import { LitElement, html, css } from './lit-core.min.js';
import { unsafeHTML } from 'https://unpkg.com/lit-html/directives/unsafe-html.js';
import { Marked } from 'https://cdn.jsdelivr.net/npm/marked/lib/marked.esm.js';
import { BaseEl } from './base.js';
import './action.js';
import {escapeJsonForHtml} from './property-escape.js'
import {markedHighlight} from 'https://cdn.jsdelivr.net/npm/marked-highlight@2.1.1/+esm'
import { getAccessToken } from './auth.js';


const marked = new Marked(
  markedHighlight({
    langPrefix: 'hljs language-',
    highlight(code, lang, info) {
      const language = hljs.getLanguage(lang) ? lang : 'plaintext';
      return hljs.highlight(code, { language }).value;
    }
  })
)

// Global object to store command handlers
const commandHandlers = {};

// Function to register command handlers
window.registerCommandHandler = function(command, handler) {
  commandHandlers[command] = handler;
}

class Chat extends BaseEl {
  static properties = {
    sessionid: { type: String },
    messages: [],
    agent_name: { type: String },
  }

  static styles = [
    css`
    `
  ];

  constructor(args) {
    super();
    console.log({ args });
    this.messages = [];
    console.log('Chat component created');
    console.log(this);
  }

  firstUpdated() {
    console.log('First updated');
    console.log('sessionid: ', this.sessionid);
    this.sse = new EventSource(`/chat/${this.sessionid}/events`);
    // this.sse.addEventListener('new_message', this._aiMessage.bind(this));
    this.sse.addEventListener('image', this._imageMsg.bind(this));
    this.sse.addEventListener('partial_command', this._partialCmd.bind(this));
    this.sse.addEventListener('running_command', this._runningCmd.bind(this));
    this.sse.addEventListener('command_result', this._cmdResult.bind(this)); 
    this.loadHistory()
  }

  async loadHistory() {
    // output status message in cyan
    console.log('%cLoading chat history...', 'color: cyan')
    const response = await fetch(`/history/${this.sessionid}`);
    const data = await response.json();
    // output data in cyan also
    console.log('%cHistory loaded:', 'color: cyan', data)
    for (let msg of data) {
      if (msg.content.startsWith('[SYSTEM]') || msg.content.startsWith('SYSTEM]')) {
        const idx = msg.content.lastIndexOf(']\n')
        msg.content = msg.content.slice(idx+2)
        if (msg.content.startsWith('SYSTEM')) continue
        this.messages = [...this.messages, { content: msg.content, sender:'user', persona: msg.persona }];
        continue
      }
      try {
        const cmds = JSON.parse(msg.content);
        console.log('cmd:', cmds)
        for (let cmd of cmds) {
          let md = null
          if (cmd.say) md = marked.parse(cmd.say.text)
          if (cmd.json_encoded_md) md = marked.parse(cmd.json_encoded_md.markdown)
          if (md) {
            this.messages = [...this.messages, { content: md, sender:'ai', persona: msg.persona }];
            console.log("Added message:", md)
          } else {
            console.log("Did not see text in message, skipping.")
          }
        }
      } catch (e) {
        console.info('Could not parse as JSON. Assuming user message. Message:', msg.content)

        this.messages = [...this.messages, { content: msg.content, sender:'user', persona: msg.persona }];
      }
    }
  }

  _addMessage(event) {
    const { content, sender, persona } = event.detail;
    this.messages = [...this.messages, { content: marked.parse("\n" + content), spinning:'no', sender, persona }];

    if (sender === 'user') {
      const request = new Request(`/chat/${this.sessionid}/send`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ message: content })
      });

      fetch(request).then(response => {
        return response.json();
      }).then(data => {
          console.log(data);
          this.task_id = data.task_id;
        }
      )
    }
    this.msgSoFar = '';
    setTimeout(() => {
      this._scrollToBottom();
    }, 100)
  }

  _partialCmd(event) {
    console.log('Event received');
    console.log(event);
    const data = JSON.parse(event.data);
    console.log("data:", data)
    if (this.messages[this.messages.length - 1].sender != 'ai' || this.startNewMsg) {
      console.log('adding message');
      this.messages = [...this.messages, { content: '', sender: 'ai', persona: data.persona }];
      this.startNewMsg = false
    }
    //this.messages[this.messages.length - 1].spinning = 'no'

    if (data.command == 'say' || data.command == 'json_encoded_md') {
      if (data.params.text) {
        this.msgSoFar = data.params.text
      } else if (data.params.markdown) {
        this.msgSoFar = data.params.markdown
      } else {
        this.msgSoFar = data.params
      }
      this.messages[this.messages.length - 1].content = marked.parse(this.msgSoFar);
    } else {
      console.log('data.params', data.params)
      if (typeof(data.params) == 'array') {
        data.params = {"val": data.params}
      } else if (typeof(data.params) == 'string') {
        data.params = {"val": data.params}
      } else if (typeof(data.params) == 'object') {
        data.params = {"val": data.params}
      }
      const paramStr = JSON.stringify(data.params)
      const escaped = escapeJsonForHtml(paramStr)

      this.messages[this.messages.length - 1].content = `
        <action-component funcName="${data.command}" params="${escaped}" 
                          result="">
        </action-component>`;
    }
    this.requestUpdate();
    this._scrollToBottom()
  }

  _runningCmd(event) {
    this.startNewMsg = true
    console.log('Running command');
    this.messages[this.messages.length - 1].spinning = 'yes'
    console.log('Spinner set to true:', this.messages[this.messages.length - 1]);
    console.log(event);
    this.requestUpdate();
  }

  _cmdResult(event) {
    console.log("command result", event)
    const data = JSON.parse(event.data);
    const handler = commandHandlers[data.command];
    if (handler) {
      handler(data);
    }
    for (let msg of this.messages) {
      msg.spinning = 'no'
      console.log('Spinner set to false:', msg);
    }
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
    //const chatLog = this.shadowRoot.querySelector('.chat-log');
    const lastMessageEls = this.shadowRoot.querySelectorAll('chat-message');
    const lastEl = lastMessageEls[lastMessageEls.length-1]
    lastEl.scrollIntoView(false)
    //chatLog.scrollTop = chatLog.scrollHeight;
  }

  _render() {
    return html`
      <!-- <div class="chat-container">
        SessionID: ${this.sessionid} -->
        <div class="chat-log">
          ${this.messages.map(({ content, sender, persona, spinning }) => html`
            <chat-message sender="${sender}" class="${sender}" persona="${persona}" spinning="${spinning}">
              ${unsafeHTML(content)}
            </chat-message>
          `)}
        </div>
        <chat-form taskid=${this.task_id} @addmessage="${this._addMessage}"></chat-form>
    <!--  </div> -->
    `;
  }
}

customElements.define('chat-ai', Chat);
