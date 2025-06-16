document.addEventListener('DOMContentLoaded', () => {
    const conversationListEl = document.getElementById('conversation-list');
    const messageListEl = document.getElementById('message-list');
    const currentConversationTitleEl = document.getElementById('current-conversation-title');
    let currentComposerId = null;

    async function fetchConversations() {
        try {
            const response = await fetch('/api/conversations');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const conversations = await response.json();
            renderConversationList(conversations);
        } catch (error) {
            conversationListEl.innerHTML = `<p>Error loading conversations: ${error.message}</p>`;
            console.error('Error fetching conversations:', error);
        }
    }

    function renderConversationList(conversations) {
        if (!conversations || conversations.length === 0) {
            conversationListEl.innerHTML = '<p>No conversations found.</p>';
            return;
        }
        const ul = document.createElement('ul');
        conversations.forEach(convo => {
            const li = document.createElement('li');
            li.dataset.composerId = convo.id;
            li.innerHTML = `
                <span class="title">${convo.title}</span>
                <span class="count">${convo.message_count} messages</span>
            `;
            li.addEventListener('click', () => {
                loadConversation(convo.id, convo.title);
                // Highlight active conversation
                document.querySelectorAll('#conversation-list li').forEach(item => item.classList.remove('active'));
                li.classList.add('active');
            });
            ul.appendChild(li);
        });
        conversationListEl.innerHTML = ''; // Clear "Loading..."
        conversationListEl.appendChild(ul);
    }

    async function loadConversation(composerId, title) {
        if (currentComposerId === composerId && messageListEl.innerHTML !== '' && !messageListEl.querySelector('.placeholder')) {
             // Already loaded and not empty or placeholder
            return;
        }
        currentComposerId = composerId;
        currentConversationTitleEl.textContent = title || `Conversation ${composerId}`;
        messageListEl.innerHTML = '<p class="placeholder">Loading messages...</p>';

        try {
            const response = await fetch(`/api/conversations/${composerId}`);
            if (!response.ok) {
                 if (response.status === 404) {
                    throw new Error(`Conversation not found or has no messages.`);
                }
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const conversationDetail = await response.json();
            renderMessages(conversationDetail.messages);
        } catch (error) {
            messageListEl.innerHTML = `<p class="placeholder">Error loading messages: ${error.message}</p>`;
            console.error(`Error fetching messages for ${composerId}:`, error);
        }
    }

    function renderMessages(messages) {
        if (!messages || messages.length === 0) {
            messageListEl.innerHTML = '<p class="placeholder">No messages in this conversation.</p>';
            return;
        }
        messageListEl.innerHTML = ''; // Clear "Loading..." or previous messages
        messages.forEach(msg => {
            const msgDiv = document.createElement('div');
            msgDiv.classList.add('message', msg.sender);
            
            // Sanitize HTML in text before passing to marked. Use DOMPurify if more complex HTML is allowed from source.
            // For now, assuming marked handles basic XSS from Markdown.
            const renderedText = msg.text ? marked.parse(msg.text) : '';

            let attachmentsHtml = '';
            if (msg.attachments && msg.attachments.length > 0) {
                attachmentsHtml = '<div class="attachments"><h4>Attachments:</h4><ul>';
                msg.attachments.forEach(att => {
                    attachmentsHtml += `<li>${att.name} ${att.path ? `<span class="attachment-path">(${att.type}: ${att.path})</span>` : `(${att.type})`}</li>`;
                });
                attachmentsHtml += '</ul></div>';
            }

            let codeBlocksHtml = '';
            if (msg.code_blocks && msg.code_blocks.length > 0) {
                msg.code_blocks.forEach(cb => {
                    // Basic escaping for content inside <pre><code>
                    const escapedCode = cb.content.replace(/</g, "&lt;").replace(/>/g, "&gt;");
                    const langClass = cb.language ? `language-${cb.language}` : '';
                    codeBlocksHtml += `<pre><code class="${langClass}">${escapedCode}</code></pre>`;
                    if (cb.uri_path) {
                         codeBlocksHtml += `<div class="attachment-path">Source: ${cb.uri_path}</div>`;
                    }
                });
            }
            
            let toolOutputsHtml = '';
            if (msg.tool_outputs && msg.tool_outputs.length > 0) {
                toolOutputsHtml = '<div class="tool-outputs"><h4>Tool Outputs:</h4><ul>';
                msg.tool_outputs.forEach(to => {
                    let dataDisplay = '';
                    if (typeof to.data === 'object' && to.data !== null) {
                        dataDisplay = `<pre><code>${JSON.stringify(to.data, null, 2).replace(/</g, "&lt;").replace(/>/g, "&gt;")}</code></pre>`;
                    } else if (to.data !== undefined && to.data !== null) {
                        dataDisplay = `<pre><code>${String(to.data).replace(/</g, "&lt;").replace(/>/g, "&gt;")}</code></pre>`;
                    }
                    toolOutputsHtml += `<li>
                        <span class="tool-output-name">${to.tool_name || 'Tool'} (Status: ${to.status || 'N/A'})</span>
                        ${dataDisplay}
                    </li>`;
                });
                toolOutputsHtml += '</ul></div>';
            }

            msgDiv.innerHTML = `
                <div class="sender">${msg.sender.charAt(0).toUpperCase() + msg.sender.slice(1)} (ID: ${msg.id})</div>
                <div class="content">${renderedText}</div>
                ${attachmentsHtml}
                ${codeBlocksHtml}
                ${toolOutputsHtml}
            `;
            messageListEl.appendChild(msgDiv);
        });
        messageListEl.scrollTop = messageListEl.scrollHeight; // Scroll to bottom
    }

    // Initial load
    fetchConversations();
});

// Configure marked
if (typeof marked !== 'undefined') {
    marked.setOptions({
        breaks: true, // Add <br> on single newlines
        gfm: true,    // Use GitHub Flavored Markdown
        sanitize: false, // Be careful with this if content can be malicious. For VSCode logs, it's likely fine.
                        // If true, it will strip HTML. If you need to allow some HTML, use a sanitizer library.
        smartypants: true
    });
}
