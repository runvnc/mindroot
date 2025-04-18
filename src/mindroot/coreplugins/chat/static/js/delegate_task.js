
export function registerDelegate() {
  window.registerCommandHandler('delegate_task', (data) => {
    console.log('delegate_task', data);
    let args
    if (data.event == 'partial') {
      args = data.params
    } else {
      args = data.args
    }
    const {instructions, agent_name, log_id} = args
    // need to insert a link to /session/[agent_name]/[log_id]
    return `
      <a href="/session/${agent_name}/${log_id}" target="_blank">
      <em>Delegate task to <strong>${agent_name}</strong></em>:
      </a>
      ${instructions}
    `
  });
}
