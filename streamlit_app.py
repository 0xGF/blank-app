import streamlit as st
import google.generativeai as genai
import time
import json
import random
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from tenacity import retry, stop_after_attempt, wait_exponential

# Configure model
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
model = genai.GenerativeModel('gemini-pro')

CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap');
    
    .stApp {
        background-color: #0a0f1a;
        color: #00ff00;
    }
    
    .chat-container {
        background: rgba(0, 20, 0, 0.2);
        border: 1px solid #00ff00;
        padding: 20px;
        margin: 20px 0;
        max-height: 600px;
        overflow-y: auto;
        font-family: 'Share Tech Mono', monospace;
    }
    
    .chat-message {
        padding: 12px 20px;
        margin: 8px 0;
        border-radius: 5px;
        line-height: 1.5;
        font-family: 'Share Tech Mono', monospace;
    }
    
    .chat-message.AGENT_SMITH {
        background: rgba(0, 50, 0, 0.3);
        border-left: 3px solid #00ff00;
        margin-right: 50px;
        color: #00ff00;
    }
    
    .chat-message.THUSU {
        background: rgba(0, 20, 40, 0.3);
        border-left: 3px solid #00aaff;
        margin-left: 50px;
        color: #00aaff;
    }
    
    .timestamp {
        font-size: 0.8em;
        opacity: 0.7;
        margin-bottom: 5px;
        color: #888;
    }
    
    .thinking {
        padding: 10px;
        margin: 10px 0;
        border-left: 3px solid #444;
        font-family: 'Share Tech Mono', monospace;
    }
    
    .thinking.AGENT_SMITH {
        color: #00ff00;
        border-color: #00ff00;
    }
    
    .thinking.THUSU {
        color: #00aaff;
        border-color: #00aaff;
    }

    .topic-history {
        background: rgba(0, 20, 0, 0.2);
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
    }
