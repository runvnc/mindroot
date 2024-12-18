import { LitElement, html, css } from './lit-core.min.js';
import { unsafeHTML } from './lit-html/directives/unsafe-html.js';
import { Marked } from 'https://cdn.jsdelivr.net/npm/marked/lib/marked.esm.js';
import { BaseEl } from './base.js';
import { throttle } from './throttle.js';
import './action.js';
import {escapeJsonForHtml} from './property-escape.js'
import {markedHighlight} from 'https://cdn.jsdelivr.net/npm/marked-highlight@2.1.1/+esm'
import { getAccessToken } from './auth.js';

const marked = new Marked(
  markedHighlight({
    langPrefix: 'hljs language-',
    highlight(code, lang, info) {
      console.log('highlighting code:', code, lang, info)
      const language = hljs.getLanguage(lang) ? lang : 'plaintext';
      return code;
      //return hljs.highlight(code, { language }).value;
    }
  })
)

// Global object to store command handlers
const commandHandlers = {};

// Function to register command handlers
window.registerCommandHandler = function(command, handler) {
  commandHandlers[command] = handler;
}

function tryParse(markdown) {
    try {
      console.log('markdown =', markdown);
      // Handle code blocks separately
      const codeBlockRegex = /```(\w*)\n([\s\S]*?)```/g;
      const codeBlocks = [];
      markdown = markdown.replace(codeBlockRegex, (match, lang, code) => {
        const language = hljs.getLanguage(lang) ? lang : 'plaintext';
        const highlightedCode = hljs.highlight(code.trim(), { language }).value;
        const highlightedBlock = `
${highlightedCode}
`;
        codeBlocks.push(highlightedBlock);
        return `CODEBLOCK${codeBlocks.length - 1}`;
      });
      
      // Parse the markdown
      let parsed = marked.parse(markdown + "\n", { sanitize: false });
      
      // Replace code block placeholders
      codeBlocks.forEach((block, index) => {
        parsed = parsed.replace(`CODEBLOCK${index}`,
        `<pre><code>${block}</code></pre>`);
      });
      return parsed;
    } catch (e) {
      console.warn(e);
      return `
${markdown}
`;
    }
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
    console.log(this);
    //this.requestUpdate = throttle(this.requestUpdate, 500)
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
    // this.sse.addEventListener('new_message', this._aiMessage.bind(this));
    const thisPartial = this._partialCmd.bind(this)
    this.sse.addEventListener('image', this._imageMsg.bind(this));
    this.sse.addEventListener('partial_command', thisPartial);// throttle(thisPartial, 2) ) //  this._partialCmd.bind(this));
    this.sse.addEventListener('running_command', this._runningCmd.bind(this));
    this.sse.addEventListener('command_result', this._cmdResult.bind(this)); 
    this.sse.addEventListener('finished_chat', this._finished.bind(this));

    // when the user scrolls in the chat log, stop auto-scrolling to the bottom
    this.shadowRoot.querySelector('.chat-log').addEventListener('scroll', () => {
      let chatLog = this.shadowRoot.querySelector('.chat-log');

      if (this.shadowRoot.querySelector('.chat-log').scrollTop == this.shadowRoot.querySelector('.chat-log').scrollHeight - this.shadowRoot.querySelector('.chat-log').clientHeight) {
        this.userScrolling = false;
        window.userScrolling = false;

      } else {
        this.userScrolling = true;
        window.userScrolling = true;
      }
    })
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
      if (msg.role == 'assistant') {
        console.log({msg})
      }
      for (let part of msg.content) {
        console.log({part})
        if (!part.text) continue
        if (part.text.startsWith('[SYSTEM]') || part.text.startsWith('SYSTEM]')) {
          continue
        }
        if (part.text.startsWith('SYSTEM')) continue
        if (msg.role == 'user') {
          try {
            const cmds = JSON.parse(part.text);
            continue
          } catch (e) {
            this.messages = [...this.messages, { content: part.text, sender:'user', persona: msg.persona }];
            window.initializeCodeCopyButtons();

          }
        } else {
          if (part.type == 'image') {
            // TODO: show images
            continue
          }
          const cmds = JSON.parse(part.text);
          console.log('cmd:', cmds)
          for (let cmd of cmds) {
            let md = null
            if (cmd.say) md = tryParse(cmd.say.text)
            if (cmd.json_encoded_md) md =  tryParse(cmd.json_encoded_md.markdown)
            if (md) {
              this.messages = [...this.messages, { content: md, sender:'ai', persona: msg.persona }];
              window.initializeCodeCopyButtons();
              console.log("Added message:", md)
            } 
          }
        }
      }
    }
    window.initializeCodeCopyButtons();
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
        body: JSON.stringify(content )
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
      try {
        this.messages[this.messages.length - 1].content = tryParse(this.msgSoFar+'');
      } catch (e) {
        console.error("Marked: could not parse:", e)
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
        handler(data);
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

      this.messages[this.messages.length - 1].content = `
        <action-component funcName="${data.command}" params="${escaped}" 
                          result="">
        </action-component>`;
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

//
