let currentChatId = null;
let eventSource = null;
let chatHistory = []; // 维护对话历史

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('messageInput');
    input.addEventListener('input', autoResize);
    input.addEventListener('input', toggleSendButton);
    
    // 加载历史对话列表
    loadChatList();
});

// 自动调整输入框高度
function autoResize() {
    const textarea = document.getElementById('messageInput');
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px';
}

// 切换发送按钮状态
function toggleSendButton() {
    const input = document.getElementById('messageInput');
    const sendBtn = document.getElementById('sendBtn');
    sendBtn.disabled = !input.value.trim();
}

// 处理回车键
function handleKeyDown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        if (!event.target.disabled) {
            sendMessage();
        }
    }
}

// 发送消息
async function sendMessage() {
    const input = document.getElementById('messageInput');
    const message = input.value.trim();
    
    if (!message) return;
    
    // 如果是新对话，创建对话记录
    if (!currentChatId) {
        await createNewChat(message);
    }
    
    // 禁用输入和按钮
    input.disabled = true;
    document.getElementById('sendBtn').disabled = true;
    
    // 添加用户消息到界面
    addMessage('user', message);
    
    // 添加到对话历史（在发送请求前添加）
    chatHistory.push({
        role: 'user',
        content: message
    });
    
    console.log('对话历史长度:', chatHistory.length);
    console.log('当前对话历史:', chatHistory);
    
    // 清空输入框
    input.value = '';
    input.style.height = 'auto';
    toggleSendButton();
    
    // 显示思考过程
    const thinkingId = showThinking();
    
    try {
        // 使用 Server-Sent Events 接收流式响应，传递对话历史
        const assistantMessage = await streamChatResponse(chatHistory, thinkingId);
        
        // 将 AI 回复添加到对话历史
        if (assistantMessage && assistantMessage.trim()) {
            chatHistory.push({
                role: 'assistant',
                content: assistantMessage
            });
            console.log('✅ 对话历史已更新，长度:', chatHistory.length);
        } else {
            console.warn('⚠️ AI 回复为空，未添加到历史');
        }
        
        // 保存对话历史
        await saveChatHistory();
    } catch (error) {
        console.error('❌ Error:', error);
        const errorMsg = error.message || '请求失败，请重试';
        
        // 确保错误信息显示在界面上
        const thinkingDiv = document.getElementById(thinkingId);
        if (thinkingDiv) {
            updateThinking(thinkingId, 'error', errorMsg);
        } else {
            // 如果 thinking 容器不存在，创建一个错误消息
            addMessage('assistant', `❌ 错误: ${errorMsg}`);
        }
    } finally {
        // 重新启用输入
        input.disabled = false;
        toggleSendButton();
    }
}

// 添加消息到聊天容器
function addMessage(role, content) {
    const container = document.getElementById('chatContainer');
    
    // 移除欢迎消息
    const welcome = container.querySelector('.welcome-message');
    if (welcome) {
        welcome.remove();
    }
    
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message';
    
    const avatar = document.createElement('div');
    avatar.className = `message-avatar ${role}-avatar`;
    avatar.textContent = role === 'user' ? '你' : 'AI';
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    const textDiv = document.createElement('div');
    textDiv.className = 'message-text';
    
    if (role === 'assistant') {
        // 使用 marked 渲染 Markdown
        textDiv.innerHTML = marked.parse(content);
    } else {
        textDiv.textContent = content;
    }
    
    contentDiv.appendChild(textDiv);
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(contentDiv);
    
    container.appendChild(messageDiv);
    container.scrollTop = container.scrollHeight;
    
    return messageDiv;
}

// 显示思考过程
function showThinking() {
    const container = document.getElementById('chatContainer');
    
    // 移除之前的思考消息（如果有）
    const oldThinking = document.getElementById('thinking-message');
    if (oldThinking) {
        oldThinking.remove();
    }
    
    const welcome = container.querySelector('.welcome-message');
    if (welcome) {
        welcome.remove();
    }
    
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message';
    messageDiv.id = 'thinking-message';
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar assistant-avatar';
    avatar.textContent = 'AI';
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    const thinkingDiv = document.createElement('div');
    thinkingDiv.className = 'thinking-container';
    thinkingDiv.id = 'thinking-content';
    
    const title = document.createElement('div');
    title.className = 'thinking-title';
    title.innerHTML = `
        <span>正在思考</span>
        <span class="thinking-dots">
            <span class="thinking-dot"></span>
            <span class="thinking-dot"></span>
            <span class="thinking-dot"></span>
        </span>
    `;
    
    thinkingDiv.appendChild(title);
    contentDiv.appendChild(thinkingDiv);
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(contentDiv);
    
    container.appendChild(messageDiv);
    container.scrollTop = container.scrollHeight;
    
    console.log('✅ 创建思考容器，ID:', 'thinking-content');
    return 'thinking-content';
}

