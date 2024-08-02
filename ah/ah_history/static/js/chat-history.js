import { html, css } from './lit-core.min.js';
import { BaseEl } from './base.js';

export class ChatHistory extends BaseEl {
  static properties = {
    user: { type: String },
    agent_name: { type: String },
    chats: { type: Array }
  };

  static styles = css`
    .chat-history {
      padding: 10px;
      font-size: 0.92em;
    }
    chat-history:hover {
      background-color: rgba(100, 100, 255, 0.2);
    }
  `;

  constructor() {
    super();
 }

  async firstUpdated() {
    await this.loadStructure();
    this.renderStructure()
  }

  async loadStructure() {
    try {
      const response = await fetch(`/history/${encodeURIComponent(this.agent_name)}`);
      console.log(response)
      this.chat = await response.json();
    } catch (error) {
      console.error('Error loading file structure:', error);
      this.error = 'Failed to load file structure. Please try again.';
    }
  }

  _render() {
      return html`
        <div class="chat-history">
          ${this.chats.map(chat => html`
        <div class="chat-item">
          <span>${chat.date}</span>
          <span>${chat.descr}</span>
        </div>
          `)}
        </div>
      `;
     }

  }

customElements.define('chat-history', ChatHistory);
