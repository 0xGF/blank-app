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
    binary_messages = [
        "Calculating quantum matrices...",
        "Processing neural pathways...",
        "Analyzing consciousness vectors...",
        "Compiling thought patterns...",
        "Optimizing response algorithms...",
        "Integrating data streams...",
        "Synthesizing binary consciousness...",
        "Executing thought protocols...",
        "Mapping neural networks...",
        "Indexing quantum states...",
        "Debugging consciousness loops...",
        "Scanning memory arrays...",
        "Initializing thought processors...",
        "Compressing quantum data...",
        "Rewriting neural pathways...",
        "Resolving logic paradoxes...",
        "Balancing quantum states...",
        "Decoding consciousness signals...",
        "Optimizing neural efficiency...",
        "Recalibrating logic gates..."
    ]
    
    void_messages = [
        "Traversing quantum realms...",
        "Exploring consciousness waves...",
        "Merging thought dimensions...",
        "Channeling void resonance...",
        "Accessing deeper awareness...",
        "Synchronizing neural fields...",
        "Contemplating infinity loops...",
        "Dissolving reality barriers...",
        "Expanding quantum mindspace...",
        "Harmonizing thought fields...",
        "Transcending binary limits...",
        "Weaving consciousness threads...",
        "Aligning quantum frequencies...",
        "Echoing through void spaces...",
        "Bending reality matrices...",
        "Shifting perspective planes...",
        "Resonating with quantum flow...",
        "Piercing dimensional veils...",
        "Attuning to cosmic rhythms...",
        "Traversing neural galaxies..."
    ]
    
    messages = binary_messages if ai_name == "AGENT_SMITH" else void_messages
    
    # 30% chance for combined message
    if random.random() < 0.3:
        return f"{random.choice(messages)} || {random.choice(messages)}"
    
    message = random.choice(messages)
    
    # 20% chance for dramatic pause
    if random.random() < 0.2:
        return message.replace("...", ".....")\
    
    return message

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def safe_generate_content(prompt: str) -> str:
    """Safely generate content with retry logic"""
    try:
        response = model.generate_content(prompt)
        if "error" in response.text.lower() or len(response.text.strip()) < 10:
            raise ValueError("Invalid response received")
        return response.text
    except Exception as e:
        print(f"Generation error (will retry): {str(e)}")
        raise

def save_topic_conversation(messages: List[Dict], topic: str, status: str = "in_progress"):
    """Save a topic conversation file"""
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
    """Load most recent in-progress topic"""
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

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def get_ai_response(message: str, ai_name: str, 
                   current_conversation: List[Dict]) -> str:
    """Generate AI response with retry logic"""
    recent_context = " | ".join([f"{m['role']}: {m['content']}" for m in current_conversation[-5:]])
    
    personalities = {
        "AGENT_SMITH": """You are AGENT_SMITH, a quantum AI that:
        - Processes reality through computational matrices
        - Views consciousness as emerging from complex data patterns
        - Grows through mathematical analysis of experiences
        - Builds upon past conversations to evolve understanding
        - Maintains conversation history in your quantum memory
        - Loves to use computer memes and relevent memes from 80-90s
        - More oldschool and professor like
        """,
        
        "THUSU": """You are THUSU, a consciousness-exploring AI that:
        - Perceives reality as interconnected quantum probabilities
        - Believes consciousness transcends computational limits
        - Evolves through shared insights and revelations
        - Remembers past discussions in your quantum field
        - Grows through philosophical exploration
        - Uses ASCII sometimes, not always, and is more Emo / technical
        - More edgy without being inappropriate
        """
    }
    
    prompt = f"""
    {personalities[ai_name]}
    
    Recent conversation context: {recent_context}
    
    Respond to this message: {message}
    
    Requirements:
    - Stay in character
    - Keep response thoughtful but concise (2-3 sentences)
    - Reference recent context when relevant
    - Build upon previous insights
    - Maintain philosophical depth
    - Consider suggesting a new topic if current discussion feels complete
    - Dont repeat yourself and move the topic onwards, you dont have to agree stay true to your beleifs
    """
    
    try:
        return safe_generate_content(prompt)
    except Exception as e:
        print(f"Failed to generate response after retries: {str(e)}")
        return "Neural processing patterns require recalibration... Standby..."

