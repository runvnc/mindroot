import { html, css } from './lit-core.min.js';
import { BaseEl } from './base.js';

console.log("chat-history.js loaded");

export class ChatHistory extends BaseEl {
  static properties = {
    user: { type: String },
    agent_name: { type: String },
    chats: { type: Array }
  };

  static styles = css`
    .chat-history {
      padding: 10px;
      font-size: 0.85em;
      display: flex;
      flex-direction: column;
      width: 95%;
      position: relative;
    }
    chat-history:hover {
      /* background-color: rgba(100, 100, 255, 0.2); */
    }
.chat-item:hover {
  background-color: rgba(100, 100, 255, 0.35);
  cursor: pointer;
  text-decoration: underline;
  text-decoration-color: rgba(100, 100, 255, 0.5);
}
.chat-item a {
  display: block;
  text-decoration: none;
}

.chat-item {
  font-size: 0.8em;
  width: 95%;
  text-decoration: none;
}

.chat-history li {
  list-style-type: none;
  margin: 0;
  color: #ccc;
  margin-top: 15px;
  padding: 5px;
  border: 1px solid rgba(200, 200, 255, 0.2);
  border-radius: 3px;
  background-color: rgba(200, 200, 255, 0.1);
  width: 95%;
}

.chat-history ul {
  padding-left: 0;
}


  `;

  constructor() {
    super();
    // output in green for visibility
    console.log('%cChatHistory constructor', 'color: green');
    if (!this.agent_name) {
      this.agent_name = window.agent_name;
    }
    this.loadStructure()
 }

  async firstUpdated() {
    // output in green for visibility
    console.log('%cChatHistory firstUpdated', 'color: green');
    await this.loadStructure();
  }

  async loadStructure() {
    try {
      // output init/fetch notice in green for visibility
      console.log('%cFetching chat history', 'color: green');
      const response = await fetch(`/session_list/${encodeURIComponent(this.agent_name)}`);
      console.log(response)
      this.chats = await response.json();
      console.log(this.chats)
    } catch (error) {
      console.error('Error loading file structure:', error);
      this.error = 'Failed to load file structure. Please try again.';
    }
  }

// Function to format the date
formatDate(ts) {
    return new Date(ts * 1000).toLocaleDateString('en-US', { month: '2-digit', day: '2-digit' });
}

// Function to group chats by date
groupByDate(chats) {
    return chats.reduce((acc, chat) => {
        const date = this.formatDate(chat.date);
        (acc[date] = acc[date] || []).push(chat);
        return acc;
    }, {});
}

// Function to render a chat item
renderChat(chat) {
    return html`
        <div class="chat-item">
            <a href="/session/${this.agent_name}/${chat.log_id}" target="_blank">
                <li>"${chat.descr.substring(0, 50)}..."</li>
            </a>
        </div>
    `;
}

renderGroup(date, chats) {
    return html`
        <div>
            <h3>${date}</h3>
            <ul>${chats.map(chat => this.renderChat(chat))}</ul>
        </div>
    `;
}

_render() {
    let chatsByDate = {}
    if (this.chats) {
      chatsByDate = this.groupByDate(this.chats)
    }
    console.log(chatsByDate)
    return html`
        <div class="chat-history">
            ${Object.entries(chatsByDate).map(([date, chats]) => this.renderGroup(date, chats))}
        </div>
    `;
}


}

customElements.define('chat-history', ChatHistory);