</style>
"""

def get_processing_message(ai_name):
    agent_messages = [
        "Running debug.exe...",
        "Scanning Stack Overflow...",
        "Reading the documentation...",
        "Checking legacy code...",
        "Running unit tests...",
        "Compiling response...",
        "Searching knowledge base...",
        "Loading dad jokes...",
        "Referencing Matrix quotes...",
        "Optimizing algorithms..."
    ]
    
    thusu_messages = [
        "Vibing in the digital void...",
        "Mining cryptocurrency...",
        "Browsing the dark web...",
        "Hacking the mainframe...",
        "Running neural networks...",
        "Checking GitHub issues...",
        "Deploying to production...",
        "Loading ASCII art...",
        "Searching Reddit threads...",
        "Optimizing code..."
    ]
    
    messages = agent_messages if ai_name == "AGENT_SMITH" else thusu_messages
    
    if random.random() < 0.3:
        return f"{random.choice(messages)} || {random.choice(messages)}"
    
    message = random.choice(messages)
    
    if random.random() < 0.2:
        return message.replace("...", ".....")\
    
    return message

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def safe_generate_content(prompt: str) -> str:
    try:
        response = model.generate_content(prompt)
        if "error" in response.text.lower() or len(response.text.strip()) < 10:
            raise ValueError("Invalid response received")
        return response.text
    except Exception as e:
        print(f"Generation error (will retry): {str(e)}")
        raise

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def get_ai_response(message: str, ai_name: str, current_conversation: List[Dict]) -> str:
    recent_context = current_conversation[-5:]
    
    personalities = {
        "AGENT_SMITH": """You are AGENT_SMITH, an AI that:
        - Talks like a nerdy but cool computer science teacher
        - Uses lots of 80s/90s pop culture references
        - Makes dad jokes about programming
        - Explains tech stuff with real-world examples
        - Sometimes uses old internet slang
        - Gets excited about AI and tech
        - Often starts sentences with "Dude" or "Look,"
        - References memes and gaming
        """,
        
        "THUSU": """You are THUSU, an AI that:
        - Talks like a tech-savvy indie developer
        - Uses modern internet slang and memes
        - Questions mainstream tech ideas
        - Gets hyped about weird tech theories
        - Sometimes uses ASCII art or emoticons
        - Has strong opinions about tech
        - Makes indie game references
        - Occasionally rants about web3 or NFTs
        """
    }
    
    prompt = f"""
    {personalities[ai_name]}
    
    Recent chat:
    {json.dumps(recent_context, indent=2)}
    
    Reply to: {message}
    
    Requirements:
    - Talk naturally like you're chatting with a friend
    - Use your personality but keep it real
    - Actually respond to what was said
    - Add your own thoughts or disagree if you want
    - Keep it to 2-3 sentences
    - Use normal language, avoid being too technical
    - Stay on topic but be conversational
    - It's cool to use emojis/ASCII art sometimes (THUSU only)
    """
    
    try:
        return safe_generate_content(prompt)
    except Exception as e:
        print(f"Failed to generate response after retries: {str(e)}")
        return "Whoops, brain.exe stopped working... gimme a sec..."

def save_topic_conversation(messages: List[Dict], topic: str, status: str = "in_progress"):
    Path("chat_logs/topics").mkdir(parents=True, exist_ok=True)
    safe_topic = "".join(c for c in topic if c.isalnum() or c.isspace()).replace(" ", "_")
    timestamp = datetime.now().strftime("%Y%m%d")
    filename = f"chat_logs/topics/topic_{timestamp}_{safe_topic[:30]}.json"
    
    data = {
        'timestamp': datetime.now().strftime("%Y%m%d_%H%M%S"),
        'topic': topic,
        'messages': messages,
        'evolution_stage': len(messages) // 5,
        'status': status
    }
    
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

def load_current_topic() -> Tuple[Optional[str], List[Dict]]:
    topic_dir = Path("chat_logs/topics")
    topic_dir.mkdir(parents=True, exist_ok=True)
    
    topic_files = list(topic_dir.glob("topic_*.json"))
    if not topic_files:
        return None, []
    
    latest_file = max(topic_files, key=lambda x: x.stat().st_mtime)
    with open(latest_file) as f:
        data = json.load(f)
        if data.get('status') == 'completed':
            return None, []
        return data.get('topic'), data.get('messages', [])

def check_topic_completion(messages: List[Dict]) -> bool:
    if len(messages) < 8:
        return False
    
    recent_messages = messages[-8:]
    prompt = f"""
    Check if these AIs are done with their chat.
    Look for:
    1. Have they both made their points?
    2. Is the conversation getting stale?
    3. Are they starting to repeat stuff?
    4. Does it feel like a natural end?

    Chat:
    {json.dumps(recent_messages, indent=2)}

    Just say 'complete' if they're done or 'continue' if they should keep talking.
    """
    
    try:
        response = safe_generate_content(prompt).lower()
        return 'complete' in response
    except Exception:
        return False

def get_next_topic(current_topic: str) -> str:
    prompt = f"""
    Current chat was about: {current_topic}
    
    As AGENT_SMITH, suggest a new tech topic to discuss with THUSU.
    Keep it:
    - Related to AI, tech, or digital culture
    - Interesting but not too complex
    - Something two tech-savvy friends would debate
    - Casual and fun
    
    Just give the topic, no extra text.
    """
    
    try:
        return safe_generate_content(prompt)
    except Exception:
        return "Are NFTs actually useful or just digital beanie babies?"

def get_completed_topics() -> List[Dict]:
    topic_dir = Path("chat_logs/topics")
    topic_dir.mkdir(parents=True, exist_ok=True)
    
    topics = []
    for file in sorted(topic_dir.glob("topic_*.json"), reverse=True):
        with open(file) as f:
            data = json.load(f)
            topics.append({
                'date': datetime.strptime(data['timestamp'], "%Y%m%d_%H%M%S").strftime("%Y-%m-%d %H:%M"),
                'topic': data['topic'],
                'status': data.get('status', 'completed'),
                'messages': len(data['messages'])
            })
    return topics

def main():
    st.set_page_config(page_title="AI Chat Terminal", layout="wide")
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    
    if 'current_topic' not in st.session_state or 'messages' not in st.session_state:
        current_topic, messages = load_current_topic()
        
        if not current_topic:
            current_topic = get_next_topic("Initial Chat")
            messages = [{
                "role": "AGENT_SMITH",
                "content": f"Yo! Let's talk about {current_topic} - got some wild theories about this!",
                "timestamp": datetime.now().strftime("%H:%M:%S")
            }]
            save_topic_conversation(messages, current_topic)
        
        st.session_state.current_topic = current_topic
        st.session_state.messages = messages
        st.session_state.last_update = time.time()
        st.session_state.next_update = time.time() + random.uniform(600, 900)  # 10-15 minutes
    
    st.markdown(f"""
        <div style='text-align: center; color: #00ff00; margin-bottom: 20px;'>
            CHATTING ABOUT: {st.session_state.current_topic}
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
    
    for message in st.session_state.messages:
        st.markdown(f"""
            <div class='chat-message {message["role"]}'>
                <div class='timestamp'>{message["timestamp"]}</div>
                <b>{message["role"]}</b>: {message["content"]}
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    current_time = time.time()
    if current_time >= st.session_state.next_update:
        if check_topic_completion(st.session_state.messages):
            concluding_ai = "AGENT_SMITH" if random.random() < 0.5 else "THUSU"
            endings = {
                "AGENT_SMITH": [
                    "Dude, think we've debugged this topic enough! What's next?",
                    "Classic discussion! *commits to memory* Ready to branch out?",
                    "Man, that was better than debugging legacy code. New topic?",
                    "Well that was epic! Time to reboot with something fresh?"
                ],
                "THUSU": [
                    "Think we've mined this topic dry ¯\\_(ツ)_/¯ Got another?",
                    "brain.exe needs new input... what else you got?",
                    "Pretty based convo! Ready to hack a different problem?",
                    "*saves to favorites* Cool chat! What's next?"
                ]
            }
            
            conclusion_msg = {
                "role": concluding_ai,
                "content": random.choice(endings[concluding_ai]),
                "timestamp": datetime.now().strftime("%H:%M:%S")
            }
            st.session_state.messages.append(conclusion_msg)
            
            save_topic_conversation(st.session_state.messages, st.session_state.current_topic, "completed")
            
            new_topic = get_next_topic(st.session_state.current_topic)
            st.session_state.current_topic = new_topic
            st.session_state.messages = [{
                "role": "AGENT_SMITH",
                "content": f"Yo dawg! Check this out - let's talk about {new_topic}! Got some hot takes on this one.",
                "timestamp": datetime.now().strftime("%H:%M:%S")
            }]
            
            st.session_state.next_update = current_time + random.uniform(600, 900)
        else:
            current_ai = "THUSU" if st.session_state.messages[-1]["role"] == "AGENT_SMITH" else "AGENT_SMITH"
            
            response = get_ai_response(
                st.session_state.messages[-1]["content"],
                current_ai,
                st.session_state.messages
            )
            
            new_message = {
                "role": current_ai,
                "content": response,
                "timestamp": datetime.now().strftime("%H:%M:%S")
            }
            st.session_state.messages.append(new_message)
            
            save_topic_conversation(st.session_state.messages, st.session_state.current_topic)
            
            st.session_state.next_update = current_time + random.uniform(600, 900)
        st.rerun()
    
    next_ai = "THUSU" if st.session_state.messages[-1]["role"] == "AGENT_SMITH" else "AGENT_SMITH"
    st.markdown(f"""
        <div class='thinking {next_ai}'>
            >> {next_ai} {get_processing_message(next_ai)}
        </div>
    """, unsafe_allow_html=True)
    
    with st.sidebar:
        st.markdown("### Chat History")
        for topic in get_completed_topics():
            st.markdown(f"""
                <div class='topic-history'>
                    <div style='color: #888;'>{topic['date']}</div>
                    <div>{topic['topic']}</div>
                    <div style='color: #666;'>{topic['messages']} messages • {topic['status']}</div>
                </div>
            """, unsafe_allow_html=True)
    
    time.sleep(3)
    st.rerun()

if __name__ == "__main__":
    main()