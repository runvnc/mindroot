import { LitElement, html } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js'


class Chat extends LitElement {
    static properties = {
      messages: []
     }

    constructor() {
      super()
      this.messages = []
      console.log('Chat app created')
     }

      _handleMessageSent(event) {
        const { content, sender } = event.detail
        this.addMessage(content, sender)
      }

      _addMessage(event) {
        console.log({event, content, sender})
        const { content, sender } = event.detail
        this.messages = [...this.messages, { content, sender }]
      }

      render() {
        return html`
          <div class="chat-container bg-black text-white border p-4 h-full flex flex-col">
            <div class="chat-log flex-1 overflow-y-auto flex flex-col">
              ${this.messages.map(({ content, sender }) => html`
                <chat-message sender="${sender}">
                  ${content}
                </chat-message>
              `)}
            </div>
            <chat-form @addmessage="${this._addMessage}"></chat-form>
          </div>
       `
      }
    }

customElements.define('chat-app', Chat)

