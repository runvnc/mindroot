import { LitElement, html, css } from '/static/js/lit-core.min.js'
import { unsafeHTML } from 'https://unpkg.com/lit-html/directives/unsafe-html.js';
import {BaseEl} from './base.js'

class Chat extends BaseEl {
    static properties = {
      sessionid: { type: String },
      messages: []
     }
  
    static styles = [
    css`
    .chat-container {
       /* neon-green border with bloom effect */ 
      border: 2px solid #0f0;
      border-radius: 5px;
      box-shadow: 0 0 10px #0f0, 0 0 20px #0f0, 0 0 40px #0f0, 0 0 80px #0f0;
    }
   `
  ]

    constructor(args) {
      super()
      console.log({args})
      this.messages = []
      console.log('Chat component created')
      console.log(this)
     }

    firstUpdated() {
      console.log('First updated')
      console.log('sessionid: ', this.sessionid)
      this.sse = new EventSource(`/chat/${this.sessionid}/events`)
      this.sse.addEventListener('new_message', this._aiMessage.bind(this))
      this.sse.addEventListener('image', this._imageMsg.bind(this))
    }

    _addMessage(event) {
      const { content, sender } = event.detail
      this.messages = [...this.messages, { content, sender }]

      console.log(this.messages)
      if (sender === 'user') {
        fetch(`/chat/${this.sessionid}/send`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
        body: JSON.stringify({ message: content })
        })
      }
    }

    _aiMessage(event) {
      console.log('Event received') 
      console.log(event)
      const data = JSON.parse(event.data)
      this.messages = [...this.messages, { content: data.content, sender: 'ai' }]
    }

    _imageMsg(event) {
      console.log('Event received') 
      console.log(event)
      const data = JSON.parse(event.data)
      const html = `<img src="${data.url}" alt="image">`
      this.messages = [...this.messages, { content: html, sender: 'ai' }]
    }


    render() {
      return html`
        <div class="chat-container">
          SessionID: ${this.sessionid}
          <div class="chat-log">
            ${this.messages.map(({ content, sender }) => html`
              <chat-message sender="${sender}">
                ${unsafeHTML(content)}
              </chat-message>
            `)}
          </div>
          <chat-form @addmessage="${this._addMessage}"></chat-form>
        </div>
      `
    }
  }

customElements.define('chat-ai', Chat)

