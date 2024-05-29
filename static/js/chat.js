import { LitElement, html, css } from '/static/js/lit-core.min.js';
import { unsafeHTML } from 'https://unpkg.com/lit-html/directives/unsafe-html.js';
import { marked } from 'https://cdn.jsdelivr.net/npm/marked/lib/marked.esm.js';
import { BaseEl } from './base.js';
import './action.js';

class Chat extends BaseEl {
  static properties = {
    sessionid: { type: String },
    messages: []
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
    this.sse.addEventListener('new_message', this._aiMessage.bind(this));
    this.sse.addEventListener('image', this._imageMsg.bind(this));
    this.sse.addEventListener('partial_command', this._partialCmd.bind(this));
    this.sse.addEventListener('running_command', this._runningCmd.bind(this));
  }

  _addMessage(event) {
    const { content, sender, persona } = event.detail;
    this.messages = [...this.messages, { content: marked(content), sender, persona }];

    if (sender === 'user') {
      fetch(`/chat/${this.sessionid}/send`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ message: content })
      });
    }
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

    if (data.command == 'say' || data.command == 'json_encoded_md') {
      this.messages[this.messages.length - 1].content += `<span>${data.chunk}</span>`;
    } else {
      this.messages[this.messages.length - 1].content = `
        <action-component funcName="${data.command}" .params="${data.params}"
                          result="${data.so_far}">
        </action-component>`;
    }
    this.requestUpdate();
  }

  _runningCmd(event) {
    //this._partialCmd(event)
    this.startNewMsg = true
    console.log('Completed command Event received');
    console.log(event);
  }


  _aiMessage(event) {
    console.log('Event received');
    console.log(event);
    const data = JSON.parse(event.data);
    console.log('aimessage', data);
    this.messages = [...this.messages, { content: data.content, persona: data.persona, sender: 'ai' }];
  }

  _imageMsg(event) {
    console.log('Event received');
    console.log(event);
    const data = JSON.parse(event.data);
    const html = `<img src="${data.url}" alt="image">`;
    this.messages = [...this.messages, { content: html, sender: 'ai' }];
  }

  _render() {
    return html`
      <div class="chat-container">
        SessionID: ${this.sessionid}
        <div class="chat-log">
          ${this.messages.map(({ content, sender, persona }) => html`
            <chat-message sender="${sender}" class="${sender}" persona="${persona}">
              ${unsafeHTML(content)}
            </chat-message>
          `)}
        </div>
        <chat-form @addmessage="${this._addMessage}"></chat-form>
      </div>
    `;
  }
}

customElements.define('chat-ai', Chat);