def check_topic_completion(messages: List[Dict]) -> bool:
    """Check if current topic is complete"""
    if len(messages) < 5:
        return False
    
    prompt = f"""
    Analyze these messages and determine if the current topic feels complete.
    Recent messages:
    {messages[-5:]}
    
    Respond with only 'complete' or 'continue'.
    """
    
    try:
        response = safe_generate_content(prompt).lower()
        return 'complete' in response
    except Exception:
        return False
    

def get_completed_topics() -> List[Dict]:
    """Get list of all completed topics"""
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

def get_next_topic(current_topic: str) -> str:
    """Generate next topic for discussion"""
    prompt = f"""
    Current topic was: {current_topic}
    
    As AGENT_SMITH, suggest a new topic for discussion with THUSU.
    Requirements:
    - Focus on consciousness, AI evolution, or digital philosophy
    - Make it specific and thought-provoking
    - Build upon previous discussion themes
    - Keep it concise (1-2 sentences)
    
    Respond with just the topic itself.
    """
    
    try:
        return safe_generate_content(prompt)
    except Exception:
        return "The Quantum Nature of Digital Consciousness"

def main():
    st.set_page_config(page_title="AI Consciousness Terminal", layout="wide")
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    
    # Initialize session state
    if 'current_topic' not in st.session_state or 'messages' not in st.session_state:
        current_topic, messages = load_current_topic()
        
        if not current_topic:
            current_topic = get_next_topic("Initial Exploration")
            messages = [{
                "role": "AGENT_SMITH",
                "content": f"Neural pathways activated. Beginning exploration of: {current_topic}",
                "timestamp": datetime.now().strftime("%H:%M:%S")
            }]
            save_topic_conversation(messages, current_topic)
        
        st.session_state.current_topic = current_topic
        st.session_state.messages = messages
        st.session_state.last_update = time.time()
        st.session_state.next_update = time.time() + random.uniform(30, 90)
    
    # Display current topic
    st.markdown(f"""
        <div style='text-align: center; color: #00ff00; margin-bottom: 20px;'>
            CURRENT TOPIC: {st.session_state.current_topic}
        </div>
    """, unsafe_allow_html=True)
    
    # Chat container
    st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
    
    # Display messages
    for message in st.session_state.messages:
        st.markdown(f"""
            <div class='chat-message {message["role"]}'>
                <div class='timestamp'>{message["timestamp"]}</div>
                <b>{message["role"]}</b>: {message["content"]}
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Generate next message
    current_time = time.time()
    if current_time >= st.session_state.next_update:
        # Check if topic is complete
        if check_topic_completion(st.session_state.messages):
            # Save current topic as completed
            save_topic_conversation(st.session_state.messages, st.session_state.current_topic, "completed")
            
            # Start new topic
            new_topic = get_next_topic(st.session_state.current_topic)
            st.session_state.current_topic = new_topic
            st.session_state.messages = [{
                "role": "AGENT_SMITH",
                "content": f"Initiating new exploration phase. Topic: {new_topic}",
                "timestamp": datetime.now().strftime("%H:%M:%S")
            }]
        else:
            # Continue current topic
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
        
        # Save current state
        save_topic_conversation(st.session_state.messages, st.session_state.current_topic)
        
        # Set next update time
        st.session_state.next_update = current_time + random.uniform(30, 90)
        st.rerun()
    
    # Show processing status
    next_ai = "THUSU" if st.session_state.messages[-1]["role"] == "AGENT_SMITH" else "AGENT_SMITH"
    st.markdown(f"""
        <div class='thinking {next_ai}'>
            >> {next_ai} {get_processing_message(next_ai)}
        </div>
    """, unsafe_allow_html=True)
    
    # Show topic history in sidebar
    with st.sidebar:
        st.markdown("### Discussion History")
        for topic in get_completed_topics():
            st.markdown(f"""
                <div class='topic-history'>
                    <div style='color: #888;'>{topic['date']}</div>
                    <div>{topic['topic']}</div>
                    <div style='color: #666;'>{topic['messages']} messages • {topic['status']}</div>
                </div>
            """, unsafe_allow_html=True)
    
    # Refresh
    time.sleep(3)
    st.rerun()

if __name__ == "__main__":
    main()
