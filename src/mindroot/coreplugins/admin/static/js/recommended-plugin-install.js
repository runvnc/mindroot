import { html, css } from '/admin/static/js/lit-core.min.js';
import { BaseEl } from '/admin/static/js/base.js';

class RecommendedPluginInstall extends BaseEl {
  static properties = {
    agent: { type: String },
    logText: { type: String }
  };

  static styles = css`
    dialog {
      width: 90%;
      max-width: 800px;
      background: #0f0f1a;
      color: #fff;
      border: 1px solid rgba(255, 255, 255, 0.2);
      border-radius: 8px;
      padding: 1rem;
    }
    pre.log {
      height: 60vh;
      overflow-y: auto;
      background: #000;
      color: #0f0;
      padding: 0.5rem;
      font-size: 0.8rem;
      border: 1px solid #333;
    }
    .actions { text-align: right; margin-top: .5rem; }
  `;

  constructor() {
    super();
    this.agent = '';
    this.logText = '';
  }

  firstUpdated() { if (this.agent) this.startStream(); }

  startStream() {
    this.logText = '';
    const es = new EventSource(`/admin/stream-install-recommended-plugins/${encodeURIComponent(this.agent)}`);
    es.onmessage = (e) => {
      if (e.data === 'END') { es.close(); return; }
      this.logText += e.data;
      this.requestUpdate();
      const pre = this.shadowRoot.querySelector('pre.log');
      if (pre) pre.scrollTop = pre.scrollHeight;
    };
    es.onerror = () => es.close();
  }

  closeDialog() { this.remove(); }

  _render() {
    return html`
      <dialog open>
        <h3>Installing recommended plugins for <b>${this.agent}</b></h3>
        <pre class="log">${this.logText}</pre>
        <div class="actions"><button @click=${this.closeDialog}>Close</button></div>
      </dialog>`; }
}
customElements.define('recommended-plugin-install', RecommendedPluginInstall);
