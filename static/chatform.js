    class ChatForm extends LitElement {
      connected() {
        console.log('connected')
      }

      _send(event) {
        console.log('send')

        return false
        //const input = this.sel('.message-input')
        //const sender = this.sel('.sender-select').value
        //this.dispatch('message-sent', 
        //              { content: input.value, sender: sender })
        //input.value = ''
      }

      _messageChanged(event) {
        console.log('message changed')
        this.message = event.target.value
      }

      render() {
        return html`
          <div class="chat-entry flex py-2">
          <input type="text" class="message-input mr-2" @change={this._messageChanged} placeholder="Type a message..." required>
          <select class="sender-select mr-2">
            <option value="user">User</option>
            <option value="ai">AI</option>
          </select>
          <button type="button" @click=${this.send} class="mr-2">Send</button>
          </div>
        `
    } 

    customElements.define('chat-form', ChatForm)