// 更新思考过程
function updateThinking(thinkingId, type, content) {
    const thinkingDiv = document.getElementById(thinkingId);
    if (!thinkingDiv) {
        console.error('思考容器不存在，ID:', thinkingId);
        // 尝试重新创建
        const messageDiv = document.getElementById('thinking-message');
        if (messageDiv) {
            const contentDiv = messageDiv.querySelector('.message-content');
            if (contentDiv) {
                const newThinkingDiv = document.createElement('div');
                newThinkingDiv.className = 'thinking-container';
                newThinkingDiv.id = thinkingId;
                contentDiv.appendChild(newThinkingDiv);
                return updateThinking(thinkingId, type, content);
            }
        }
        console.error('无法创建思考容器');
        return;
    }
    
    if (type === 'log') {
        // 添加日志项
        const logItem = document.createElement('div');
        logItem.className = 'log-item';
        
        // 提取图标和文本
        let icon = '🤔';
        let text = content;
        
        // 从内容中提取图标（如果存在）
        const iconMatch = content.match(/^([^\s]+)\s/);
        if (iconMatch && ['🚀', '🧠', '🔧', '🔍', '✅', '⚠️'].includes(iconMatch[1])) {
            icon = iconMatch[1];
            text = content.substring(iconMatch[0].length);
        } else {
            // 根据内容判断图标
            if (content.includes('LLM') || content.includes('模型') || content.includes('分析')) {
                icon = '🧠';
            } else if (content.includes('工具') || content.includes('调用')) {
                icon = '🔧';
            } else if (content.includes('搜索')) {
                icon = '🔍';
            } else if (content.includes('完成')) {
                icon = '✅';
            } else if (content.includes('开始')) {
                icon = '🚀';
            }
        }
        
        // 高亮关键词
        text = text.replace(/正在搜索:\s*(.+)/g, (match, keyword) => {
            return `正在搜索: <span class="log-keyword">${keyword}</span>`;
        });
        
        logItem.innerHTML = `
            <span class="log-icon">${icon}</span>
            <span class="log-text">${text}</span>
        `;
        
        thinkingDiv.appendChild(logItem);
        
        // 滚动到底部
        const container = document.getElementById('chatContainer');
        container.scrollTop = container.scrollHeight;
    } else if (type === 'content') {
        // 更新内容（流式）
        const messageDiv = document.getElementById('thinking-message');
        if (messageDiv) {
            let textDiv = messageDiv.querySelector('.message-text');
            if (!textDiv) {
                const contentDiv = messageDiv.querySelector('.message-content');
                textDiv = document.createElement('div');
                textDiv.className = 'message-text';
                contentDiv.innerHTML = '';
                contentDiv.appendChild(textDiv);
            }
            textDiv.innerHTML = marked.parse(content);
        }
    } else if (type === 'complete') {
        // 思考完成，转换为正常消息
        const messageDiv = document.getElementById('thinking-message');
        if (messageDiv) {
            const contentDiv = messageDiv.querySelector('.message-content');
            const newTextDiv = document.createElement('div');
            newTextDiv.className = 'message-text';
            newTextDiv.innerHTML = marked.parse(content);
            contentDiv.innerHTML = '';
            contentDiv.appendChild(newTextDiv);
            messageDiv.removeAttribute('id');
        }
    } else if (type === 'error') {
        // 显示错误
        thinkingDiv.innerHTML = `<div class="log-item" style="color: #ef4444;">❌ ${content}</div>`;
    }
    
    const container = document.getElementById('chatContainer');
    container.scrollTop = container.scrollHeight;
}

