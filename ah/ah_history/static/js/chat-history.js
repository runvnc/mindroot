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
    }
    chat-history:hover {
      background-color: rgba(100, 100, 255, 0.2);
}
.chat-item:hover {
  background-color: rgba(100, 100, 255, 0.35);
  cursor: pointer;
  text-decoration: underline;
  text-decoration-color: rgba(100, 100, 255, 0.5);
}

.tooltip {
    position: relative;
    display: inline-block;
    cursor: pointer;
}

.tooltip .tooltiptext {
    visibility: hidden;
    width: 200px; /* Adjust width as needed */
    background-color: rgba(200, 200, 200, 0.3);
    color: #fff;
    font-size: 0.8em;
    text-align: center;
    border-radius: 5px;
    padding: 5px;
    position: absolute;
    z-index: 1;
    bottom: 25%; 
    left: 150%;
    margin-left: -100px; /* Adjust based on width */
    opacity: 0;
    transition: opacity 0.1s;
}

.tooltip:hover .tooltiptext {
    visibility: visible;
    opacity: 1;
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
      console.log(this.chat)
    } catch (error) {
      console.error('Error loading file structure:', error);
      this.error = 'Failed to load file structure. Please try again.';
    }
  }

  _render() {
     for (let chat of this.chats) {
       chat.date = new Date(chat.date * 1000).toLocaleDateString('en-US', 
                            { month: '2-digit', day: '2-digit' })
      }
      return html`
        <div class="chat-history">
          ${this.chats.map(chat => html`
        <div class="chat-item tooltip">
          <div>${chat.date}</div>
          <div><a target="_blank" href="/session/${this.agent_name}/${chat.log_id}">${chat.descr.substring(0,35)}...</a>
          <span class="tooltiptext">${chat.descr}</span>
        </<div>
        </div>
          `)}
        </div>
      `;
     }

  }

customElements.define('chat-history', ChatHistory);