// 流式接收聊天响应（使用 fetch + ReadableStream）
async function streamChatResponse(history, thinkingId) {
    let reader = null;
    
    try {
        // 关闭之前的连接
        if (eventSource) {
            eventSource.close();
            eventSource = null;
        }
        
        console.log('📤 发送请求，对话历史长度:', history.length);
        console.log('📤 对话历史:', JSON.stringify(history, null, 2));
        
        // 使用 POST 方法发送请求，支持更长的对话历史
        const response = await fetch('/api/chat/stream', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                history: history,
                model: 'gpt-5'
            })
        });
        
        console.log('📥 响应状态:', response.status, response.statusText);
        console.log('📥 Content-Type:', response.headers.get('content-type'));
        
        if (!response.ok) {
            let errorText = '';
            try {
                errorText = await response.text();
            } catch (e) {
                errorText = '无法读取错误信息';
            }
            console.error('❌ HTTP 错误响应:', response.status, errorText);
            throw new Error(`请求失败 (${response.status}): ${errorText || response.statusText}`);
        }
        
        if (!response.body) {
            throw new Error('响应体为空');
        }
        
        reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let finalMessage = '';
        let hasComplete = false;
        
        while (true) {
            const { done, value } = await reader.read();
            
            if (done) {
                console.log('流读取完成，buffer:', buffer);
                // 处理剩余的 buffer
                if (buffer.trim()) {
                    const lines = buffer.split('\n').filter(line => line.trim());
                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            try {
                                const jsonStr = line.substring(6);
                                const data = JSON.parse(jsonStr);
                                if (data.type === 'complete') {
                                    finalMessage = data.content || finalMessage;
                                    hasComplete = true;
                                }
                            } catch (e) {
                                console.error('解析最后数据失败:', e);
                            }
                        }
                    }
                }
                break;
            }
            
            // 解码数据
            buffer += decoder.decode(value, { stream: true });
            
            // 处理 SSE 格式的数据
            const lines = buffer.split('\n');
            buffer = lines.pop() || ''; // 保留最后不完整的行
            
            for (const line of lines) {
                if (line.trim() === '') continue; // 跳过空行
                
                if (line.startsWith('data: ')) {
                    try {
                        const jsonStr = line.substring(6).trim(); // 移除 'data: ' 前缀并去除空白
                        if (!jsonStr) continue; // 跳过空数据
                        
                        const data = JSON.parse(jsonStr);
                        console.log('收到数据:', data.type, data.content ? data.content.substring(0, 50) : data.message);
                        
                        if (data.type === 'log') {
                            // 日志信息
                            updateThinking(thinkingId, 'log', data.content);
                        } else if (data.type === 'content') {
                            // 内容片段（流式）
                            finalMessage += data.content;
                            updateThinking(thinkingId, 'content', finalMessage);
                        } else if (data.type === 'complete') {
                            // 完成
                            finalMessage = data.content || finalMessage;
                            updateThinking(thinkingId, 'complete', finalMessage);
                            hasComplete = true;
                            // 继续读取直到流结束
                        } else if (data.type === 'error') {
                            // 错误
                            updateThinking(thinkingId, 'error', data.message);
                            throw new Error(data.message);
                        }
                    } catch (error) {
                        console.error('解析 SSE 数据失败:', error, '原始行:', line);
                        // 继续处理，不中断
                    }
                }
            }
            
            // 如果已经完成，可以提前退出（但继续读取确保流结束）
            // 不提前退出，确保所有数据都被处理
        }
        
        // 检查完成状态
        if (hasComplete) {
            // 已收到完成信号
            return finalMessage;
        } else if (finalMessage) {
            // 有消息但没有 complete 信号，手动完成
            console.warn('收到消息但未收到 complete 信号，手动完成');
            updateThinking(thinkingId, 'complete', finalMessage);
            return finalMessage;
        } else {
            // 既没有消息也没有完成信号
            throw new Error('未收到完整响应，请重试');
        }
        
    } catch (error) {
        console.error('Stream error:', error);
        const errorMsg = error.message || '请求失败，请重试';
        updateThinking(thinkingId, 'error', errorMsg);
        throw error;
    } finally {
        // 确保释放 reader
        if (reader) {
            try {
                await reader.cancel();
            } catch (e) {
                console.error('取消 reader 失败:', e);
            }
        }
    }
}

// 加载对话列表
async function loadChatList() {
    try {
        const response = await fetch('/api/chats');
        const data = await response.json();
        renderChatList(data.chats || []);
    } catch (error) {
        console.error('加载对话列表失败:', error);
    }
}

// 渲染对话列表
function renderChatList(chats) {
    const chatHistoryDiv = document.querySelector('.chat-history');
    if (!chatHistoryDiv) return;
    
    if (chats.length === 0) {
        chatHistoryDiv.innerHTML = '<div class="empty-chat-list">暂无历史对话</div>';
        return;
    }
    
    chatHistoryDiv.innerHTML = chats.map(chat => `
        <div class="chat-item ${chat.id === currentChatId ? 'active' : ''}" data-chat-id="${chat.id}">
            <div class="chat-item-content">
                <div class="chat-item-title" data-chat-id="${chat.id}">${escapeHtml(chat.title)}</div>
                <div class="chat-item-actions">
                    <button class="chat-edit-btn" data-chat-id="${chat.id}" title="编辑标题">✏️</button>
                    <button class="chat-delete-btn" data-chat-id="${chat.id}" title="删除">🗑️</button>
                </div>
            </div>
        </div>
    `).join('');
    
    // 添加点击事件
    chatHistoryDiv.querySelectorAll('.chat-item').forEach(item => {
        const chatId = item.dataset.chatId;
        item.addEventListener('click', (e) => {
            // 如果点击的是按钮，不触发加载
            if (e.target.closest('.chat-item-actions')) {
                return;
            }
            loadChat(chatId);
        });
    });
    
    // 添加编辑按钮事件
    chatHistoryDiv.querySelectorAll('.chat-edit-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            editChatTitle(btn.dataset.chatId, e);
        });
    });
    
    // 添加删除按钮事件
    chatHistoryDiv.querySelectorAll('.chat-delete-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            deleteChat(btn.dataset.chatId, e);
        });
    });
}

// 创建新对话
async function createNewChat(firstMessage) {
    try {
        const response = await fetch('/api/chats', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                first_message: firstMessage
            })
        });
        
        const chat = await response.json();
        currentChatId = chat.id;
        
        // 重新加载对话列表
        await loadChatList();
        
        return chat;
    } catch (error) {
        console.error('创建新对话失败:', error);
        // 即使创建失败，也继续发送消息
        return null;
    }
}

// 保存对话历史
async function saveChatHistory() {
    if (chatHistory.length === 0) return;
    
    // 如果没有currentChatId，尝试从历史记录中获取第一条用户消息来创建对话
    if (!currentChatId) {
        const firstUserMessage = chatHistory.find(msg => msg.role === 'user');
        if (firstUserMessage) {
            const chat = await createNewChat(firstUserMessage.content);
            if (!chat) {
                console.warn('创建对话失败，无法保存历史');
                return;
            }
        } else {
            return;
        }
    }
    
    try {
        await fetch(`/api/chats/${currentChatId}/save`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                chat_id: currentChatId,
                history: chatHistory
            })
        });
        
        // 更新对话列表（标题可能已更新）
        await loadChatList();
    } catch (error) {
        console.error('保存对话历史失败:', error);
    }
}

// 加载对话
async function loadChat(chatId) {
    try {
        const response = await fetch(`/api/chats/${chatId}`);
        const chat = await response.json();
        
        currentChatId = chat.id;
        chatHistory = chat.history || [];
        
        // 清空并重新渲染消息
        const container = document.getElementById('chatContainer');
        container.innerHTML = '';
        
        if (chatHistory.length === 0) {
            container.innerHTML = `
                <div class="welcome-message">
                    <h1>欢迎使用 AI Chat</h1>
                    <p>支持 Agentic Loop，可以自动调用搜索工具获取最新信息</p>
                </div>
            `;
        } else {
            // 渲染历史消息
            chatHistory.forEach(msg => {
                if (msg.role === 'user' || msg.role === 'assistant') {
                    addMessage(msg.role, msg.content);
                }
            });
        }
        
        // 更新对话列表的激活状态
        await loadChatList();
    } catch (error) {
        console.error('加载对话失败:', error);
        alert('加载对话失败: ' + error.message);
    }
}

// 编辑对话标题
async function editChatTitle(chatId, event) {
    event.stopPropagation();
    
    const chatItem = event.target.closest('.chat-item');
    const titleDiv = chatItem.querySelector('.chat-item-title');
    const currentTitle = titleDiv.textContent;
    
    const newTitle = prompt('请输入新标题:', currentTitle);
    if (newTitle === null || newTitle.trim() === '') {
        return;
    }
    
    try {
        const response = await fetch(`/api/chats/${chatId}/title`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                title: newTitle.trim()
            })
        });
        
        const result = await response.json();
        if (result.success) {
            // 重新加载对话列表
            await loadChatList();
        }
    } catch (error) {
        console.error('更新标题失败:', error);
        alert('更新标题失败: ' + error.message);
    }
}

// 删除对话
async function deleteChat(chatId, event) {
    event.stopPropagation();
    
    if (!confirm('确定要删除这个对话吗？')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/chats/${chatId}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        if (result.success) {
            // 如果删除的是当前对话，清空界面
            if (chatId === currentChatId) {
                currentChatId = null;
                chatHistory = [];
                const container = document.getElementById('chatContainer');
                container.innerHTML = `
                    <div class="welcome-message">
                        <h1>欢迎使用 AI Chat</h1>
                        <p>支持 Agentic Loop，可以自动调用搜索工具获取最新信息</p>
                    </div>
                `;
            }
            
            // 重新加载对话列表
            await loadChatList();
        }
    } catch (error) {
        console.error('删除对话失败:', error);
        alert('删除对话失败: ' + error.message);
    }
}

// HTML转义
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 新对话
function newChat() {
    const container = document.getElementById('chatContainer');
    container.innerHTML = `
        <div class="welcome-message">
            <h1>欢迎使用 AI Chat</h1>
            <p>支持 Agentic Loop，可以自动调用搜索工具获取最新信息</p>
        </div>
    `;
    
    // 清空对话历史
    chatHistory = [];
    currentChatId = null;
    
    // 更新对话列表的激活状态
    loadChatList();
    
    if (eventSource) {
        eventSource.close();
        eventSource = null;
    }
}
